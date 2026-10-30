"""Immutable bounded local observations; unknown is not zero."""

import re
from dataclasses import dataclass

CASES = tuple(f"IS{i:02d}" for i in range(1, 9))
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


def uint(value: object, *, positive: bool = False) -> None:
    if type(value) is not int or not (int(positive) <= value < 2**64):
        raise ValueError("unsigned exact integer required")


@dataclass(frozen=True)
class SealEvent:
    seq: int
    time_ns: int
    kind: str
    label: str
    values: tuple[int | str | None, ...]

    def __post_init__(self) -> None:
        uint(self.seq)
        uint(self.time_ns, positive=True)
        if type(self.label) is not str or not re.fullmatch(r"[A-Za-z0-9_]{1,40}", self.label):
            raise ValueError("invalid event label")
        if type(self.values) not in (list, tuple):
            raise ValueError("event vector required")
        object.__setattr__(self, "values", tuple(self.values))
        v = self.values
        lengths = {"BEGIN": 1, "END": 0, "SNAP": 7, "OP": 2, "BIND": 5, "LOCAL": 1}
        if type(self.kind) is not str or self.kind not in lengths or len(v) != lengths[self.kind]:
            raise ValueError("unknown event shape")
        if self.kind == "BEGIN":
            if self.label not in CASES or v != ("guest-input-seal-v1",):
                raise ValueError("unsupported capture schema/case")
        elif self.kind == "END":
            if self.label not in CASES:
                raise ValueError("unsupported case")
        elif self.kind == "OP":
            if type(v[0]) is not int or not -1 <= v[0] < 2**63:
                raise ValueError("libc result required, not raw syscall return")
            uint(v[1])
            if (v[0] == -1) != (v[1] != 0):
                raise ValueError("result/errno mismatch")
        elif self.kind == "SNAP":
            for i in (0, 1, 2, 5, 6):
                uint(v[i])
            if type(v[3]) is not str or not re.fullmatch(r"[a-f0-9]{64}", v[3]):
                raise ValueError("actual read SHA256 required")
            if v[4] is not None:
                uint(v[4])
            if (v[4] is None) != (v[5] != 0) or v[6] > 0o7777:
                raise ValueError("seal availability/mode mismatch")
        else:
            for value in v:
                uint(value)
            if self.kind == "LOCAL" and v[0] > 255:
                raise ValueError("byte outside range")


@dataclass(frozen=True)
class SealCapture:
    events: tuple[SealEvent, ...]

    def __post_init__(self) -> None:
        if type(self.events) not in (tuple, list) or not 3 <= len(self.events) <= 64:
            raise ValueError("bounded complete capture required")
        object.__setattr__(self, "events", tuple(self.events))
        previous = 0
        for i, event in enumerate(self.events):
            if type(event) is not SealEvent:
                raise ValueError("typed event required")
            event.__post_init__()
            if event.seq != i or event.time_ns < previous:
                raise ValueError("sequence/time order invalid")
            previous = event.time_ns
            if event.kind in ("BEGIN", "END") and i not in (0, len(self.events) - 1):
                raise ValueError("frame boundary inside capture")
        if (
            self.events[0].kind != "BEGIN"
            or self.events[-1].kind != "END"
            or self.events[0].label != self.events[-1].label
        ):
            raise ValueError("missing/mismatched complete frame")

    @property
    def case(self) -> str:
        return self.events[0].label


@dataclass(frozen=True)
class SealDecision:
    case: str
    scenario_recognized: bool
    object_seal_observed: bool
    reasons: tuple[str, ...]

    @property
    def overall(self) -> str:
        return "BLOCKED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    @property
    def prohibited_operation_count(self) -> None:
        return None
