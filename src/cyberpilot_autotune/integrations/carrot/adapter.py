"""Caller-driven read-only extraction state machine; outputs MappingDecision only."""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from cyberpilot_autotune.adapters.carrot_receipt_contract import (
    CarrotSnapshotPolicy,
    MappingAttempt,
    MappingDecision,
    MappingReason,
    ReceiptEvidence,
    SourceCarStateEvidence,
    SourceCommandEvidence,
    StaticVehicleContext,
    TimestampEvidence,
    evaluate,
)
from cyberpilot_autotune.contracts.validation import parameters

from .availability import INTEGRATION_MERGE, SCHEMA_REVISION, SOURCE_REVISION, require_schema
from .cache import CacheMetrics, ExactCache, capacity
from .errors import CarrotInputError, CarrotSessionRequired
from .extraction import (
    DecodedTopicSample,
    extract_car_control,
    extract_car_output,
    extract_car_state,
)
from .health import SessionToken, uint64

# Pinned Hyundai source flags, not controller limits or inferred fingerprints.
HYUNDAI_CANFD_FLAG = 8192
HYUNDAI_PLATFORM_FLAGS = (("HYUNDAI_SANTA_FE_2022", 65536), ("HYUNDAI_IONIQ_5", 10240))


@dataclass(frozen=True, slots=True)
class CachePolicy:
    maximum_car_control_entries: int
    maximum_car_state_entries: int
    maximum_consumed_cohorts: int

    def __post_init__(self) -> None:
        for value in (
            self.maximum_car_control_entries,
            self.maximum_car_state_entries,
            self.maximum_consumed_cohorts,
        ):
            capacity(value)


@dataclass(frozen=True, slots=True)
class SteeringPressedCapability:
    producer_path: str
    producer_symbol: str
    source_revision: str

    def supports(self, context: StaticVehicleContext, *, platform_key: str | None = None) -> bool:
        if self.source_revision != SOURCE_REVISION:
            return False
        if context.brand == "tesla":
            return (
                self.producer_path == "opendbc_repo/opendbc/car/tesla/carstate.py"
                and self.producer_symbol == "CarState.update"
            )
        if context.brand == "volkswagen" and context.controller_kind == "mebCurvature":
            return (
                self.producer_path == "opendbc_repo/opendbc/car/volkswagen/carstate.py"
                and self.producer_symbol == "CarState.update_meb"
            )
        if context.brand == "hyundai":
            required = next(
                (flags for key, flags in HYUNDAI_PLATFORM_FLAGS if key == platform_key), None
            )
            if required is None or context.flags & required != required:
                return False
            canfd = bool(context.flags & HYUNDAI_CANFD_FLAG)
            if canfd != bool(required & HYUNDAI_CANFD_FLAG):
                return False
            return (
                self.producer_path == "opendbc_repo/opendbc/car/hyundai/carstate.py"
                and self.producer_symbol
                == ("CarState.update_canfd" if canfd else "CarState.update")
            )
        return False


@dataclass(frozen=True, slots=True)
class ProducerAttestation:
    source_revision: str
    integration_merge: str
    observation_schema_revision: str
    static_context_digest: str
    baseline_epoch: int
    session: SessionToken
    permitted_controller_kinds: tuple[str, ...]
    steering_pressed_capability: SteeringPressedCapability | None
    platform_key: str | None = None

    def __post_init__(self) -> None:
        if self.platform_key is not None and (
            type(self.platform_key) is not str
            or self.platform_key not in tuple(key for key, _ in HYUNDAI_PLATFORM_FLAGS)
        ):
            raise CarrotInputError("UNQUALIFIED_PLATFORM_ATTESTATION")
        if (
            self.source_revision != SOURCE_REVISION
            or self.integration_merge != INTEGRATION_MERGE
            or self.observation_schema_revision != SCHEMA_REVISION
            or type(self.session) is not SessionToken
        ):
            raise CarrotInputError("UNQUALIFIED_SOURCE_ATTESTATION")
        object.__setattr__(
            self, "permitted_controller_kinds", tuple(self.permitted_controller_kinds)
        )


@dataclass(frozen=True, slots=True)
class AdapterConfig:
    static_context: StaticVehicleContext
    snapshot_policy: CarrotSnapshotPolicy
    baseline_parameters: Mapping[str, float]
    cache_policy: CachePolicy
    attestation: ProducerAttestation

    def __post_init__(self) -> None:
        # Copy/revalidate caller configuration; never read actual CarParams or Params.
        context, policy = replace(self.static_context), replace(self.snapshot_policy)
        attestation = replace(self.attestation)
        cache_policy = replace(self.cache_policy)
        if (
            context.digest != policy.static_context_digest
            or context.digest != attestation.static_context_digest
            or type(attestation.baseline_epoch) is not int
            or attestation.baseline_epoch != policy.baseline_epoch
            or attestation.observation_schema_revision != context.observation_schema_revision
            or context.controller_kind not in attestation.permitted_controller_kinds
            or attestation.permitted_controller_kinds != policy.allowed_controller_kinds
            or (attestation.platform_key is not None and context.brand != "hyundai")
        ):
            raise CarrotInputError("INCONSISTENT_CALLER_CONTEXT")
        object.__setattr__(self, "static_context", context)
        object.__setattr__(self, "snapshot_policy", policy)
        object.__setattr__(self, "attestation", attestation)
        object.__setattr__(self, "cache_policy", cache_policy)
        object.__setattr__(self, "baseline_parameters", parameters(self.baseline_parameters))


class CarrotReadOnlyAdapter:
    def __init__(self, config: AdapterConfig) -> None:
        self._config = replace(config)
        self._binding = require_schema()
        self._initialize_state()

    def _initialize_state(self) -> None:
        policy = self._config.cache_policy
        self._commands: ExactCache[SourceCommandEvidence] = ExactCache(
            policy.maximum_car_control_entries
        )
        self._states: ExactCache[SourceCarStateEvidence] = ExactCache(
            policy.maximum_car_state_entries
        )
        self._consumed: dict[tuple[int, int], None] = {}
        self._topic_high_water: dict[str, int] = {}
        self._next_sequence = 0
        self._previous_host_apply_ns: int | None = None
        self._session_required = False

    @property
    def next_sequence(self) -> int:
        return self._next_sequence

    @property
    def cache_metrics(self) -> tuple[CacheMetrics, CacheMetrics]:
        """Frozen observations only; never expose cache entries or alter admission."""
        return self._commands.metrics, self._states.metrics

    @property
    def previous_host_apply_ns(self) -> int | None:
        return self._previous_host_apply_ns

    @property
    def session_required(self) -> bool:
        return self._session_required

    def producer_restarted(self) -> None:
        """Explicit caller observation; no restart detection or automatic recovery."""
        self._session_required = True

    def reset_session(self, config: AdapterConfig) -> None:
        candidate = replace(config)
        previous = self._config.attestation.session
        current = candidate.attestation.session
        if current.generation <= previous.generation or current.token == previous.token:
            raise CarrotInputError("SESSION_RESET_MUST_ADVANCE")
        self._config = candidate
        self._initialize_state()

    def _identity(self, sample: DecodedTopicSample, topic: str) -> None:
        if type(sample) is not DecodedTopicSample or sample.topic != topic:
            raise CarrotInputError("WRONG_TOPIC")
        if sample.session_token != self._config.attestation.session:
            raise CarrotInputError("SESSION_TAG_MISMATCH")

    def _sample(self, sample: DecodedTopicSample, topic: str) -> bool:
        self._identity(sample, topic)
        if self._session_required:
            raise CarrotSessionRequired()
        timestamp = uint64(sample.log_mono_time_ns)
        previous = self._topic_high_water.get(topic)
        if previous is not None and timestamp < previous:
            self._session_required = True
            raise CarrotSessionRequired()
        self._topic_high_water[topic] = timestamp
        return timestamp == previous

    def ingest_car_control(self, sample: DecodedTopicSample) -> None:
        self._sample(sample, "carControl")
        try:
            source = extract_car_control(
                sample,
                self._binding,
                static_context_digest=self._config.attestation.static_context_digest,
            )
        except CarrotInputError:
            self._commands.poison(sample.log_mono_time_ns)
            raise
        if (
            source.controller_kind in ("pid", "torque", "angle", "mebCurvature")
            and source.controller_kind != self._config.static_context.controller_kind
        ):
            self._session_required = True
            raise CarrotSessionRequired()
        self._commands.put(sample.log_mono_time_ns, source, sample.transport_health)

    def ingest_car_state(self, sample: DecodedTopicSample) -> None:
        self._sample(sample, "carState")
        capability = self._config.attestation.steering_pressed_capability
        supported = (
            sample.transport_health.healthy
            and sample.event_valid is True
            and capability is not None
            and capability.supports(
                self._config.static_context, platform_key=self._config.attestation.platform_key
            )
        )
        try:
            source = extract_car_state(sample, self._binding, steering_pressed_supported=supported)
        except CarrotInputError:
            self._states.poison(sample.log_mono_time_ns)
            raise
        self._states.put(sample.log_mono_time_ns, source, sample.transport_health)

    @staticmethod
    def _cohort(receipt: ReceiptEvidence) -> tuple[int, int] | None:
        if (
            receipt.source_command_time.domain != "monotonic"
            or receipt.host_apply_time.domain != "monotonic"
        ):
            return None
        try:
            return uint64(receipt.source_command_time.value_ns), uint64(
                receipt.host_apply_time.value_ns
            )
        except CarrotInputError:
            return None

    def _consume(self, cohort: tuple[int, int] | None) -> None:
        if cohort is not None:
            self._consumed[cohort] = None
            if len(self._consumed) > self._config.cache_policy.maximum_consumed_cohorts:
                del self._consumed[next(iter(self._consumed))]

    def _attestation_failure(
        self,
        receipt: ReceiptEvidence,
        command: SourceCommandEvidence | None,
        publication_ns: int,
    ) -> MappingReason | None:
        """Known producer faults cannot be hidden by another admission failure."""
        if receipt.version not in (0, 1):
            return MappingReason.UNSUPPORTED_VERSION
        kinds = ("pid", "torque", "angle", "mebCurvature")
        if (
            receipt.controller_kind in kinds
            and receipt.controller_kind != self._config.static_context.controller_kind
        ):
            return MappingReason.CONTROLLER_MISMATCH
        clocks: tuple[tuple[TimestampEvidence, str], ...] = (
            (receipt.source_command_time, "monotonic"),
            (receipt.host_apply_time, "monotonic"),
            (receipt.safety_state_time, "bootTime"),
            (receipt.safety_observation_time, "bootTime"),
        )
        pairs: tuple[tuple[TimestampEvidence, TimestampEvidence, str], ...] = (
            (receipt.source_command_time, receipt.host_apply_time, "monotonic"),
            (receipt.safety_state_time, receipt.safety_observation_time, "bootTime"),
        )
        if type(publication_ns) is int and publication_ns > 0:
            pairs += (
                (
                    receipt.host_apply_time,
                    TimestampEvidence(publication_ns, "monotonic"),
                    "monotonic",
                ),
            )
        if command is not None:
            m = command.measurement
            if command.observation_version not in (0, 1, 2) or m.version not in (0, 1):
                return MappingReason.UNSUPPORTED_VERSION
            clocks += (
                (command.event_time, "monotonic"),
                (m.car_state_time, "monotonic"),
                (m.live_parameters_time, "monotonic"),
                (m.calculation_time, "monotonic"),
            )
            pairs += (
                (m.car_state_time, m.calculation_time, "monotonic"),
                (m.live_parameters_time, m.calculation_time, "monotonic"),
                (m.calculation_time, command.event_time, "monotonic"),
                (command.event_time, receipt.host_apply_time, "monotonic"),
            )
        if any(stamp.value_ns is not None and stamp.domain != domain for stamp, domain in clocks):
            return MappingReason.CLOCK_DOMAIN
        # Only version 0's absent/default receipt is a normal startup exception.
        if receipt.version == 1 and self._cohort(receipt) is None:
            return MappingReason.MISSING_TIMESTAMP
        if any(
            left.value_ns is not None
            and right.value_ns is not None
            and left.domain == right.domain == domain
            and left.value_ns > right.value_ns
            for left, right, domain in pairs
        ):
            return MappingReason.TIME_ORDER
        return None

    def evaluate_car_output(
        self, sample: DecodedTopicSample, *, evaluation_mono_time_ns: int
    ) -> MappingDecision:
        sequence = self._next_sequence
        self._next_sequence += 1
        previous_apply = self._previous_host_apply_ns
        previous_cohorts = tuple(self._consumed)
        cohort = None
        try:
            self._identity(sample, "carOutput")
            sample_error = None
            try:
                duplicate_publication = self._sample(sample, "carOutput")
            except CarrotInputError as exc:
                # Still consume any readable cohort before reporting this failure.
                sample_error = exc
                duplicate_publication = False
            try:
                receipt = extract_car_output(sample, self._binding)
            except CarrotInputError:
                # No safe cohort identity can be recovered from malformed data.
                # Explicit new-session reset is required, never repaired input.
                self._session_required = True
                raise
            cohort = self._cohort(receipt)
            self._consume(cohort)
            apply = receipt.host_apply_time
            host = None
            if apply.domain == "monotonic" and apply.value_ns is not None:
                host = uint64(apply.value_ns)
                # A readable same-session attempt is consumed before later
                # sample/evaluation-clock/health checks can reject it.
                self._previous_host_apply_ns = max(host, previous_apply or host)
                if previous_apply is not None and host < previous_apply:
                    # A known producer-clock regression cannot be hidden by a
                    # malformed evaluation argument or a later admission exit.
                    self._session_required = True
            command_entry = self._commands.lookup(receipt.source_command_time.value_ns)
            fault = self._attestation_failure(
                receipt, command_entry.evidence if command_entry else None, sample.log_mono_time_ns
            )
            if fault is not None:
                self._session_required = True
                return MappingDecision(None, fault, cohort)
            if sample_error is not None:
                raise sample_error
            now = uint64(evaluation_mono_time_ns)
            if host is not None:
                if host > sample.log_mono_time_ns or sample.log_mono_time_ns > now:
                    self._session_required = True
                    return MappingDecision(None, MappingReason.TIME_ORDER, cohort)
            if duplicate_publication:
                return MappingDecision(None, MappingReason.DUPLICATE_COHORT, cohort)
            command = (
                command_entry.evidence
                if command_entry is not None and command_entry.health.healthy
                else None
            )
            state_entry = (
                self._states.lookup(command.measurement.car_state_time.value_ns)
                if command
                else None
            )
            source_cs = (
                state_entry.evidence
                if state_entry is not None and state_entry.health.healthy
                else None
            )
            attempt = MappingAttempt(
                receipt=receipt,
                source_command=command,
                source_car_state=source_cs,
                static_context=self._config.static_context,
                baseline_parameters=self._config.baseline_parameters,
                baseline_epoch=self._config.attestation.baseline_epoch,
                evaluation_time=TimestampEvidence(now, "monotonic"),
                sequence=sequence,
                previous_sequence=sequence - 1 if sequence else None,
                previous_host_apply_ns=previous_apply,
                consumed_cohorts=previous_cohorts,
                exact_lookup_unambiguous=not self._commands.is_ambiguous(
                    receipt.source_command_time.value_ns
                ),
                car_output_transport_healthy=sample.transport_health.healthy,
                outer_car_output_valid=sample.event_valid,
            )
            decision = evaluate(
                attempt, self._config.snapshot_policy, self._config.baseline_parameters
            )
            if decision.reason is MappingReason.TIME_ORDER:
                self._session_required = True
            return decision
        except CarrotSessionRequired:
            return MappingDecision(None, MappingReason.OUT_OF_ORDER, cohort)
        except Exception:
            # Sequence/publication/cohort consumption is intentionally not rolled back.
            return MappingDecision(None, MappingReason.INVALID_INPUT, cohort)
