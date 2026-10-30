"""Pure finite observed-untrusted diagnostics; no kernel or qualification bridge."""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

CASES = tuple(f"HH0{i}" for i in range(1, 8))
SCHEMA = "guest-data-fd-handoff-observed-v1"
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
# n: exact nonnegative integer; i: signed integer; o: unavailable or integer;
# s: bounded ASCII string; h: SHA256; x: returned bytes as hex; z: explicit unknown.
FIELDS = {
    "BEGIN": "sss",
    "OBJECT": "sn nnhon".replace(" ", ""),
    "BIRTH": "n",
    "FD": "snnnnn nnonhon".replace(" ", ""),
    "SNAP": "snnnnnnz",
    "OFD_PIN": "nin",
    "EXEC": "nnnnnh",
    "READY": "n",
    "READ": "nnnnnix",
    "CLOSE": "nnni",
    "DUP": "nnnni",
    "DENY": "sno",
    "REAP": "nsi",
    "RELEASE": "si",
    "END": "nz",
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha(value: Any) -> None:
    require(
        type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None, "SHA256 required"
    )


@dataclass(frozen=True)
class Event:
    seq: int
    time_ns: int
    kind: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        require(type(self.seq) is int and self.seq > 0, "exact sequence required")
        require(type(self.time_ns) is int and self.time_ns >= 0, "exact monotonic time required")
        require(type(self.kind) is str and self.kind in FIELDS, "unsupported event")
        require(type(self.values) in (tuple, list), "scalar event vector required")
        object.__setattr__(self, "values", tuple(self.values))
        require(len(self.values) == len(FIELDS[self.kind]), "event arity")
        for value, field in zip(self.values, FIELDS[self.kind], strict=True):
            if field in "nio":
                require(
                    (field == "o" and value is None)
                    or (
                        type(value) is int
                        and -(2**63) <= value < 2**64
                        and (field != "n" or value >= 0)
                    ),
                    "exact kernel integer required",
                )
            elif field == "z":
                require(value is None, "unqualified generation/count must stay unavailable")
            elif field == "h":
                sha(value)
            elif field == "x":
                require(
                    type(value) is str and re.fullmatch("(?:[0-9a-f]{2}){0,17}", value) is not None,
                    "bounded actual returned bytes required",
                )
            else:
                require(
                    type(value) is str
                    and re.fullmatch("[A-Za-z0-9_./:-]{1,96}", value) is not None,
                    "bounded ASCII token required",
                )


@dataclass(frozen=True)
class Capture:
    case: str
    events: tuple[Event, ...]

    def __post_init__(self) -> None:
        require(type(self.case) is str and self.case in CASES, "fixed case required")
        require(
            type(self.events) in (tuple, list) and 1 <= len(self.events) <= 1024,
            "bounded event vector required",
        )
        object.__setattr__(self, "events", tuple(self.events))
        previous = -1
        for i, event in enumerate(self.events, 1):
            require(
                type(event) is Event and event.seq == i and event.time_ns > previous,
                "event sequence/time order",
            )
            previous = event.time_ns
        require(
            self.events[0].kind == "BEGIN"
            and self.events[0].values == (SCHEMA, self.case, "GUEST_MONOTONIC_NS"),
            "wrong observed schema/case/clock",
        )
        require(self.events[-1].kind == "END", "closed capture required")


@dataclass(frozen=True)
class Check:
    case: str
    transport_observed: bool
    returned_bytes: bytes | None
    status: str = "BLOCKED"
    fd_table_generation: None = None
    global_prohibited_counts: None = None
    permissions: tuple[tuple[str, bool], ...] = PERMISSIONS


def parse_serial(raw: bytes, case: str) -> Capture:
    require(
        type(raw) is bytes and len(raw) <= 1024 * 1024 and raw.endswith(b"\n"),
        "bounded LF-terminated serial required",
    )
    # Physical LF only; splitlines would repair malformed control separators.
    lines = raw.split(b"\n")[:-1]
    lines = [line[:-1] if line.endswith(b"\r") else line for line in lines]
    start, stop, done = b"HFD_EXEC", b"HFD_PROBE_EXIT=0", b"HFD_DONE"
    require(all(lines.count(m) == 1 for m in (start, stop, done)), "exact execution markers")
    a, b, c = (lines.index(m) for m in (start, stop, done))
    require(a < b < c and c == b + 1, "execution marker ordering")
    require(not any(b"HFD" in line for line in lines[:a] + lines[c + 1 :]), "out of window marker")
    require(all(line.startswith(b"HFD ") for line in lines[a + 1 : b]), "unexpected diagnostic row")
    events = []
    for line in lines[a + 1 : b]:
        try:
            row = json.loads(line[4:].decode("ascii"), parse_constant=lambda _: None)
        except (ValueError, UnicodeError) as exc:
            raise ValueError("invalid physical JSON record") from exc
        # NaN/Inf are not unknowns: reject their source spelling before decoding.
        require(not any(t in line for t in (b"NaN", b"Infinity")), "nonfinite JSON forbidden")
        require(type(row) is list and len(row) >= 3, "flat event row required")
        events.append(Event(row[0], row[1], row[2], tuple(row[3:])))
    return Capture(case, tuple(events))


def check_case(capture: Capture, program_sha: str) -> Check:
    """Check scoped fixed-case facts, never establish authenticity/full closure."""
    require(type(capture) is Capture, "validated capture required")
    sha(program_sha)
    if capture.case not in ("HH01", "HH07"):
        return _check_negative(capture, program_sha)
    events = capture.events
    objects = {e.values[0]: e.values[1:] for e in events if e.kind == "OBJECT"}
    require(len(objects) == sum(e.kind == "OBJECT" for e in events), "duplicate object")
    require(set(objects) == {"primary", "program"}, "fixed object set required")
    primary, program = objects["primary"], objects["program"]
    require(
        primary[4:] == (47, 0) and program[3] == program_sha, "bound sealed input/program required"
    )
    require(capture.case in ("HH01", "HH07"), "negative case checker not implemented")
    require(primary[2] == (0 if capture.case == "HH07" else 17), "fixed input length")
    # Shape checks are intentionally closed to these fixed harmless programs.
    skeleton = [
        (e.kind, e.values[0] if e.kind in ("SNAP", "FD") else None)
        for e in events
        if e.kind not in ("OBJECT", "RELEASE")
    ]
    require(
        skeleton
        == [
            ("BEGIN", None),
            ("BIRTH", None),
            ("SNAP", "PRE_TRANSFER"),
            ("FD", "PRE_EXEC"),
            ("SNAP", "PRE_EXEC"),
            ("OFD_PIN", None),
            ("EXEC", None),
            ("FD", "POST_EXEC"),
            ("SNAP", "POST_EXEC"),
            ("READY", None),
            ("FD", "READ_CHECK"),
            ("READ", None),
            ("CLOSE", None),
            ("SNAP", "CLOSED"),
            ("REAP", None),
            ("END", None),
        ],
        "fixed control/barrier/lifetime order",
    )
    require(next(e.values for e in events if e.kind == "BIRTH") == (1,), "actual root birth")
    birth = next(e.seq for e in events if e.kind == "BIRTH")
    require(
        all(1 < e.seq < birth for e in events if e.kind == "OBJECT"),
        "actual held objects before root birth",
    )
    snapshots = {e.values[0]: e.values for e in events if e.kind == "SNAP"}
    require(
        snapshots
        == {
            "PRE_TRANSFER": ("PRE_TRANSFER", 0, 0, 1, 0, 0, 0, None),
            "PRE_EXEC": ("PRE_EXEC", 0, 1, 1, 65534, 65534, 1, None),
            "POST_EXEC": ("POST_EXEC", 1, 1, 1, 65534, 65534, 1, None),
            "CLOSED": ("CLOSED", 1, 0, 1, 65534, 65534, 1, None),
        },
        "actual snapshot/credential/exec cohort required",
    )
    fds = [e for e in events if e.kind == "FD"]
    require(
        [e.values[0] for e in fds] == ["PRE_EXEC", "POST_EXEC", "READ_CHECK"],
        "actual target FD snapshots required",
    )
    for e in fds:
        v = e.values
        stage, generation, fd, slot, dev, ino, size, flags, seals, err, digest, same, se = v
        require(
            (generation, fd, slot) == (0 if stage == "PRE_EXEC" else 1, 0, 0),
            "target FD/exec/slot observation cohort",
        )
        require(
            (dev, ino, size, digest) == primary[:4] and (seals, err) == (47, 0),
            "actual target object/seal mismatch",
        )
        require(
            flags & 3 == 0 and bool(flags & 524288) == (stage != "PRE_EXEC"),
            "actual target RDONLY/CLOEXEC flags",
        )
        require(
            (same is None and se > 0) or (type(same) is int and same == 0 and se == 0),
            "OFD equality unavailable is not zero",
        )
    pins = [e.values for e in events if e.kind == "OFD_PIN"]
    require(
        len(pins) == 1
        and pins[0][0] == 0
        and ((pins[0][1] == -1 and pins[0][2] > 0) or (pins[0][1] >= 0 and pins[0][2] == 0)),
        "actual OFD pin result required",
    )
    require(
        next(e.values for e in events if e.kind == "EXEC") == (0, 1, *program[:4]),
        "actual executed image must equal held program object",
    )
    require(next(e.values for e in events if e.kind == "READY") == (1,), "post-exec barrier")
    read = next(e.values for e in events if e.kind == "READ")
    require(read[:5] == (1, 0, 0, 0, 17) and read[5] == primary[2], "actual pread return")
    returned = bytes.fromhex(read[6])
    require(
        len(returned) == read[5] and hashlib.sha256(returned).hexdigest() == primary[3],
        "actual returned buffer/hash mismatch",
    )
    require(
        next(e.values for e in events if e.kind == "CLOSE") == (1, 0, 0, 0),
        "actual close success required",
    )
    require(
        next(e.values for e in events if e.kind == "REAP") == (1, "EXITED", 0),
        "actual successful root reap required",
    )
    release = [e for e in events if e.kind == "RELEASE"]
    labels = {e.values[0] for e in release}
    needed = {"primary_rw", "primary_ro", "program"}
    if pins[0][1] >= 0:
        needed.add("ofd_0")
    reap_seq = next(e.seq for e in events if e.kind == "REAP")
    require(
        labels == needed
        and len(labels) == len(release)
        and all(e.seq > reap_seq and e.values[1] == 0 for e in release),
        "all held pins released only after actual root reap",
    )
    require(events[-1].values == (1, None), "unknown drops is not observed zero")
    return Check(capture.case, True, returned)


def _check_negative(capture: Capture, program_sha: str) -> Check:
    """Only the five predeclared fixed diagnostic fault-injection sequences."""
    case, events = capture.case, capture.events
    alt = case in ("HH02", "HH06")
    gen = 0 if case in ("HH02", "HH03") else 1
    objects = {e.values[0]: e.values[1:] for e in events if e.kind == "OBJECT"}
    need = {"primary", "program"} | ({"alternate"} if alt else set())
    require(
        set(objects) == need and len(objects) == sum(e.kind == "OBJECT" for e in events),
        "fixed unique negative object set",
    )
    primary, program = objects["primary"], objects["program"]
    require(
        primary[2] == 17 and primary[4:] == (47, 0) and program[3] == program_sha,
        "fixed sealed input/program",
    )
    if alt:
        require(
            objects["alternate"][:2] != primary[:2] and objects["alternate"][2:] == primary[2:],
            "equal bytes are not same object",
        )
    # Closed order including individual FD rows, not a caller inventory digest.
    tokens = [
        (e.kind, e.values[0] if e.kind in ("FD", "SNAP") else None)
        for e in events
        if e.kind not in ("OBJECT", "RELEASE")
    ]
    order = [("BEGIN", None), ("BIRTH", None), ("SNAP", "PRE_TRANSFER"), ("FD", "PRE_EXEC")]
    if case in ("HH03", "HH06"):
        order.append(("FD", "PRE_EXEC"))
    order.append(("SNAP", "PRE_EXEC"))
    if gen:
        order += [("OFD_PIN", None)] * (2 if case == "HH06" else 1) + [("EXEC", None)]
    if case == "HH05":
        order.append(("SNAP", "POST_EXEC"))
    if case == "HH06":
        order += [
            ("FD", "POST_EXEC"),
            ("FD", "POST_EXEC"),
            ("SNAP", "POST_EXEC"),
            ("READY", None),
            ("CLOSE", None),
            ("DUP", None),
            ("FD", "REUSED"),
            ("FD", "REUSED"),
            ("SNAP", "REUSED"),
        ]
    order += [("DENY", None), ("REAP", None), ("END", None)]
    require(tokens == order, "fixed negative stage/barrier/lifetime order")
    birth = next(e for e in events if e.kind == "BIRTH")
    require(
        birth.values == (1,) and all(1 < e.seq < birth.seq for e in events if e.kind == "OBJECT"),
        "objects before actual birth",
    )
    snaps = {e.values[0]: e.values for e in events if e.kind == "SNAP"}
    expected = {
        "PRE_TRANSFER": ("PRE_TRANSFER", 0, 0, 1, 0, 0, 0, None),
        "PRE_EXEC": ("PRE_EXEC", 0, 2 if case in ("HH03", "HH06") else 1, 1, 65534, 65534, 1, None),
    }
    if case == "HH05":
        expected["POST_EXEC"] = ("POST_EXEC", 1, 0, 1, 65534, 65534, 1, None)
    if case == "HH06":
        expected.update(
            {
                "POST_EXEC": ("POST_EXEC", 1, 2, 1, 65534, 65534, 1, None),
                "REUSED": ("REUSED", 1, 2, 1, 65534, 65534, 1, None),
            }
        )
    require(snaps == expected, "actual negative inventory/credentials")
    fds = [e.values for e in events if e.kind == "FD"]
    bindings = [("PRE_EXEC", 0, 0, "alternate" if case == "HH02" else "primary")]
    if case in ("HH03", "HH06"):
        bindings.append(("PRE_EXEC", 3, 0, "alternate" if case == "HH06" else "primary"))
    if case == "HH06":
        bindings += [
            ("POST_EXEC", 0, 0, "primary"),
            ("POST_EXEC", 3, 0, "alternate"),
            ("REUSED", 0, 1, "alternate"),
            ("REUSED", 3, 0, "alternate"),
        ]
    require(len(fds) == len(bindings), "actual target FD rows required")
    for value, binding in zip(fds, bindings, strict=True):
        stage, fd, slot, label = binding
        require(
            value[:4] == (stage, 0 if stage == "PRE_EXEC" else 1, fd, slot)
            and (value[4], value[5], value[6], value[10]) == objects[label][:4]
            and value[8:10] == (47, 0),
            "actual wrong/reused object witness",
        )
        require(
            value[7] & 3 == 0
            and bool(value[7] & 524288)
            == ((stage != "PRE_EXEC" or case == "HH05") and not (stage == "REUSED" and fd == 0)),
            "actual negative FD flags",
        )
        same, error = value[11:]
        require(
            (same is None and error > 0)
            or (
                type(same) is int
                and error == 0
                and (same > 0 if stage == "REUSED" and fd == 0 else same == 0)
            ),
            "actual OFD result/errno, never invented identity",
        )
    pins = [e.values for e in events if e.kind == "OFD_PIN"]
    require(
        [p[0] for p in pins] == ([] if not gen else [0, 3] if case == "HH06" else [0])
        and all((p[1] == -1 and p[2] > 0) or (p[1] >= 0 and p[2] == 0) for p in pins),
        "negative actual OFD pin results",
    )
    require(
        all(e.values == (0, 1, *program[:4]) for e in events if e.kind == "EXEC"),
        "negative actual exec image binding",
    )
    require(all(e.values == (1,) for e in events if e.kind == "READY"), "negative local barrier")
    require(
        all(e.values == (1, 0, 0, 0) for e in events if e.kind == "CLOSE")
        and all(e.values == (1, 3, 0, 1, 0) for e in events if e.kind == "DUP"),
        "actual close/dup2 fault-injection results",
    )
    reasons = {
        "HH02": "PRE_EXEC_BINDING",
        "HH03": "EXTRA_FD",
        "HH04": "EARLY_READ",
        "HH05": "POST_EXEC_BINDING",
        "HH06": "BINDING_CHANGED",
    }
    require(
        next(e.values for e in events if e.kind == "DENY") == (reasons[case], gen, 0),
        "actual expected denial",
    )
    reap = next(e for e in events if e.kind == "REAP")
    require(reap.values == (gen, "SIGNALLED", 9), "actual kill/reap before release")
    releases = [e for e in events if e.kind == "RELEASE"]
    labels = {"primary_rw", "primary_ro", "program"}
    if alt:
        labels.update({"alternate_rw", "alternate_ro"})
    labels.update(f"ofd_{p[0]}" for p in pins if p[1] >= 0)
    require(
        {e.values[0] for e in releases} == labels
        and len(releases) == len(labels)
        and all(e.seq > reap.seq and e.values[1] == 0 for e in releases),
        "all negative pins released after root reap",
    )
    require(events[-1].values == (gen, None), "unknown event loss remains unknown")
    return Check(case, False, None)
