"""Pure diagnostics of available CPR scalars; never a lifetime/HB admission engine."""

from tests.guest_raw_lifetime.model import require

from .contracts import Capture, Decision, Event, Snapshot
from .wire import CONTEXT, PAYLOAD


def _validate_markers(indexed: dict[tuple[int, str, int], Event]) -> None:
    groups: dict[tuple[int, int], dict[str, Event]] = {}
    pointers = {
        (copy, int(dict(event.values)["local"])): fd
        for (copy, stage, fd), event in indexed.items()
        if stage == "POINTER_READ"
    }
    for (copy, stage, fd), event in indexed.items():
        groups.setdefault((copy, fd), {})[stage] = event
        if stage != "POINTER_READ":
            values = dict(event.values)
            ordinal = int(values["read_ordinal"])
            require(ordinal < int(values["local"]), "CONSUMED_READ_NOT_PRECEDING")
            pointer_fd = pointers.get((copy, ordinal))
            require(pointer_fd is None or pointer_fd == fd, "CONSUMED_POINTER_FOREIGN_FD")
    for group in groups.values():
        ordinals = {
            int(dict(event.values)["local" if stage == "POINTER_READ" else "read_ordinal"])
            for stage, event in group.items()
        }
        require(len(ordinals) == 1, "CONSUMED_ORDINAL_CONTRADICTION")
        presence = {
            dict(group[stage].values)["presence"]
            for stage in ("POINTER_READ", "STORE")
            if stage in group
        }
        require(len(presence) <= 1, "POINTER_STORE_PRESENCE_CONTRADICTION")
        present_branch = "PRESENT" in presence or bool({"REFERENCE", "TAG_SNAPSHOT"} & group.keys())
        require(
            not present_branch or ("CLEAR_OPEN" not in group and "NULL" not in presence),
            "NULL_PRESENT_BRANCH_CONTRADICTION",
        )
        observed = [
            group[stage].n
            for stage in ("POINTER_READ", "REFERENCE", "CLEAR_OPEN", "STORE", "TAG_SNAPSHOT")
            if stage in group
        ]
        require(observed == sorted(observed), "OBSERVED_MARKER_ORDER_INVALID")


def assess(capture: Capture) -> Decision:
    a, r, c, f, d, p = capture.counts
    balanced = a == r + f and r == c + d + p and c == len(capture.events)
    balanced = balanced and all(e.n <= a for e in capture.events)
    reasons = []
    if not balanced:
        reasons.append("LOCAL_ACCOUNTING_UNBALANCED")
    if f or d or p:
        reasons.append("LOCAL_LOSS_OBSERVED")
    contexts: dict[int, tuple[object, ...]] = {}
    last: dict[int, int] = {}
    indexed: dict[tuple[int, str, int], Event] = {}
    raw_snapshots: list[Event] = []
    for event in capture.events:
        if event.kind not in PAYLOAD:
            continue
        v = dict(event.values)
        copy, local = int(v["copy"]), int(v["local"])
        context = tuple(v[k] for k in sorted(CONTEXT - {"local"}))
        require(copy not in contexts or contexts[copy] == context, "COPY_CONTEXT_CHANGED")
        require(local > last.get(copy, 0), "LOCAL_ORDER_INVALID")
        contexts[copy], last[copy] = context, local
        if event.kind == "TAG_SNAPSHOT":
            raw_snapshots.append(event)
        if "fd" not in v:
            continue
        key = copy, event.kind, int(v["fd"])
        require(key not in indexed, "DUPLICATE_STAGE_FD")
        indexed[key] = event
    _validate_markers(indexed)
    snapshots = []
    for event in raw_snapshots:
        v = dict(event.values)
        copy, fd, ordinal = (int(v[k]) for k in ("copy", "fd", "read_ordinal"))
        joined = [
            indexed.get((copy, stage, fd)) for stage in ("POINTER_READ", "REFERENCE", "STORE")
        ]
        previous = 0
        for source in joined:
            if source is None:
                continue
            sv = dict(source.values)
            require(previous < source.n < event.n, "OBSERVED_STAGE_ORDER_INVALID")
            previous = source.n
            if source.kind == "POINTER_READ":
                require(
                    sv["presence"] == "PRESENT" and sv["local"] == ordinal,
                    "CONSUMED_POINTER_MISMATCH",
                )
            else:
                require(sv["read_ordinal"] == ordinal, "CONSUMED_SOURCE_MISMATCH")
                require(
                    source.kind != "STORE" or sv["presence"] == "PRESENT", "STORE_PRESENCE_MISMATCH"
                )
        # A marker with this read ordinal but another fd is a contradiction,
        # not a reason to pretend the expected marker was merely lost.
        for (other_copy, stage, other_fd), source in indexed.items():
            if other_copy != copy or stage not in {"REFERENCE", "STORE"}:
                continue
            sv = dict(source.values)
            require(sv["read_ordinal"] != ordinal or other_fd == fd, "SOURCE_FD_MISMATCH")
        complete = all(source is not None for source in joined)
        if not complete:
            reasons.append("SOURCE_RECEIPT_UNAVAILABLE")
        cookie, scope, epoch, origin = (
            int(v[k]) for k in ("raw_cookie", "raw_scope", "raw_epoch", "raw_origin")
        )
        logical = cookie if cookie > 0 and epoch == 1 and origin in (1, 2) else None
        snapshots.append(
            Snapshot(
                copy,
                fd,
                ordinal,
                cookie,
                scope,
                epoch,
                origin,
                logical,
                joined[0].n if joined[0] else None,
                joined[1].n if joined[1] else None,
                joined[2].n if joined[2] else None,
                complete,
            )
        )
    for (copy, stage, fd), event in indexed.items():
        if stage == "POINTER_READ" and dict(event.values)["presence"] == "PRESENT":
            if (copy, "TAG_SNAPSHOT", fd) not in indexed:
                reasons.append("SNAPSHOT_RECEIPT_UNAVAILABLE")
    return Decision(
        tuple(snapshots), bool(balanced), bool(f or d or p), tuple(sorted(set(reasons)))
    )
