"""Baseline identity across mode, learner, gate and clock boundaries."""

from importlib import import_module

import pytest

from cyberpilot_autotune.contracts import ObservationSnapshot, ValidationError
from cyberpilot_autotune.runtime.mode import RuntimeMode as M
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from tests.fixtures.synthetic import FakeClock, ScriptedLearner
from tests.unit.test_contracts import observation, proposal
from tests.unit.test_gate import BASELINE, gate


def engine(mode=M.SHADOW, learner=None, clock=None, **kwargs):
    return import_module("cyberpilot_autotune.runtime.engine").AutoTuneEngine(
        mode=mode,
        baseline_parameters=BASELINE,
        learner=learner or ScriptedLearner(),
        gate=gate(),
        clock=clock or FakeClock(),
        **kwargs,
    )


def prime(runtime):
    return runtime.step(observation(timestamp_s=9, sequence=0))


def test_off_does_not_call_learner_clock_or_change_state():
    class ForbiddenClock:
        def now_s(self):
            raise AssertionError("OFF must not read time")

    learner = ScriptedLearner(error=AssertionError("OFF must not invoke learner"))
    runtime = engine(mode=M.OFF, learner=learner, clock=ForbiddenClock())
    first = runtime.step(observation())
    assert runtime.step(observation()) == first
    assert first.proposals == first.gate_decisions == ()
    assert first.events[0].reason is R.MODE_OFF
    assert dict(first.effective_parameters) == BASELINE
    assert learner.calls == 0


def test_shadow_records_eligible_candidate_but_retains_baseline():
    learner = ScriptedLearner()
    runtime = engine(learner=learner)
    prime(runtime)
    learner.output = (proposal(),)
    result = runtime.step(observation())
    assert result.gate_decisions[0].reason is R.ACCEPTED_FOR_SHADOW
    assert result.gate_decisions[0].evaluated_candidate == 10.5
    assert result.proposals[0].proposed_value == 10.5
    assert dict(result.effective_parameters) == BASELINE
    assert result.effective_parameters == result.baseline_parameters


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"driver_override": True}, R.DRIVER_OVERRIDE),
        ({"controller_saturated": True}, R.CONTROLLER_SATURATED),
    ],
)
def test_runtime_vetoes_retain_baseline(changes, expected):
    learner = ScriptedLearner()
    runtime = engine(learner=learner)
    prime(runtime)
    learner.output = (proposal(),)
    result = runtime.step(observation(**changes))
    assert result.events[0].reason is expected
    assert learner.calls == 1  # Only the prime frame was observed.
    assert result.proposals == result.gate_decisions == ()
    assert result.effective_parameters == BASELINE


def test_rate_violation_retains_baseline():
    learner = ScriptedLearner()
    runtime = engine(learner=learner)
    prime(runtime)
    learner.output = (proposal(proposed_value=11.1),)
    result = runtime.step(observation())
    assert result.gate_decisions[0].reason is R.RATE_LIMIT_EXCEEDED
    assert result.effective_parameters == BASELINE


@pytest.mark.parametrize(
    "snapshot,reason",
    [
        (None, R.INVALID_OBSERVATION),
        (observation(source_age_s=2), R.STALE_OBSERVATION),
        (observation(timestamp_s=11), R.FUTURE_TIMESTAMP),
        (observation(source_valid=False), R.INVALID_OBSERVATION),
    ],
)
def test_invalid_input_never_reaches_learner_even_with_no_proposals(snapshot, reason):
    learner = ScriptedLearner()
    runtime = engine(learner=learner)
    result = runtime.step(snapshot)
    assert result.events[0].reason is reason
    assert learner.calls == 0
    assert result.effective_parameters == BASELINE


@pytest.mark.parametrize("output", [None, {}, "bad", [object()], [proposal(), object()]])
def test_malformed_learner_output_fails_closed(output):
    runtime = engine(learner=ScriptedLearner(output=output))
    result = runtime.step(observation())
    assert result.events[0].reason is R.INVALID_PROPOSAL
    assert result.effective_parameters == BASELINE


def test_duplicate_or_excessive_proposals_are_rejected_atomically():
    for output in [(proposal(), proposal()), (proposal(),) * 65]:
        result = engine(learner=ScriptedLearner(output)).step(observation())
        assert result.events[0].reason is R.INVALID_PROPOSAL
        assert result.proposals == ()
        assert result.gate_decisions == ()


def test_exception_fallback_drops_partial_results_and_redacts_messages():
    learner = ScriptedLearner(error=RuntimeError("SECRET_VIN_TOKEN"))
    runtime = engine(learner=learner)
    result = runtime.step(observation())
    assert result.events[0].reason is R.INTERNAL_ERROR
    assert "RuntimeError" in result.events[0].detail
    assert "SECRET" not in repr(result)
    assert result.effective_parameters == BASELINE
    assert result.proposals == result.gate_decisions == ()
    learner.error = None
    assert runtime.step(observation(timestamp_s=10.1, sequence=2)).events[0].reason is R.UNHEALTHY


@pytest.mark.parametrize("component", ["gate", "clock"])
def test_unexpected_component_errors_become_internal_error(component):
    runtime = engine()
    if component == "gate":
        runtime._gate.validate_observation = lambda *a, **k: 1 / 0
    else:
        runtime._clock.now_s = lambda: 1 / 0
    result = runtime.step(observation())
    assert result.events[0].reason is R.INTERNAL_ERROR
    assert result.effective_parameters == BASELINE


def test_baseline_is_trusted_and_defensively_copied():
    baseline = dict(BASELINE)
    runtime = import_module("cyberpilot_autotune.runtime.engine").AutoTuneEngine(
        mode=M.SHADOW,
        baseline_parameters=baseline,
        learner=ScriptedLearner(),
        gate=gate(),
        clock=FakeClock(),
    )
    baseline["synthetic.test_only"] = 19
    result = runtime.step(observation(baseline_parameters=baseline))
    assert result.events[0].reason is R.BASELINE_MISMATCH
    assert result.effective_parameters == BASELINE


def test_attempted_baseline_mutation_by_learner_falls_back():
    class MutatingLearner:
        def observe(self, snapshot):
            snapshot.baseline_parameters["synthetic.test_only"] = 15
            return ()

    result = engine(learner=MutatingLearner()).step(observation())
    assert result.events[0].reason is R.INTERNAL_ERROR
    assert result.effective_parameters == BASELINE


def test_repeated_sequence_is_rejected_after_success_and_after_failure():
    learner = ScriptedLearner()
    runtime = engine(learner=learner)
    runtime.step(observation())
    assert runtime.step(observation()).events[0].reason is R.OUT_OF_ORDER
    assert learner.calls == 1


def test_clock_regression_and_slow_learner_fail_closed():
    clock = FakeClock()
    runtime = engine(clock=clock)
    runtime.step(observation())
    clock.value = 9.9
    assert runtime.step(observation(timestamp_s=9.8, sequence=2)).events[0].reason is R.UNHEALTHY

    class SlowLearner:
        def observe(self, snapshot):
            clock.value += 2
            return ()

    clock.value = 10
    result = engine(clock=clock, learner=SlowLearner()).step(observation())
    assert result.events[0].reason is R.STALE_OBSERVATION
    assert result.effective_parameters == BASELINE


def test_identical_streams_produce_identical_results():
    def run():
        clock, learner = FakeClock(), ScriptedLearner()
        runtime = engine(clock=clock, learner=learner)
        results = []
        for index in range(4):
            clock.value = 10 + index
            learner.output = (proposal(timestamp_s=clock.value),)
            results.append(runtime.step(observation(timestamp_s=clock.value, sequence=index)))
        return results

    assert run() == run()


@pytest.mark.parametrize("mode", ["APPLY", "SHADOW", None, 1])
def test_engine_rejects_unsupported_modes(mode):
    with pytest.raises(ValidationError):
        engine(mode=mode)


def test_noop_learner_is_stateless_and_deterministic():
    learner = import_module("cyberpilot_autotune.core.no_op").NoOpLearner()
    assert learner.observe(observation()) == learner.observe(observation()) == ()


def test_configuration_errors_are_visible():
    with pytest.raises(ValidationError):
        engine(maximum_proposals=0)


@pytest.mark.parametrize("mode", [M.OFF, M.SHADOW])
def test_uninitialized_observation_cannot_escape_runtime_boundary(mode):
    malformed = object.__new__(ObservationSnapshot)
    result = engine(mode=mode).step(malformed)
    assert result.effective_parameters == BASELINE
    assert result.events[0].reason is R.INTERNAL_ERROR


def test_mid_call_clock_regression_latches_fault():
    clock = FakeClock()

    class RegressingLearner:
        def observe(self, snapshot):
            clock.value = 9
            return ()

    result = engine(clock=clock, learner=RegressingLearner()).step(observation())
    assert result.events[0].reason is R.UNHEALTHY
    assert result.effective_parameters == BASELINE


def test_gate_exception_after_partial_evaluation_discards_all_results(monkeypatch):
    from cyberpilot_autotune.safety.gate import GateConfig, SafetyGate
    from tests.unit.test_contracts import spec

    first = spec()
    second = spec(parameter_id="synthetic.second")
    baseline = {"synthetic.test_only": 10.0, "synthetic.second": 10.0}
    g = SafetyGate(
        {first.parameter_id: first, second.parameter_id: second},
        GateConfig(1, 10, 0.8, minimum_speed_mps=1),
    )
    real_evaluate = g.evaluate

    def fail_on_second(snapshot, candidate, **kwargs):
        if candidate.parameter_id == "synthetic.second":
            raise RuntimeError("private input must not leak")
        return real_evaluate(snapshot, candidate, **kwargs)

    monkeypatch.setattr(g, "evaluate", fail_on_second)
    runtime = import_module("cyberpilot_autotune.runtime.engine").AutoTuneEngine(
        mode=M.SHADOW,
        baseline_parameters=baseline,
        gate=g,
        clock=FakeClock(),
        learner=ScriptedLearner((proposal(), proposal(parameter_id="synthetic.second"))),
    )
    result = runtime.step(observation(baseline_parameters=baseline))
    assert result.events[0].reason is R.INTERNAL_ERROR
    assert result.proposals == result.gate_decisions == ()
    assert result.effective_parameters == baseline


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_observation_falls_back_before_learner(bad):
    snapshot, learner = observation(), ScriptedLearner()
    object.__setattr__(snapshot, "speed_mps", bad)
    result = engine(learner=learner).step(snapshot)
    assert result.events[0].reason is R.NON_FINITE
    assert learner.calls == 0
    assert result.effective_parameters == BASELINE


@pytest.mark.parametrize("mode", [M.OFF, M.SHADOW])
def test_baseline_preserves_integer_values_beyond_float_exact_precision(mode):
    # Synthetic numeric boundary, unrelated to any vehicle value or tuning range.
    baseline = {"synthetic.test_only": 2**53 + 1}
    runtime = import_module("cyberpilot_autotune.runtime.engine").AutoTuneEngine(
        mode=mode,
        baseline_parameters=baseline,
        learner=ScriptedLearner(),
        gate=gate(),
        clock=FakeClock(),
    )
    result = runtime.step(observation(baseline_parameters=baseline))
    assert result.effective_parameters == baseline
    assert result.baseline_parameters == baseline
