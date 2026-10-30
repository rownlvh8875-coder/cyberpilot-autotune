"""Bounded immutable wire observations and untrusted known-content context."""

import re
from dataclasses import dataclass
from typing import cast

from compatibility.guest_build_receipt.models import (
    CLOCK_DOMAIN,
    BuildIdentity,
    MaterialRole,
    opaque,
    path,
    records,
    sha,
    uint,
)

VERSION = "guest-consumption-prototype-v1"
CASES = tuple(f"CP{i:02d}" for i in range(1, 8))
MAX_RECORDS = 10000
Value = int | str | bool | None
ARITIES = {
    "BEGIN": 3,
    "OBJECT": 5,
    "BIRTH": 2,
    "EXEC": 1,
    "READ": 4,
    "MAP": 3,
    "META": 1,
    "FAILED": 2,
    "ERROR": 1,
    "PAYLOAD": 1,
    "EXIT": 2,
    "END": 4,
}


def integer(value: Value, *, positive: bool = False) -> int:
    uint(cast(int, value), positive=positive)
    return cast(int, value)


def hex_bytes(value: Value, limit: int) -> bytes:
    if (
        type(value) is not str
        or len(value) % 2
        or len(value) > limit * 2
        or re.fullmatch(r"[0-9a-f]*", value) is None
    ):
        raise ValueError("invalid observed bytes")
    return bytes.fromhex(value)


@dataclass(frozen=True, slots=True)
class CaptureEvent:
    seq: int
    time_ns: int
    kind: str
    task: int
    image: int
    values: tuple[Value, ...]

    def __post_init__(self) -> None:
        uint(self.seq, positive=True)
        for value in (self.time_ns, self.task, self.image):
            uint(value)
        if (
            type(self.kind) is not str
            or self.kind not in ARITIES
            or type(self.values) not in (tuple, list)
            or len(self.values) != ARITIES[self.kind]
        ):
            raise ValueError("unsupported capture record shape")
        v = tuple(self.values)
        object.__setattr__(self, "values", v)
        if self.kind in ("BEGIN", "OBJECT", "END", "PAYLOAD"):
            if self.task != 0 or self.image != 0:
                raise ValueError("observer record cannot claim a task image")
        elif self.kind != "ERROR":
            uint(self.task, positive=True)
        if self.kind == "BEGIN":
            if (
                v[0] != VERSION
                or type(v[0]) is not str
                or type(v[1]) is not str
                or v[1] not in CASES
                or v[2] != CLOCK_DOMAIN
            ):
                raise ValueError("wrong capture version/case/clock")
        elif self.kind == "OBJECT":
            integer(v[0], positive=True)
            for object_scalar in v[1:4]:
                integer(object_scalar)
            if integer(v[3]) > 4 * 1024 * 1024:
                raise ValueError("object capture bound exceeded")
            sha(cast(str, v[4]))
        elif self.kind == "BIRTH":
            if v[0] is not None:
                integer(v[0], positive=True)
            integer(v[1], positive=True)
        elif self.kind in ("READ", "MAP", "META", "EXEC"):
            integer(v[0], positive=True)
            if self.kind in ("READ", "MAP"):
                integer(v[1])
                integer(v[2], positive=self.kind == "MAP")
            if self.kind == "READ" and len(hex_bytes(v[3], 4096)) != v[2]:
                raise ValueError("returned-byte length mismatch")
        elif self.kind == "FAILED":
            integer(v[0])
            if type(v[1]) is not int or not -(2**63) <= v[1] < 0:
                raise ValueError("failed syscall is not a zero-byte success")
        elif self.kind == "EXIT":
            if type(v[0]) is not str or v[0] not in ("EXITED", "SIGNALLED"):
                raise ValueError("unknown exit observation")
            integer(v[1], positive=v[0] == "SIGNALLED")
            if integer(v[1]) > (255 if v[0] == "EXITED" else 64):
                raise ValueError("exit observation out of range")
        elif self.kind == "ERROR":
            if type(v[0]) is not str or re.fullmatch(r"[A-Z][A-Z0-9_]{0,95}", v[0]) is None:
                raise ValueError("invalid error identity")
        elif self.kind == "PAYLOAD":
            hex_bytes(v[0], 4096)
        else:
            if type(v[0]) is not bool:
                raise ValueError("unknown completion is not false")
            integer(v[1])
            integer(v[2])
            if v[3] is not None:
                integer(v[3])


@dataclass(frozen=True, slots=True)
class ConsumptionCapture:
    events: tuple[CaptureEvent, ...]

    def __post_init__(self) -> None:
        events = records(self.events, CaptureEvent)
        if (
            not 2 <= len(events) <= MAX_RECORDS
            or events[0].kind != "BEGIN"
            or events[-1].kind != "END"
        ):
            raise ValueError("missing capture boundary/resource bound")
        previous = 0
        for i, event in enumerate(events, 1):
            if (
                event.seq != i
                or event.time_ns < previous
                or (event.kind == "BEGIN" and i != 1)
                or (event.kind == "END" and i != len(events))
            ):
                raise ValueError("capture sequence/time/boundary invalid")
            previous = event.time_ns
        object.__setattr__(self, "events", events)

    @property
    def case(self) -> str:
        return cast(str, self.events[0].values[1])


@dataclass(frozen=True, slots=True)
class KnownMaterial:
    material_id: str
    role: MaterialRole
    logical_path: str
    size: int
    sha256: str

    def __post_init__(self) -> None:
        opaque(self.material_id)
        path(self.logical_path)
        uint(self.size)
        sha(self.sha256)
        if type(self.role) is not MaterialRole or self.role is MaterialRole.GENERATED:
            raise ValueError("unsupported known material role")


@dataclass(frozen=True, slots=True)
class ConsumptionProfile:
    identity: BuildIdentity
    materials: tuple[KnownMaterial, ...]

    def __post_init__(self) -> None:
        if type(self.identity) is not BuildIdentity:
            raise ValueError("invalid profile context")
        self.identity.__post_init__()
        items = records(self.materials, KnownMaterial, ("material_id",))
        if not items or len({(m.size, m.sha256) for m in items}) != len(items):
            raise ValueError("ambiguous/missing known material content")
        object.__setattr__(self, "materials", items)
