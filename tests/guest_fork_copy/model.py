"""Pure bounded OBSERVED_UNTRUSTED wire diagnostic,not synthetic-oracle admission."""

from dataclasses import dataclass, field

from tests.guest_raw_lifetime.model import PERMISSIONS, _fields, _uint, require

CASES = ("NORMAL", "READ_LOSS", "SMALL_BUFFER", "CONSTRUCTOR_FAIL", "TASK_FAIL", "ALLOC_FAIL")
RELEASE = "6.12.113-cpcopy-v1"
PAYLOADS = {
    "BEGIN": {"scan_bound", "capacity"},
    "BITMAPS": {"open_fds", "cloexec"},
    "READ": {"fd", "presence", "ofd"},
    "REFERENCE": {"fd", "read_ordinal"},
    "CLEAR_OPEN": {"fd", "read_ordinal"},
    "STORE": {"fd", "read_ordinal", "presence", "ofd"},
    "COPY_RETURN": {"result", "tail_zeroed", "reason"},
    "TASK_FINALIZE": {"result", "reason"},
    "ALLOC_FREE": {"reason"},
}
COMMON = {"n", "copy", "local", "scope", "actor", "task", "source", "dest", "kind"}
REASONS = {
    "NONE",
    "ALLOC_INJECTED",
    "CONSTRUCTOR_INJECTED",
    "TASK_INJECTED",
    "COPY_FAILED",
    "TASK_FAILED",
    "NATURAL_ALLOC",
}
Value = str | int | bool | None


@dataclass(frozen=True)
class Event:
    n: int
    copy_id: int
    local: int
    kind: str
    scope_id: int
    actor_id: int | None
    task_id: int
    source_id: int | None
    dest_id: int | None
    values: tuple[tuple[str, Value], ...]


@dataclass(frozen=True)
class Capture:
    case: str
    capacity: int
    copies: int
    attempted: int
    reserved: int
    committed: int
    failed: int
    discarded: int
    pending: int
    events: tuple[Event, ...]


@dataclass(frozen=True)
class Slot:
    copy_id: int
    fd: int
    presence: str
    file_id: int | None
    open_after: bool
    cloexec_bitmap_bit: bool
    binding_cloexec: bool | None


@dataclass(frozen=True)
class Decision:
    local_accounting_balanced: bool
    local_loss_observed: bool
    committed_stage_sequences: tuple[int, ...]
    identity_complete: bool
    slots: tuple[Slot, ...]
    reasons: tuple[str, ...]
    evidence_class: str = field(default="OBSERVED_UNTRUSTED", init=False)
    status: str = field(default="BLOCKED", init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def parse_serial(raw: bytes) -> Capture:
    require(type(raw) is bytes and 0 < len(raw) <= 2**21, "SERIAL_BOUND")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("SERIAL_ENCODING") from exc
    lines = [s.rstrip("\r") for s in text.splitlines() if s.startswith("CPC_")]
    require(5 <= len(lines) <= 517, "COPY_RECORD_BOUND")
    require(lines[0] == "CPC_DRIVER ok=1 root=0 child=0", "FIXED_DRIVER_FAILED")
    require(lines[-2:] == ["CPC_END", "CPC_EXIT ok=1"], "COMPLETED_SOURCE_FRAME_REQUIRED")
    meta = _fields(
        lines[1], "CPC_META", {"version", "case", "release", "cpus", "capacity", "copies"}
    )
    require(
        meta["version"] == "1"
        and meta["case"] in CASES
        and meta["release"] == RELEASE
        and meta["cpus"] == "1",
        "OBSERVED_SOURCE_COHORT",
    )
    cap, copies = _uint(meta["capacity"]), _uint(meta["copies"])
    require(
        cap == (128 if meta["case"] == "SMALL_BUFFER" else 512) and copies == 2,
        "FIXED_BUFFER_COPY_COHORT",
    )
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    counts = _fields(lines[2], "CPC_COUNT", set(names))
    events: list[Event] = []
    contexts: dict[int, tuple[int, ...]] = {}
    locals_seen: dict[int, int] = {}
    for line in lines[3:-2]:
        pairs = line.split(" ")
        kinds = [s[5:] for s in pairs if s.startswith("kind=")]
        require(len(kinds) == 1 and kinds[0] in PAYLOADS, "UNSUPPORTED_COPY_STAGE")
        kind = kinds[0]
        row = _fields(line, "CPC_EVENT", COMMON | PAYLOADS[kind])
        n, copy, local, scope, actor, task, source, dest = (
            _uint(row[k])
            for k in ("n", "copy", "local", "scope", "actor", "task", "source", "dest")
        )
        require(
            n > (events[-1].n if events else 0)
            and 1 <= copy <= copies
            and local > locals_seen.get(copy, 0)
            and scope > 0
            and task > 0,
            "COPY_SOURCE_ORDER",
        )
        context = (scope, actor, task, source, dest)
        require(contexts.setdefault(copy, context) == context, "COPY_CONTEXT_DRIFT")
        require(
            (task == scope and actor == source == 0)
            or (task != scope and actor > 0 and source > 0),
            "CREATOR_SOURCE_CONTEXT_REQUIRED",
        )
        roles = [v for v in (actor, task, source, dest) if v]
        require(
            len(roles) == len(set(roles)) and scope not in (source, dest), "COOKIE_ROLE_COLLISION"
        )
        values: dict[str, Value] = {}
        for name in PAYLOADS[kind]:
            value = row[name]
            if name == "presence":
                require(value in ("PRESENT", "NULL"), "POINTER_PRESENCE_REQUIRED")
                values[name] = value
            elif name == "reason":
                require(value in REASONS, "SOURCE_REASON_REQUIRED")
                values[name] = value
            elif name == "result":
                require(
                    value
                    in (
                        ("SUCCESS", "FAILED") if kind == "COPY_RETURN" else ("COMMITTED", "ABORTED")
                    ),
                    "SOURCE_RESULT_REQUIRED",
                )
                values[name] = value
            elif name == "tail_zeroed":
                require(value in ("-1", "0", "1"), "TAIL_AVAILABILITY_REQUIRED")
                values[name] = None if value == "-1" else value == "1"
            else:
                number = _uint(value)
                require(name != "fd" or number < 64, "FD_WIDTH_PROFILE")
                values[name] = (number or None) if name == "ofd" else number
        if kind in ("READ", "STORE"):
            require(values["presence"] != "NULL" or values["ofd"] is None, "NULL_IS_NOT_OFD")
            require(values["ofd"] not in set(roles) | {scope}, "COOKIE_ROLE_COLLISION")
        locals_seen[copy] = local
        events.append(
            Event(
                n,
                copy,
                local,
                kind,
                scope,
                actor or None,
                task,
                source or None,
                dest or None,
                tuple(sorted(values.items())),
            )
        )
    require(len(events) <= cap, "BUFFER_RECORD_BOUND")
    a, r, c, f, d, p = (_uint(counts[k]) for k in names)
    return Capture(meta["case"], cap, copies, a, r, c, f, d, p, tuple(events))


def _sequence(group: list[Event], reasons: list[str]) -> tuple[tuple[Slot, ...], bool]:
    require(
        len(group) == 196 and all(e.local == i for i, e in enumerate(group, 1)),
        "COPY_SEQUENCE_INCOMPLETE",
    )
    begin, bitmap = group[:2]
    require(begin.kind == "BEGIN" and bitmap.kind == "BITMAPS", "COPY_STAGE_ORDER")
    require(begin.dest_id is not None, "CONSTRUCTOR_ID_UNAVAILABLE")
    require(dict(begin.values) == {"scan_bound": 64, "capacity": 64}, "UNSUPPORTED_COPY_GEOMETRY")
    bits = dict(bitmap.values)
    opened, cloexec = bits["open_fds"], bits["cloexec"]
    assert type(opened) is int and type(cloexec) is int
    slots = []
    for fd in range(64):
        read, branch, store = group[2 + 3 * fd : 5 + 3 * fd]
        require(
            read.kind == "READ"
            and store.kind == "STORE"
            and branch.kind in ("REFERENCE", "CLEAR_OPEN"),
            "COPY_STAGE_ORDER",
        )
        x, y, z = dict(read.values), dict(branch.values), dict(store.values)
        require(x["fd"] == y["fd"] == z["fd"] == fd, "COPY_FD_ORDER")
        require(y["read_ordinal"] == z["read_ordinal"] == read.local, "READ_PAIR_MISMATCH")
        require(x["presence"] == z["presence"] and x["ofd"] == z["ofd"], "READ_STORE_MISMATCH")
        present = x["presence"] == "PRESENT"
        require(branch.kind == ("REFERENCE" if present else "CLEAR_OPEN"), "COPY_BRANCH_MISMATCH")
        bit, cl = bool(opened & (1 << fd)), bool(cloexec & (1 << fd))
        require(not present or bit, "OPEN_POINTER_CONTRADICTION")
        ofd = x["ofd"]
        assert ofd is None or type(ofd) is int
        if present and ofd is None:
            reasons.append("OFD_ID_UNAVAILABLE")
        slots.append(
            Slot(
                read.copy_id,
                fd,
                "PRESENT" if present else "NULL",
                ofd,
                present and bit,
                cl,
                cl if present else None,
            )
        )
    returned, finalized = group[-2:]
    require(
        returned.kind == "COPY_RETURN" and finalized.kind == "TASK_FINALIZE", "COPY_STAGE_ORDER"
    )
    require(
        dict(returned.values)["result"] == "SUCCESS"
        and dict(returned.values)["tail_zeroed"] is True,
        "COPY_CONSTRUCTOR_FAILED",
    )
    committed = dict(finalized.values)["result"] == "COMMITTED"
    if not committed:
        reasons.append("TASK_ABORTED")
    return tuple(slots), committed


def assess(capture: Capture) -> Decision:
    reasons: list[str] = []
    balanced = (
        capture.attempted == capture.reserved + capture.failed
        and capture.reserved == capture.committed + capture.discarded + capture.pending
        and capture.committed == len(capture.events)
        and capture.discarded == capture.pending == 0
    )
    if not balanced:
        reasons.append("LOCAL_ACCOUNTING_MISMATCH")
    if capture.failed:
        reasons.append("LOCAL_RESERVATION_LOSS")
    if (
        any(e.n != i for i, e in enumerate(capture.events, 1))
        or len(capture.events) != capture.attempted
    ):
        reasons.append("GLOBAL_COPY_EMISSION_GAP")
    committed: list[int] = []
    slots: list[Slot] = []
    identity = True
    creators: dict[int, int] = {}
    for copy in range(1, capture.copies + 1):
        group = [e for e in capture.events if e.copy_id == copy]
        if not group:
            reasons.append("COPY_ATTEMPT_MISSING")
            identity = False
            continue
        if any(v is None for v in (group[0].actor_id, group[0].source_id, group[0].dest_id)):
            reasons.append("SOURCE_CONTEXT_UNAVAILABLE")
            identity = False
        if any(e.kind == "COPY_RETURN" and dict(e.values)["result"] == "FAILED" for e in group):
            reasons.append("COPY_CONSTRUCTOR_FAILED")
        if any(e.kind == "TASK_FINALIZE" and dict(e.values)["result"] == "ABORTED" for e in group):
            reasons.append("TASK_ABORTED")
        first = group[0]
        if first.task_id != first.scope_id and creators.get(first.actor_id or 0) != first.source_id:
            reasons.append("SOURCE_TASK_NAMESPACE_MISMATCH")
            continue
        try:
            observed, done = _sequence(group, reasons)
            slots.extend(observed)
            if done:
                committed.append(copy)
                if first.dest_id is not None:
                    creators[first.task_id] = first.dest_id
        except ValueError as exc:
            reasons.append(str(exc))
    identity = identity and not any(s.presence == "PRESENT" and s.file_id is None for s in slots)
    return Decision(
        balanced,
        capture.failed > 0,
        tuple(committed),
        identity,
        tuple(slots),
        tuple(dict.fromkeys(reasons)),
    )
