"""Pure structural admission only. No estimator, cohort cache, IO or authority."""

import math
from dataclasses import dataclass, field, fields
from enum import StrEnum

from .contracts import (
    SOURCE_SCHEMA_DIGESTS,
    CycleIdentity,
    LateralTorqueIdentificationReceipt,
    ScalarObservation,
)
from .context import epoch_context
from .types import (
    CURRENT,
    RUNTIME,
    VERSION,
    AlignmentMethod,
    CallbackFamily,
    CallbackFunction,
    CallbackSite,
    CallbackStage,
    ClockDomain,
    ControllerMode,
    DelaySource,
    GeometryOrigin,
    Precision,
    ScalarOrigin,
    Signal,
    SourceOrigin,
    SourceRole,
    Stage,
    enum_value,
    require,
    sha,
)


class EligibilityStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"


class ObservationReason(StrEnum):
    UNSUPPORTED_RECEIPT_VERSION = "UNSUPPORTED_RECEIPT_VERSION"
    UNSUPPORTED_SOURCE_REVISION = "UNSUPPORTED_SOURCE_REVISION"
    SOURCE_SCHEMA_MISMATCH = "SOURCE_SCHEMA_MISMATCH"
    IDENTIFICATION_MODEL_UNSUPPORTED = "IDENTIFICATION_MODEL_UNSUPPORTED"
    WRONG_CALLBACK_STAGE = "WRONG_CALLBACK_STAGE"
    MODE_IDENTITY_INCOMPLETE = "MODE_IDENTITY_INCOMPLETE"
    MISSING_RAW_CALLBACK_OUTPUT = "MISSING_RAW_CALLBACK_OUTPUT"
    MISSING_Q = "MISSING_Q"
    MISSING_REQUIRED_SIGNAL = "MISSING_REQUIRED_SIGNAL"
    Q_NOT_INDEPENDENTLY_OBSERVED = "Q_NOT_INDEPENDENTLY_OBSERVED"
    RAW_PRECISION_UNAVAILABLE = "RAW_PRECISION_UNAVAILABLE"
    WRONG_SIGNAL_STAGE = "WRONG_SIGNAL_STAGE"
    NONLOCAL_SIGNAL_ORIGIN = "NONLOCAL_SIGNAL_ORIGIN"
    SOURCE_COHORT_INCOMPLETE = "SOURCE_COHORT_INCOMPLETE"
    SOURCE_TIMESTAMP_MISMATCH = "SOURCE_TIMESTAMP_MISMATCH"
    WRONG_CLOCK_DOMAIN = "WRONG_CLOCK_DOMAIN"
    TIME_ORDER_INVALID = "TIME_ORDER_INVALID"
    SOURCE_UNHEALTHY = "SOURCE_UNHEALTHY"
    GEOMETRY_CONTEXT_INCOMPLETE = "GEOMETRY_CONTEXT_INCOMPLETE"
    GEOMETRY_NOT_ACTUALLY_APPLIED = "GEOMETRY_NOT_ACTUALLY_APPLIED"
    GEOMETRY_CONTEXT_INCONSISTENT = "GEOMETRY_CONTEXT_INCONSISTENT"
    INSTALLED_CONTEXT_INCOMPLETE = "INSTALLED_CONTEXT_INCOMPLETE"
    MISSING_GAIN_COHORT = "MISSING_GAIN_COHORT"
    DELAY_CONTEXT_INCOMPLETE = "DELAY_CONTEXT_INCOMPLETE"
    DOUBLE_ALIGNMENT = "DOUBLE_ALIGNMENT"
    ALIGNMENT_METADATA_INCONSISTENT = "ALIGNMENT_METADATA_INCONSISTENT"
    ALIGNMENT_NOT_RAW_CALLBACK = "ALIGNMENT_NOT_RAW_CALLBACK"
    MISSING_LIMIT_STATE = "MISSING_LIMIT_STATE"
    DRIVER_OVERRIDE = "DRIVER_OVERRIDE"
    SATURATED = "SATURATED"
    CONTROLLER_LIMITED = "CONTROLLER_LIMITED"
    VEHICLE_ACTUATOR_LIMITED = "VEHICLE_ACTUATOR_LIMITED"
    CONTROLLER_INACTIVE = "CONTROLLER_INACTIVE"
    LINEAR_INPUT_INCONSISTENT = "LINEAR_INPUT_INCONSISTENT"
    CALLBACK_FLAG_INCONSISTENT = "CALLBACK_FLAG_INCONSISTENT"
    Q_SEMANTICS_INCONSISTENT = "Q_SEMANTICS_INCONSISTENT"
    FRICTION_INPUT_DOMAIN_INVALID = "FRICTION_INPUT_DOMAIN_INVALID"
    RAW_OUTPUT_INCONSISTENT = "RAW_OUTPUT_INCONSISTENT"
    MISSING_PID_DECOMPOSITION = "MISSING_PID_DECOMPOSITION"
    PID_STAGE_INCONSISTENT = "PID_STAGE_INCONSISTENT"
    DOWNSTREAM_COHORT_INCOMPLETE = "DOWNSTREAM_COHORT_INCOMPLETE"
    DUPLICATE_CONTROLLER_CYCLE = "DUPLICATE_CONTROLLER_CYCLE"
    MODE_CHANGED = "MODE_CHANGED"
    INSTALLED_PARAMETER_CONTEXT_CHANGED = "INSTALLED_PARAMETER_CONTEXT_CHANGED"
    GEOMETRY_CONTEXT_CHANGED = "GEOMETRY_CONTEXT_CHANGED"
    DELAY_CONTEXT_CHANGED = "DELAY_CONTEXT_CHANGED"
    EPOCH_CONTEXT_CHANGED = "EPOCH_CONTEXT_CHANGED"
    PREVIOUS_RECEIPT_NOT_ELIGIBLE = "PREVIOUS_RECEIPT_NOT_ELIGIBLE"


@dataclass(frozen=True, slots=True)
class ObservationPolicy:
    receipt_versions: tuple[str, ...] = (VERSION,)
    source_revisions: tuple[str, ...] = (RUNTIME, CURRENT)

    def __post_init__(self) -> None:
        versions, revisions = tuple(self.receipt_versions), tuple(self.source_revisions)
        require(bool(versions) and set(versions) == {VERSION}, "POLICY_VERSION")
        require(
            bool(revisions)
            and len(set(revisions)) == len(revisions)
            and set(revisions) <= {RUNTIME, CURRENT},
            "POLICY_SOURCE",
        )
        object.__setattr__(self, "receipt_versions", versions)
        object.__setattr__(self, "source_revisions", revisions)


@dataclass(frozen=True, slots=True)
class ObservationEligibilityDecision:
    status: EligibilityStatus
    reasons: tuple[ObservationReason, ...]
    receipt_digest: str
    epoch_digest: str
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    owner_proposal_allowed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        enum_value(self.status, EligibilityStatus)
        frozen = tuple(self.reasons)
        require(all(type(r) is ObservationReason for r in frozen), "DECISION_REASON")
        require(
            (self.status == EligibilityStatus.ELIGIBLE) == (len(frozen) == 0), "DECISION_STATUS"
        )
        sha(self.receipt_digest)
        sha(self.epoch_digest)
        object.__setattr__(self, "reasons", frozen)


def _equivalent(a: float, b: float) -> bool:
    # At most eight binary64 ulps for a few arithmetic operations, NOT a data/safety cutoff.
    return (
        math.isfinite(a)
        and math.isfinite(b)
        and abs(a - b) <= 8 * math.ulp(max(1.0, abs(a), abs(b)))
    )


def reconstruct_q_diagnostic(
    error: float, deadzone: float, threshold: float, enabled: bool
) -> float:
    """Diagnostic only: never supplies a missing q_observed or depends on C."""
    require(
        all(type(v) in (int, float) and math.isfinite(v) for v in (error, deadzone, threshold))
        and deadzone >= 0
        and threshold > 0
        and type(enabled) is bool,
        "FRICTION_INPUT_DOMAIN_INVALID",
    )
    if not enabled or -deadzone < error < deadzone:
        return 0.0
    return max(-1.0, min(1.0, error / threshold))


def _scalar(
    s: ScalarObservation | None,
    signal: Signal,
    stage: Stage,
    cycle: CycleIdentity,
    reasons: list[ObservationReason],
    *,
    optional: bool = False,
) -> float | None:
    R = ObservationReason
    if s is None or s.value is None:
        if not optional:
            reasons.append(
                R.MISSING_Q
                if signal == Signal.Q_OBSERVED
                else R.MISSING_RAW_CALLBACK_OUTPUT
                if signal == Signal.CALLBACK_OUTPUT
                else R.MISSING_REQUIRED_SIGNAL
            )
        return None
    if s.signal != signal or s.stage != stage:
        reasons.append(
            R.WRONG_CALLBACK_STAGE if signal == Signal.CALLBACK_OUTPUT else R.WRONG_SIGNAL_STAGE
        )
    if s.precision != Precision.BINARY64:
        reasons.append(R.RAW_PRECISION_UNAVAILABLE)
    expected_origin = (
        ScalarOrigin.HELPER_OBSERVED
        if signal == Signal.Q_OBSERVED
        else ScalarOrigin.DOWNSTREAM
        if optional
        else ScalarOrigin.LOCAL_DIRECT
    )
    if s.origin != expected_origin:
        reasons.append(
            R.Q_NOT_INDEPENDENTLY_OBSERVED
            if signal == Signal.Q_OBSERVED
            else R.NONLOCAL_SIGNAL_ORIGIN
        )
    if s.cycle_digest != cycle.digest or s.captured_mono_time_ns is None:
        reasons.append(R.SOURCE_COHORT_INCOMPLETE)
    else:
        lower = (
            cycle.callback_enter_mono_time_ns
            if stage in {Stage.CALLBACK_INPUT, Stage.HELPER_Q, Stage.RAW_CALLBACK}
            else cycle.callback_exit_mono_time_ns
        )
        upper = (
            cycle.callback_exit_mono_time_ns
            if stage in {Stage.CALLBACK_INPUT, Stage.HELPER_Q, Stage.RAW_CALLBACK}
            else cycle.receipt_complete_mono_time_ns
        )
        if not lower <= s.captured_mono_time_ns <= upper:
            reasons.append(R.TIME_ORDER_INVALID)
    return s.value


def _sources(receipt: LateralTorqueIdentificationReceipt, reasons: list[ObservationReason]) -> None:
    R = ObservationReason
    sources = {s.role: s for s in receipt.sources}
    required = {
        SourceRole.CAR_STATE,
        SourceRole.LIVE_POSE,
        SourceRole.LIVE_PARAMETERS,
        SourceRole.CAR_CONTROL,
    }
    if not required <= sources.keys() or receipt.consumption_manifest_complete is not True:
        reasons.append(R.SOURCE_COHORT_INCOMPLETE)
    for source in receipt.sources:
        if source.consumed is None or (
            source.role
            in {SourceRole.CAR_STATE, SourceRole.LIVE_PARAMETERS, SourceRole.CAR_CONTROL}
            and not source.consumed
        ):
            reasons.append(R.SOURCE_COHORT_INCOMPLETE)
        if source.consumed:
            if (
                source.source_time_ns is None
                or (source.sequence is None and source.source_identity is None)
                or source.origin == SourceOrigin.UNKNOWN
            ):
                reasons.append(R.SOURCE_COHORT_INCOMPLETE)
            if source.clock_domain != ClockDomain.MONOTONIC:
                reasons.append(R.WRONG_CLOCK_DOMAIN)
            if (
                source.source_time_ns is not None
                and source.source_time_ns > receipt.cycle.context_capture_mono_time_ns
            ):
                reasons.append(R.TIME_ORDER_INVALID)
            if source.valid is not True or source.alive is not True:
                reasons.append(R.SOURCE_UNHEALTHY)


def _context(receipt: LateralTorqueIdentificationReceipt, reasons: list[ObservationReason]) -> None:
    R = ObservationReason
    ctx, cycle = receipt.context, receipt.cycle
    if (
        ctx.cycle_digest != cycle.digest
        or ctx.snapshot_time_ns != cycle.context_capture_mono_time_ns
    ):
        reasons.append(R.SOURCE_COHORT_INCOMPLETE)
    installed, gains, geom, delay = ctx.installed, ctx.gains, ctx.geometry, ctx.delay
    if (
        installed is None
        or installed.generation != cycle.installed_parameter_generation
        or installed.factor_installed is None
        or installed.friction_installed is None
        or installed.custom_selector is None
        or installed.precision != Precision.BINARY64
    ):
        reasons.append(R.INSTALLED_CONTEXT_INCOMPLETE)
    else:
        if receipt.controller_mode == ControllerMode.UNKNOWN or (
            (receipt.controller_mode == ControllerMode.CUSTOM) != (installed.custom_selector > 0)
        ):
            reasons.append(R.MODE_IDENTITY_INCOMPLETE)
    if (
        gains is None
        or gains.generation != cycle.installed_parameter_generation
        or any(getattr(gains, name) is None for name in ("k_p", "k_i", "k_d", "k_f"))
        or gains.precision != Precision.BINARY64
    ):
        reasons.append(R.MISSING_GAIN_COHORT)
    geometry_fields = (
        "source_revision",
        "vehicle_context_digest",
        "generation",
        "applied_vm_context_id",
        "wheelbase",
        "center_to_front",
        "center_to_front_ratio",
        "stiffness_factor",
        "effective_steer_ratio",
        "steer_ratio_rate_raw",
        "steer_ratio_rate_effective",
        "custom_sr_raw",
        "custom_sr_effective",
    )
    if (
        geom is None
        or any(getattr(geom, name) is None for name in geometry_fields)
        or geom.precision != Precision.BINARY64
    ):
        reasons.append(R.GEOMETRY_CONTEXT_INCOMPLETE)
    else:
        if (
            geom.generation != cycle.geometry_generation
            or geom.source_revision != cycle.source_revision
            or geom.vehicle_context_digest != cycle.vehicle_context_digest
        ):
            reasons.append(R.GEOMETRY_CONTEXT_INCOMPLETE)
        expected = (
            GeometryOrigin.STATIC_CP
            if cycle.source_revision == RUNTIME
            else GeometryOrigin.APPLIED_VM
        )
        if geom.origin != expected:
            reasons.append(R.GEOMETRY_NOT_ACTUALLY_APPLIED)
        assert (
            geom.wheelbase is not None
            and geom.center_to_front is not None
            and geom.center_to_front_ratio is not None
        )
        assert geom.stiffness_factor is not None and geom.effective_steer_ratio is not None
        if not (
            0 < geom.center_to_front < geom.wheelbase
            and 0 < geom.center_to_front_ratio < 1
            and geom.stiffness_factor > 0
            and geom.effective_steer_ratio > 0
            and _equivalent(geom.center_to_front, geom.wheelbase * geom.center_to_front_ratio)
        ):
            reasons.append(R.GEOMETRY_CONTEXT_INCONSISTENT)
    if (
        delay is None
        or delay.effective_delay_s is None
        or delay.effective_delay_s < 0
        or delay.source == DelaySource.UNAVAILABLE
        or delay.alignment_method == AlignmentMethod.UNKNOWN
        or delay.alignment_version is None
        or delay.correction_count is None
        or delay.values_already_aligned is None
    ):
        reasons.append(R.DELAY_CONTEXT_INCOMPLETE)
    else:
        if delay.correction_count > 1:
            reasons.append(R.DOUBLE_ALIGNMENT)
        if delay.alignment_method == AlignmentMethod.NONE:
            if (
                delay.correction_count != 0
                or delay.sample_pair_id is not None
                or delay.values_already_aligned
            ):
                reasons.append(R.ALIGNMENT_METADATA_INCONSISTENT)
        elif delay.alignment_method == AlignmentMethod.SINGLE_DOWNSTREAM_PAIR:
            if (
                delay.correction_count != 1
                or delay.sample_pair_id is None
                or delay.values_already_aligned
            ):
                reasons.append(R.ALIGNMENT_METADATA_INCONSISTENT)
        else:
            reasons.append(R.ALIGNMENT_NOT_RAW_CALLBACK)


def _limits(receipt: LateralTorqueIdentificationReceipt, reasons: list[ObservationReason]) -> None:
    R = ObservationReason
    limits = receipt.limits
    if any(getattr(limits, f.name) is None for f in fields(limits)):
        reasons.append(R.MISSING_LIMIT_STATE)
    if limits.source_healthy is False:
        reasons.append(R.SOURCE_UNHEALTHY)
    if limits.controller_active is False:
        reasons.append(R.CONTROLLER_INACTIVE)
    if limits.steering_pressed or limits.driver_override:
        reasons.append(R.DRIVER_OVERRIDE)
    if limits.timer_saturated:
        reasons.append(R.SATURATED)
    if (
        limits.instantaneous_controller_limited
        or limits.curvature_limited
        or limits.steer_limited_by_controls
    ):
        reasons.append(R.CONTROLLER_LIMITED)
    if limits.vehicle_actuator_limited:
        reasons.append(R.VEHICLE_ACTUATOR_LIMITED)


def _linear(receipt: LateralTorqueIdentificationReceipt, reasons: list[ObservationReason]) -> None:
    R = ObservationReason
    values = {
        signal: _scalar(
            getattr(receipt.signals, signal.value),
            signal,
            Stage.HELPER_Q if signal == Signal.Q_OBSERVED else Stage.CALLBACK_INPUT,
            receipt.cycle,
            reasons,
        )
        for signal in (
            Signal.DESIRED_ACCEL,
            Signal.ACTUAL_ACCEL,
            Signal.ROLL,
            Signal.ROLL_COMPENSATION,
            Signal.CALLBACK_ACCEL,
            Signal.FRICTION_INPUT,
            Signal.DEADZONE,
            Signal.THRESHOLD,
            Signal.Q_OBSERVED,
        )
    }
    raw = _scalar(
        receipt.stages.callback_output_raw,
        Signal.CALLBACK_OUTPUT,
        Stage.RAW_CALLBACK,
        receipt.cycle,
        reasons,
    )
    enabled = receipt.signals.friction_compensation_enabled
    if enabled is not True or receipt.signals.gravity_adjusted is not True:
        reasons.append(R.CALLBACK_FLAG_INCONSISTENT)
    if all(v is not None for v in values.values()) and enabled is not None:
        desired, actual, roll, rc, a, error, deadzone, threshold, observed_q = (
            values[s]
            for s in (
                Signal.DESIRED_ACCEL,
                Signal.ACTUAL_ACCEL,
                Signal.ROLL,
                Signal.ROLL_COMPENSATION,
                Signal.CALLBACK_ACCEL,
                Signal.FRICTION_INPUT,
                Signal.DEADZONE,
                Signal.THRESHOLD,
                Signal.Q_OBSERVED,
            )
        )
        assert (
            desired is not None
            and actual is not None
            and roll is not None
            and rc is not None
            and a is not None
            and error is not None
            and deadzone is not None
            and threshold is not None
            and observed_q is not None
        )
        if not (
            _equivalent(a, desired - rc)
            and _equivalent(error, desired - actual)
            and _equivalent(rc, roll * 9.81)
        ):
            reasons.append(R.LINEAR_INPUT_INCONSISTENT)
        if deadzone < 0 or threshold <= 0 or not _equivalent(threshold, 0.3):
            reasons.append(R.FRICTION_INPUT_DOMAIN_INVALID)
        else:
            reconstructed = reconstruct_q_diagnostic(error, deadzone, threshold, enabled)
            if not _equivalent(observed_q, reconstructed):
                reasons.append(R.Q_SEMANTICS_INCONSISTENT)
        installed = receipt.context.installed
        if (
            raw is not None
            and installed is not None
            and installed.factor_installed is not None
            and installed.friction_installed is not None
        ):
            if installed.factor_installed == 0:
                reasons.append(R.FRICTION_INPUT_DOMAIN_INVALID)
            elif not _equivalent(
                raw, a / installed.factor_installed + installed.friction_installed * observed_q
            ):
                reasons.append(R.RAW_OUTPUT_INCONSISTENT)
    pid = {}
    for signal, stage in (
        (Signal.PID_P, Stage.PID_P),
        (Signal.PID_I, Stage.PID_I),
        (Signal.PID_D, Stage.PID_D),
        (Signal.PID_F, Stage.PID_F),
        (Signal.PID_SUM, Stage.PID_SUM),
        (Signal.PID_OUTPUT, Stage.PID_CLIPPED),
    ):
        pid[signal] = _scalar(
            getattr(receipt.stages, signal.value), signal, stage, receipt.cycle, reasons
        )
    if any(v is None for v in pid.values()):
        reasons.append(R.MISSING_PID_DECOMPOSITION)
    else:
        p, i, d, f, total, output = (
            pid[s]
            for s in (
                Signal.PID_P,
                Signal.PID_I,
                Signal.PID_D,
                Signal.PID_F,
                Signal.PID_SUM,
                Signal.PID_OUTPUT,
            )
        )
        assert (
            p is not None
            and i is not None
            and d is not None
            and f is not None
            and total is not None
            and output is not None
        )
        gains = receipt.context.gains
        if (
            not _equivalent(p + i + d + f, total)
            or (
                receipt.limits.instantaneous_controller_limited is False
                and not _equivalent(output, total)
            )
            or (
                raw is not None
                and gains is not None
                and gains.k_f is not None
                and not _equivalent(f, raw * gains.k_f)
            )
        ):
            reasons.append(R.PID_STAGE_INCONSISTENT)
    for signal, stage in (
        (Signal.REQUESTED_TORQUE, Stage.REQUESTED_TORQUE),
        (Signal.HOST_OUTPUT, Stage.HOST_OUTPUT),
        (Signal.APPLIED_TORQUE, Stage.APPLIED_TORQUE),
    ):
        value = _scalar(
            getattr(receipt.stages, signal.value),
            signal,
            stage,
            receipt.cycle,
            reasons,
            optional=True,
        )
        if value is not None and receipt.stages.downstream_cycle_id != receipt.cycle.digest:
            reasons.append(R.DOWNSTREAM_COHORT_INCOMPLETE)
        pid_output = pid[Signal.PID_OUTPUT]
        if signal == Signal.REQUESTED_TORQUE and value is not None and pid_output is not None:
            if not _equivalent(value, -pid_output):
                reasons.append(R.PID_STAGE_INCONSISTENT)


def _previous(
    receipt: LateralTorqueIdentificationReceipt,
    previous: LateralTorqueIdentificationReceipt,
    policy: ObservationPolicy,
    reasons: list[ObservationReason],
) -> None:
    R = ObservationReason
    if evaluate(previous, policy).status != EligibilityStatus.ELIGIBLE:
        reasons.append(R.PREVIOUS_RECEIPT_NOT_ELIGIBLE)
    same_instance = (
        receipt.cycle.session_id == previous.cycle.session_id
        and receipt.cycle.controller_instance_generation
        == previous.cycle.controller_instance_generation
    )
    if same_instance and receipt.cycle.controller_cycle_id == previous.cycle.controller_cycle_id:
        reasons.append(R.DUPLICATE_CONTROLLER_CYCLE)
    if same_instance and (
        receipt.cycle.controller_cycle_id < previous.cycle.controller_cycle_id
        or receipt.cycle.control_event_mono_time_ns <= previous.cycle.control_event_mono_time_ns
    ):
        reasons.append(R.TIME_ORDER_INVALID)
    before_context, after_context = epoch_context(previous.context), epoch_context(receipt.context)
    for name, reason in (
        ("geometry", R.GEOMETRY_CONTEXT_CHANGED),
        ("installed", R.INSTALLED_PARAMETER_CONTEXT_CHANGED),
        ("gains", R.INSTALLED_PARAMETER_CONTEXT_CHANGED),
        ("delay", R.DELAY_CONTEXT_CHANGED),
    ):
        if before_context[name] != after_context[name]:
            reasons.append(reason)
    if (
        receipt.callback_family,
        receipt.callback_stage,
        receipt.controller_mode,
        receipt.callback_function,
        receipt.callback_site,
    ) != (
        previous.callback_family,
        previous.callback_stage,
        previous.controller_mode,
        previous.callback_function,
        previous.callback_site,
    ):
        reasons.append(R.MODE_CHANGED)
    if receipt.epoch_digest != previous.epoch_digest:
        reasons.append(R.EPOCH_CONTEXT_CHANGED)
    prior_sources = {
        s.source_identity: s for s in previous.sources if s.source_identity is not None
    }
    prior_sequences = {(s.role, s.sequence): s for s in previous.sources if s.sequence is not None}
    for source in receipt.sources:
        before_source = (
            prior_sources.get(source.source_identity)
            if source.source_identity is not None
            else None
        )
        if before_source is not None and any(
            getattr(before_source, name) != getattr(source, name)
            for name in ("role", "source_time_ns", "sequence", "clock_domain", "origin")
        ):
            reasons.append(R.SOURCE_TIMESTAMP_MISMATCH)
        before_sequence = (
            prior_sequences.get((source.role, source.sequence))
            if source.sequence is not None
            else None
        )
        if before_sequence is not None and any(
            getattr(before_sequence, name) != getattr(source, name)
            for name in ("source_time_ns", "clock_domain", "origin", "source_identity")
        ):
            reasons.append(R.SOURCE_TIMESTAMP_MISMATCH)


def evaluate(
    receipt: LateralTorqueIdentificationReceipt,
    policy: ObservationPolicy,
    *,
    previous: LateralTorqueIdentificationReceipt | None = None,
) -> ObservationEligibilityDecision:
    require(
        type(receipt) is LateralTorqueIdentificationReceipt
        and type(policy) is ObservationPolicy
        and (previous is None or type(previous) is LateralTorqueIdentificationReceipt),
        "EVALUATOR_INPUT",
    )
    R = ObservationReason
    reasons: list[ObservationReason] = []
    cycle = receipt.cycle
    if receipt.receipt_schema_version not in policy.receipt_versions:
        reasons.append(R.UNSUPPORTED_RECEIPT_VERSION)
    if cycle.source_revision not in policy.source_revisions:
        reasons.append(R.UNSUPPORTED_SOURCE_REVISION)
    if (cycle.source_revision, cycle.source_schema_digest) not in SOURCE_SCHEMA_DIGESTS:
        reasons.append(R.SOURCE_SCHEMA_MISMATCH)
    if cycle.clock_domain != ClockDomain.MONOTONIC:
        reasons.append(R.WRONG_CLOCK_DOMAIN)
    if (
        not cycle.context_capture_mono_time_ns
        <= cycle.callback_enter_mono_time_ns
        <= cycle.callback_exit_mono_time_ns
        <= cycle.control_event_mono_time_ns
        <= cycle.receipt_complete_mono_time_ns
    ):
        reasons.append(R.TIME_ORDER_INVALID)
    if (
        receipt.callback_stage != CallbackStage.LINEAR_CALLBACK_PRE_PID
        or receipt.callback_family != CallbackFamily.LINEAR
        or receipt.callback_function != CallbackFunction.BASE_LINEAR
    ):
        reasons.append(R.IDENTIFICATION_MODEL_UNSUPPORTED)
    if receipt.callback_site != CallbackSite.FEEDFORWARD:
        reasons.append(R.WRONG_CALLBACK_STAGE)
    _sources(receipt, reasons)
    _context(receipt, reasons)
    _limits(receipt, reasons)
    _linear(receipt, reasons)
    if previous is not None:
        _previous(receipt, previous, policy, reasons)
    unique = tuple(dict.fromkeys(reasons))
    return ObservationEligibilityDecision(
        EligibilityStatus.REJECTED if unique else EligibilityStatus.ELIGIBLE,
        unique,
        receipt.digest,
        receipt.epoch_digest,
    )
