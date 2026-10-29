"""Neutral evidence records, with distinct per-value stage/precision provenance."""

from dataclasses import asdict, dataclass, fields

from .context import FrictionObservationContext, epoch_context
from .types import (
    CURRENT,
    RUNTIME,
    VERSION,
    CallbackFamily,
    CallbackFunction,
    CallbackSite,
    CallbackStage,
    ClockDomain,
    ControllerMode,
    Precision,
    ScalarOrigin,
    Signal,
    SourceOrigin,
    SourceRole,
    Stage,
    boolean,
    digest,
    enum_value,
    real,
    require,
    sha,
    token,
    uint64,
)

SOURCE_SCHEMA_DIGESTS = (
    (RUNTIME, "7d5c19cc2a534fb6918ba51d393eff288f096b68b6c13fd5608c46d17454ba35"),
    (CURRENT, "0d546ea5f37bc26a16f71ae0433a9a617728c78d77de872c1d327a10cf0fe1db"),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CycleIdentity:
    session_id: str
    controller_cycle_id: int
    context_capture_mono_time_ns: int
    callback_enter_mono_time_ns: int
    callback_exit_mono_time_ns: int
    control_event_mono_time_ns: int
    receipt_complete_mono_time_ns: int
    source_revision: str
    source_schema_digest: str
    vehicle_context_digest: str
    controller_instance_generation: int
    installed_parameter_generation: int
    geometry_generation: int
    callback_invocation_index: int
    clock_domain: ClockDomain

    def __post_init__(self) -> None:
        sha(self.session_id)
        sha(self.source_revision, 40)
        sha(self.source_schema_digest)
        sha(self.vehicle_context_digest)
        enum_value(self.clock_domain, ClockDomain)
        for item in fields(self):
            if item.name not in {
                "session_id",
                "source_revision",
                "source_schema_digest",
                "vehicle_context_digest",
                "clock_domain",
            }:
                uint64(getattr(self, item.name))

    @property
    def digest(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class ConsumedSourceIdentity:
    role: SourceRole
    source_time_ns: int | None = None
    clock_domain: ClockDomain = ClockDomain.UNKNOWN
    sequence: int | None = None
    source_identity: str | None = None
    consumed: bool | None = None
    valid: bool | None = None
    alive: bool | None = None
    origin: SourceOrigin = SourceOrigin.UNKNOWN

    def __post_init__(self) -> None:
        enum_value(self.role, SourceRole)
        enum_value(self.clock_domain, ClockDomain)
        enum_value(self.origin, SourceOrigin)
        uint64(self.source_time_ns, optional=True)
        uint64(self.sequence, optional=True)
        sha(self.source_identity, optional=True)
        for value in (self.consumed, self.valid, self.alive):
            boolean(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScalarObservation:
    signal: Signal
    stage: Stage
    value: float | None = None
    precision: Precision = Precision.UNKNOWN
    origin: ScalarOrigin = ScalarOrigin.UNAVAILABLE
    cycle_digest: str | None = None
    captured_mono_time_ns: int | None = None

    def __post_init__(self) -> None:
        enum_value(self.signal, Signal)
        enum_value(self.stage, Stage)
        enum_value(self.precision, Precision)
        enum_value(self.origin, ScalarOrigin)
        object.__setattr__(self, "value", real(self.value))
        sha(self.cycle_digest, optional=True)
        uint64(self.captured_mono_time_ns, optional=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class ControllerCallbackSignals:
    desired_lateral_accel: ScalarObservation | None = None
    actual_lateral_accel: ScalarObservation | None = None
    roll: ScalarObservation | None = None
    roll_compensation: ScalarObservation | None = None
    callback_acceleration: ScalarObservation | None = None
    friction_input: ScalarObservation | None = None
    friction_deadzone: ScalarObservation | None = None
    friction_threshold: ScalarObservation | None = None
    q_observed: ScalarObservation | None = None
    friction_compensation_enabled: bool | None = None
    gravity_adjusted: bool | None = None

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name in {"friction_compensation_enabled", "gravity_adjusted"}:
                boolean(value)
            else:
                require(value is None or type(value) is ScalarObservation, "SCALAR_TYPE")


@dataclass(frozen=True, slots=True, kw_only=True)
class DownstreamStageIdentity:
    stage: Stage
    source_event_id: str
    source_command_event_id: str
    source_time_ns: int
    clock_domain: ClockDomain
    controller_cycle_digest: str
    exact_source_command_reference: bool | None
    source_valid: bool | None = None
    source_transport_healthy: bool | None = None

    def __post_init__(self) -> None:
        enum_value(self.stage, Stage)
        require(
            self.stage in {Stage.REQUESTED_TORQUE, Stage.HOST_OUTPUT, Stage.APPLIED_TORQUE},
            "DOWNSTREAM_STAGE",
        )
        sha(self.source_event_id)
        sha(self.source_command_event_id)
        sha(self.controller_cycle_digest)
        uint64(self.source_time_ns)
        enum_value(self.clock_domain, ClockDomain)
        boolean(self.exact_source_command_reference)
        boolean(self.source_valid)
        boolean(self.source_transport_healthy)


@dataclass(frozen=True, slots=True, kw_only=True)
class ControllerStageDecomposition:
    callback_output_raw: ScalarObservation | None = None
    pid_p: ScalarObservation | None = None
    pid_i: ScalarObservation | None = None
    pid_d: ScalarObservation | None = None
    pid_f: ScalarObservation | None = None
    pid_sum: ScalarObservation | None = None
    post_pid_output: ScalarObservation | None = None
    requested_torque: ScalarObservation | None = None
    host_output: ScalarObservation | None = None
    applied_torque: ScalarObservation | None = None
    downstream_cycle_id: str | None = None
    downstream_identities: tuple[DownstreamStageIdentity, ...] = ()

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name == "downstream_identities":
                identities = tuple(value)
                require(
                    all(type(i) is DownstreamStageIdentity for i in identities),
                    "DOWNSTREAM_IDENTITY_TYPE",
                )
                require(
                    len({i.stage for i in identities}) == len(identities)
                    and len({i.source_event_id for i in identities}) == len(identities),
                    "DUPLICATE_DOWNSTREAM_IDENTITY",
                )
                object.__setattr__(
                    self, item.name, tuple(sorted(identities, key=lambda i: i.stage.value))
                )
            elif item.name == "downstream_cycle_id":
                sha(value, optional=True)
            else:
                require(value is None or type(value) is ScalarObservation, "SCALAR_TYPE")


@dataclass(frozen=True, slots=True, kw_only=True)
class LimitState:
    controller_active: bool | None = None
    source_healthy: bool | None = None
    steering_pressed: bool | None = None
    driver_override: bool | None = None
    timer_saturated: bool | None = None
    instantaneous_controller_limited: bool | None = None
    curvature_limited: bool | None = None
    steer_limited_by_controls: bool | None = None
    vehicle_actuator_limited: bool | None = None

    def __post_init__(self) -> None:
        for item in fields(self):
            boolean(getattr(self, item.name))


@dataclass(frozen=True, slots=True, kw_only=True)
class LateralTorqueIdentificationReceipt:
    cycle: CycleIdentity
    callback_stage: CallbackStage
    controller_mode: ControllerMode
    callback_family: CallbackFamily
    callback_function: CallbackFunction
    callback_site: CallbackSite
    sources: tuple[ConsumedSourceIdentity, ...]
    signals: ControllerCallbackSignals
    stages: ControllerStageDecomposition
    context: FrictionObservationContext
    limits: LimitState
    receipt_schema_version: str = VERSION
    consumption_manifest_complete: bool | None = None

    def __post_init__(self) -> None:
        token(self.receipt_schema_version)
        boolean(self.consumption_manifest_complete)
        for name, cls in (
            ("cycle", CycleIdentity),
            ("signals", ControllerCallbackSignals),
            ("stages", ControllerStageDecomposition),
            ("context", FrictionObservationContext),
            ("limits", LimitState),
        ):
            require(type(getattr(self, name)) is cls, "RECEIPT_TYPE")
        for name, enum_cls in (
            ("callback_stage", CallbackStage),
            ("controller_mode", ControllerMode),
            ("callback_family", CallbackFamily),
            ("callback_function", CallbackFunction),
            ("callback_site", CallbackSite),
        ):
            enum_value(getattr(self, name), enum_cls)
        sources = tuple(self.sources)
        require(all(type(s) is ConsumedSourceIdentity for s in sources), "SOURCE_TYPE")
        identities = [s.source_identity for s in sources if s.source_identity is not None]
        require(
            len({s.role for s in sources}) == len(sources)
            and len(set(identities)) == len(identities),
            "DUPLICATE_CONSUMED_SOURCE",
        )
        object.__setattr__(self, "sources", tuple(sorted(sources, key=lambda s: s.role.value)))

    @property
    def digest(self) -> str:
        return digest(asdict(self))

    @property
    def epoch_digest(self) -> str:
        context = epoch_context(self.context)
        identity = {
            name: getattr(self.cycle, name)
            for name in (
                "session_id",
                "source_revision",
                "source_schema_digest",
                "vehicle_context_digest",
                "controller_instance_generation",
                "installed_parameter_generation",
                "geometry_generation",
            )
        }
        return digest(
            {
                "identity": identity,
                "stage": self.callback_stage,
                "mode": self.controller_mode,
                "family": self.callback_family,
                "function": self.callback_function,
                "site": self.callback_site,
                "context": context,
                "version": self.receipt_schema_version,
            }
        )
