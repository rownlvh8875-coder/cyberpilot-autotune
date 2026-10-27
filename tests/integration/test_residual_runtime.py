"""Real residual learner and engine; all parameters and observations synthetic."""

import pytest

from cyberpilot_autotune.runtime.engine import AutoTuneEngine
from cyberpilot_autotune.runtime.mode import RuntimeMode as M
from cyberpilot_autotune.safety.gate import GateConfig, SafetyGate
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from tests.fixtures.synthetic import FakeClock
from tests.unit.test_contracts import spec
from tests.unit.test_residual import learner, sample, warm

BASELINE = {"synthetic.test_only": 10.0}


def setup(mode=M.SHADOW, **configuration):
    value, clock = learner(**configuration), FakeClock()
    engine = AutoTuneEngine(
        mode=mode,
        baseline_parameters=BASELINE,
        learner=value,
        gate=SafetyGate({"synthetic.test_only": spec()}, GateConfig(1, 3, 0.8)),
        clock=clock,
    )
    return engine, value, clock


def feed(engine, clock, index, **changes):
    clock.value = 10 + index
    return engine.step(sample(index, **changes))


def warm_engine(engine, clock):
    for index in range(3):
        result = feed(engine, clock, index)
    return result


def test_eligible_real_learner_proposal_is_recorded_and_never_applied():
    engine, value, clock = setup()
    result = warm_engine(engine, clock)
    assert value.statistics.sample_count == 3
    assert result.proposals[0].proposed_value == 10.5
    assert result.gate_decisions[0].reason is R.ACCEPTED_FOR_SHADOW
    assert result.effective_parameters == result.baseline_parameters == BASELINE


@pytest.mark.parametrize(
    "changes",
    [
        {"source_valid": False},
        {"source_age_s": 2},
        {"speed_mps": None},
        {"baseline_parameters": {"synthetic.test_only": 11.0}},
        {"timestamp_s": 20},
        {"sequence": 2},
    ],
)
def test_pre_admission_rejection_resets_warm_statistics(changes):
    engine, value, clock = setup()
    warm_engine(engine, clock)
    rejected = feed(engine, clock, 3, **changes)
    assert rejected.effective_parameters == BASELINE
    assert rejected.events
    assert value.statistics is None
    recovered = feed(engine, clock, 4)
    assert recovered.proposals == ()
    assert value.statistics.sample_count == 1


@pytest.mark.parametrize("flag", ["driver_override", "controller_saturated"])
def test_override_and_saturation_exclude_samples_and_require_fresh_warmup(flag):
    engine, value, clock = setup()
    warm_engine(engine, clock)
    result = feed(engine, clock, 3, **{flag: True})
    assert result.effective_parameters == BASELINE
    assert result.proposals == ()
    assert value.statistics is None
    assert feed(engine, clock, 4).proposals == ()


def test_post_work_expiration_resets_already_updated_statistics(monkeypatch):
    engine, value, clock = setup()
    warm_engine(engine, clock)
    actual_observe = value.observe

    def slow_observe(snapshot):
        result = actual_observe(snapshot)
        clock.value += 2
        return result

    monkeypatch.setattr(value, "observe", slow_observe)
    result = feed(engine, clock, 3)
    assert result.events[0].reason is R.STALE_OBSERVATION
    assert result.effective_parameters == BASELINE
    assert value.statistics is None


def test_reset_error_is_internal_error_with_baseline_and_health_latch(monkeypatch):
    engine, value, clock = setup()
    warm_engine(engine, clock)

    def broken_reset():
        raise RuntimeError("PRIVATE_INPUT")

    monkeypatch.setattr(value, "reset", broken_reset)
    result = feed(engine, clock, 3, source_valid=False)
    assert result.events[0].reason is R.INTERNAL_ERROR
    assert "PRIVATE_INPUT" not in repr(result)
    assert result.effective_parameters == BASELINE
    assert feed(engine, clock, 4).events[0].reason is R.UNHEALTHY


def test_off_preserves_existing_statistics_without_observe_or_reset(monkeypatch):
    engine, value, clock = setup(mode=M.OFF)
    warm(value)
    before = value.statistics

    def forbidden(*args):
        raise AssertionError("OFF must not call learner lifecycle")

    monkeypatch.setattr(value, "observe", forbidden)
    monkeypatch.setattr(value, "reset", forbidden)
    result = feed(engine, clock, 3, source_valid=False)
    assert result.events[0].reason is R.MODE_OFF
    assert result.effective_parameters == BASELINE
    assert value.statistics == before


@pytest.mark.parametrize(
    "coefficient,reason",
    [(100, R.OUT_OF_BOUNDS), (10, R.STEP_LIMIT_EXCEEDED), (6, R.RATE_LIMIT_EXCEEDED)],
)
def test_gate_limits_are_independent_of_learner_and_always_retain_baseline(coefficient, reason):
    engine, _, clock = setup(parameter_delta_per_inv_m=coefficient)
    result = warm_engine(engine, clock)
    assert result.gate_decisions[0].reason is reason
    assert result.effective_parameters == BASELINE


def test_malformed_input_clears_evidence_and_cannot_escape():
    engine, value, clock = setup()
    warm_engine(engine, clock)
    assert engine.step(None).events[0].reason is R.INVALID_OBSERVATION
    assert value.statistics is None
