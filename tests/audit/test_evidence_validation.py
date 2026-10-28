"""Catch corrupted pins, source manifests, and contradictory expected decisions."""

import copy

import pytest

from tests.audit.validate_observability import load_evidence, validate


def test_evidence_validates_without_reference_installation():
    sources, cases = load_evidence()
    result = validate(sources, cases)
    assert result["changed_files"] == 21
    assert result["cases"] >= 25


@pytest.mark.parametrize("defect", ["hash", "duplicate_path", "head", "range", "ordinal"])
def test_source_corruption_is_rejected(defect):
    sources, cases = load_evidence()
    sources = copy.deepcopy(sources)
    if defect == "hash":
        sources["changed_files"][0]["head"]["sha256"] = "invalid"
    elif defect == "duplicate_path":
        sources["changed_files"][0] = sources["changed_files"][1]
    elif defect == "head":
        sources["observability_head"] = "0" * 40
    elif defect == "range":
        sources["evidence_ranges"][0]["end_line"] = 0
    else:
        sources["schema_ordinals"]["CarOutput.actuationReceipt"] = 0
    with pytest.raises(ValueError):
        validate(sources, cases)


def test_expected_admission_cannot_be_changed_without_detection():
    sources, cases = load_evidence()
    cases = copy.deepcopy(cases)
    unavailable = next(case for case in cases["cases"] if case["id"] == "safety_unavailable")
    unavailable["expected"]["control_active"] = True
    with pytest.raises(ValueError):
        validate(sources, cases)


def test_receipt_ordinals_cannot_be_permuted_while_retaining_the_same_set():
    sources, cases = load_evidence()
    sources["schema_ordinals"]["ActuationReceipt"]["hostApplyMonoTime"] = 11
    sources["schema_ordinals"]["ActuationReceipt"]["controllerOutputReturned"] = 10
    with pytest.raises(ValueError):
        validate(sources, cases)
