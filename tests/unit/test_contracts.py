"""Constructor validation and aliasing regressions; every value is synthetic."""

from dataclasses import FrozenInstanceError, replace
from importlib import import_module

import pytest


def api():
    return import_module("cyberpilot_autotune.contracts")


def observation(**changes):
    values = dict(
        timestamp_s=10.0,
        sequence=1,
        source_age_s=0.0,
        context_key="synthetic/test-only",
        source_valid=True,
        speed_mps=2.0,
        desired_curvature_inv_m=0.01,
        measured_curvature_inv_m=0.0,
        lateral_acceleration_mps2=None,
        controller_saturated=False,
        driver_override=False,
        baseline_parameters={"synthetic.test_only": 10.0},
    )
    values.update(changes)
    return api().ObservationSnapshot(**values)


def spec(**changes):
    values = dict(
        parameter_id="synthetic.test_only",
        units="synthetic_unit",
        lower_bound=0.0,
        upper_bound=20.0,
        maximum_step=2.0,
        maximum_rate_per_second=1.0,
        description="Test only; not for vehicle use; no relationship to real tuning values",
        persistence_eligible=False,
    )
    values.update(changes)
    return api().ParameterSpec(**values)


def proposal(**changes):
    values = dict(
        parameter_id="synthetic.test_only",
        baseline_value=10.0,
        proposed_value=10.5,
        confidence=0.9,
        sample_count=20,
        context_key="synthetic/test-only",
        learner_version="scripted-test-v1",
        timestamp_s=10.0,
        evidence_summary=("synthetic evidence only",),
    )
    values.update(changes)
    return api().TuningProposal(**values)


def test_valid_observation_and_unavailable_is_distinct_from_zero():
    assert observation().measured_curvature_inv_m == 0.0
    assert observation(speed_mps=None).speed_mps is None
    assert observation().lateral_acceleration_mps2 is None


@pytest.mark.parametrize(
    "field",
    [
        "timestamp_s",
        "source_age_s",
        "speed_mps",
        "desired_curvature_inv_m",
        "measured_curvature_inv_m",
        "lateral_acceleration_mps2",
    ],
)
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), True, "1"])
def test_observation_rejects_invalid_numbers(field, bad):
    with pytest.raises(api().ValidationError):
        observation(**{field: bad})


@pytest.mark.parametrize(
    "changes",
    [
        {"timestamp_s": -1},
        {"source_age_s": -1},
        {"sequence": -1},
        {"sequence": True},
        {"sequence": 1.5},
        {"source_valid": 1},
        {"driver_override": 0},
        {"controller_saturated": "false"},
        {"context_key": ""},
        {"speed_mps": -1},
        {"baseline_parameters": {"x": float("nan")}},
        {"baseline_parameters": {"": 0}},
    ],
)
def test_observation_rejects_invalid_metadata(changes):
    with pytest.raises(api().ValidationError):
        observation(**changes)


def test_observation_defensively_copies_baseline_and_is_frozen():
    baseline = {"synthetic.test_only": 10.0}
    snapshot = observation(baseline_parameters=baseline)
    baseline["synthetic.test_only"] = 19.0
    assert snapshot.baseline_parameters["synthetic.test_only"] == 10.0
    with pytest.raises(TypeError):
        snapshot.baseline_parameters["synthetic.test_only"] = 11
    with pytest.raises(FrozenInstanceError):
        snapshot.sequence = 2


def test_valid_spec_defaults_to_reject_and_is_frozen():
    assert spec().out_of_range_policy.value == "REJECT"
    with pytest.raises(FrozenInstanceError):
        spec().upper_bound = 100


@pytest.mark.parametrize(
    "changes",
    [
        {"lower_bound": 21},
        {"maximum_step": -1},
        {"maximum_rate_per_second": -1},
        {"upper_bound": float("inf")},
        {"lower_bound": float("nan")},
        {"parameter_id": ""},
        {"units": ""},
        {"description": ""},
        {"persistence_eligible": 1},
        {"out_of_range_policy": "CLIP"},
    ],
)
def test_invalid_spec_rejected(changes):
    with pytest.raises(api().ValidationError):
        spec(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"confidence": -0.01},
        {"confidence": 1.01},
        {"confidence": float("nan")},
        {"sample_count": -1},
        {"sample_count": False},
        {"baseline_value": float("inf")},
        {"proposed_value": -float("inf")},
        {"timestamp_s": -1},
        {"learner_version": ""},
        {"evidence_summary": [2]},
    ],
)
def test_invalid_proposal_rejected(changes):
    with pytest.raises(api().ValidationError):
        proposal(**changes)


def test_proposal_is_frozen_and_copies_evidence():
    evidence = ["synthetic only"]
    candidate = proposal(evidence_summary=evidence)
    evidence.append("later")
    assert candidate.evidence_summary == ("synthetic only",)
    with pytest.raises(FrozenInstanceError):
        candidate.proposed_value = 12


def test_gate_decision_cannot_misrepresent_acceptance():
    contracts = api()
    reasons = import_module("cyberpilot_autotune.safety.reasons").ReasonCode
    with pytest.raises(contracts.ValidationError):
        contracts.GateDecision(True, "synthetic.test_only", 10.0, reasons.OUT_OF_BOUNDS, (), 10)


def test_result_is_immutable_and_enforces_baseline_identity():
    contracts = api()
    mode = import_module("cyberpilot_autotune.runtime.mode").RuntimeMode
    baseline = {"synthetic.test_only": 10.0}
    result = contracts.EngineResult(mode.OFF, 1, (), (), baseline, baseline, ())
    baseline["synthetic.test_only"] = 20
    assert dict(result.effective_parameters) == {"synthetic.test_only": 10.0}
    with pytest.raises(TypeError):
        result.effective_parameters["synthetic.test_only"] = 12
    with pytest.raises(FrozenInstanceError):
        result.mode = mode.SHADOW
    with pytest.raises(contracts.ValidationError):
        replace(result, effective_parameters={"synthetic.test_only": 11.0})


@pytest.mark.parametrize("bad", ["APPLY", "ADVISORY", "PRODUCTION", "OFF", None])
def test_unimplemented_or_untyped_modes_rejected(bad):
    contracts = api()
    with pytest.raises(contracts.ValidationError):
        contracts.EngineResult(bad, None, (), (), {}, {}, ())
