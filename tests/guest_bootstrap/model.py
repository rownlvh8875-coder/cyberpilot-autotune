"""Pure observed origin diagnostics. No synthetic-oracle or operational admission."""

from tests.guest_raw_lifetime.model import require

from .contracts import Capture, CopyBinding, Decision, Event, SeedBinding, Value

Catalog = dict[int, tuple[str, str, int]]


def _control_order(capture: Capture) -> None:
    """Check only observed one-shot relations;absence never invents a transition."""
    stages = {
        kind: [e.n for e in capture.events if e.kind == kind]
        for kind in ("SEED_BEGIN", "SEED_END", "SEED_ABORT", "ARM")
    }
    require(all(len(v) <= 1 for v in stages.values()), "CONTROL_STAGE_CONTRADICTION")
    begin, end, abort, arm = (
        stages[k][0] if stages[k] else None for k in ("SEED_BEGIN", "SEED_END", "SEED_ABORT", "ARM")
    )
    copies = [e.n for e in capture.events if "copy" in dict(e.values)]
    if abort is not None:
        require(
            capture.seed_walk == "ABORTED" and end is None and arm is None and not copies,
            "CONTROL_STAGE_CONTRADICTION",
        )
    if end is not None:
        require(capture.seed_walk == "COMPLETE", "CONTROL_STAGE_CONTRADICTION")
    require(
        all(
            left is None or right is None or left < right
            for left, right in ((begin, end), (begin, abort), (begin, arm), (end, arm))
        ),
        "CONTROL_STAGE_CONTRADICTION",
    )
    terminal = end if end is not None else abort
    for e in capture.events:
        row = dict(e.values)
        if "copy" in row:
            require(arm is None or arm < e.n, "CONTROL_STAGE_CONTRADICTION")
        if e.kind == "SEED_SLOT" or (e.kind == "NODE" and row["origin"] == "FIRST_OBSERVED"):
            require(
                (begin is None or begin < e.n) and (terminal is None or e.n < terminal),
                "CONTROL_STAGE_CONTRADICTION",
            )
        if e.kind == "SEED_REJECT":
            require(begin is None or begin < e.n, "CONTROL_STAGE_CONTRADICTION")
        if e.kind == "ARM_REJECT":
            require(
                (end is None or e.n < end) and (arm is None or e.n < arm),
                "CONTROL_STAGE_CONTRADICTION",
            )


def _number(value: Value) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("POSITIVE_ID_OR_ORDINAL_REQUIRED")
    return value


def _lookup(value: Value, role: str, n: int, catalog: Catalog, missing: set[int]) -> int | None:
    if value is None:
        return None
    cookie = _number(value)
    if cookie not in catalog:
        missing.add(cookie)
        return None
    actual_role, _, issued = catalog[cookie]
    require(actual_role == role, "OBJECT_ROLE_COLLISION")
    require(issued < n, "FUTURE_ORIGIN_WITNESS")
    return cookie


def _origin(value: Value, origin: Value, n: int, catalog: Catalog, missing: set[int]) -> int | None:
    cookie = _lookup(value, "OFD", n, catalog, missing)
    if cookie is not None:
        require(catalog[cookie][1] == origin, "OBJECT_ORIGIN_MISMATCH")
    return cookie


def _catalog(capture: Capture, fatal: list[str]) -> tuple[Catalog, int | None, bool]:
    arms = [e.n for e in capture.events if e.kind == "ARM"]
    stops = [e.n for e in capture.events if e.kind == "STOP"]
    require(len(arms) <= 1 and len(stops) <= 1, "DUPLICATE_CONTROL_STAGE")
    arm = arms[0] if arms else None
    require(not stops or capture.events[-1].n == stops[0], "EVENT_AFTER_STOP")
    catalog: Catalog = {}
    for e in capture.events:
        row = dict(e.values)
        if e.kind == "NODE":
            cookie = _number(row["object"])
            if cookie in catalog:
                fatal.append("OBJECT_ID_REISSUED")
                continue
            role, origin = row["role"], row["origin"]
            assert type(role) is str and type(origin) is str
            if arm is not None:
                if origin == "FIRST_OBSERVED" and e.n > arm:
                    fatal.append("POST_ARM_SEED_ORIGIN")
                if origin == "ALLOCATION" and e.n < arm:
                    fatal.append("PRE_ARM_ALLOCATION_ORIGIN")
            catalog[cookie] = role, origin, e.n
        if e.kind in ("SEED_REJECT", "ARM_REJECT"):
            expected = "ALREADY_ATTEMPTED" if e.kind == "SEED_REJECT" else "SEED_NOT_COMPLETE"
            require(row["reason"] == expected, "REJECT_REASON_CONTRADICTION")
        if e.kind == "SEED_ABORT":
            require(
                row["reason"]
                in ("INJECTED", "CONTEXT_UNSUPPORTED", "TAG_STATE_INVALID", "ISSUER_EXHAUSTED"),
                "ABORT_REASON_CONTRADICTION",
            )
    return catalog, arm, bool(stops)


def _seed(
    capture: Capture, catalog: Catalog, missing: set[int]
) -> tuple[tuple[SeedBinding, ...], tuple[int, int] | None, bool]:
    begins = [e.n for e in capture.events if e.kind == "SEED_BEGIN"]
    ends = [e for e in capture.events if e.kind == "SEED_END"]
    require(len(begins) <= 1 and len(ends) <= 1, "DUPLICATE_SEED_STAGE")
    group = [e for e in capture.events if e.kind == "SEED_SLOT"]
    result = []
    context = None
    for i, e in enumerate(group):
        row = dict(e.values)
        require(row["fd"] == i and (not begins or e.n > begins[0]), "SEED_SLOT_ORDER")
        if ends:
            require(e.n < ends[0].n, "SEED_SLOT_AFTER_END")
        parent, source = _number(row["task"]), _number(row["source"])
        _lookup(parent, "TASK", e.n, catalog, missing)
        _lookup(source, "NAMESPACE", e.n, catalog, missing)
        pair = parent, source
        require(context is None or context == pair, "SEED_CONTEXT_DRIFT")
        context = pair
        _origin(row["ofd"], row["origin"], e.n, catalog, missing)
        presence, origin, ofd, opened, cloexec = (
            row[k] for k in ("presence", "origin", "ofd", "open", "cloexec")
        )
        assert type(presence) is str and type(origin) is str
        assert ofd is None or type(ofd) is int
        assert type(opened) is bool and type(cloexec) is bool
        require(presence != "PRESENT" or opened, "SEED_OPEN_POINTER_CONTRADICTION")
        result.append(
            SeedBinding(
                i,
                presence,
                ofd,
                origin,
                opened,
                cloexec,
                cloexec if presence == "PRESENT" else None,
            )
        )
    if ends:
        end = dict(ends[0].values)
        require(context == (end["parent"], end["source"]), "SEED_END_CONTEXT_MISMATCH")
    complete = bool(begins and ends and len(group) == 64 and capture.seed_walk == "COMPLETE")
    return tuple(result), context, complete


def _sequence(
    group: list[Event], catalog: Catalog, missing: set[int]
) -> tuple[tuple[CopyBinding, ...], bool]:
    require(
        len(group) == 196 and all(dict(e.values)["local"] == i for i, e in enumerate(group, 1)),
        "COPY_SEQUENCE_INCOMPLETE",
    )
    begin, bitmaps = group[:2]
    x = dict(begin.values)
    known = [x[k] for k in ("actor", "task", "source", "dest") if x[k] is not None]
    require(len(known) == len(set(known)), "COPY_IDENTITY_COLLISION")
    require(begin.kind == "BEGIN" and bitmaps.kind == "BITMAPS", "COPY_STAGE_ORDER")
    require(x["scan_bound"] == x["capacity"] == 64, "COPY_SCAN_PROFILE")
    for key, role in (
        ("actor", "TASK"),
        ("task", "TASK"),
        ("source", "NAMESPACE"),
        ("dest", "NAMESPACE"),
    ):
        value = _lookup(x[key], role, begin.n, catalog, missing)
        if value is not None and key in ("task", "dest"):
            require(catalog[value][1] == "ALLOCATION", "FORK_SUBJECT_ALLOCATION_REQUIRED")
    bits = dict(bitmaps.values)
    opened, cloexec = bits["open_fds"], bits["cloexec"]
    assert type(opened) is int and type(cloexec) is int
    bindings = []
    for fd in range(64):
        read, branch, store = group[2 + 3 * fd : 5 + 3 * fd]
        a, b, c = dict(read.values), dict(branch.values), dict(store.values)
        require(read.kind == "READ" and store.kind == "STORE", "COPY_STAGE_ORDER")
        require(a["fd"] == b["fd"] == c["fd"] == fd, "COPY_FD_ORDER")
        require(b["read_ordinal"] == c["read_ordinal"] == a["local"], "READ_PAIR_MISMATCH")
        require(
            (a["presence"], a["ofd"], a["origin"]) == (c["presence"], c["ofd"], c["origin"]),
            "READ_STORE_ORIGIN_MISMATCH",
        )
        present = a["presence"] == "PRESENT"
        require(branch.kind == ("REFERENCE" if present else "CLEAR_OPEN"), "COPY_BRANCH_MISMATCH")
        _origin(a["ofd"], a["origin"], read.n, catalog, missing)
        bit, cl = bool(opened & (1 << fd)), bool(cloexec & (1 << fd))
        require(not present or bit, "COPY_OPEN_POINTER_CONTRADICTION")
        ofd, origin = a["ofd"], a["origin"]
        assert ofd is None or type(ofd) is int
        assert type(origin) is str
        bindings.append(
            CopyBinding(
                _number(a["copy"]),
                fd,
                "PRESENT" if present else "NULL",
                ofd,
                origin,
                present and bit,
                cl,
                cl if present else None,
            )
        )
    returned, finalized = group[-2:]
    a, b = dict(returned.values), dict(finalized.values)
    require(
        returned.kind == "COPY_RETURN" and finalized.kind == "TASK_FINALIZE", "COPY_STAGE_ORDER"
    )
    require(a["result"] == "SUCCESS" and a["tail_zeroed"] is True, "COPY_CONSTRUCTOR_FAILED")
    done = b["result"] == "COMMITTED"
    require(
        a["reason"] == "NONE"
        and b["reason"] in (("NONE",) if done else ("TASK_INJECTED", "TASK_FAILED")),
        "TERMINAL_REASON_CONTRADICTION",
    )
    return tuple(bindings), done


def assess(capture: Capture) -> Decision:
    reasons: list[str] = []
    fatal: list[str] = []
    missing: set[int] = set()
    seeds: tuple[SeedBinding, ...] = ()
    copied: list[CopyBinding] = []
    committed: list[int] = []
    catalog: Catalog = {}
    complete = False
    links: list[tuple[int, int]] = []
    balanced = (
        capture.attempted == capture.reserved + capture.failed
        and capture.reserved == capture.committed + capture.discarded + capture.pending
        and capture.committed == len(capture.events)
        and capture.discarded == capture.pending == 0
    )
    if not balanced:
        fatal.append("LOCAL_ACCOUNTING_MISMATCH")
    if capture.failed:
        reasons.append("LOCAL_RESERVATION_LOSS")
    if len(capture.events) != capture.attempted or any(
        e.n != i for i, e in enumerate(capture.events, 1)
    ):
        reasons.append("EMISSION_GAP")
    try:
        catalog, arm, stopped = _catalog(capture, fatal)
        _control_order(capture)
        if not stopped:
            reasons.append("STOP_RECORD_UNAVAILABLE")
        if arm is None:
            reasons.append("ARM_RECORD_UNAVAILABLE")
        seeds, seed_context, complete = _seed(capture, catalog, missing)
        if not complete:
            reasons.append("INCOMPLETE_SEED_WALK")
        creators: dict[int, int] = {}
        root_context_witnessed = False
        for copy in range(1, capture.copies + 1):
            group = [e for e in capture.events if dict(e.values).get("copy") == copy]
            if not group:
                reasons.append("COPY_ATTEMPT_UNAVAILABLE")
                continue
            first = dict(group[0].values)
            context = tuple(first[k] for k in ("scope", "actor", "task", "source", "dest"))
            require(
                all(
                    tuple(dict(e.values)[k] for k in ("scope", "actor", "task", "source", "dest"))
                    == context
                    for e in group
                ),
                "COPY_CONTEXT_DRIFT",
            )
            require(first["scope"] == capture.root_id, "MANAGED_ROOT_SCOPE_MISMATCH")
            if copy == 1:
                require(
                    first["task"] == capture.root_id and first["actor"] != capture.root_id,
                    "MANAGED_ROOT_MEMBERSHIP_MISMATCH",
                )
                require(
                    seed_context is None or (first["actor"], first["source"]) == seed_context,
                    "SEED_TO_COPY_CONTEXT_MISMATCH",
                )
            else:
                parent = creators.get(_number(first["actor"]))
                if parent is not None:
                    require(parent == first["source"], "SOURCE_TASK_NAMESPACE_MISMATCH")
                else:
                    reasons.append("SOURCE_TASK_NAMESPACE_UNAVAILABLE")
            try:
                bindings, done = _sequence(group, catalog, missing)
                copied.extend(bindings)
                if done:
                    committed.append(copy)
                    creators[_number(first["task"])] = _number(first["dest"])
                    if copy == 1:
                        root_context_witnessed = all(
                            type(first[k]) is int and first[k] in catalog
                            for k in ("actor", "task", "source", "dest")
                        )
                else:
                    reasons.append("TASK_ABORTED")
            except ValueError as exc:
                if str(exc) in ("COPY_SEQUENCE_INCOMPLETE", "COPY_CONSTRUCTOR_FAILED"):
                    reasons.append(str(exc))
                else:
                    fatal.append(str(exc))
        if complete and arm is not None and stopped and 1 in committed and root_context_witnessed:
            root_bindings = {b.fd: b for b in copied if b.copy_id == 1}
            for seed in seeds:
                target = root_bindings[seed.fd]
                require(
                    (seed.presence, seed.file_id, seed.origin)
                    == (target.presence, target.file_id, target.origin),
                    "SEED_COPY_BINDING_MISMATCH",
                )
                if (
                    seed.presence == "PRESENT"
                    and seed.file_id is not None
                    and seed.file_id in catalog
                ):
                    links.append((seed.fd, seed.file_id))
    except ValueError as exc:
        fatal.append(str(exc))
    if missing:
        reasons.append("OBJECT_ISSUANCE_UNAVAILABLE")
    unknown = sum(
        e.kind == "READ"
        and dict(e.values)["presence"] == "PRESENT"
        and dict(e.values)["ofd"] is None
        for e in capture.events
    )
    return Decision(
        balanced,
        capture.failed > 0,
        complete,
        seeds,
        tuple(copied),
        tuple(committed),
        () if fatal else tuple(links),
        tuple(sorted(k for k, v in catalog.items() if v[1] == "FIRST_OBSERVED")),
        tuple(sorted(k for k, v in catalog.items() if v[1] == "ALLOCATION")),
        unknown,
        tuple(sorted(missing)),
        tuple(dict.fromkeys([*reasons, *fatal])),
    )
