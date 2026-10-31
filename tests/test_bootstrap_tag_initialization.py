"""Real catalog-consumer behavior; source evidence never becomes admission."""

import copy
import importlib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def catalog():
    # Independent literal contract,not generated from the model's registry.
    values = [
        (
            "TASK",
            "TASK_X86_DUP TASK_DUP_FAILURES TASK_ALLOC_CALL TASK_RESET_GATE "
            "TASK_LATE_ABORT TASK_FREE STATIC_INIT_TASK TASK_LAYOUT",
            "PRE_HOOK_DUP_FAILURES_UNOBSERVED TASK_FINAL_DESTRUCTION_UNOBSERVED "
            "UNSUPPORTED_CLONE_SCOPE_UNQUALIFIED",
        ),
        (
            "NAMESPACE",
            "NS_CONSTRUCTOR NS_SHARED NS_ATTACH NS_FREE NS_UNSHARE NS_UNSHARE_EFFECT "
            "NS_STATIC_INIT NS_LAYOUT NS_CPC_ALLOCATED",
            "UNSHARE_AND_SHARED_CONTEXT_UNQUALIFIED FALLBACK_NAMESPACE_ORIGIN_INCOMPLETE "
            "BACKING_FDT_REPLACEMENT_NOT_NAMESPACE_IDENTITY",
        ),
        (
            "OFD",
            "OFD_INIT OFD_NORMAL_ALLOC OFD_NOACCOUNT OFD_BACKING OFD_FREE OFD_CACHE "
            "OFD_LAYOUT OFD_RCU_REVALIDATE RCU_REUSE_WARNING",
            "NONSTANDARD_ALLOCATOR_HOOK_COVERAGE_INCOMPLETE RCU_OBJECT_REUSE_IDENTITY_UNQUALIFIED "
            "TAG_TUPLE_PUBLICATION_UNQUALIFIED",
        ),
        (
            "SEED",
            "SEED_WALK SEED_ABORT ORIGIN_READ COPY_RAW_READ",
            "ALL_MUTATOR_SEED_CUT_UNPROVEN ABORTED_SEED_TAGS_RETAINED_NO_HISTORY",
        ),
        (
            "ISSUER",
            "COOKIE_STORAGE COOKIE_CAS COHORT_NONCE",
            "ISSUER_WRAP_EXHAUSTION_RUNTIME_UNTESTED COHORT_NONCE_AUTHENTICITY_UNQUALIFIED",
        ),
    ]
    return [dict(subject=s, citations=c.split(), open_obligations=o.split()) for s, c, o in values]


def claims():
    return frozenset(c for row in catalog() for c in row["citations"])


def api():
    assert (ROOT / "tests/bootstrap_tag_audit/model.py").is_file(), "MISSING_SOURCE_AUDIT_MODEL"
    return importlib.import_module("tests.bootstrap_tag_audit.model").assess


def test_complete_selected_source_catalog_keeps_all_thirteen_runtime_obligations_open():
    decision = api()(catalog(), claims())
    assert tuple(b.subject for b in decision.boundaries) == (
        "TASK",
        "NAMESPACE",
        "OFD",
        "SEED",
        "ISSUER",
    )
    assert sum(len(b.citations) for b in decision.boundaries) == 33
    assert sum(len(b.open_obligations) for b in decision.boundaries) == 13
    assert decision.status == "BLOCKED" and decision.evidence_class == "STATIC_SOURCE_AUDIT_ONLY"
    assert decision.actual_global_drops is decision.actual_prohibited_operations is None
    assert all(value is False for _, value in decision.permissions)
    for field in (
        "initialization_qualified",
        "reuse_qualified",
        "publication_qualified",
        "issuer_runtime_qualified",
        "allocation_history_complete",
        "atomic_cut_proven",
        "runtime_qualified",
    ):
        assert getattr(decision, field) is False
        with pytest.raises(ValueError):
            replace(decision, **{field: True})


def test_order_does_not_change_canonical_source_scope_output():
    rows = catalog()
    for row in rows:
        row["citations"].reverse()
        row["open_obligations"].reverse()
    assert api()(list(reversed(rows)), claims()) == api()(catalog(), claims())


def test_output_defensively_copies_mutable_catalog_and_cannot_be_reclassified():
    rows = catalog()
    result = api()(rows, claims())
    before = copy.deepcopy(result)
    rows[0]["citations"].clear()
    rows[0]["open_obligations"].clear()
    rows.clear()
    assert result == before
    with pytest.raises(FrozenInstanceError):
        result.status = "ELIGIBLE"
    with pytest.raises(FrozenInstanceError):
        result.boundaries[0].subject = "QUALIFIED"


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate", "wrong", "not_list"])
def test_incomplete_or_cross_cohort_subjects_cannot_yield_a_silent_partial_audit(change):
    rows = catalog()
    if change == "missing":
        rows.pop()
    elif change == "extra":
        rows.append(copy.deepcopy(rows[0]))
    elif change == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif change == "wrong":
        rows[-1]["subject"] = "APPLICATION"
    else:
        rows = tuple(rows)
    with pytest.raises(ValueError):
        api()(rows, claims())


@pytest.mark.parametrize("column", ["citations", "open_obligations"])
@pytest.mark.parametrize("change", ["missing", "duplicate", "cross_subject", "bad_type", "tuple"])
def test_missing_duplicate_cross_subject_or_malformed_evidence_never_closes_obligations(
    column, change
):
    rows = catalog()
    if change == "missing":
        rows[0][column].pop()
    elif change == "duplicate":
        rows[0][column][0] = rows[0][column][1]
    elif change == "cross_subject":
        rows[0][column][0] = rows[1][column][0]
    elif change == "bad_type":
        rows[0][column][0] = []
    else:
        rows[0][column] = tuple(rows[0][column])
    with pytest.raises(ValueError):
        api()(rows, claims())


@pytest.mark.parametrize("value", [None, False, 0, {}, [], "TASK"])
def test_unavailable_or_ill_typed_subject_row_is_not_a_default_valid_subject(value):
    rows = catalog()
    rows[0] = value
    with pytest.raises(ValueError):
        api()(rows, claims())


@pytest.mark.parametrize("value", [None, False, 0, [], {}])
def test_unavailable_or_ill_typed_subject_name_is_not_zero_or_a_default(value):
    rows = catalog()
    rows[0]["subject"] = value
    with pytest.raises(ValueError):
        api()(rows, claims())


@pytest.mark.parametrize("field", ["runtime_qualified", "permissions", "application_authorized"])
def test_injected_authority_fields_are_rejected_not_ignored(field):
    rows = catalog()
    rows[0][field] = True
    with pytest.raises(ValueError):
        api()(rows, claims())


@pytest.mark.parametrize("change", ["missing", "extra", "mutable", "unavailable"])
def test_unverified_or_mismatched_source_claim_cohort_is_rejected(change):
    selected = claims()
    if change == "missing":
        selected = selected - {"TASK_X86_DUP"}
    elif change == "extra":
        selected = selected | {"UNPINNED_CLAIM"}
    elif change == "mutable":
        selected = set(selected)
    else:
        selected = None
    with pytest.raises(ValueError):
        api()(catalog(), selected)
