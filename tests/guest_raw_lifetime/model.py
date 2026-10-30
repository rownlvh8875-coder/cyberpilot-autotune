"""Pure partial raw-event diagnostic; never a qualified lifecycle graph or authority."""

import re
from dataclasses import dataclass, field

CASES = ("NORMAL", "FORCED_LOSS", "SMALL_BUFFER")
RELEASE = "6.12.113-cplife-v1"
KINDS = frozenset(
    ("FILE_NEW", "FILE_FREE", "TABLE_NEW", "TABLE_FREE", "INSTALL", "CLOSE", "FLAGS", "REPLACE")
)
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


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


@dataclass(frozen=True)
class RawEvent:
    seq: int
    kind: str
    table_id: int | None
    file_id: int | None
    old_id: int | None
    fd: int | None
    flags: int
    mono_ns: int


@dataclass(frozen=True)
class Capture:
    case: str
    capacity: int
    attempted: int
    reserved: int
    committed: int
    failed: int
    discarded: int
    pending: int
    events: tuple[RawEvent, ...]


@dataclass(frozen=True)
class Diagnostic:
    local_accounting_balanced: bool
    local_loss_observed: bool
    reasons: tuple[str, ...]
    status: str = field(default="BLOCKED", init=False)
    actual_global_drops: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def _fields(line: str, prefix: str, names: set[str]) -> dict[str, str]:
    require(line.startswith(prefix + " "), "WRONG_RAW_RECORD")
    pairs = [p.split("=") for p in line[len(prefix) + 1 :].split(" ")]
    require(all(len(p) == 2 and p[0] and p[1] for p in pairs), "MALFORMED_RAW_FIELD")
    require(len(pairs) == len(names) and {p[0] for p in pairs} == names, "RAW_FIELD_COHORT")
    return dict(pairs)


def _uint(text: str) -> int:
    require(re.fullmatch(r"0|[1-9][0-9]*", text) is not None, "EXACT_UINT_REQUIRED")
    value = int(text)
    require(value < 2**64, "UINT64_OVERFLOW")
    return value


def parse_serial(raw: bytes) -> Capture:
    require(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024, "SERIAL_BOUND")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("SERIAL_ENCODING") from exc
    lines = [line.rstrip("\r") for line in text.splitlines() if line.startswith("CPL_")]
    require(len(lines) >= 5 and len(lines) <= 134, "RAW_RECORD_BOUND")
    require(lines[0] == "CPL_DRIVER ok=1 child=0", "DRIVER_WORKLOAD_FAILED")
    meta = _fields(lines[1], "CPL_META", {"version", "case", "release", "cpus", "capacity"})
    require(
        meta["version"] == "1"
        and meta["release"] == RELEASE
        and meta["cpus"] == "1"
        and meta["case"] in CASES,
        "RAW_SOURCE_COHORT",
    )
    capacity = _uint(meta["capacity"])
    require(capacity == (2 if meta["case"] == "SMALL_BUFFER" else 128), "BUFFER_COHORT")
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    counts = _fields(lines[2], "CPL_COUNT", set(names))
    # CPL_EXIT is an optional outer driver completion, never part of the source frame.
    if lines[-1] == "CPL_EXIT ok=1":
        lines.pop()
    require(lines[-1] == "CPL_END", "SOURCE_END_REQUIRED")
    events: list[RawEvent] = []
    for line in lines[3:-1]:
        row = _fields(
            line, "CPL_EVENT", {"seq", "kind", "table", "ofd", "old", "fd", "flags", "mono"}
        )
        require(row["kind"] in KINDS, "UNSUPPORTED_RAW_STAGE")
        seq, table, ofd, old, flags, mono = (
            _uint(row[n]) for n in ("seq", "table", "ofd", "old", "flags", "mono")
        )
        fd = None if row["fd"] == "-1" else _uint(row["fd"])
        require((fd is None or fd < 2**31) and flags < 2**32, "RAW_INT_WIDTH")
        require(seq > (events[-1].seq if events else 0), "DUPLICATE_OR_REORDERED_SOURCE_SEQ")
        events.append(
            RawEvent(seq, row["kind"], table or None, ofd or None, old or None, fd, flags, mono)
        )
    require(len(events) <= capacity, "BUFFER_RECORD_BOUND")
    attempted, reserved, committed, failed, discarded, pending = (_uint(counts[n]) for n in names)
    return Capture(
        meta["case"],
        capacity,
        attempted,
        reserved,
        committed,
        failed,
        discarded,
        pending,
        tuple(events),
    )


def assess(capture: Capture) -> Diagnostic:
    """Only local self-reported accounting consistency; no completeness/authenticity proof."""
    reasons = []
    balanced = (
        capture.attempted == capture.reserved + capture.failed
        and capture.reserved == capture.committed + capture.discarded + capture.pending
        and capture.committed == len(capture.events)
        and capture.discarded == capture.pending == 0
    )
    if not balanced:
        reasons.append("LOCAL_ACCOUNTING_OR_TRANSPORT_MISMATCH")
    if capture.failed:
        reasons.append("LOCAL_RESERVATION_LOSS")
    if len(capture.events) != capture.attempted or any(
        e.seq != index for index, e in enumerate(capture.events, 1)
    ):
        reasons.append("SOURCE_SEQUENCE_GAP")
    return Diagnostic(balanced, capture.failed > 0, tuple(reasons))
