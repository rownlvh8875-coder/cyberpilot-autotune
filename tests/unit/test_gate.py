"""Gate veto ordering and limits for synthetic parameters only."""

from importlib import import_module

import pytest

from cyberpilot_autotune.contracts import ValidationError
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from tests.unit.test_contracts import observation, proposal, spec

BASELINE = {"synthetic.test_only": 10.0}


def gate(**config):
    module = import_module("cyberpilot_autotune.safety.gate")
    values = dict(maximum_observation_age_s=1.0, minimum_samples=10, minimum_confidence=0.8)
    values.update(config)
    return module.SafetyGate({"synthetic.test_only": spec()}, module.GateConfig(**values))


def evaluate(snapshot=None, candidate=None, **changes):
    values = dict(
        now_s=10.0,
        baseline_parameters=BASELINE,
        previous_sequence=0,
        previous_timestamp_s=9.0,
        engine_healthy=True,
    )
    values.update(changes)
    return gate().evaluate(
        observation() if snapshot is None else snapshot,
        proposal() if candidate is None else candidate,
        **values,
    )


def test_valid_proposal_is_eligible_for_shadow_only():
    decision = evaluate()
    assert decision.eligible
    assert decision.reason is R.ACCEPTED_FOR_SHADOW
    assert decision.evaluated_candidate == 10.5


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"parameter_id": "unknown"}, R.UNKNOWN_PARAMETER),
        ({"baseline_value": 9}, R.BASELINE_MISMATCH),
        ({"context_key": "wrong"}, R.CONTEXT_MISMATCH),
        ({"sample_count": 9}, R.INSUFFICIENT_SAMPLES),
        ({"confidence": 0.79}, R.LOW_CONFIDENCE),
        ({"proposed_value": -0.1}, R.OUT_OF_BOUNDS),
        ({"proposed_value": 20.1}, R.OUT_OF_BOUNDS),
        ({"proposed_value": 12.1}, R.STEP_LIMIT_EXCEEDED),
        ({"proposed_value": 11.1}, R.RATE_LIMIT_EXCEEDED),
        ({"timestamp_s": 9.9}, R.INVALID_PROPOSAL),
        ({"timestamp_s": 10.1}, R.FUTURE_TIMESTAMP),
    ],
)
def test_proposal_rejections(changes, reason):
    decision = evaluate(candidate=proposal(**changes))
    assert not decision.eligible
    assert decision.reason is reason


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"source_age_s": 1.01}, R.STALE_OBSERVATION),
        ({"timestamp_s": 10.01}, R.FUTURE_TIMESTAMP),
        ({"sequence": 0}, R.OUT_OF_ORDER),
        ({"timestamp_s": 9.0}, R.OUT_OF_ORDER),
        ({"source_valid": False}, R.INVALID_OBSERVATION),
        ({"speed_mps": None}, R.INVALID_OBSERVATION),
        ({"desired_curvature_inv_m": None}, R.INVALID_OBSERVATION),
        ({"measured_curvature_inv_m": None}, R.INVALID_OBSERVATION),
        ({"driver_override": None}, R.INVALID_OBSERVATION),
        ({"controller_saturated": None}, R.INVALID_OBSERVATION),
        ({"driver_override": True}, R.DRIVER_OVERRIDE),
        ({"controller_saturated": True}, R.CONTROLLER_SATURATED),
        ({"baseline_parameters": {}}, R.BASELINE_MISMATCH),
    ],
)
def test_observation_rejections(changes, reason):
    assert evaluate(snapshot=observation(**changes)).reason is reason


def test_total_source_age_includes_time_since_snapshot():
    snapshot = observation(timestamp_s=9.5, source_age_s=0.6)
    assert evaluate(snapshot=snapshot).reason is R.STALE_OBSERVATION


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("target", ["baseline", "candidate", "observation", "now"])
def test_nonfinite_corruption_rejected(bad, target):
    snapshot, candidate = observation(), proposal()
    kwargs = {}
    if target == "baseline":
        kwargs["baseline_parameters"] = {"synthetic.test_only": bad}
    elif target == "candidate":
        object.__setattr__(candidate, "proposed_value", bad)
    elif target == "observation":
        object.__setattr__(snapshot, "speed_mps", bad)
    else:
        kwargs["now_s"] = bad
    assert evaluate(snapshot, candidate, **kwargs).reason is R.NON_FINITE


def test_invalid_objects_are_rejected():
    assert gate().validate_observation(None, now_s=10) is R.INVALID_OBSERVATION
    assert evaluate(candidate={}).reason is R.INVALID_PROPOSAL


def test_ordered_veto_precedence():
    assert (
        evaluate(
            snapshot=observation(source_age_s=2), candidate=proposal(parameter_id="unknown")
        ).reason
        is R.STALE_OBSERVATION
    )
    assert (
        evaluate(
            snapshot=observation(driver_override=True, controller_saturated=True),
            candidate=proposal(confidence=0),
        ).reason
        is R.LOW_CONFIDENCE
    )
    assert (
        evaluate(snapshot=observation(driver_override=True, controller_saturated=True)).reason
        is R.DRIVER_OVERRIDE
    )


def test_first_frame_rate_and_zero_rate_configuration():
    assert (
        evaluate(previous_sequence=None, previous_timestamp_s=None).reason is R.RATE_LIMIT_EXCEEDED
    )
    assert evaluate(
        candidate=proposal(proposed_value=10), previous_sequence=None, previous_timestamp_s=None
    ).eligible
    zero = spec(maximum_rate_per_second=0)
    module = import_module("cyberpilot_autotune.safety.gate")
    g = module.SafetyGate({zero.parameter_id: zero}, module.GateConfig(1, 10, 0.8))
    assert (
        g.evaluate(
            observation(),
            proposal(),
            now_s=10,
            baseline_parameters=BASELINE,
            previous_timestamp_s=9,
            previous_sequence=0,
        ).reason
        is R.RATE_LIMIT_EXCEEDED
    )


def test_exact_limits_are_allowed_without_clipping():
    decision = evaluate(candidate=proposal(proposed_value=11.0))
    assert decision.eligible
    assert decision.evaluated_candidate == 11.0


def test_health_veto_is_last():
    assert evaluate(engine_healthy=False).reason is R.UNHEALTHY
    assert (
        evaluate(candidate=proposal(proposed_value=11.1), engine_healthy=False).reason
        is R.RATE_LIMIT_EXCEEDED
    )


def test_registry_is_defensively_copied_and_missing_spec_rejects():
    module = import_module("cyberpilot_autotune.safety.gate")
    registry = {"synthetic.test_only": spec()}
    g = module.SafetyGate(registry, module.GateConfig(1, 10, 0.8))
    registry.clear()
    assert g.evaluate(
        observation(),
        proposal(),
        now_s=10,
        baseline_parameters=BASELINE,
        previous_timestamp_s=9,
        previous_sequence=0,
    ).eligible
    with pytest.raises(ValidationError):
        module.SafetyGate({"wrong": spec()}, module.GateConfig(1, 10, 0.8))
    empty = module.SafetyGate({}, module.GateConfig(1, 10, 0.8))
    assert (
        empty.evaluate(observation(), proposal(), now_s=10, baseline_parameters=BASELINE).reason
        is R.UNKNOWN_PARAMETER
    )


@pytest.mark.parametrize(
    "args", [(-1, 10, 0.8), (1, -1, 0.8), (1, 10, 1.1), (float("nan"), 10, 0.8)]
)
def test_invalid_gate_config_is_not_hidden(args):
    with pytest.raises(ValidationError):
        import_module("cyberpilot_autotune.safety.gate").GateConfig(*args)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("timestamp_s", "bad", R.INVALID_OBSERVATION),
        ("source_age_s", float("inf"), R.NON_FINITE),
        ("source_age_s", -1, R.INVALID_OBSERVATION),
        ("sequence", -1, R.INVALID_OBSERVATION),
        ("driver_override", 0, R.INVALID_OBSERVATION),
    ],
)
def test_forged_observation_fields_are_revalidated(field, value, reason):
    snapshot = observation()
    object.__setattr__(snapshot, field, value)
    assert evaluate(snapshot=snapshot).reason is reason


def test_forged_proposal_and_invalid_baseline_types_rejected():
    candidate = proposal()
    object.__setattr__(candidate, "sample_count", "many")
    assert evaluate(candidate=candidate).reason is R.INVALID_PROPOSAL
    assert evaluate(baseline_parameters={"synthetic.test_only": True}).reason is R.BASELINE_MISMATCH


def test_invalid_registry_configuration_and_programming_errors_remain_visible():
    module = import_module("cyberpilot_autotune.safety.gate")
    with pytest.raises(ValidationError):
        module.SafetyGate({}, None)
