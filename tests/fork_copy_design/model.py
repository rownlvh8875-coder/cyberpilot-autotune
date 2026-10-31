"""Pure SYNTHETIC per-slot copy premises; never an atomic cut or producer receipt."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, canonical, need, shape, uint

SOURCE_PROFILE = "PR38_LINUX_6_12_113_X86_64_PRIVATE64"
SOURCE_HASHES = {
    "source_sha256": "129263d5c6923429eb2e98d93a67b9b6e6b2de7de10a48b924595adeab518284",
    "fork_sha256": "32788952871be9b6cc106a47cfd6f6d0b7207cd3a83eafa4aa60f46af5462b7d",
    "fdtable_sha256": "86b2acb622e4bd1d03eeeaa4fe2b8f3bf33ce1779ec32d959402b47d42857dd4",
}
FIELDS = {
    "BEGIN": {"scan_bound", "capacity"},
    "BITMAPS": {"open_fds", "cloexec"},
    "READ": {"fd", "presence", "ofd"},
    "REFERENCE": {"fd", "read_ordinal"},
    "CLEAR_OPEN": {"fd", "read_ordinal"},
    "STORE": {"fd", "read_ordinal", "presence", "ofd"},
    "COPY_RETURN": {"result", "tail_zeroed"},
    "TASK_FINALIZE": {"result"},
}


@dataclass(frozen=True)
class CopiedSlot:
    fd: int
    presence: str
    file_id: int | None
    open_after: bool | None
    cloexec_bitmap_bit: bool | None
    binding_cloexec: bool | None


@dataclass(frozen=True)
class Decision:
    consistent: bool
    reasons: tuple[str, ...]
    digest: str | None
    slots: tuple[CopiedSlot, ...] = ()
    status: str = field(default="BLOCKED", init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    runtime_producer_implemented: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def _identity(value: Any, *, optional: bool = False) -> int | None:
    if value is None and optional:
        return None
    result = uint(value)
    need(result > 0, "SOURCE_ID_REQUIRED")
    return result


def _context(context: Any, reasons: list[str]) -> set[int]:
    shape(
        context,
        {
            "source_profile",
            *SOURCE_HASHES,
            "boot_scope",
            "scope_id",
            "copy_attempt_id",
            "actor_task_id",
            "subject_task_id",
            "source_table_id",
            "destination_table_id",
            "root_copy",
            "clone_mode",
        },
    )
    need(
        context["source_profile"] == SOURCE_PROFILE
        and context["clone_mode"] == "PRIVATE_FORK"
        and all(context[k] == sha for k, sha in SOURCE_HASHES.items()),
        "SOURCE_COHORT_MISMATCH",
    )
    boot = context["boot_scope"]
    need(
        type(boot) is str
        and 1 <= len(boot) <= 64
        and all(
            c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in boot
        ),
        "BOOT_SCOPE_REQUIRED",
    )
    scope = _identity(context["scope_id"])
    _identity(context["copy_attempt_id"])
    subject, dest = (_identity(context[k]) for k in ("subject_task_id", "destination_table_id"))
    actor, source = (
        _identity(context[k], optional=True) for k in ("actor_task_id", "source_table_id")
    )
    need(type(context["root_copy"]) is bool, "EXACT_BOOL_REQUIRED")
    if context["root_copy"]:
        need(subject == scope and actor is None and source is None, "ROOT_PARENT_CONTEXT_MISMATCH")
        reasons.append("SOURCE_CONTEXT_UNAVAILABLE")
    else:
        need(actor is not None, "DESCENDANT_CREATOR_UNAVAILABLE")
        need(source is not None, "SOURCE_NAMESPACE_UNAVAILABLE")
        need(subject != scope, "SUBJECT_SCOPE_MISMATCH")
    ids = [v for v in (actor, subject, source, dest) if v is not None]
    need(len(ids) == len(set(ids)), "SOURCE_COOKIE_ROLE_COLLISION")
    return set(ids)


def _accounting(data: Any, events: list[Any], reasons: list[str]) -> None:
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    shape(data, set(names))
    for v in data.values():
        if v is not None:
            uint(v)
    if any(data[n] is None for n in names):
        reasons.append("ACCOUNTING_UNAVAILABLE")
        return
    a, r, c, f, d, p = (data[n] for n in names)
    if a != r + f or r != c + d + p or c != len(events) or d or p:
        reasons.append("LOCAL_ACCOUNTING_MISMATCH")
    if f:
        reasons.append("LOCAL_RESERVATION_LOSS")
    if any(e["n"] > a for e in events):
        reasons.append("EMISSION_ACCOUNTING_MISMATCH")


def _events(events: Any, reasons: list[str]) -> None:
    need(type(events) is list and len(events) <= 196, "EVENT_BOUND")
    previous = 0
    for index, e in enumerate(events, 1):
        need(
            type(e) is dict and type(e.get("kind")) is str and e["kind"] in FIELDS,
            "UNSUPPORTED_COPY_STAGE",
        )
        shape(e, {"n", "kind"} | FIELDS[e["kind"]])
        n = uint(e["n"])
        need(n > previous, "DUPLICATE_OR_REORDERED_EMISSION")
        previous = n
        if n != index:
            reasons.append("SOURCE_EMISSION_GAP")


def _slots(events: list[Any], roles: set[int], reasons: list[str]) -> tuple[CopiedSlot, ...]:
    need(len(events) == 196, "INCOMPLETE_COPY_WITNESS")
    begin, bitmaps = events[:2]
    need(begin["kind"] == "BEGIN" and bitmaps["kind"] == "BITMAPS", "COPY_STAGE_ORDER")
    need(
        uint(begin["scan_bound"]) == 64 and uint(begin["capacity"]) == 64,
        "UNSUPPORTED_SCAN_PROFILE",
    )
    for name in ("open_fds", "cloexec"):
        bits = bitmaps[name]
        need(type(bits) is list and len(bits) == 64, "BITMAP_COHORT_MISMATCH")
        need(all(v is None or type(v) is bool for v in bits), "EXACT_BITMAP_VALUE")
        if None in bits:
            reasons.append("BITMAP_UNAVAILABLE")
    slots = []
    for fd in range(64):
        read, branch, store = events[2 + 3 * fd : 5 + 3 * fd]
        need(read["kind"] == "READ" and store["kind"] == "STORE", "COPY_STAGE_ORDER")
        need(branch["kind"] in ("REFERENCE", "CLEAR_OPEN"), "COPY_BRANCH_STAGE")
        need(all(uint(e["fd"]) == fd for e in (read, branch, store)), "COPY_FD_SEQUENCE")
        presence = read["presence"]
        need(presence in ("PRESENT", "NULL"), "POINTER_READ_UNAVAILABLE")
        ofd = _identity(read["ofd"], optional=True)
        need(store["presence"] == presence and store["ofd"] == ofd, "READ_STORE_MISMATCH")
        need(
            all(uint(e["read_ordinal"]) == read["n"] for e in (branch, store)), "READ_PAIR_MISMATCH"
        )
        open_bit, cloexec = bitmaps["open_fds"][fd], bitmaps["cloexec"][fd]
        if presence == "PRESENT":
            need(branch["kind"] == "REFERENCE", "REFERENCE_STAGE_REQUIRED")
            need(open_bit is not False, "OPEN_POINTER_CONTRADICTION")
            need(ofd not in roles, "SOURCE_COOKIE_ROLE_COLLISION")
            if ofd is None:
                reasons.append("OFD_ID_UNAVAILABLE")
            child_open = open_bit
            effective = cloexec if child_open is True else None
        else:
            need(ofd is None and branch["kind"] == "CLEAR_OPEN", "NULL_CLEAR_STAGE_REQUIRED")
            child_open, effective = False, None
        slots.append(CopiedSlot(fd, presence, ofd, child_open, cloexec, effective))
    returned, finalized = events[-2:]
    need(
        returned["kind"] == "COPY_RETURN" and finalized["kind"] == "TASK_FINALIZE",
        "COPY_STAGE_ORDER",
    )
    need(returned["result"] in ("SUCCESS", "FAILED"), "COPY_RESULT_REQUIRED")
    need(
        returned["tail_zeroed"] is None or type(returned["tail_zeroed"]) is bool,
        "EXACT_BOOL_REQUIRED",
    )
    if returned["tail_zeroed"] is not True:
        reasons.append("TAIL_COMPLETION_UNAVAILABLE")
    if returned["result"] != "SUCCESS":
        reasons.append("COPY_CONSTRUCTOR_FAILED")
    need(finalized["result"] in ("COMMITTED", "ABORTED", "UNAVAILABLE"), "TASK_RESULT_REQUIRED")
    if finalized["result"] != "COMMITTED":
        reasons.append("TASK_NOT_COMMITTED")
    return tuple(slots)


def evaluate(data: object) -> Decision:
    """Closed synthetic premises only. Coherent fabrication remains undetectable."""
    raw = None
    reasons: list[str] = []
    slots: tuple[CopiedSlot, ...] = ()
    try:
        raw = canonical(data)
        copied = json.loads(raw)
        shape(copied, {"schema", "evidence_class", "context", "events", "accounting"})
        need(
            copied["schema"] == "fork-copy-evidence-design-v1"
            and copied["evidence_class"] == "SYNTHETIC_ONLY",
            "SYNTHETIC_CONTRACT_REQUIRED",
        )
        roles = _context(copied["context"], reasons)
        events = copied["events"]
        _events(events, reasons)
        _accounting(copied["accounting"], events, reasons)
        slots = _slots(events, roles, reasons)
    except ValueError as exc:
        reasons.append(str(exc))
    return Decision(
        not reasons,
        tuple(dict.fromkeys(reasons)),
        hashlib.sha256(raw).hexdigest() if raw is not None else None,
        slots,
    )
