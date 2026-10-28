"""Catch unsafe admission, clock mixing and latest-value joins in the audit model."""

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from tests.audit.receipt_model import AuditInput, Policy, evaluate, from_record

EVIDENCE = Path(__file__).resolve().parents[2] / "docs/evidence"


def test_literal_golden_cases():
    document = json.loads((EVIDENCE / "carrot_observability_cases.json").read_text())
    assert len(document["cases"]) >= 25
    for case in document["cases"]:
        sample = from_record(case["input"])
        before = sample.baseline_parameters
        actual = evaluate(sample, Policy(**document["synthetic_policy"]))
        assert actual.as_record() == case["expected"], case["id"]
        assert sample.baseline_parameters == before


def test_receipt_model_has_no_defaults_for_age_or_skew_policy():
    with pytest.raises(TypeError):
        Policy()
    for age, skew in ((-1, 0), (float("nan"), 0), (1, float("inf"))):
        with pytest.raises(ValueError):
            Policy(age, skew)


def test_synthetic_input_and_decision_are_immutable():
    sample = AuditInput()
    with pytest.raises(FrozenInstanceError):
        sample.host = "inactive"
    result = evaluate(sample, Policy(0.2, 0.03))
    with pytest.raises(FrozenInstanceError):
        result.source_valid = False


@pytest.mark.parametrize("host", ["active", "inactive", "unavailable", "unknown-wire"])
@pytest.mark.parametrize("safety", ["allowed", "disallowed", "unavailable", "unknown-wire"])
def test_activity_truth_table_requires_complete_permission_evidence(host, safety):
    sample = replace(AuditInput(), host=host, safety=safety)
    want = None
    if safety in {"allowed", "disallowed"}:
        if host == "inactive" or host == "active" and safety == "disallowed":
            want = False
        elif host == "active":
            want = True
    assert evaluate(sample, Policy(0.2, 0.03)).control_active is want


@pytest.mark.parametrize("instant", ["limited", "notLimited", "unavailable", "unknown-wire"])
@pytest.mark.parametrize("output", ["limited", "notLimited", "unavailable", "unknown-wire"])
def test_limit_truth_table_cannot_promote_missing_evidence_to_false(instant, output):
    sample = replace(AuditInput(), instantaneous=instant, output_limit=output)
    want = True if "limited" in (instant, output) else None
    if instant == output == "notLimited":
        want = False
    assert evaluate(sample, Policy(0.2, 0.03)).controller_saturated is want


def test_same_command_distinct_apply_and_duplicate_delivery_identity():
    first = AuditInput()
    second = replace(first, apply_ns=10_001_000_000)
    policy = Policy(0.2, 0.03)
    assert evaluate(first, policy).cohort_key != evaluate(second, policy).cohort_key
    assert evaluate(first, policy) == evaluate(first, policy)


def test_gate_age_algebra_does_not_double_count_delayed_publication():
    result = evaluate(AuditInput(), Policy(0.2, 0.03))
    assert result.source_age_s == 0.015
    assert result.evaluated_source_age_s == 0.035
    assert result.source_age_s + (10.02 - 10.0) == pytest.approx(0.035)


@pytest.mark.parametrize("kind", ["pid", "torque", "angle", "mebCurvature"])
def test_recognized_controller_requires_matching_calculation_version_and_kind(kind):
    sample = replace(AuditInput(), kind=kind, expected_kind=kind)
    assert evaluate(sample, Policy(0.2, 0.03)).conditional_checks_passed
    assert not evaluate(
        replace(sample, calculation_version=0), Policy(0.2, 0.03)
    ).conditional_checks_passed


def test_future_source_and_nonfinite_output_do_not_claim_activity():
    for sample in (
        replace(AuditInput(), command_ns=10_001_000_000),
        replace(AuditInput(), returned_actuators=(float("nan"), 0.0, 0.0)),
        replace(AuditInput(), returned_actuators=(float("inf"), 0.0, 0.0)),
    ):
        result = evaluate(sample, Policy(0.2, 0.03))
        assert result.control_active is None
        assert result.controller_saturated is None
        assert not result.source_valid


def test_boolean_versions_are_not_supported_numeric_versions():
    for sample in (
        replace(AuditInput(), receipt_version=True),
        replace(AuditInput(), calculation_version=True),
    ):
        assert not evaluate(sample, Policy(0.2, 0.03)).conditional_checks_passed


def test_caller_baseline_is_frozen_before_external_input_mutation():
    record = {"baseline_parameters": {"synthetic.test_only": 10.0}}
    sample = from_record(record)
    record["baseline_parameters"]["synthetic.test_only"] = 11.0
    assert sample.baseline_parameters == (("synthetic.test_only", 10.0),)


def test_newer_controls_state_is_not_joined_to_an_older_command():
    sample = replace(AuditInput(), controls_state_ns=9_995_000_000)
    assert not evaluate(sample, Policy(0.2, 0.03)).conditional_checks_passed


def test_pinned_missing_measurement_provenance_cannot_be_bypassed_by_synthetic_health():
    decision = evaluate(AuditInput(measurement_valid=True), Policy(0.2, 0.03))
    assert not decision.source_valid
    assert "MEASUREMENT_PROVENANCE_UNPROVEN_AT_PIN" in decision.reasons


def test_meb_real_pid_proof_does_not_prove_desired_target_semantics():
    sample = replace(AuditInput(), kind="mebCurvature", expected_kind="mebCurvature")
    decision = evaluate(sample, Policy(0.2, 0.03))
    assert decision.control_active is True
    assert decision.controller_saturated is False
    assert not decision.source_valid
    assert "MEB_DESIRED_RESPONSE_UNPROVEN_AT_PIN" in decision.reasons


@pytest.mark.parametrize("speed", [True, False, "4", None, float("nan"), float("inf")])
def test_speed_must_be_a_finite_numeric_estimate_not_a_boolean_or_missing_value(speed):
    decision = evaluate(replace(AuditInput(), speed_mps=speed), Policy(0.2, 0.03))
    assert "SPEED_UNAVAILABLE" in decision.reasons
