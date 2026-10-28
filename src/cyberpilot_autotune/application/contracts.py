"""Immutable caller policy and host-application evidence; no vehicle defaults."""

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum

from cyberpilot_autotune.contracts import ObservationSnapshot, ParameterSpec, TuningProposal
from cyberpilot_autotune.contracts.validation import (
    ValidationError,
    count,
    nonnegative,
    parameters,
    text,
)

TUNABLE_IDS = frozenset(("lat_accel_factor", "friction"))
TARGET_IDS = TUNABLE_IDS | {"lat_accel_offset"}


def identity(value: str, length: int) -> None:
    if type(value) is not str or re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is None:
        raise ValidationError("invalid exact identity")


def _canonical(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    return value


def digest(value: object) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ApplicationScope(Enum):
    SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY"
    OWNER_REVIEWED_STEERING = "OWNER_REVIEWED_STEERING"


class EvidenceQuality(Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    INDEPENDENTLY_QUALIFIED = "INDEPENDENTLY_QUALIFIED"


class ApplicationState(Enum):
    READY = "READY"
    ACTIVE = "ACTIVE"
    DISARMED = "DISARMED"
    FAULTED = "FAULTED"


class ApplicationReason(Enum):
    VERIFIED = "VERIFIED"
    UNCHANGED = "UNCHANGED"
    BASELINE_RESTORED = "BASELINE_RESTORED"
    INVALID_INPUT = "INVALID_INPUT"
    REPLAYED = "REPLAYED"
    UNQUALIFIED_EVIDENCE = "UNQUALIFIED_EVIDENCE"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    SOURCE_INVALID = "SOURCE_INVALID"
    CONTROL_INACTIVE = "CONTROL_INACTIVE"
    OVERRIDE = "OVERRIDE"
    SATURATED = "SATURATED"
    STALE_SOURCE = "STALE_SOURCE"
    ORDERING = "ORDERING"
    BASELINE_MISMATCH = "BASELINE_MISMATCH"
    TARGET_CONFLICT = "TARGET_CONFLICT"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    STEP_LIMIT = "STEP_LIMIT"
    RATE_LIMIT = "RATE_LIMIT"
    CONFIDENCE = "CONFIDENCE"
    SAMPLES = "SAMPLES"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    AUTHORIZATION_INVALID = "AUTHORIZATION_INVALID"
    TRANSACTION_TIMEOUT = "TRANSACTION_TIMEOUT"
    ROLLBACK_TIMEOUT = "ROLLBACK_TIMEOUT"
    CLOCK_FAULT = "CLOCK_FAULT"
    TARGET_FAULT = "TARGET_FAULT"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    HOLD_EXPIRED = "HOLD_EXPIRED"
    DISARMED = "DISARMED"
    FAULT_LATCHED = "FAULT_LATCHED"


@dataclass(frozen=True, slots=True, kw_only=True)
class SteeringPolicy:
    scope: ApplicationScope
    owner_id: str
    source_revision: str
    context_digest: str
    observation_context: str
    baseline_epoch: int
    session_token: str
    parameters: tuple[ParameterSpec, ...]
    minimum_samples: int
    minimum_confidence: float
    minimum_speed_mps: float
    maximum_source_age_s: float
    maximum_target_age_s: float
    maximum_evidence_age_s: float
    maximum_authorization_age_s: float
    maximum_transaction_s: float
    maximum_rollback_s: float
    maximum_hold_s: float
    maximum_consumed_proposals: int

    def __post_init__(self) -> None:
        if type(self.scope) is not ApplicationScope:
            raise ValidationError("explicit typed scope required")
        for label in (self.owner_id, self.observation_context):
            text(label, "policy context")
        identity(self.source_revision, 40)
        identity(self.context_digest, 64)
        identity(self.session_token, 32)
        count(self.baseline_epoch, "epoch")
        for value in (self.minimum_samples, self.maximum_consumed_proposals):
            count(value, "positive count")
            if value == 0:
                raise ValidationError("positive count required")
        if not 0 <= nonnegative(self.minimum_confidence, "confidence") <= 1:
            raise ValidationError("confidence exceeds one")
        for name in (
            "minimum_speed_mps",
            "maximum_source_age_s",
            "maximum_target_age_s",
            "maximum_evidence_age_s",
        ):
            nonnegative(getattr(self, name), name)
        for name in (
            "maximum_authorization_age_s",
            "maximum_transaction_s",
            "maximum_rollback_s",
            "maximum_hold_s",
        ):
            if nonnegative(getattr(self, name), name) == 0:
                raise ValidationError("positive duration required")
        if type(self.parameters) is not tuple or not self.parameters:
            raise ValidationError("explicit nonempty steering registry required")
        specs: list[ParameterSpec] = []
        for spec in self.parameters:
            if type(spec) is not ParameterSpec:
                raise ValidationError("typed parameter specification required")
            spec = replace(spec)
            if spec.parameter_id not in TUNABLE_IDS or spec.persistence_eligible:
                raise ValidationError("not an eligible steering parameter contract")
            specs.append(spec)
        if len({spec.parameter_id for spec in specs}) != len(specs):
            raise ValidationError("duplicate parameter specification")
        object.__setattr__(self, "parameters", tuple(specs))

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    revision: int
    timestamp_s: float
    owner_id: str
    context_digest: str
    baseline_epoch: int
    scope: ApplicationScope
    values: Mapping[str, float]

    def __post_init__(self) -> None:
        count(self.revision, "revision")
        nonnegative(self.timestamp_s, "target timestamp")
        text(self.owner_id, "owner")
        identity(self.context_digest, 64)
        count(self.baseline_epoch, "epoch")
        if type(self.scope) is not ApplicationScope:
            raise ValidationError("explicit target scope required")
        copied = parameters(self.values)
        if not copied or not set(copied) <= TARGET_IDS:
            raise ValidationError("target must expose steering-only values")
        object.__setattr__(self, "values", copied)


@dataclass(frozen=True, slots=True)
class SteeringEvidence:
    quality: EvidenceQuality
    content_sha256: str
    source_revision: str
    context_digest: str
    target_revision: int
    generated_at_s: float
    estimator_version: str

    def __post_init__(self) -> None:
        if type(self.quality) is not EvidenceQuality:
            raise ValidationError("typed evidence quality required")
        identity(self.content_sha256, 64)
        identity(self.source_revision, 40)
        identity(self.context_digest, 64)
        count(self.target_revision, "evidence target revision")
        nonnegative(self.generated_at_s, "evidence timestamp")
        text(self.estimator_version, "estimator version")

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class SteeringRequest:
    sequence: int
    proposal_id: str
    policy_sha256: str
    session_token: str
    expected_revision: int
    proposal: TuningProposal
    observation: ObservationSnapshot
    evidence: SteeringEvidence

    def __post_init__(self) -> None:
        count(self.sequence, "attempt sequence")
        identity(self.proposal_id, 32)
        identity(self.policy_sha256, 64)
        identity(self.session_token, 32)
        count(self.expected_revision, "expected revision")
        for name, kind in (
            ("proposal", TuningProposal),
            ("observation", ObservationSnapshot),
            ("evidence", SteeringEvidence),
        ):
            value = getattr(self, name)
            if type(value) is not kind:
                raise ValidationError("typed application input required")
            object.__setattr__(self, name, replace(value))

    @property
    def digest(self) -> str:
        return digest(self)


@dataclass(frozen=True, slots=True)
class AuthorizationGrant:
    authorization_id: str
    request_sha256: str
    policy_sha256: str
    evidence_sha256: str
    issued_at_s: float
    expires_at_s: float

    def __post_init__(self) -> None:
        identity(self.authorization_id, 32)
        for value in (self.request_sha256, self.policy_sha256, self.evidence_sha256):
            identity(value, 64)
        nonnegative(self.issued_at_s, "authorization timestamp")
        nonnegative(self.expires_at_s, "authorization expiry")
        if self.expires_at_s <= self.issued_at_s:
            raise ValidationError("authorization requires positive validity interval")


@dataclass(frozen=True, slots=True)
class ApplicationReceipt:
    reason: ApplicationReason
    state: ApplicationState
    sequence: int | None
    baseline_parameters: Mapping[str, float]
    effective_parameters: Mapping[str, float] | None
    verified_revision: int | None
    timestamp_s: float | None
    recovery_reason: ApplicationReason | None = None

    def __post_init__(self) -> None:
        if type(self.reason) is not ApplicationReason or type(self.state) is not ApplicationState:
            raise ValidationError("typed receipt state required")
        if self.recovery_reason is not None and type(self.recovery_reason) is not ApplicationReason:
            raise ValidationError("typed recovery reason required")
        for value in (self.sequence, self.verified_revision):
            if value is not None:
                count(value, "receipt counter")
        if self.timestamp_s is not None:
            nonnegative(self.timestamp_s, "receipt timestamp")
        object.__setattr__(self, "baseline_parameters", parameters(self.baseline_parameters))
        if self.effective_parameters is not None:
            object.__setattr__(self, "effective_parameters", parameters(self.effective_parameters))
