"""Author reproductions of independently found missing-fact suppression."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.diagnostics.actual_binding import assess_actual_binding
from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    complete_vector,
    document,
    replace_document,
)


def assess(v):
    return assess_actual_binding(v.bundle, expected_pre=v.pre, expected_post=v.post)


@pytest.mark.parametrize(
    "changes",
    (
        {"host_clock_cohort_sha256": None, "host_clock_generation": 1},
        {"host_clock_cohort_sha256": "9" * 64, "host_clock_generation": None},
    ),
)
def test_partial_expected_clock_known_conflict_survives(changes):
    v = complete_vector()
    r = assess(replace(v, pre=replace(v.pre, **changes)))
    assert "MISSING_PRE_REFERENCE" in r.reasons
    assert r.structural_status == "REJECTED" and "CONTEXT_MISMATCH" in r.reasons


@pytest.mark.parametrize("variant", ("reported_mismatch", "observed_image", "expected_image"))
def test_missing_asset_peer_known_conflict_survives(variant):
    v = complete_vector()
    if variant == "reported_mismatch":
        checks = document(v, "preflight")["body"]["asset_checks"]
        checks["kernel"] = "MISMATCH_REPORTED"
        v = complete_vector(body_changes={"preflight": {"asset_checks": checks}})
        v = replace_document(v, "baseline", None)
    elif variant == "observed_image":
        assets = document(v, "preflight")["body"]["observed_assets"]
        assets["image"] = "0" * 64
        v = complete_vector(body_changes={"preflight": {"observed_assets": assets}})
        v = replace_document(v, "baseline", None)
    else:
        assets = document(v, "baseline")["body"]["expected_assets"]
        assets["image"] = "0" * 64
        v = complete_vector(body_changes={"baseline": {"expected_assets": assets}})
        v = replace_document(v, "preflight", None)
    r = assess(v)
    assert "MISSING_DOCUMENT" in r.reasons and "assets" in r.not_evaluated_checks
    assert r.structural_status == "REJECTED" and "CONTEXT_MISMATCH" in r.reasons


@pytest.mark.parametrize(
    "field,new",
    (("workflow_run_id", "9" * 32), ("workflow_attempt_id", "9" * 32), ("case", "DFD03")),
)
def test_cross_reference_identity_survives_all_documents_missing(field, new):
    v = complete_vector()
    v = replace(
        v,
        bundle=replace(v.bundle, documents=tuple((r, None) for r, _ in v.bundle.documents)),
        post=replace(v.post, **{field: new}),
    )
    r = assess(v)
    assert r.structural_status == "REJECTED" and "CONTEXT_MISMATCH" in r.reasons


@pytest.mark.parametrize("missing", ("none", "partial"))
def test_known_pre_reference_hash_claims_conflict_without_complete_pre(missing):
    v = complete_vector()
    pre = None if missing == "none" else replace(v.pre, host_clock_generation=None)
    v = replace(v, pre=pre, post=replace(v.post, pre_reference_content_sha256="0" * 64))
    r = assess(v)
    assert "MISSING_PRE_REFERENCE" in r.reasons
    assert r.structural_status == "REJECTED" and "HASH_MISMATCH" in r.reasons


def test_known_document_hash_claims_conflict_without_target_bytes():
    v = complete_vector(body_changes={"preflight": {"baseline_sha256": "0" * 64}})
    v = replace_document(v, "baseline", None)
    r = assess(v)
    assert "MISSING_DOCUMENT" in r.reasons
    assert r.structural_status == "REJECTED" and "HASH_MISMATCH" in r.reasons


def test_missing_peer_does_not_invent_conflict_when_present_claims_agree():
    v = complete_vector()
    assert assess(replace_document(v, "baseline", None)).structural_status == "INCOMPLETE"
    v = replace(v, pre=replace(v.pre, host_clock_generation=None))
    r = assess(v)
    assert r.structural_status == "INCOMPLETE" and "HASH_MISMATCH" not in r.reasons
