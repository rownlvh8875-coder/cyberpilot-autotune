"""Synthetic premise adversaries; never actual receipt or allocation evidence."""

import copy
import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest


def api():
    assert importlib.util.find_spec("tests.inherited_ofd_design") is not None, "missing design API"
    return importlib.import_module("tests.inherited_ofd_design.model")


def example():
    objects = []
    for cookie, role, origin, stage, ordinal in (
        (1, "TASK", "FIRST_OBSERVED", "PRE_ARM_SEED", 5),
        (2, "NAMESPACE", "FIRST_OBSERVED", "PRE_ARM_SEED", 6),
        (3, "OFD", "FIRST_OBSERVED", "PRE_ARM_SEED", 7),
        (4, "TASK", "ALLOCATION", "POST_INIT_ALLOC", 21),
        (5, "NAMESPACE", "ALLOCATION", "POST_INIT_ALLOC", 22),
    ):
        objects.append(
            dict(
                cookie=cookie,
                role=role,
                generation=0,
                origin=origin,
                stage=stage,
                ordinal=ordinal,
                boot_scope="synthetic_boot",
                issuer_epoch="issuer1",
            )
        )
    bindings = []
    for fd in range(3):
        read = 41 + 3 * fd
        bindings.append(
            dict(
                fd=fd,
                presence="PRESENT" if fd < 2 else "NULL",
                source_ofd=3 if fd < 2 else None,
                destination_ofd=3 if fd < 2 else None,
                read=read,
                branch="REFERENCE" if fd < 2 else "CLEAR_OPEN",
                branch_ordinal=read + 1,
                branch_read=read,
                store=read + 2,
                store_read=read,
            )
        )
    return dict(
        schema="inherited-ofd-provenance-design-v1",
        evidence_class="SYNTHETIC_ONLY",
        context=dict(
            source_profile="PR40_PRIVATE64_BOOTSTRAP_DESIGN",
            source_revision="21a542eba9e889323b2cb1b7d7c75d9c9cab1025",
            source_manifest_sha256="69e566058e77804800e803d9faaa9e52f127cd652aaee39bf26b1966f0558013",
            boot_scope="synthetic_boot",
            issuer_epoch="issuer1",
            record_domain="PROPOSED_LINEAGE_V1",
        ),
        objects=objects,
        copy=dict(
            parent_task=1,
            source_namespace=2,
            child_task=4,
            destination_namespace=5,
            arm=10,
            begin=40,
            returned=1000,
            finalized=1001,
            return_result="SUCCESS",
            return_reason="NONE",
            task_result="COMMITTED",
            task_reason="NONE",
            bindings=bindings,
        ),
    )


def test_first_observation_links_aliases_without_inventing_birth_or_authority():
    data = example()
    result = api().evaluate(data)
    assert result.premises_consistent and result.linked_fds == ((0, 3), (1, 3))
    assert not result.unavailable and not result.reasons
    assert result.origins[0].origin == "FIRST_OBSERVED"
    assert result.origins[2].origin == "FIRST_OBSERVED"
    assert result.evidence_class == "SYNTHETIC_ONLY" and result.status == "BLOCKED"
    assert result.allocation_history_complete is False and not result.runtime_producer_implemented
    assert result.actual_global_drops is None and result.actual_prohibited_operations is None
    assert len(result.permissions) == 9 and all(v is False for _, v in result.permissions)
    data["objects"][0]["origin"] = "ALLOCATION"
    assert result.origins[0].origin == "FIRST_OBSERVED"
    with pytest.raises(FrozenInstanceError):
        result.origins[0].origin = "ALLOCATION"


@pytest.mark.parametrize(
    "field", ["parent_task", "source_namespace", "source_ofd", "destination_ofd"]
)
def test_unavailable_source_is_not_filled_from_neighbor_or_zero(field):
    data = example()
    if field.endswith("ofd"):
        for row in data["copy"]["bindings"][:2]:
            row[field] = None
    else:
        data["copy"][field] = None
    result = api().evaluate(data)
    assert result.premises_consistent and result.linked_fds == ()
    assert result.unavailable and not result.allocation_history_complete


def test_allocation_stage_premises_still_do_not_prove_whole_history():
    data = example()
    for i, row in enumerate(data["objects"][:3], 11):
        row.update(origin="ALLOCATION", stage="POST_INIT_ALLOC", ordinal=i)
    result = api().evaluate(data)
    assert result.premises_consistent and result.linked_fds == ((0, 3), (1, 3))
    assert not result.allocation_history_complete


@pytest.mark.parametrize("reason", ["TASK_INJECTED", "TASK_FAILED"])
def test_successful_copy_with_aborted_child_is_not_committed_lineage(reason):
    data = example()
    data["copy"].update(task_result="ABORTED", task_reason=reason)
    result = api().evaluate(data)
    assert result.premises_consistent and result.linked_fds == ()


@pytest.mark.parametrize("reason", ["ALLOC_INJECTED", "CONSTRUCTOR_INJECTED", "NATURAL_ALLOC"])
def test_failed_constructor_can_have_no_destination_and_no_child_links(reason):
    data = example()
    data["copy"].update(
        destination_namespace=None,
        return_result="FAILED",
        return_reason=reason,
        task_result="ABORTED",
        task_reason="COPY_FAILED",
        bindings=[],
    )
    result = api().evaluate(data)
    assert result.premises_consistent and result.linked_fds == ()


MUTATIONS = [
    (
        "seeded_child",
        lambda d: d["objects"][3].update(origin="FIRST_OBSERVED", stage="PRE_ARM_SEED", ordinal=8),
    ),
    (
        "seeded_destination",
        lambda d: d["objects"][4].update(origin="FIRST_OBSERVED", stage="PRE_ARM_SEED", ordinal=8),
    ),
    ("observed_class", lambda d: d.update(evidence_class="OBSERVED_UNTRUSTED")),
    ("origin_promotion", lambda d: d["objects"][0].update(origin="ALLOCATION")),
    ("duplicate_cookie", lambda d: d["objects"].append(copy.deepcopy(d["objects"][0]))),
    ("role_collision", lambda d: d["objects"][2].update(cookie=4)),
    ("boot_drift", lambda d: d["objects"][2].update(boot_scope="other")),
    ("issuer_drift", lambda d: d["objects"][2].update(issuer_epoch="other")),
    ("generation", lambda d: d["objects"][2].update(generation=1)),
    ("seed_after_arm", lambda d: d["objects"][2].update(ordinal=11)),
    ("allocation_before_arm", lambda d: d["objects"][3].update(ordinal=9)),
    ("allocation_after_read", lambda d: d["objects"][3].update(ordinal=45)),
    ("unknown_origin", lambda d: d["objects"][2].update(origin="INODE_HASH")),
    ("wrong_role", lambda d: d["copy"].update(parent_task=3)),
    ("unknown_handle", lambda d: d["copy"].update(child_task=9)),
    ("zero_handle", lambda d: d["copy"].update(parent_task=0)),
    ("bool_handle", lambda d: d["copy"].update(parent_task=True)),
    ("float_handle", lambda d: d["copy"].update(parent_task=1.0)),
    ("unknown_child", lambda d: d["copy"].update(child_task=None)),
    ("wrong_domain", lambda d: d["context"].update(record_domain="CPC_PLUS_CPS_SORTED")),
    ("wrong_source", lambda d: d["context"].update(source_revision="0" * 40)),
    ("bad_boot", lambda d: d["context"].update(boot_scope="route/identity")),
    ("wrong_pair", lambda d: d["copy"]["bindings"][0].update(store_read=44)),
    ("wrong_branch_pair", lambda d: d["copy"]["bindings"][0].update(branch_read=44)),
    ("wrong_branch", lambda d: d["copy"]["bindings"][0].update(branch="CLEAR_OPEN")),
    ("null_ofd", lambda d: d["copy"]["bindings"][2].update(source_ofd=3)),
    ("ofd_wrong_role", lambda d: d["copy"]["bindings"][0].update(destination_ofd=5)),
    ("wrong_presence", lambda d: d["copy"]["bindings"][0].update(presence="UNKNOWN")),
    ("duplicate_fd", lambda d: d["copy"]["bindings"][1].update(fd=0)),
    ("wide_fd", lambda d: d["copy"]["bindings"][2].update(fd=64)),
    ("overlap", lambda d: d["copy"]["bindings"][1].update(read=42)),
    ("late_store", lambda d: d["copy"]["bindings"][2].update(store=1000)),
    ("reversed_terminal", lambda d: d["copy"].update(returned=1002)),
    ("success_failure_reason", lambda d: d["copy"].update(return_reason="CONSTRUCTOR_INJECTED")),
    ("commit_failure_reason", lambda d: d["copy"].update(task_reason="TASK_INJECTED")),
    (
        "failed_committed",
        lambda d: d["copy"].update(return_result="FAILED", return_reason="NATURAL_ALLOC"),
    ),
    ("unknown_return", lambda d: d["copy"].update(return_result="UNKNOWN")),
    ("unknown_task", lambda d: d["copy"].update(task_result="UNKNOWN")),
    ("authority", lambda d: d.update(application_authorized=True)),
    ("nan", lambda d: d["copy"].update(begin=float("nan"))),
    ("too_many_objects", lambda d: d.update(objects=d["objects"] * 14)),
    ("too_many_bindings", lambda d: d["copy"].update(bindings=d["copy"]["bindings"] * 22)),
]


@pytest.mark.parametrize(("label", "mutate"), MUTATIONS, ids=[label for label, _ in MUTATIONS])
def test_malformed_or_fabricated_provenance_never_produces_conditional_links(label, mutate):
    data = example()
    mutate(data)
    result = api().evaluate(data)
    assert not result.premises_consistent and result.reasons, label
    assert result.linked_fds == () and result.status == "BLOCKED"
    if label.startswith("seeded_"):
        assert "FORK_SUBJECT_ALLOCATION_REQUIRED" in result.reasons


def test_distinct_ofd_handles_are_not_merged_even_when_alias_copy_is_possible():
    data = example()
    data["objects"].append({**data["objects"][2], "cookie": 6, "ordinal": 8})
    data["copy"]["bindings"][1].update(source_ofd=6, destination_ofd=6)
    result = api().evaluate(data)
    assert result.premises_consistent and result.linked_fds == ((0, 3), (1, 6))
    data["copy"]["bindings"][1]["destination_ofd"] = 3
    assert not api().evaluate(data).premises_consistent


def test_empty_bindings_do_not_prove_execution_or_complete_allocation_history():
    data = example()
    data["copy"]["bindings"] = []
    result = api().evaluate(data)
    assert result.premises_consistent and not result.linked_fds
    assert not result.allocation_history_complete and not result.runtime_producer_implemented


def test_canonical_digest_preserves_identity_cohort_and_ignores_field_order():
    data = example()
    baseline = api().evaluate(data).digest
    assert baseline == api().evaluate(dict(reversed(list(data.items())))).digest
    data["context"]["issuer_epoch"] = "issuer2"
    for row in data["objects"]:
        row["issuer_epoch"] = "issuer2"
    assert api().evaluate(data).digest != baseline


def test_cyclic_input_is_bounded_rejection_not_recursion_or_authority():
    data = example()
    data["loop"] = data
    result = api().evaluate(data)
    assert not result.premises_consistent and result.digest is None
