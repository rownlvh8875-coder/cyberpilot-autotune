"""Finite assumed-HB consistency,not C semantics or target-lifetime verification."""

import re
from dataclasses import dataclass, field
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need, shape

VERSION = "tag-read-protocol-design-v1"
BASE = "e01cdc127bbb17073aa47967b926b68088f57ded"
SOURCE_DIGEST = "4b0712a7d12069a74032f8f9f91861bf22397436927a278818968d9f647930af"
TOP_FIELDS = frozenset(
    "schema evidence_class source identity observed_identity writer reader membership graph".split()
)
IDENTITY_FIELDS = frozenset("object_kind cohort cookie epoch generation origin".split())
SECTION_FIELDS = (
    ("source", frozenset("base_revision catalog_digest".split())),
    ("identity", IDENTITY_FIELDS),
    ("observed_identity", IDENTITY_FIELDS),
    (
        "writer",
        frozenset(
            "components_initialized writer_set_closed identity_write_once "
            "publication witness_identity".split()
        ),
    ),
    (
        "reader",
        frozenset(
            "mode stage lifetime observer_refs observer_locks "
            "all_component_reads_bounded emission witness_identity".split()
        ),
    ),
    (
        "membership",
        frozenset("cohort root_before root_after generation_before generation_after guard".split()),
    ),
    ("graph", frozenset(("nodes", "edges"))),
)
FALSE_FIELDS = (
    "runtime_producer_implemented",
    "target_lifetime_proven",
    "tag_publication_qualified",
    "source_happens_before_proven",
    "allocation_history_complete",
    "atomic_cut_proven",
    "runtime_qualified",
)


@dataclass(frozen=True)
class TagIdentity:
    object_kind: str
    cohort: str
    cookie: int
    epoch: int
    generation: int
    origin: str


@dataclass(frozen=True)
class SyntheticTagSnapshot(TagIdentity):
    root: int
    membership_generation: int
    stage: str


@dataclass(frozen=True)
class ReadProtocolDecision:
    premises_consistent: bool
    proposed_snapshot: SyntheticTagSnapshot | None
    reasons: tuple[str, ...]
    evidence_class: str = field(default="SYNTHETIC_ONLY", init=False)
    status: str = field(default="BLOCKED", init=False)
    runtime_producer_implemented: bool = field(default=False, init=False)
    target_lifetime_proven: bool = field(default=False, init=False)
    tag_publication_qualified: bool = field(default=False, init=False)
    source_happens_before_proven: bool = field(default=False, init=False)
    allocation_history_complete: bool = field(default=False, init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def _truth(value: Any, label: str) -> None:
    need(value is not None, label + "_UNAVAILABLE")
    need(type(value) is bool, label + "_TYPE")
    need(value, label + "_NOT_ASSERTED")


def _uint(value: Any, label: str) -> int:
    need(value is not None, label + "_UNAVAILABLE")
    need(type(value) is int and 0 <= value < 2**64, label + "_UINT64")
    return int(value)


def _identity(data: Any) -> TagIdentity:
    shape(data, set(IDENTITY_FIELDS))
    need(
        type(data["object_kind"]) is str and data["object_kind"] in ("TASK", "NAMESPACE", "OFD"),
        "UNSUPPORTED_OBJECT_KIND",
    )
    need(
        type(data["cohort"]) is str
        and re.fullmatch("[A-Za-z0-9_-]{1,64}", data["cohort"]) is not None,
        "COHORT_REQUIRED",
    )
    need(
        type(data["origin"]) is str and data["origin"] in ("ALLOCATION", "FIRST_OBSERVED"),
        "TAG_ORIGIN_UNAVAILABLE",
    )
    cookie = _uint(data["cookie"], "TAG_COOKIE")
    epoch = _uint(data["epoch"], "TAG_EPOCH")
    generation = _uint(data["generation"], "TAG_GENERATION")
    need(cookie > 0 and epoch > 0, "RESERVED_ZERO_IDENTITY")
    return TagIdentity(
        data["object_kind"], data["cohort"], cookie, epoch, generation, data["origin"]
    )


def _causal(graph: Any, private: bool) -> None:
    """Edges are assumptions in a synthetic domain;vector order proves nothing."""
    wanted = {
        "tag_init",
        "tag_freeze",
        "read_begin",
        "read_end",
        "save",
        "emit",
        "context_begin",
        "context_end",
    }
    wanted |= (
        {"owner_begin", "owner_end"} if private else {"publish_release", "ref_begin", "ref_end"}
    )
    nodes, edges = graph["nodes"], graph["edges"]
    need(
        type(nodes) is list and len(nodes) == len(wanted) and all(type(n) is str for n in nodes),
        "EXACT_CAUSAL_ANCHORS_REQUIRED",
    )
    need(set(nodes) == wanted, "EXACT_CAUSAL_ANCHORS_REQUIRED")
    need(type(edges) is list and len(edges) <= 128, "CAUSAL_EDGE_BOUND")
    adjacent: dict[str, set[str]] = {n: set() for n in nodes}
    seen_edges: set[tuple[str, str]] = set()
    for pair in edges:
        need(
            type(pair) is list and len(pair) == 2 and all(type(n) is str for n in pair),
            "CAUSAL_EDGE_TYPE",
        )
        left, right = pair
        need(left in wanted and right in wanted, "FOREIGN_CAUSAL_ANCHOR")
        need((left, right) not in seen_edges, "DUPLICATE_CAUSAL_EDGE")
        seen_edges.add((left, right))
        adjacent[left].add(right)
    reach: dict[str, set[str]] = {}
    for start in nodes:
        pending = list(adjacent[start])
        visited: set[str] = set()
        while pending:
            node = pending.pop()
            if node not in visited:
                visited.add(node)
                pending.extend(adjacent[node])
        need(start not in visited, "CAUSAL_CYCLE")
        reach[start] = visited
    required = [
        ("tag_init", "tag_freeze"),
        ("tag_freeze", "read_begin"),
        ("read_begin", "read_end"),
        ("read_end", "save"),
        ("save", "emit"),
        ("context_begin", "read_begin"),
        ("save", "context_end"),
    ]
    required += (
        [("owner_begin", "tag_init"), ("save", "owner_end")]
        if private
        else [
            ("tag_freeze", "publish_release"),
            ("publish_release", "ref_begin"),
            ("ref_begin", "read_begin"),
            ("save", "ref_end"),
        ]
    )
    need(all(right in reach[left] for left, right in required), "MISSING_CAUSAL_RELATION")


def _check(payload: Any) -> SyntheticTagSnapshot:
    shape(payload, set(TOP_FIELDS))
    need(
        payload["schema"] == VERSION and payload["evidence_class"] == "SYNTHETIC_ONLY",
        "SYNTHETIC_PROTOCOL_DOMAIN_REQUIRED",
    )
    for section, fields in SECTION_FIELDS:
        shape(payload[section], set(fields))
    need(
        payload["source"] == {"base_revision": BASE, "catalog_digest": SOURCE_DIGEST},
        "PROTOCOL_SOURCE_MISMATCH",
    )
    expected, observed = _identity(payload["identity"]), _identity(payload["observed_identity"])
    need(expected == observed, "TAG_IDENTITY_MISMATCH")
    need(observed.origin == "ALLOCATION", "SEED_PROTOCOL_UNQUALIFIED")
    writer, reader, context = payload["writer"], payload["reader"], payload["membership"]
    need(
        _identity(writer["witness_identity"]) == observed
        and _identity(reader["witness_identity"]) == observed,
        "TAG_WITNESS_IDENTITY_MISMATCH",
    )
    mode = reader["mode"]
    need(
        type(mode) is str and mode in ("PRIVATE_OWNER", "EXISTING_REFERENCE"),
        "UNSUPPORTED_READER_MODE",
    )
    private = mode == "PRIVATE_OWNER"
    need(private or observed.object_kind == "OFD", "UNSUPPORTED_REFERENCE_OBJECT")
    need(
        reader["stage"]
        == ("PRIVATE_PRE_PUBLICATION" if private else "POST_EXISTING_REFERENCE_PRE_STORE"),
        "WRONG_CAPTURE_STAGE",
    )
    need(
        reader["lifetime"]
        == ("PRIVATE_OWNER" if private else "EXISTING_OPERATION_REFERENCE_WITH_SOURCE_BINDING"),
        "UNSUPPORTED_LIFETIME",
    )
    need(
        writer["publication"]
        == ("OWNER_PRIVATE_ORDERED" if private else "EXISTING_RELEASE_ACQUIRE"),
        "UNSUPPORTED_PUBLICATION",
    )
    for name in ("components_initialized", "writer_set_closed", "identity_write_once"):
        _truth(writer[name], name.upper())
    _truth(reader["all_component_reads_bounded"], "READ_BOUNDS")
    for name in ("observer_refs", "observer_locks"):
        need(_uint(reader[name], name.upper()) == 0, "OBSERVER_EFFECT_UNSUPPORTED")
    need(reader["emission"] == "SAVED_SCALARS_ONLY", "UNSAFE_EMISSION_STAGE")
    need(context["cohort"] == observed.cohort, "MEMBERSHIP_COHORT_MISMATCH")
    need(context["guard"] == "EXISTING_OPERATION_GUARD", "MEMBERSHIP_GUARD_UNAVAILABLE")
    root = _uint(context["root_before"], "MEMBERSHIP_ROOT")
    root_after = _uint(context["root_after"], "MEMBERSHIP_ROOT")
    generation = _uint(context["generation_before"], "MEMBERSHIP_GENERATION")
    generation_after = _uint(context["generation_after"], "MEMBERSHIP_GENERATION")
    need(
        root > 0 and root == root_after and generation == generation_after,
        "MEMBERSHIP_CONTEXT_CHANGED",
    )
    _causal(payload["graph"], private)
    return SyntheticTagSnapshot(
        observed.object_kind,
        observed.cohort,
        observed.cookie,
        observed.epoch,
        observed.generation,
        observed.origin,
        root,
        generation,
        reader["stage"],
    )


def evaluate(payload: Any) -> ReadProtocolDecision:
    """A consistent hypothetical story is still BLOCKED,never an actual witness."""
    try:
        snapshot = _check(payload)
    except ValueError as exc:
        return ReadProtocolDecision(False, None, (str(exc),))
    return ReadProtocolDecision(True, snapshot, ())
