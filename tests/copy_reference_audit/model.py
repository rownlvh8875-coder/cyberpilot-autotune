"""Closed immutable reviewed metadata,not a C analyzer or qualified observation."""

from dataclasses import dataclass, field
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need, shape

DIMENSIONS = (
    (
        "CONSUMED_REFERENCE",
        "CALLER_COPY_FILES FDTABLE_LOOKUP COPY_LOCK_RELOAD COPY_LOCAL_REFERENCE "
        "GET_FILE_RELAXED FD_REMOVE_LOCK FD_REPLACE_LOCK TABLE_RELEASE "
        "RCU_REF_REVALIDATE VFS_REFERENCE_RULES",
        "SOURCE_LOCAL_F_CHAIN_VISIBLE EXISTING_REFERENCE_WINDOW_CONDITIONAL_TABLE_INVARIANTS",
        "OLD_TABLE_OWNERSHIP_NOT_RUNTIME_ATTESTED ALL_REMOVAL_ROUTES_NOT_CLOSED "
        "BORROWED_POINTER_VALIDITY_NOT_RUNTIME_ATTESTED",
    ),
    (
        "TAG_PUBLICATION",
        "NORMAL_ALLOCATION NORMAL_TAG_WRITER FD_INSTALL_PUBLICATION RCU_RAW_LOAD "
        "RCU_PUBLISH RCU_DEPENDENCY_RULES SEED_WRITER SAME_LOCK_HANDOFF COPY_LOCK_RELOAD",
        "PREINSTALL_INITIALIZATION_ORDER_CONDITIONAL SAME_NAMESPACE_LOCK_HANDOFF_CONDITIONAL",
        "ALL_TAG_WRITERS_NOT_CLOSED AFTER_PUBLICATION_SEED_REQUIRES_EXACT_GUARD "
        "ALIAS_NAMESPACE_WRITERS_NOT_EXCLUDED COMPILER_DEPENDENCY_PATH_NOT_PROVEN",
    ),
    (
        "SNAPSHOT_TRANSFER",
        "COPY_LOCAL_REFERENCE SNAPSHOT_RAW_HELPER SNAPSHOT_EMITTER WIRE_OUTPUT COPY_CONTEXT_FIELDS",
        "LOCAL_SCALAR_CAPTURE_BEFORE_STORE_SOURCE_VISIBLE "
        "POST_STORE_EMISSION_SAVED_VALUES_ONLY_SOURCE_VISIBLE",
        "TUPLE_ATOMICITY_NOT_ESTABLISHED SOURCE_WITNESSES_UNAVAILABLE "
        "DECLARED_TYPE_FIDELITY_UNQUALIFIED",
    ),
    (
        "IDENTITY_MEMBERSHIP",
        "OFD_CACHE_REUSE RCU_REF_REVALIDATE VFS_REFERENCE_RULES SEED_WRITER "
        "NORMAL_TAG_WRITER COOKIE_ISSUER ACTOR_SCOPE_GATE OFD_NOACCOUNT_ROUTE",
        "OBJECT_REFERENCE_DISTINCT_FROM_NAMESPACE_MEMBERSHIP",
        "ABA_AND_REUSE_COHORT_NOT_ATTESTED MEMBERSHIP_GENERATION_UNAVAILABLE "
        "NONCE_NOT_AUTHENTICATION",
    ),
    (
        "REPRESENTATION",
        "OFD_TAG_LAYOUT SNAPSHOT_RAW_HELPER BUFFER_TAG_TYPES WIRE_OUTPUT "
        "PR45_DECODER_EPOCH PR45_STANDIN_EPOCH",
        "COOKIE_SCOPE_U64_CHAIN_SOURCE_VISIBLE ORIGIN_U8_TO_UNSIGNED_INT_WIDENING "
        "EPOCH_U64_TO_UNSIGNED_INT_NARROWING_VISIBLE",
        "LOSSLESS_SOURCE_EPOCH_NOT_ESTABLISHED DECODER_UINT32_EPOCH_BOUND_NOT_ENFORCED "
        "STANDIN_PROBE_DOES_NOT_MATCH_SOURCE_EPOCH_WIDTH",
    ),
    (
        "ADMISSION",
        "PR45_FIXED_PROOF_FLAGS COPY_CONTEXT_FIELDS COOKIE_ISSUER",
        "OBSERVED_SOURCE_JOINS_NOT_RUNTIME_GUARDS",
        "NO_ACTUAL_TO_QUALIFIED_ADAPTER RUNTIME_SOURCE_WITNESS_CAPTURE_NOT_IMPLEMENTED "
        "ALL_PREVIOUS_BLOCKERS_RETAINED",
    ),
)
CLAIMS = frozenset(c for _, citations, _, _ in DIMENSIONS for c in citations.split())
FLOW_KEYS = (
    "object_type",
    "saved_type",
    "buffer_type",
    "wire",
    "decoder_domain",
    "probe_object_type",
    "source_width_effect",
)
FLOWS = (
    ("raw_cookie", ("u64", "u64", "u64", "%llu", "UInt64", "u64", "DECLARED_WIDTH_PRESERVED")),
    ("raw_scope", ("u64", "u64", "u64", "%llu", "UInt64", "u64", "DECLARED_WIDTH_PRESERVED")),
    (
        "raw_epoch",
        (
            "u64",
            "unsigned int",
            "unsigned int",
            "%u",
            "UInt64",
            "unsigned int",
            "SOURCE_TO_SAVED_NARROWING_POSSIBLE",
        ),
    ),
    (
        "raw_origin",
        (
            "u8",
            "unsigned int",
            "unsigned int",
            "%u",
            "ENUM_0_1_2",
            "unsigned int",
            "DECLARED_WIDENING",
        ),
    ),
)


@dataclass(frozen=True)
class Dimension:
    dimension: str
    citations: tuple[str, ...]
    conditional_arguments: tuple[str, ...]
    open_obligations: tuple[str, ...]


@dataclass(frozen=True)
class TypeFlow:
    field: str
    object_type: str
    saved_type: str
    buffer_type: str
    wire: str
    decoder_domain: str
    probe_object_type: str
    source_width_effect: str


@dataclass(frozen=True)
class ReferenceAudit:
    dimensions: tuple[Dimension, ...]
    type_flows: tuple[TypeFlow, ...]
    evidence_class: str = field(default="STATIC_SOURCE_AUDIT_ONLY", init=False)
    status: str = field(default="BLOCKED", init=False)
    source_binding_qualified: bool = field(default=False, init=False)
    publication_qualified: bool = field(default=False, init=False)
    type_fidelity_qualified: bool = field(default=False, init=False)
    epoch_range_invariant_proven: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    allocation_history_complete: bool = field(default=False, init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    actual_epoch_loss: None = field(default=None, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def _vector(value: Any, expected: str) -> tuple[str, ...]:
    wanted = frozenset(expected.split())
    need(type(value) is list and len(value) == len(wanted), "CLOSED_VECTOR_COHORT")
    need(all(type(item) is str for item in value), "VECTOR_TYPE")
    need(len(set(value)) == len(value) and frozenset(value) == wanted, "CLOSED_VECTOR_COHORT")
    return tuple(sorted(value))


def assess(rows: Any, flows: Any, available_claims: frozenset[str]) -> ReferenceAudit:
    need(type(available_claims) is frozenset and available_claims == CLAIMS, "CLAIM_COHORT")
    need(type(rows) is list and len(rows) == len(DIMENSIONS), "DIMENSION_COHORT")
    definitions = {
        name: (citations, arguments, obligations)
        for name, citations, arguments, obligations in DIMENSIONS
    }
    found = {}
    for row in rows:
        need(type(row) is dict, "CLOSED_DIMENSION_ROW")
        shape(row, {"dimension", "citations", "conditional_arguments", "open_obligations"})
        name = row["dimension"]
        need(type(name) is str and name in definitions and name not in found, "DIMENSION_COHORT")
        expected = definitions[name]
        found[name] = Dimension(
            name,
            *(
                _vector(row[key], values)
                for key, values in zip(
                    ("citations", "conditional_arguments", "open_obligations"),
                    expected,
                    strict=True,
                )
            ),
        )
    need(type(flows) is list and len(flows) == len(FLOWS), "TYPE_FLOW_COHORT")
    expected_flows = dict(FLOWS)
    found_flows = {}
    for row in flows:
        need(type(row) is dict, "CLOSED_TYPE_FLOW_ROW")
        shape(row, {"field", *FLOW_KEYS})
        name = row["field"]
        need(
            type(name) is str and name in expected_flows and name not in found_flows,
            "TYPE_FLOW_COHORT",
        )
        values = tuple(row[key] for key in FLOW_KEYS)
        need(
            all(type(value) is str for value in values) and values == expected_flows[name],
            "DECLARED_TYPE_FLOW_DRIFT",
        )
        found_flows[name] = TypeFlow(name, *values)
    return ReferenceAudit(
        tuple(found[name] for name, *_ in DIMENSIONS), tuple(found_flows[name] for name, _ in FLOWS)
    )
