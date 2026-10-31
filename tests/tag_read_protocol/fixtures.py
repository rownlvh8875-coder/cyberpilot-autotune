"""Test-only independent pre-model premises;never reconstructed from real captures."""

import copy
from typing import Any


def example(mode: str = "EXISTING_REFERENCE", kind: str = "OFD") -> dict[str, Any]:
    private = mode == "PRIVATE_OWNER"
    identity = dict(
        object_kind=kind,
        cohort="synthetic-boot-a",
        cookie=17,
        epoch=1,
        generation=0,
        origin="ALLOCATION",
    )
    nodes = [
        "tag_init",
        "tag_freeze",
        "read_begin",
        "read_end",
        "save",
        "emit",
        "context_begin",
        "context_end",
    ]
    edges = [
        ["tag_init", "tag_freeze"],
        ["tag_freeze", "read_begin"],
        ["read_begin", "read_end"],
        ["read_end", "save"],
        ["save", "emit"],
        ["context_begin", "read_begin"],
        ["save", "context_end"],
    ]
    if private:
        nodes += ["owner_begin", "owner_end"]
        edges += [["owner_begin", "tag_init"], ["save", "owner_end"], ["owner_end", "emit"]]
    else:
        nodes += ["publish_release", "ref_begin", "ref_end"]
        edges += [
            ["tag_freeze", "publish_release"],
            ["publish_release", "ref_begin"],
            ["ref_begin", "read_begin"],
            ["save", "ref_end"],
            ["ref_end", "emit"],
        ]
    return dict(
        schema="tag-read-protocol-design-v1",
        evidence_class="SYNTHETIC_ONLY",
        source=dict(
            base_revision="e01cdc127bbb17073aa47967b926b68088f57ded",
            catalog_digest="4b0712a7d12069a74032f8f9f91861bf22397436927a278818968d9f647930af",
        ),
        identity=identity,
        observed_identity=copy.deepcopy(identity),
        writer=dict(
            components_initialized=True,
            writer_set_closed=True,
            identity_write_once=True,
            publication="OWNER_PRIVATE_ORDERED" if private else "EXISTING_RELEASE_ACQUIRE",
            witness_identity=copy.deepcopy(identity),
        ),
        reader=dict(
            mode=mode,
            stage="PRIVATE_PRE_PUBLICATION" if private else "POST_EXISTING_REFERENCE_PRE_STORE",
            lifetime="PRIVATE_OWNER"
            if private
            else "EXISTING_OPERATION_REFERENCE_WITH_SOURCE_BINDING",
            observer_refs=0,
            observer_locks=0,
            all_component_reads_bounded=True,
            emission="SAVED_SCALARS_ONLY",
            witness_identity=copy.deepcopy(identity),
        ),
        membership=dict(
            cohort="synthetic-boot-a",
            root_before=5,
            root_after=5,
            generation_before=0,
            generation_after=0,
            guard="EXISTING_OPERATION_GUARD",
        ),
        graph=dict(nodes=nodes, edges=edges),
    )


def scenarios() -> list[tuple[str, dict[str, Any], bool]]:
    rows = [
        ("private_task", example("PRIVATE_OWNER", "TASK"), True),
        ("private_namespace", example("PRIVATE_OWNER", "NAMESPACE"), True),
        ("private_ofd", example("PRIVATE_OWNER", "OFD"), True),
        ("reference_ofd_saved_after_release", example(), True),
    ]
    p = example()
    p["graph"]["nodes"].reverse()
    p["graph"]["edges"].reverse()
    rows.append(("graph_vector_order_irrelevant", p, True))
    p = example()
    p["graph"]["edges"].remove(["tag_freeze", "read_begin"])
    p["graph"]["edges"].remove(["save", "emit"])
    rows.append(("transitive_paths_not_direct_edges", p, True))
    p = example()
    p["graph"]["edges"].remove(["ref_end", "emit"])
    p["graph"]["edges"].append(["emit", "ref_end"])
    rows.append(("saved_emit_before_reference_release", p, True))
    changes = [
        ("rcu_only", "reader", "lifetime", "RCU_ONLY"),
        ("address_only", "reader", "lifetime", "ADDRESS_UNCHANGED"),
        ("wrong_pre_reference_stage", "reader", "stage", "RAW_READ_PRE_REFERENCE"),
        ("unknown_mode", "reader", "mode", "OTHER"),
        ("relaxed_reference_is_not_acquire", "writer", "publication", "RELAXED_REFERENCE_ONLY"),
        ("buffer_release_is_not_target_publish", "writer", "publication", "BUFFER_RELEASE"),
        ("barrier_only", "writer", "publication", "BARRIER_ONLY"),
        ("partial_init", "writer", "components_initialized", False),
        ("missing_init", "writer", "components_initialized", None),
        ("zero_is_not_false_init", "writer", "components_initialized", 0),
        ("writer_coverage_unknown", "writer", "writer_set_closed", None),
        ("writer_coverage_false", "writer", "writer_set_closed", False),
        ("mutable_tag", "writer", "identity_write_once", False),
        ("missing_read_bounds", "reader", "all_component_reads_bounded", None),
        ("read_outside_bounds", "reader", "all_component_reads_bounded", False),
        ("added_reference", "reader", "observer_refs", 1),
        ("added_lock", "reader", "observer_locks", 1),
        ("false_is_not_zero_count", "reader", "observer_refs", False),
        ("unknown_reference_count", "reader", "observer_refs", None),
        ("live_lookup_emission", "reader", "emission", "LIVE_TARGET_LOOKUP"),
        ("root_changed", "membership", "root_after", 6),
        ("membership_generation_changed", "membership", "generation_after", 1),
        ("membership_generation_unknown", "membership", "generation_before", None),
        ("membership_guard_unknown", "membership", "guard", None),
        ("membership_other_cohort", "membership", "cohort", "synthetic-boot-b"),
        ("different_incarnation", "observed_identity", "cookie", 18),
        ("different_generation", "observed_identity", "generation", 1),
        ("different_epoch", "observed_identity", "epoch", 2),
        ("different_boot", "observed_identity", "cohort", "synthetic-boot-b"),
        ("unknown_cookie", "observed_identity", "cookie", None),
        ("reserved_zero_cookie", "observed_identity", "cookie", 0),
        ("unknown_generation", "observed_identity", "generation", None),
        ("false_generation_not_zero", "observed_identity", "generation", False),
        ("actual_source_head_drift", "source", "base_revision", "0" * 40),
        ("source_catalog_drift", "source", "catalog_digest", "0" * 64),
    ]
    for name, section, key, value in changes:
        p = example()
        p[section][key] = value
        rows.append((name, p, False))
    for kind in ("TASK", "NAMESPACE"):
        rows.append(("unsupported_reference_" + kind, example(kind=kind), False))
    for mode in ("PRIVATE_OWNER", "EXISTING_REFERENCE"):
        p = example(mode)
        p["identity"]["origin"] = p["observed_identity"]["origin"] = "FIRST_OBSERVED"
        p["reader"]["witness_identity"]["origin"] = "FIRST_OBSERVED"
        p["writer"]["witness_identity"]["origin"] = "FIRST_OBSERVED"
        rows.append(("seed_not_promoted_" + mode, p, False))
    for section in ("reader", "writer"):
        p = example()
        p[section]["witness_identity"]["cookie"] = 18
        rows.append((section + "_witness_other_object", p, False))
    for before, after in (("read_end", "save"), ("save", "ref_end"), ("ref_begin", "read_begin")):
        p = example()
        p["graph"]["edges"].remove([before, after])
        rows.append(("missing_relation_" + before + "_" + after, p, False))
    p = example()
    p["graph"]["edges"].append(["emit", "read_begin"])
    rows.append(("causal_cycle", p, False))
    p = example()
    p["graph"]["edges"].append(["context_end", "context_begin"])
    rows.append(("context_cycle", p, False))
    p = example()
    p["graph"]["edges"] = []
    rows.append(("ordered_vector_is_not_causality", p, False))
    p = example()
    p["graph"]["nodes"].append("raw_log_mono_time")
    rows.append(("unknown_clock_anchor", p, False))
    p = example()
    p["graph"]["nodes"][0] = p["graph"]["nodes"][1]
    rows.append(("duplicate_anchor", p, False))
    p = example()
    p["graph"]["edges"].append(copy.deepcopy(p["graph"]["edges"][0]))
    rows.append(("duplicate_edge", p, False))
    p = example()
    p["graph"]["edges"].append(["save", "outside"])
    rows.append(("foreign_anchor", p, False))
    p = example()
    p["evidence_class"] = "OBSERVED_UNTRUSTED"
    rows.append(("actual_evidence_not_synthetic", p, False))
    p = example()
    p["application_authorized"] = True
    rows.append(("injected_authority", p, False))
    return rows
