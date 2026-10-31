"""Immutable source-scope catalog,not a C analyzer or runtime identity proof."""

from dataclasses import dataclass, field
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need

CITATIONS = (
    (
        "TASK",
        frozenset(
            "TASK_X86_DUP TASK_DUP_FAILURES TASK_ALLOC_CALL TASK_RESET_GATE "
            "TASK_LATE_ABORT TASK_FREE STATIC_INIT_TASK TASK_LAYOUT".split()
        ),
    ),
    (
        "NAMESPACE",
        frozenset(
            "NS_CONSTRUCTOR NS_SHARED NS_ATTACH NS_FREE NS_UNSHARE "
            "NS_UNSHARE_EFFECT NS_STATIC_INIT NS_LAYOUT NS_CPC_ALLOCATED".split()
        ),
    ),
    (
        "OFD",
        frozenset(
            "OFD_INIT OFD_NORMAL_ALLOC OFD_NOACCOUNT OFD_BACKING OFD_FREE OFD_CACHE "
            "OFD_LAYOUT OFD_RCU_REVALIDATE RCU_REUSE_WARNING".split()
        ),
    ),
    ("SEED", frozenset("SEED_WALK SEED_ABORT ORIGIN_READ COPY_RAW_READ".split())),
    ("ISSUER", frozenset("COOKIE_STORAGE COOKIE_CAS COHORT_NONCE".split())),
)
OBLIGATIONS = (
    (
        "TASK",
        frozenset(
            "PRE_HOOK_DUP_FAILURES_UNOBSERVED TASK_FINAL_DESTRUCTION_UNOBSERVED "
            "UNSUPPORTED_CLONE_SCOPE_UNQUALIFIED".split()
        ),
    ),
    (
        "NAMESPACE",
        frozenset(
            "UNSHARE_AND_SHARED_CONTEXT_UNQUALIFIED "
            "FALLBACK_NAMESPACE_ORIGIN_INCOMPLETE "
            "BACKING_FDT_REPLACEMENT_NOT_NAMESPACE_IDENTITY".split()
        ),
    ),
    (
        "OFD",
        frozenset(
            "NONSTANDARD_ALLOCATOR_HOOK_COVERAGE_INCOMPLETE "
            "RCU_OBJECT_REUSE_IDENTITY_UNQUALIFIED TAG_TUPLE_PUBLICATION_UNQUALIFIED".split()
        ),
    ),
    (
        "SEED",
        frozenset("ALL_MUTATOR_SEED_CUT_UNPROVEN ABORTED_SEED_TAGS_RETAINED_NO_HISTORY".split()),
    ),
    (
        "ISSUER",
        frozenset(
            "ISSUER_WRAP_EXHAUSTION_RUNTIME_UNTESTED COHORT_NONCE_AUTHENTICITY_UNQUALIFIED".split()
        ),
    ),
)
CLAIMS = frozenset(c for _, values in CITATIONS for c in values)


@dataclass(frozen=True)
class SubjectBoundary:
    subject: str
    citations: tuple[str, ...]
    open_obligations: tuple[str, ...]


@dataclass(frozen=True)
class BoundaryAudit:
    boundaries: tuple[SubjectBoundary, ...]
    evidence_class: str = field(default="STATIC_SOURCE_AUDIT_ONLY", init=False)
    status: str = field(default="BLOCKED", init=False)
    initialization_qualified: bool = field(default=False, init=False)
    reuse_qualified: bool = field(default=False, init=False)
    publication_qualified: bool = field(default=False, init=False)
    issuer_runtime_qualified: bool = field(default=False, init=False)
    allocation_history_complete: bool = field(default=False, init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def _cohort(value: Any, expected: frozenset[str]) -> tuple[str, ...]:
    need(type(value) is list and len(value) == len(expected), "SOURCE_VECTOR_COHORT")
    need(all(type(v) is str for v in value), "SOURCE_VECTOR_TYPE")
    need(len(value) == len(set(value)) and frozenset(value) == expected, "SOURCE_VECTOR_COHORT")
    return tuple(sorted(value))


def assess(rows: Any, available_claims: frozenset[str]) -> BoundaryAudit:
    """Consume the closed metadata catalog; never infer C semantics or readiness."""
    need(type(available_claims) is frozenset and available_claims == CLAIMS, "CLAIM_COHORT")
    need(type(rows) is list and len(rows) == len(CITATIONS), "SUBJECT_COHORT")
    citations, obligations = dict(CITATIONS), dict(OBLIGATIONS)
    found: dict[str, SubjectBoundary] = {}
    for row in rows:
        need(
            type(row) is dict and set(row) == {"subject", "citations", "open_obligations"},
            "CLOSED_SOURCE_ROW",
        )
        subject = row["subject"]
        need(
            type(subject) is str and subject in citations and subject not in found, "SUBJECT_COHORT"
        )
        found[subject] = SubjectBoundary(
            subject,
            _cohort(row["citations"], citations[subject]),
            _cohort(row["open_obligations"], obligations[subject]),
        )
    return BoundaryAudit(tuple(found[subject] for subject, _ in CITATIONS))
