"""Pure partial source-scope diagnostic; never a graph, inventory or authority."""

from dataclasses import dataclass, field

from tests.guest_raw_lifetime.model import PERMISSIONS, _fields, _uint
from tests.guest_raw_lifetime.model import require as require

CASES = ("NORMAL", "ROOT_BIRTH_LOSS", "SMALL_BUFFER")
RELEASE = "6.12.113-cpscope-v1"
CREATION = {"TASK_ALLOC", "TABLE_NEW", "TASK_COMMIT"}
BINDING = {"INSTALL", "CLOSE", "FLAGS", "REPLACE"}
KINDS = CREATION | BINDING | {"FILE_NEW", "FILE_FREE", "TABLE_FREE"}


@dataclass(frozen=True)
class RawEvent:
    seq: int
    kind: str
    scope_id: int
    actor_id: int | None
    task_id: int | None
    table_id: int | None
    file_id: int | None
    old_id: int | None
    fd: int | None
    flags: int | None
    mono_ns: int


@dataclass(frozen=True)
class Capture:
    case: str
    root_id: int
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
    root_creation_observed: bool
    reasons: tuple[str, ...]
    status: str = field(default="BLOCKED", init=False)
    actual_global_drops: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def parse_serial(raw: bytes) -> Capture:
    require(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024, "SERIAL_BOUND")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("SERIAL_ENCODING") from exc
    lines = [s.rstrip("\r") for s in text.splitlines() if s.startswith("CPS_")]
    require(5 <= len(lines) <= 133, "RAW_RECORD_BOUND")
    require(lines[0] == "CPS_DRIVER ok=1 root=0 child=0", "FIXED_WORKLOAD_FAILED")
    require(lines[-2:] == ["CPS_END", "CPS_EXIT ok=1"], "COMPLETED_SOURCE_FRAME_REQUIRED")
    m = _fields(lines[1], "CPS_META", {"version", "case", "release", "cpus", "capacity", "root"})
    require(
        m["version"] == "1" and m["release"] == RELEASE and m["cpus"] == "1" and m["case"] in CASES,
        "RAW_SOURCE_COHORT",
    )
    root, capacity = _uint(m["root"]), _uint(m["capacity"])
    require(root > 0, "ROOT_ID_UNAVAILABLE")
    require(capacity == (2 if m["case"] == "SMALL_BUFFER" else 128), "BUFFER_COHORT")
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    counts = _fields(lines[2], "CPS_COUNT", set(names))
    events: list[RawEvent] = []
    for line in lines[3:-2]:
        row = _fields(
            line,
            "CPS_EVENT",
            {"seq", "kind", "scope", "actor", "task", "table", "ofd", "old", "fd", "flags", "mono"},
        )
        kind = row["kind"]
        require(kind in KINDS, "UNSUPPORTED_RAW_STAGE")
        seq, scope, actor, task, table, ofd, old, mono = (
            _uint(row[n]) for n in ("seq", "scope", "actor", "task", "table", "ofd", "old", "mono")
        )
        fd = None if row["fd"] == "-1" else _uint(row["fd"])
        flags = None if row["flags"] == "-1" else _uint(row["flags"])
        require(scope == root, "WRONG_SOURCE_SCOPE")
        require(seq > (events[-1].seq if events else 0), "DUPLICATE_OR_REORDERED_SOURCE_SEQ")
        require((fd is None or fd < 2**31) and (flags is None or flags <= 1), "RAW_INT_WIDTH")
        require((task > 0) == (kind in CREATION), "SUBJECT_TASK_STAGE")
        require((fd is not None) == (kind in BINDING), "FD_STAGE")
        require((flags is not None) == (kind in {"INSTALL", "FLAGS", "REPLACE"}), "FLAG_STAGE")
        require((table > 0) == (kind not in {"TASK_ALLOC", "FILE_NEW", "FILE_FREE"}), "TABLE_STAGE")
        require((ofd > 0) == (kind in {"FILE_NEW", "FILE_FREE"}) or kind in BINDING, "OFD_STAGE")
        require(not old or kind in {"TABLE_NEW", "REPLACE"}, "OLD_COOKIE_STAGE")
        events.append(
            RawEvent(
                seq,
                kind,
                scope,
                actor or None,
                task or None,
                table or None,
                ofd or None,
                old or None,
                fd,
                flags,
                mono,
            )
        )
    require(len(events) <= capacity, "BUFFER_RECORD_BOUND")
    attempted, reserved, committed, failed, discarded, pending = (_uint(counts[n]) for n in names)
    return Capture(
        m["case"],
        root,
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
    """Self-reported creation linkage only, never source closure or authenticity."""
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
        e.seq != i for i, e in enumerate(capture.events, 1)
    ):
        reasons.append("SOURCE_SEQUENCE_GAP")
    tasks: dict[int, dict[str, RawEvent]] = {}
    issuers: set[int] = set()
    for e in capture.events:
        cookie = (
            e.task_id
            if e.kind == "TASK_ALLOC"
            else e.table_id
            if e.kind == "TABLE_NEW"
            else e.file_id
            if e.kind == "FILE_NEW"
            else None
        )
        if cookie is not None:
            if cookie in issuers:
                reasons.append("SOURCE_COOKIE_COLLISION")
            issuers.add(cookie)
        if e.task_id is not None:
            stages = tasks.setdefault(e.task_id, {})
            if e.kind in stages:
                reasons.append("DUPLICATE_CREATION_STAGE")
            stages[e.kind] = e
    complete: dict[int, RawEvent] = {}
    for task, stages in tasks.items():
        if set(stages) != CREATION:
            continue
        a, t, c = (stages[k] for k in ("TASK_ALLOC", "TABLE_NEW", "TASK_COMMIT"))
        if task != capture.root_id and a.actor_id is None:
            reasons.append("DESCENDANT_CREATOR_UNAVAILABLE")
            continue
        if (
            a.seq < t.seq < c.seq
            and a.actor_id == t.actor_id == c.actor_id
            and t.table_id == c.table_id
            and a.actor_id != task
        ):
            complete[task] = c
    root = complete.get(capture.root_id)
    if root is None or root.actor_id is not None:
        reasons.append("ROOT_CREATION_LINK_INCOMPLETE")
    root_table = tasks.get(capture.root_id, {}).get("TABLE_NEW")
    if root_table is not None and root_table.old_id is not None:
        reasons.append("ROOT_PARENT_CONTEXT_MISMATCH")
    for e in capture.events:
        if e.actor_id is not None:
            parent = complete.get(e.actor_id)
            if parent is None or parent.seq >= e.seq:
                reasons.append("TASK_COHORT_INCOMPLETE")
            elif e.kind in BINDING and parent.table_id != e.table_id:
                reasons.append("TASK_NAMESPACE_MISMATCH")
        if e.kind == "TABLE_NEW" and e.actor_id is not None:
            parent = complete.get(e.actor_id)
            if parent is None or parent.table_id != e.old_id:
                reasons.append("TASK_NAMESPACE_MISMATCH")
    # Missing descendants and record loss cannot produce an affirmative context verdict.
    if set(tasks) != set(complete):
        reasons.append("TASK_COHORT_INCOMPLETE")
    unique = tuple(dict.fromkeys(reasons))
    return Diagnostic(balanced, capture.failed > 0, not unique, unique)
