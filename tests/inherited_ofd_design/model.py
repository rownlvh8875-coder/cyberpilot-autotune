"""Pure SYNTHETIC origin/link premises, never birth-history or runtime admission."""

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, canonical, need, shape, uint

BASE = "21a542eba9e889323b2cb1b7d7c75d9c9cab1025"
SOURCE_SHA = "69e566058e77804800e803d9faaa9e52f127cd652aaee39bf26b1966f0558013"
PROFILE = "PR40_PRIVATE64_BOOTSTRAP_DESIGN"
DOMAIN = "PROPOSED_LINEAGE_V1"
COPY_FIELDS = {
    "parent_task",
    "source_namespace",
    "child_task",
    "destination_namespace",
    "arm",
    "begin",
    "returned",
    "finalized",
    "return_result",
    "return_reason",
    "task_result",
    "task_reason",
    "bindings",
}
BINDING_FIELDS = {
    "fd",
    "presence",
    "source_ofd",
    "destination_ofd",
    "read",
    "branch",
    "branch_ordinal",
    "branch_read",
    "store",
    "store_read",
}
OBJECT_FIELDS = {
    "cookie",
    "role",
    "generation",
    "origin",
    "stage",
    "ordinal",
    "boot_scope",
    "issuer_epoch",
}


@dataclass(frozen=True)
class Origin:
    cookie: int
    role: str
    origin: str


@dataclass(frozen=True)
class Decision:
    premises_consistent: bool
    reasons: tuple[str, ...]
    unavailable: tuple[str, ...]
    origins: tuple[Origin, ...]
    linked_fds: tuple[tuple[int, int], ...]
    digest: str | None
    evidence_class: str = field(default="SYNTHETIC_ONLY", init=False)
    status: str = field(default="BLOCKED", init=False)
    allocation_history_complete: bool = field(default=False, init=False)
    runtime_producer_implemented: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def _context(c: Any) -> None:
    shape(
        c,
        {
            "source_profile",
            "source_revision",
            "source_manifest_sha256",
            "boot_scope",
            "issuer_epoch",
            "record_domain",
        },
    )
    need(
        c["source_profile"] == PROFILE
        and c["source_revision"] == BASE
        and c["source_manifest_sha256"] == SOURCE_SHA
        and c["record_domain"] == DOMAIN,
        "SOURCE_OR_RECORD_DOMAIN_MISMATCH",
    )
    for key in ("boot_scope", "issuer_epoch"):
        need(
            type(c[key]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", c[key]) is not None,
            "BOOT_ISSUER_CONTEXT_REQUIRED",
        )


def _id(value: Any) -> int:
    result = uint(value)
    need(result > 0, "POSITIVE_HANDLE_REQUIRED")
    return result


def _objects(rows: Any, context: Any, arm: int, begin: int) -> dict[int, Origin]:
    need(type(rows) is list and len(rows) <= 68, "OBJECT_BOUND")
    result: dict[int, Origin] = {}
    ordinals: set[int] = set()
    for row in rows:
        shape(row, OBJECT_FIELDS)
        cookie, ordinal = _id(row["cookie"]), _id(row["ordinal"])
        need(cookie not in result and ordinal not in ordinals, "HANDLE_OR_ISSUANCE_REUSE")
        need(
            row["role"] in ("TASK", "NAMESPACE", "OFD") and uint(row["generation"]) == 0,
            "ROLE_OR_GENERATION_UNSUPPORTED",
        )
        need(all(row[k] == context[k] for k in ("boot_scope", "issuer_epoch")), "MIXED_BOOT_ISSUER")
        seeded = row["origin"] == "FIRST_OBSERVED" and row["stage"] == "PRE_ARM_SEED"
        allocated = row["origin"] == "ALLOCATION" and row["stage"] == "POST_INIT_ALLOC"
        need(
            (seeded and ordinal < arm) or (allocated and arm < ordinal < begin),
            "ORIGIN_STAGE_OR_ORDER_CONTRADICTION",
        )
        result[cookie] = Origin(cookie, row["role"], row["origin"])
        ordinals.add(ordinal)
    return result


def _reference(
    value: Any,
    role: str,
    catalog: dict[int, Origin],
    unavailable: list[str],
    label: str,
    optional: bool = False,
) -> int | None:
    if value is None and optional:
        unavailable.append(label)
        return None
    cookie = _id(value)
    need(cookie in catalog and catalog[cookie].role == role, "UNKNOWN_OR_WRONG_ROLE_HANDLE")
    return cookie


def _terminal(c: Any) -> bool:
    success = c["return_result"] == "SUCCESS"
    need(
        c["return_result"] in ("SUCCESS", "FAILED")
        and c["task_result"] in ("COMMITTED", "ABORTED"),
        "TERMINAL_RESULT_UNSUPPORTED",
    )
    if success:
        need(c["return_reason"] == "NONE", "TERMINAL_REASON_CONTRADICTION")
        committed = bool(c["task_result"] == "COMMITTED")
        need(
            c["task_reason"] in (("NONE",) if committed else ("TASK_INJECTED", "TASK_FAILED")),
            "TERMINAL_REASON_CONTRADICTION",
        )
        return committed
    need(
        c["return_reason"] in ("ALLOC_INJECTED", "CONSTRUCTOR_INJECTED", "NATURAL_ALLOC")
        and c["task_result"] == "ABORTED"
        and c["task_reason"] == "COPY_FAILED"
        and c["bindings"] == [],
        "FAILED_CONSTRUCTOR_CONTRADICTION",
    )
    return False


def _copy(
    c: Any, catalog: dict[int, Origin], unavailable: list[str], begin: int, returned: int
) -> tuple[tuple[int, int], ...]:
    committed = _terminal(c)
    parent = _reference(c["parent_task"], "TASK", catalog, unavailable, "parent_task", True)
    source = _reference(
        c["source_namespace"], "NAMESPACE", catalog, unavailable, "source_namespace", True
    )
    child = _reference(c["child_task"], "TASK", catalog, unavailable, "child_task")
    dest = _reference(
        c["destination_namespace"],
        "NAMESPACE",
        catalog,
        unavailable,
        "destination_namespace",
        c["return_result"] == "FAILED",
    )
    need(
        all(catalog[v].origin == "ALLOCATION" for v in (child, dest) if v is not None),
        "FORK_SUBJECT_ALLOCATION_REQUIRED",
    )
    known = [v for v in (parent, source, child, dest) if v is not None]
    need(len(known) == len(set(known)), "COPY_ROLE_OR_NAMESPACE_COLLISION")
    rows = c["bindings"]
    need(type(rows) is list and len(rows) <= 64, "BINDING_BOUND")
    links: list[tuple[int, int]] = []
    previous_fd, previous_store = -1, begin
    for row in rows:
        shape(row, BINDING_FIELDS)
        fd = uint(row["fd"], 64)
        read, branch, store = (_id(row[k]) for k in ("read", "branch_ordinal", "store"))
        need(
            fd > previous_fd and previous_store < read < branch < store < returned,
            "BINDING_ORDER_OR_OVERLAP",
        )
        need(
            uint(row["branch_read"]) == uint(row["store_read"]) == read,
            "CONSUMED_READ_PAIR_MISMATCH",
        )
        need(row["presence"] in ("PRESENT", "NULL"), "POINTER_PRESENCE_REQUIRED")
        present = row["presence"] == "PRESENT"
        need(row["branch"] == ("REFERENCE" if present else "CLEAR_OPEN"), "POINTER_BRANCH_MISMATCH")
        if present:
            src = _reference(
                row["source_ofd"], "OFD", catalog, unavailable, f"binding[{fd}].source_ofd", True
            )
            dst = _reference(
                row["destination_ofd"],
                "OFD",
                catalog,
                unavailable,
                f"binding[{fd}].destination_ofd",
                True,
            )
            need(src is None or dst is None or src == dst, "COPIED_OBJECT_IDENTITY_MISMATCH")
            if (
                committed
                and parent is not None
                and source is not None
                and src is not None
                and dst == src
            ):
                links.append((fd, src))
        else:
            need(row["source_ofd"] is None and row["destination_ofd"] is None, "NULL_IS_NOT_OFD")
        previous_fd, previous_store = fd, store
    return tuple(links)


def evaluate(data: object) -> Decision:
    """Check hypothetical premises only; coherent fabrication is undetectable."""
    raw = None
    errors: list[str] = []
    unavailable: list[str] = []
    origins: tuple[Origin, ...] = ()
    links: tuple[tuple[int, int], ...] = ()
    try:
        raw = canonical(data)
        copied = json.loads(raw)
        shape(copied, {"schema", "evidence_class", "context", "objects", "copy"})
        need(
            copied["schema"] == "inherited-ofd-provenance-design-v1"
            and copied["evidence_class"] == "SYNTHETIC_ONLY",
            "SYNTHETIC_DESIGN_REQUIRED",
        )
        _context(copied["context"])
        c = copied["copy"]
        shape(c, COPY_FIELDS)
        arm, begin, returned, finalized = (
            _id(c[k]) for k in ("arm", "begin", "returned", "finalized")
        )
        need(arm < begin < returned < finalized, "COPY_PROGRAM_ORDER_INVALID")
        catalog = _objects(copied["objects"], copied["context"], arm, begin)
        links = _copy(c, catalog, unavailable, begin, returned)
        origins = tuple(catalog[k] for k in sorted(catalog))
    except ValueError as exc:
        errors.append(str(exc))
    return Decision(
        not errors,
        tuple(errors),
        tuple(unavailable),
        origins,
        links,
        hashlib.sha256(raw).hexdigest() if raw is not None else None,
    )
