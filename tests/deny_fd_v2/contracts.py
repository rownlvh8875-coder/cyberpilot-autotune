"""Immutable flat wire values, not acquisition authenticity or authority."""

import re
from dataclasses import dataclass
from typing import Any

VERSION = "guest-data-fd-denial-observed-v2"
STAGE = "PRE_EXEC_INVENTORY"
FIELDS = {
    "BEGIN": "tcrhttt",
    "POLICY": "uok",
    "EXPECT": "uf",
    "BIRTH": "uu",
    "FD": "utuufz",
    "SNAP": "utuuukuuuuzz",
    "CAUSE": "ufu",
    "DENY": "utuuutzk",
    "RESULT": "utuuut",
    "REAP": "uutu",
    "END": "uuz",
}
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


def require(condition: bool) -> None:
    if not condition:
        raise ValueError("invalid untrusted v2 structure")


def _field(value: Any, code: str) -> None:
    if code == "z":
        require(value is None)
    elif code in "ukfo":
        if code == "o" and value is None:
            return
        limit = 64 if code == "k" else 2**31 - 1 if code in "fo" else 2**64 - 1
        require(type(value) is int and 0 <= value <= limit)
    else:
        pattern = {"c": "[0-9a-f]{32}", "r": "[0-9a-f]{40}", "h": "[0-9a-f]{64}"}.get(
            code, "[A-Za-z0-9_./:-]{1,96}"
        )
        require(type(value) is str and re.fullmatch(pattern, value) is not None)


@dataclass(frozen=True, slots=True)
class Event:
    seq: int
    time_ns: int
    kind: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        _field(self.seq, "u")
        _field(self.time_ns, "u")
        require(self.seq > 0 and type(self.kind) is str and self.kind in FIELDS)
        require(type(self.values) in (tuple, list) and len(self.values) == len(FIELDS[self.kind]))
        object.__setattr__(self, "values", tuple(self.values))
        for value, code in zip(self.values, FIELDS[self.kind], strict=True):
            _field(value, code)
        if self.kind == "BEGIN":
            require(
                self.values[0] == VERSION
                and self.values[4:6] == ("GUEST_MONOTONIC_NS", "OBSERVED_UNTRUSTED")
                and self.values[6] in ("DFD01", "DFD02", "DFD03", "DFD04", "DFD05", "DFD06")
            )
        if self.kind in ("FD", "SNAP", "DENY", "RESULT"):
            require(self.values[1] == STAGE)
        if self.kind == "DENY":
            require(self.values[5] == "UNEXPECTED_FD")
        if self.kind == "RESULT":
            require(self.values[5] in ("NO_DENIAL", "UNSUPPORTED_MISSING", "UNSUPPORTED_MIXED"))
        if self.kind == "REAP":
            require(self.values[2] == "SIGNALLED")


@dataclass(frozen=True, slots=True)
class Capture:
    events: tuple[Event, ...]

    def __post_init__(self) -> None:
        require(type(self.events) in (tuple, list) and 1 <= len(self.events) <= 1024)
        object.__setattr__(self, "events", tuple(self.events))
        previous = -1
        for seq, event in enumerate(self.events, 1):
            require(type(event) is Event)
            event.__post_init__()
            require(event.seq == seq and event.time_ns > previous)
            previous = event.time_ns
        kinds = tuple(event.kind for event in self.events)
        require(
            kinds[0] == "BEGIN"
            and kinds[-1] == "END"
            and kinds.count("BEGIN") == 1
            and kinds.count("END") == 1
        )


@dataclass(frozen=True, slots=True)
class Decision:
    outcome: str
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        require(
            type(self.outcome) is str and self.outcome in ("REJECTED", "WIRE_DIAGNOSTIC_CONSISTENT")
        )
        require(type(self.reasons) in (tuple, list))
        require(all(type(r) is str and re.fullmatch("[A-Z_]{1,96}", r) for r in self.reasons))
        require(bool(self.reasons) == (self.outcome == "REJECTED"))
        object.__setattr__(self, "reasons", tuple(self.reasons))

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS
