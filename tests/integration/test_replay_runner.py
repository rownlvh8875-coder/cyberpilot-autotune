"""Independent replay evidence and software acceptance, synthetic only."""

import json
from dataclasses import FrozenInstanceError
from fractions import Fraction
from importlib import import_module

import pytest

from cyberpilot_autotune.contracts import GateDecision, ValidationError
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from tests.fixtures.replay_data import replay_document, replay_event


class Timer:
    def __init__(self, step=1):
        self.value = 0
        self.step = step

    def __call__(self):
        self.value += self.step
        return self.value


def run(document=None, timer=None):
    api = import_module("cyberpilot_autotune.replay")
    return api.run_replay(
        api.load_replay(json.dumps(document or replay_document())), timer_ns=timer or Timer()
    )


def test_three_event_stream_has_exact_counts_and_baseline_identity():
    report = run()
    assert report.summary.event_count == 3
    assert report.summary.proposal_count == report.summary.eligible_count == 1
    assert report.summary.rejection_counts == {}
    assert report.summary.maximum_proposed_delta == Fraction(1, 2)
    assert report.summary.invariant_violations == report.summary.internal_error_count == 0
    assert report.software_checks_passed
    for off, shadow in zip(report.off_results, report.shadow_results, strict=True):
        assert off.proposals == off.gate_decisions == ()
        assert (
            off.effective_parameters == shadow.effective_parameters == {"synthetic.test_only": 10}
        )
    assert report.latency.off_ns == report.latency.shadow_ns == (1, 1, 1)
    assert report.latency.off_total_ns == report.latency.shadow_total_ns == 3


def test_timing_changes_do_not_change_authoritative_bytes_or_digest():
    slow, fast = run(timer=Timer(1000)), run(timer=Timer(1))
    assert slow.latency != fast.latency
    assert slow.deterministic_bytes() == fast.deterministic_bytes()
    assert slow.digest == fast.digest
    assert len(slow.digest) == 64
    assert "latency" not in slow.deterministic_bytes().decode()


def test_policy_input_and_float_types_are_bound_to_digest():
    baseline = run().digest
    document = replay_document()
    document["learner_config"]["alpha"] = 0.25  # Constant stream output remains unchanged.
    assert run(document).summary == run().summary
    assert run(document).digest != baseline
    document = replay_document()
    document["events"][0]["observation"]["speed_mps"] = 3.0
    assert run(document).digest != baseline
    document = replay_document()
    document["baseline_parameters"]["synthetic.test_only"] = 10  # Exact integer vs float.
    assert run(document).digest != baseline


def test_expected_admission_vetoes_are_counted_by_actual_reason():
    document = replay_document()
    document["events"] = [
        replay_event(0, driver_override=True),
        replay_event(1, controller_saturated=True),
        replay_event(2, control_active=None),
        replay_event(3, control_active=False),
        replay_event(4, speed_mps=0.5),
    ]
    summary = run(document).summary
    assert summary.proposal_count == 0
    assert summary.rejection_counts == {
        R.DRIVER_OVERRIDE: 1,
        R.CONTROLLER_SATURATED: 1,
        R.CONTROL_STATE_UNAVAILABLE: 1,
        R.CONTROL_INACTIVE: 1,
        R.BELOW_MINIMUM_SPEED: 1,
    }
    assert summary.override_exclusion_count == summary.saturation_exclusion_count == 1


@pytest.mark.parametrize(
    "coefficient,reason,delta",
    [(100, R.OUT_OF_BOUNDS, 25), (10, R.STEP_LIMIT_EXCEEDED, 2.5), (6, R.RATE_LIMIT_EXCEEDED, 1.5)],
)
def test_candidate_gate_vetoes_remain_counterfactual(coefficient, reason, delta):
    document = replay_document()
    document["learner_config"]["parameter_delta_per_inv_m"] = coefficient
    report = run(document)
    assert report.summary.rejection_counts == {reason: 1}
    assert report.summary.maximum_proposed_delta == delta
    assert report.summary.eligible_count == 0
    assert report.software_checks_passed


def test_post_work_clock_expiration_is_replayed_without_sleep():
    document = replay_document()
    document["events"][-1]["clock_after_s"] += 2
    report = run(document)
    assert report.summary.rejection_counts == {R.STALE_OBSERVATION: 1}
    assert report.summary.proposal_count == 0
    assert report.summary.maximum_proposed_delta == 0


def test_freshness_check_retains_small_age_at_large_monotonic_origin():
    document = replay_document()
    document["monotonic_origin_s"] = 1e16
    document["gate_config"].update(minimum_samples=2, maximum_observation_age_s=1.25)
    document["learner_config"].update(minimum_samples=2, maximum_source_age_s=1.25)
    document["events"] = [replay_event(i, source_age_s=1.25) for i in range(2)]
    for i, event in enumerate(document["events"]):
        capture = 1e16 + 2 * i
        event["observation"]["timestamp_s"] = capture
        event["clock_before_s"] = event["clock_after_s"] = capture
    report = run(document)
    assert report.summary.eligible_count == 1
    assert report.summary.invariant_violations == 0
    assert report.software_checks_passed


def test_internal_error_fails_software_acceptance_and_redacts_raw_message(monkeypatch):
    module = import_module("cyberpilot_autotune.replay.runner")

    def broken(snapshot):
        raise RuntimeError("PRIVATE_TOKEN")

    monkeypatch.setattr(module.ResidualStatisticsLearner, "observe", staticmethod(broken))
    report = run()
    assert report.summary.internal_error_count == 1
    assert report.summary.rejection_counts == {R.INTERNAL_ERROR: 1, R.UNHEALTHY: 2}
    assert not report.software_checks_passed
    assert b"PRIVATE_TOKEN" not in report.deterministic_bytes()
    assert all(
        result.effective_parameters == {"synthetic.test_only": 10}
        for result in report.shadow_results
    )


def test_checker_compares_to_trusted_baseline_not_result_self_equality(monkeypatch):
    module = import_module("cyberpilot_autotune.replay.runner")
    real_step = module.AutoTuneEngine.step

    def wrong_baseline(self, snapshot):
        result = real_step(self, snapshot)
        forged = {"synthetic.test_only": 99.0}
        object.__setattr__(result, "baseline_parameters", forged)
        object.__setattr__(result, "effective_parameters", forged)
        return result

    monkeypatch.setattr(module.AutoTuneEngine, "step", wrong_baseline)
    report = run()
    assert report.summary.invariant_violations > 0
    assert not report.software_checks_passed


@pytest.mark.parametrize("limit", ["bounds", "step", "rate", "binding"])
def test_checker_independently_detects_unsafe_gate_eligibility(monkeypatch, limit):
    module = import_module("cyberpilot_autotune.replay.runner")
    document = replay_document()
    if limit == "bounds":
        document["learner_config"]["parameter_delta_per_inv_m"] = 100
    elif limit == "step":
        document["parameter_spec"]["maximum_step"] = 0
    elif limit == "rate":
        document["parameter_spec"]["maximum_rate_per_second"] = 0

    def bypass(self, snapshot, proposal, **kwargs):
        candidate = proposal.proposed_value + (1 if limit == "binding" else 0)
        return GateDecision(
            True, proposal.parameter_id, candidate, R.ACCEPTED_FOR_SHADOW, (), kwargs["now_s"]
        )

    monkeypatch.setattr(module.SafetyGate, "evaluate", bypass)
    report = run(document)
    assert report.summary.invariant_violations > 0
    assert not report.software_checks_passed


def test_repeated_runs_have_fresh_learner_state_and_immutable_results():
    first, second = run(), run()
    assert first.digest == second.digest
    assert first.shadow_results == second.shadow_results
    with pytest.raises(FrozenInstanceError):
        first.summary.event_count = 100
    with pytest.raises(TypeError):
        first.summary.rejection_counts[R.INTERNAL_ERROR] = 9
    with pytest.raises(TypeError):
        first.shadow_results[0].effective_parameters["synthetic.test_only"] = 99


def test_forged_invalid_scenario_never_executes_and_invalid_timer_cannot_pass(monkeypatch):
    module = import_module("cyberpilot_autotune.replay.runner")
    api = import_module("cyberpilot_autotune.replay")
    scenario = api.load_replay(json.dumps(replay_document()))
    object.__setattr__(scenario, "schema_version", 9)

    def forbidden(*args):
        raise AssertionError("invalid scenario executed")

    monkeypatch.setattr(module.AutoTuneEngine, "step", forbidden)
    with pytest.raises(ValidationError):
        api.run_replay(scenario, timer_ns=Timer())
    valid = api.load_replay(json.dumps(replay_document()))
    with pytest.raises(ValidationError):
        api.run_replay(valid, timer_ns=lambda: True)
