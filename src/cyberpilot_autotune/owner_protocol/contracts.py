"""Immutable logical protocol values. No units, encoding or vehicle policy."""

import hashlib
import json
import math
import re
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum

UINT64_MAX = (1 << 64) - 1


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def count(value: int) -> None:
    require(type(value) is int and 0 <= value <= UINT64_MAX, "uint64 required")


def finite(value: float) -> None:
    require(type(value) is float and math.isfinite(value), "finite logical float required")


def time_value(value: float) -> None:
    finite(value)
    require(value >= 0, "nonnegative time required")


def token(value: str, size: int) -> None:
    require(
        type(value) is str and re.fullmatch(f"[0-9a-f]{{{size}}}", value) is not None,
        "exact identity required",
    )


def canonical(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [canonical(v) for v in value]
    return value


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            canonical(value), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


class OwnerState(Enum):
    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    OWNED = "OWNED"
    RECOVERING = "RECOVERING"
    DISARMED = "DISARMED"
    FAULTED = "FAULTED"
    STOPPED = "STOPPED"


class ControllerMode(Enum):
    LINEAR_TORQUE = "LINEAR_TORQUE"
    CUSTOM_TORQUE = "CUSTOM_TORQUE"
    NN_TORQUE = "NN_TORQUE"
    GM_CALLBACK = "GM_CALLBACK"
    UNKNOWN = "UNKNOWN"


class ProducerKind(Enum):
    TORQUED = "TORQUED"
    CYBERPILOT = "CYBERPILOT"
    MANUAL_CUSTOM = "MANUAL_CUSTOM"
    BASELINE = "BASELINE"


@dataclass(frozen=True, slots=True)
class TorqueParameterTuple:
    lat_accel_factor: float
    friction: float
    lat_accel_offset: float

    def __post_init__(self) -> None:
        for value in (self.lat_accel_factor, self.friction, self.lat_accel_offset):
            finite(value)

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class OwnerIdentity:
    protocol_version: str
    source_revision: str
    integration_revision: str
    controller_family: str
    vehicle_context_digest: str
    session_generation: int
    baseline_epoch: int
    owner_instance_id: str

    def __post_init__(self) -> None:
        require(self.protocol_version == "torque-owner-v1", "protocol version")
        require(type(self.controller_family) is str and bool(self.controller_family), "controller")
        for value in (self.source_revision, self.integration_revision):
            token(value, 40)
        token(self.vehicle_context_digest, 64)
        token(self.owner_instance_id, 32)
        count(self.session_generation)
        count(self.baseline_epoch)

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class InstalledTuple:
    values: TorqueParameterTuple
    revision: int
    identity_digest: str
    mode: ControllerMode
    installed_at_s: float
    commit_id: str

    def __post_init__(self) -> None:
        require(type(self.values) is TorqueParameterTuple, "complete tuple required")
        require(type(self.mode) is ControllerMode, "typed mode required")
        count(self.revision)
        token(self.identity_digest, 64)
        token(self.commit_id, 32)
        time_value(self.installed_at_s)

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class BaselineRecord:
    identity: OwnerIdentity
    values: TorqueParameterTuple
    revision_anchor: int
    mode: ControllerMode
    captured_at_s: float
    capture_evidence_digest: str
    capture_id: str

    def __post_init__(self) -> None:
        require(type(self.identity) is OwnerIdentity, "typed identity")
        token(self.capture_evidence_digest, 64)
        _ = self.installed

    @property
    def installed(self) -> InstalledTuple:
        return InstalledTuple(
            self.values,
            self.revision_anchor,
            self.identity.digest,
            self.mode,
            self.captured_at_s,
            self.capture_id,
        )


@dataclass(frozen=True, slots=True)
class ProducerBinding:
    producer: ProducerKind
    generation: int
    compatible_modes: frozenset[ControllerMode]

    def __post_init__(self) -> None:
        require(type(self.producer) is ProducerKind, "producer kind")
        count(self.generation)
        require(
            type(self.compatible_modes) is frozenset
            and bool(self.compatible_modes)
            and all(
                type(m) is ControllerMode and m is not ControllerMode.UNKNOWN
                for m in self.compatible_modes
            ),
            "explicit compatible modes",
        )


@dataclass(frozen=True, slots=True)
class OwnerPolicy:
    maximum_proposal_age_s: float
    maximum_observation_age_s: float
    maximum_lease_s: float
    maximum_transaction_s: float
    maximum_rollback_s: float
    producers: tuple[ProducerBinding, ...]

    def __post_init__(self) -> None:
        for value in (
            self.maximum_proposal_age_s,
            self.maximum_observation_age_s,
            self.maximum_lease_s,
            self.maximum_transaction_s,
            self.maximum_rollback_s,
        ):
            time_value(value)
            require(value > 0, "positive explicit duration")
        require(
            type(self.producers) is tuple
            and bool(self.producers)
            and all(type(p) is ProducerBinding for p in self.producers),
            "producer bindings",
        )
        require(
            len({p.producer for p in self.producers}) == len(self.producers), "duplicate producer"
        )


@dataclass(frozen=True, slots=True)
class TorqueProposal:
    producer: ProducerKind
    sequence: int
    proposal_id: str
    producer_generation: int
    source_revision: str
    context_digest: str
    baseline_epoch: int
    observed_revision: int
    candidate: TorqueParameterTuple
    generated_at_s: float
    expires_at_s: float
    evidence_digest: str
    required_mode: ControllerMode

    def __post_init__(self) -> None:
        require(
            type(self.producer) is ProducerKind
            and type(self.candidate) is TorqueParameterTuple
            and type(self.required_mode) is ControllerMode,
            "typed proposal",
        )
        for value in (
            self.sequence,
            self.producer_generation,
            self.baseline_epoch,
            self.observed_revision,
        ):
            count(value)
        for identity_value, size in (
            (self.proposal_id, 32),
            (self.source_revision, 40),
            (self.context_digest, 64),
            (self.evidence_digest, 64),
        ):
            token(identity_value, size)
        time_value(self.generated_at_s)
        time_value(self.expires_at_s)
        require(self.expires_at_s > self.generated_at_s, "proposal lifetime")

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class AuthorityContext:
    authorization_id: str
    owner_digest: str
    operation_digest: str
    issued_at_s: float
    expires_at_s: float

    def __post_init__(self) -> None:
        token(self.authorization_id, 32)
        token(self.owner_digest, 64)
        token(self.operation_digest, 64)
        time_value(self.issued_at_s)
        time_value(self.expires_at_s)
        require(self.expires_at_s > self.issued_at_s, "grant lifetime")


@dataclass(frozen=True, slots=True)
class OwnerLease:
    revision: int
    producer: ProducerKind
    proposal_id: str
    issued_at_s: float
    expires_at_s: float
    baseline_epoch: int


@dataclass(frozen=True, slots=True)
class CommitAck:
    prior_revision: int
    new_revision: int
    committed_digest: str
    owner_identity: OwnerIdentity
    commit_id: str
    timestamp_s: float
    state: OwnerState


@dataclass(frozen=True, slots=True)
class TorqueOwnerSnapshot:
    values: TorqueParameterTuple
    revision: int
    owner_identity: OwnerIdentity
    controller_mode: ControllerMode
    timestamp_s: float
    state: OwnerState
    lease: OwnerLease | None

    @property
    def tuple_digest(self) -> str:
        return self.values.digest


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    values: TorqueParameterTuple | None
    revision: int | None
    verified: bool
    reason: str
    state: OwnerState
    ack: CommitAck | None


@dataclass(frozen=True, slots=True)
class WatchdogInput:
    source_revision: str
    context_digest: str
    baseline_epoch: int
    controller_mode: ControllerMode
    active_producer_alive: bool
    owner_alive: bool
    generated_at_s: float

    def __post_init__(self) -> None:
        token(self.source_revision, 40)
        token(self.context_digest, 64)
        count(self.baseline_epoch)
        require(
            type(self.controller_mode) is ControllerMode
            and type(self.active_producer_alive) is bool
            and type(self.owner_alive) is bool,
            "typed watchdog input",
        )
        time_value(self.generated_at_s)


class OwnerProtocolError(Exception):
    """Rejection/fault never implies verified effective values or baseline."""
