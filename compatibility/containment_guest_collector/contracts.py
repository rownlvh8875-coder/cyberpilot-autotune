"""Immutable exact integer wire records. Completeness is not qualification."""

from __future__ import annotations

from dataclasses import dataclass

VERSION = "guest-syscall-fd-v1"
CLOCK = "GUEST_TRACER_OBSERVATION_MONOTONIC_NS"
PERMISSIONS = (
    "runtime_qualified",
    "device_class_qualified",
    "policy_adopted",
    "candidate_generation_allowed",
    "application_authorized",
    "runtime_accepted",
    "owner_proposal_allowed",
)
LENGTHS = {
    "BIRTH": 2,
    "ENTER": 9,
    "RETURN": 2,
    "ABORT": 2,
    "EXEC": 1,
    "NOTIFY_RECV": 13,
    "ADDFD": 7,
    "NOTIFY_SEND": 6,
    "SIGNAL": 2,
    "PRE_EXIT": 1,
    "EXIT": 1,
    "ERROR": 2,
}
SIGNED = {"RETURN": {1}, "ADDFD": {6}, "NOTIFY_SEND": {2, 3, 5}, "SIGNAL": {1}}


def integer(value: object, *, signed: bool = False) -> None:
    lower = -(2**63) if signed else 0
    upper = 2**63 if signed else 2**64
    if type(value) is not int or not lower <= value < upper:
        raise ValueError("expected exact bounded integer")


@dataclass(frozen=True, slots=True)
class TraceEvent:
    kind: str
    seq: int
    mono_ns: int
    task: int
    tid: int
    image: int
    values: tuple[int, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in LENGTHS.keys() | {"FDS"}:
            raise ValueError("unknown event kind")
        for value in (self.seq, self.mono_ns, self.task, self.tid, self.image):
            integer(value)
        if self.seq == 0 or self.task == 0 or not 0 < self.tid < 2**32:
            raise ValueError("invalid sequence/task/tid")
        if type(self.values) not in (list, tuple):
            raise ValueError("expected integer array")
        for index, value in enumerate(self.values):
            integer(value, signed=index in SIGNED.get(self.kind, set()))
        if self.kind == "FDS":
            if len(self.values) < 2 or len(self.values) != 2 + 6 * self.values[1]:
                raise ValueError("invalid FD table shape")
            fds = self.values[2::6]
            if list(fds) != sorted(set(fds)) or any(fd >= 2**31 for fd in fds):
                raise ValueError("duplicate, unordered or oversized FD")
        elif len(self.values) != LENGTHS[self.kind]:
            raise ValueError("wrong kind value count")
        object.__setattr__(self, "values", tuple(self.values))


def permissions(value: Capture | CaptureAssessment) -> None:
    for name in PERMISSIONS:
        if getattr(value, name) is not False:
            raise ValueError("all permissions are fixed false")
    if (
        value.successful_prohibited_handles is not None
        or value.successful_prohibited_effects is not None
    ):
        raise ValueError("global effect/handle counts remain unknown")


@dataclass(frozen=True, slots=True)
class Capture:
    fixture_id: str
    events: tuple[TraceEvent, ...]
    end_values: tuple[int, ...]
    version: str = VERSION
    clock_domain: str = CLOCK
    evidence_kind: str = "UNTRUSTED_CAPTURE_REPORT"
    runtime_qualified: bool = False
    device_class_qualified: bool = False
    policy_adopted: bool = False
    candidate_generation_allowed: bool = False
    application_authorized: bool = False
    runtime_accepted: bool = False
    owner_proposal_allowed: bool = False
    successful_prohibited_handles: None = None
    successful_prohibited_effects: None = None

    def __post_init__(self) -> None:
        if type(self.fixture_id) is not str or self.fixture_id not in tuple(
            f"HF{i:02d}" for i in range(1, 25)
        ):
            raise ValueError("unknown fixture")
        if (
            type(self.version) is not str
            or self.version != VERSION
            or type(self.clock_domain) is not str
            or self.clock_domain != CLOCK
            or type(self.evidence_kind) is not str
            or self.evidence_kind != "UNTRUSTED_CAPTURE_REPORT"
        ):
            raise ValueError("unsupported capture semantics or authority kind")
        if type(self.events) not in (list, tuple) or not self.events:
            raise ValueError("missing events")
        for event in self.events:
            if type(event) is not TraceEvent:
                raise ValueError("expected immutable event")
            event.__post_init__()
        if type(self.end_values) not in (list, tuple) or len(self.end_values) != 4:
            raise ValueError("expected four end counters")
        for value in self.end_values:
            integer(value)
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "end_values", tuple(self.end_values))
        permissions(self)


@dataclass(frozen=True, slots=True)
class CaptureAssessment:
    capture_complete: bool
    fd_profile_complete: bool
    task_count: int
    call_pairs: int
    aborted_calls: int
    exec_count: int
    fd_transitions: int
    notifications: int
    donations: int
    reasons: tuple[str, ...]
    evidence_kind: str = "UNTRUSTED_CAPTURE_REPORT"
    runtime_qualified: bool = False
    device_class_qualified: bool = False
    policy_adopted: bool = False
    candidate_generation_allowed: bool = False
    application_authorized: bool = False
    runtime_accepted: bool = False
    owner_proposal_allowed: bool = False
    successful_prohibited_handles: None = None
    successful_prohibited_effects: None = None

    def __post_init__(self) -> None:
        if type(self.capture_complete) is not bool or type(self.fd_profile_complete) is not bool:
            raise ValueError("expected exact completeness bool")
        if self.fd_profile_complete and not self.capture_complete:
            raise ValueError("FD completeness requires capture completeness")
        for value in (
            self.task_count,
            self.call_pairs,
            self.aborted_calls,
            self.exec_count,
            self.fd_transitions,
            self.notifications,
            self.donations,
        ):
            integer(value)
        if type(self.reasons) not in (list, tuple) or any(
            type(x) is not str or not x for x in self.reasons
        ):
            raise ValueError("expected reason strings")
        for reason in self.reasons:
            reason.encode("utf-8")
        if self.evidence_kind != "UNTRUSTED_CAPTURE_REPORT":
            raise ValueError("no authenticity promotion")
        object.__setattr__(self, "reasons", tuple(self.reasons))
        permissions(self)
