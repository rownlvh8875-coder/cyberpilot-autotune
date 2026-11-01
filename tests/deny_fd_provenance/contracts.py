"""Immutable neutral synthetic envelopes. Identity is content, never authenticity."""

import re
from dataclasses import dataclass
from enum import StrEnum


class EvidenceKind(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    OBSERVED_UNTRUSTED = "OBSERVED_UNTRUSTED"


class ClockDomain(StrEnum):
    SYNTHETIC_MONOTONIC_NS = "SYNTHETIC_MONOTONIC_NS"
    GUEST_MONOTONIC_NS = "GUEST_MONOTONIC_NS"


class DenialStage(StrEnum):
    PRE_EXEC_INVENTORY = "PRE_EXEC_INVENTORY"
    PRE_EXEC_BINDING = "PRE_EXEC_BINDING"
    POST_EXEC_BINDING = "POST_EXEC_BINDING"
    SYSCALL_ENTRY = "SYSCALL_ENTRY"
    OTHER_UNSUPPORTED = "OTHER_UNSUPPORTED"


class DenialReason(StrEnum):
    UNEXPECTED_FD = "UNEXPECTED_FD"
    MISSING_FD = "MISSING_FD"
    BINDING_MISMATCH = "BINDING_MISMATCH"
    EARLY_READ = "EARLY_READ"
    BINDING_CHANGED = "BINDING_CHANGED"
    OTHER_UNSUPPORTED = "OTHER_UNSUPPORTED"


class Outcome(StrEnum):
    SYNTHETIC_DIAGNOSTIC_CONSISTENT = "SYNTHETIC_DIAGNOSTIC_CONSISTENT"
    REJECTED = "REJECTED"


class RejectionReason(StrEnum):
    PRODUCER_NOT_IMPLEMENTED = "PRODUCER_NOT_IMPLEMENTED"
    WRONG_CLOCK_DOMAIN = "WRONG_CLOCK_DOMAIN"
    UNSUPPORTED_STAGE = "UNSUPPORTED_STAGE"
    UNSUPPORTED_REASON = "UNSUPPORTED_REASON"
    INVENTORY_HAS_OPERATION_FD = "INVENTORY_HAS_OPERATION_FD"
    MISSING_POLICY = "MISSING_POLICY"
    MISSING_SNAPSHOT = "MISSING_SNAPSHOT"
    MISSING_INVENTORY = "MISSING_INVENTORY"
    MISSING_CAUSE_FDS = "MISSING_CAUSE_FDS"
    MISSING_CAUSE_REFS = "MISSING_CAUSE_REFS"
    COHORT_MISMATCH = "COHORT_MISMATCH"
    EVENT_ORDER_INVALID = "EVENT_ORDER_INVALID"
    DUPLICATE_WITNESS = "DUPLICATE_WITNESS"
    INCOMPLETE_WITNESS_SET = "INCOMPLETE_WITNESS_SET"
    UNSUPPORTED_MISSING_OR_MIXED_INVENTORY = "UNSUPPORTED_MISSING_OR_MIXED_INVENTORY"
    NO_UNEXPECTED_FD = "NO_UNEXPECTED_FD"
    CAUSE_SET_MISMATCH = "CAUSE_SET_MISMATCH"
    CAUSE_REFERENCE_MISMATCH = "CAUSE_REFERENCE_MISMATCH"


PERMISSIONS = tuple(
    (name, False)
    for name in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    )
)


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError("invalid denial provenance structure")


def _uint(value: object) -> None:
    _require(type(value) is int and 0 <= value < 2**64)


def _optional_uint(value: object) -> None:
    if value is not None:
        _uint(value)


def _fd(value: object) -> None:
    _require(type(value) is int and 0 <= value < 2**31)


def _optional_fd(value: object) -> None:
    if value is not None:
        _fd(value)


def _hash(value: str, width: int) -> None:
    _require(type(value) is str and re.fullmatch("[0-9a-f]{" + str(width) + "}", value) is not None)


def _fds(value: tuple[int, ...] | None) -> tuple[int, ...] | None:
    if value is None:
        return None
    _require(type(value) in (tuple, list) and len(value) <= 64)
    for fd in value:
        _fd(fd)
    _require(len(set(value)) == len(value))
    return tuple(sorted(value))


@dataclass(frozen=True, slots=True)
class CaptureContext:
    capture_id: str
    source_revision: str
    source_manifest_digest: str
    evidence_kind: EvidenceKind
    clock_domain: ClockDomain
    root_birth_ordinal: int
    exec_ordinal: int
    fd_table_generation: int | None = None
    ofd_generation: int | None = None

    def __post_init__(self) -> None:
        _require(
            type(self.capture_id) is str
            and re.fullmatch("[A-Za-z0-9_.:-]{1,96}", self.capture_id) is not None
        )
        _hash(self.source_revision, 40)
        _hash(self.source_manifest_digest, 64)
        _require(
            type(self.evidence_kind) is EvidenceKind and type(self.clock_domain) is ClockDomain
        )
        _uint(self.root_birth_ordinal)
        _uint(self.exec_ordinal)
        _optional_uint(self.fd_table_generation)
        _optional_uint(self.ofd_generation)


@dataclass(frozen=True, slots=True)
class PointRef:
    context: CaptureContext
    snapshot_id: int
    stage: DenialStage
    seq: int
    time_ns: int
    slot_observation_epoch: int | None = None

    def __post_init__(self) -> None:
        _require(type(self.context) is CaptureContext and type(self.stage) is DenialStage)
        self.context.__post_init__()
        for value in (self.snapshot_id, self.seq, self.time_ns):
            _uint(value)
        _optional_uint(self.slot_observation_epoch)


@dataclass(frozen=True, slots=True)
class FdWitness:
    ref: PointRef
    fd: int

    def __post_init__(self) -> None:
        _require(type(self.ref) is PointRef)
        self.ref.__post_init__()
        _fd(self.fd)


@dataclass(frozen=True, slots=True)
class InventoryWitness:
    ref: PointRef
    observed_fds: tuple[int, ...] | None
    fd_witnesses: tuple[FdWitness, ...]

    def __post_init__(self) -> None:
        _require(type(self.ref) is PointRef)
        self.ref.__post_init__()
        object.__setattr__(self, "observed_fds", _fds(self.observed_fds))
        _require(type(self.fd_witnesses) in (tuple, list) and len(self.fd_witnesses) <= 64)
        for witness in self.fd_witnesses:
            _require(type(witness) is FdWitness)
            witness.__post_init__()
        object.__setattr__(self, "fd_witnesses", tuple(self.fd_witnesses))


@dataclass(frozen=True, slots=True)
class InventoryPolicyContext:
    expected_fds: tuple[int, ...] | None
    configured_subject_fd: int | None
    schema_version: str = "unexpected-fd-point-policy-v1"

    def __post_init__(self) -> None:
        _require(
            type(self.schema_version) is str
            and self.schema_version == "unexpected-fd-point-policy-v1"
        )
        object.__setattr__(self, "expected_fds", _fds(self.expected_fds))
        _optional_fd(self.configured_subject_fd)


@dataclass(frozen=True, slots=True)
class DenialReceipt:
    ref: PointRef
    reason: DenialReason
    policy: InventoryPolicyContext
    snapshot: InventoryWitness | None
    operation_fd: int | None
    cause_fds: tuple[int, ...] | None
    cause_refs: tuple[PointRef, ...] | None
    schema_version: str = "deny-fd-provenance-receipt-v1"

    def __post_init__(self) -> None:
        _require(
            type(self.schema_version) is str
            and self.schema_version == "deny-fd-provenance-receipt-v1"
        )
        _require(type(self.ref) is PointRef and type(self.reason) is DenialReason)
        _require(type(self.policy) is InventoryPolicyContext)
        self.ref.__post_init__()
        self.policy.__post_init__()
        if self.snapshot is not None:
            _require(type(self.snapshot) is InventoryWitness)
            self.snapshot.__post_init__()
        _optional_fd(self.operation_fd)
        object.__setattr__(self, "cause_fds", _fds(self.cause_fds))
        if self.cause_refs is not None:
            _require(type(self.cause_refs) in (tuple, list) and len(self.cause_refs) <= 64)
            for ref in self.cause_refs:
                _require(type(ref) is PointRef)
                ref.__post_init__()
            object.__setattr__(self, "cause_refs", tuple(self.cause_refs))


@dataclass(frozen=True, slots=True)
class DenialDecision:
    outcome: Outcome
    reasons: tuple[RejectionReason, ...]

    def __post_init__(self) -> None:
        _require(type(self.outcome) is Outcome and type(self.reasons) in (tuple, list))
        _require(all(type(reason) is RejectionReason for reason in self.reasons))
        _require(bool(self.reasons) == (self.outcome is Outcome.REJECTED))
        object.__setattr__(self, "reasons", tuple(self.reasons))

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS
