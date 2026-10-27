"""Pre-observe admission, synthetic speed policies and replay-safe reset semantics."""

import math
from dataclasses import replace

import pytest

from cyberpilot_autotune.contracts import ValidationError
from cyberpilot_autotune.core.residual import ResidualStatisticsLearner
from cyberpilot_autotune.runtime.engine import AutoTuneEngine
from cyberpilot_autotune.runtime.mode import RuntimeMode
from cyberpilot_autotune.safety.gate import GateConfig, SafetyGate
from tests.fixtures.synthetic import FakeClock
from tests.unit.test_contracts import observation, proposal, spec
from tests.unit.test_residual import config, sample

BASELINE = {"synthetic.test_only": 10.0}


class CountingLearner(ResidualStatisticsLearner):
    def __init__(self, minimum_speed=1.0):
        super().__init__(spec(), config(minimum_speed_mps=minimum_speed))
        self.calls = 0
        self.resets = 0

    def observe(self, snapshot):
        self.calls += 1
        return super().observe(snapshot)

    def reset(self):
        self.resets += 1
        super().reset()


def setup(*, mode=RuntimeMode.SHADOW, gate_minimum=1.0, learner_minimum=1.0):
    value, clock = CountingLearner(learner_minimum), FakeClock()
    gate = SafetyGate(
        {"synthetic.test_only": spec()}, GateConfig(1, 3, 0.8, minimum_speed_mps=gate_minimum)
    )
    engine = AutoTuneEngine(
        mode=mode, baseline_parameters=BASELINE, learner=value, gate=gate, clock=clock
    )
    return engine, value, clock, gate


REJECTIONS = [
    ({"control_active": None}, "CONTROL_STATE_UNAVAILABLE"),
    ({"control_active": False}, "CONTROL_INACTIVE"),
    ({"speed_mps": math.nextafter(1.0, 0.0)}, "BELOW_MINIMUM_SPEED"),
    ({"speed_mps": None}, "INVALID_OBSERVATION"),
    ({"driver_override": True}, "DRIVER_OVERRIDE"),
    ({"controller_saturated": True}, "CONTROLLER_SATURATED"),
    ({"driver_override": None}, "INVALID_OBSERVATION"),
    ({"controller_saturated": None}, "INVALID_OBSERVATION"),
    ({"source_valid": False}, "INVALID_OBSERVATION"),
    ({"source_age_s": 2}, "STALE_OBSERVATION"),
    ({"timestamp_s": 20}, "FUTURE_TIMESTAMP"),
    ({"baseline_parameters": {"synthetic.test_only": 11}}, "BASELINE_MISMATCH"),
]


@pytest.mark.parametrize("changes,reason", REJECTIONS)
def test_common_admission_rejects_before_observe_and_keeps_baseline(changes, reason):
    engine, value, _, _ = setup()
    result = engine.step(observation(**changes))
    assert value.calls == 0
    assert value.statistics is None
    assert value.resets == 1
    assert result.events[0].reason.value == reason
    assert result.proposals == result.gate_decisions == ()
    assert result.effective_parameters == result.baseline_parameters == BASELINE


@pytest.mark.parametrize("speed", [1.0, 2.0])
def test_active_frame_at_or_above_minimum_observes_exactly_once(speed):
    engine, value, _, _ = setup()
    result = engine.step(observation(control_active=True, speed_mps=speed))
    assert value.calls == 1
    assert value.statistics.sample_count == 1
    assert result.effective_parameters == BASELINE


@pytest.mark.parametrize("changes,reason", REJECTIONS)
def test_rejected_frame_cannot_be_repaired_and_replayed_to_increase_sample_count(changes, reason):
    engine, value, clock, _ = setup()
    for index in range(3):
        clock.value = 10 + index
        engine.step(sample(index))
    assert value.calls == 3
    clock.value = 13
    rejected = sample(3, **changes)
    result = engine.step(rejected)
    assert result.events[0].reason.value == reason
    assert value.calls == 3
    assert value.statistics is None
    repaired = replace(
        rejected,
        timestamp_s=13,
        control_active=True,
        speed_mps=2,
        driver_override=False,
        controller_saturated=False,
        source_valid=True,
        source_age_s=0,
        baseline_parameters=BASELINE,
    )
    replay = engine.step(repaired)
    assert replay.events[0].reason.value == "OUT_OF_ORDER"
    assert replay.effective_parameters == BASELINE
    assert value.calls == 3
    assert value.statistics is None
    clock.value = 14
    assert engine.step(sample(4)).effective_parameters == BASELINE
    assert value.calls == 4
    assert value.statistics.sample_count == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"control_active": None},
        {"control_active": False},
        {"speed_mps": 0.5},
        {"speed_mps": None},
        {"driver_override": True},
        {"controller_saturated": True},
    ],
)
def test_standalone_learner_repeats_admission_checks_as_defense_in_depth(changes):
    value = CountingLearner()
    for index in range(3):
        value.observe(sample(index))
    assert value.observe(sample(3, **changes)) == ()
    assert value.statistics is None
    assert value.observe(sample(3)) == ()  # reset cannot erase rejected frame's cursor.
    assert value.statistics is None
    assert value.observe(sample(4, speed_mps=1)) == ()
    assert value.statistics.sample_count == 1


def test_reset_preserves_high_water_but_new_instance_accepts_restarted_domain():
    value = CountingLearner()
    for index in range(3):
        value.observe(sample(index))
    value.reset()
    assert value.statistics is None
    assert value.observe(sample(0, timestamp_s=0)) == ()
    assert value.statistics is None
    assert value.observe(sample(3, timestamp_s=0)) == ()
    assert value.statistics is None
    fresh = CountingLearner()
    assert fresh.observe(sample(0, timestamp_s=0)) == ()
    assert fresh.statistics.sample_count == 1


def test_off_does_not_call_clock_admission_observe_or_reset(monkeypatch):
    engine, value, clock, gate = setup(mode=RuntimeMode.OFF)

    def forbidden(*args, **kwargs):
        raise AssertionError("OFF called a forbidden collaborator")

    monkeypatch.setattr(clock, "now_s", forbidden)
    monkeypatch.setattr(gate, "validate_observation", forbidden)
    monkeypatch.setattr(gate, "validate_learning_sample", forbidden, raising=False)
    monkeypatch.setattr(value, "observe", forbidden)
    monkeypatch.setattr(value, "reset", forbidden)
    result = engine.step(observation(control_active=None))
    assert result.events[0].reason.value == "MODE_OFF"
    assert result.effective_parameters == BASELINE


@pytest.mark.parametrize("changes,reason", REJECTIONS[:10])
def test_public_common_admission_returns_stable_reason(changes, reason):
    _, _, _, gate = setup()
    assert (
        gate.validate_learning_sample(
            observation(**changes), now_s=10, baseline_parameters=BASELINE
        ).value
        == reason
    )


def test_trusted_baseline_validation_precedes_control_veto():
    _, _, _, gate = setup()
    assert (
        gate.validate_learning_sample(
            observation(control_active=False), now_s=10, baseline_parameters={}
        ).value
        == "BASELINE_MISMATCH"
    )


@pytest.mark.parametrize(
    "baseline,reason",
    [
        ({"synthetic.test_only": float("nan")}, "NON_FINITE"),
        ({"synthetic.test_only": True}, "BASELINE_MISMATCH"),
        (None, "BASELINE_MISMATCH"),
    ],
)
def test_public_admission_rejects_malformed_trusted_baseline(baseline, reason):
    _, _, _, gate = setup()
    assert (
        gate.validate_learning_sample(observation(), now_s=10, baseline_parameters=baseline).value
        == reason
    )


@pytest.mark.parametrize(
    "bad_timestamp,reason",
    [
        (float("nan"), "NON_FINITE"),
        (-1, "INVALID_OBSERVATION"),
        ("invalid", "INVALID_OBSERVATION"),
    ],
)
def test_malformed_time_rejection_consumes_sequence_without_poisoning_time(bad_timestamp, reason):
    engine, value, clock, _ = setup()
    snapshot = observation(sequence=1)
    object.__setattr__(snapshot, "timestamp_s", bad_timestamp)
    assert engine.step(snapshot).events[0].reason.value == reason
    assert value.calls == 0
    assert engine.step(observation(sequence=1)).events[0].reason.value == "OUT_OF_ORDER"
    assert value.calls == 0
    clock.value = 11
    engine.step(observation(sequence=2, timestamp_s=11))
    assert value.calls == 1


def test_invalid_sequence_rejects_before_observe_and_preserves_valid_high_water():
    engine, value, clock, _ = setup()
    engine.step(observation(sequence=1))
    malformed = observation(sequence=2, timestamp_s=11)
    object.__setattr__(malformed, "sequence", -1)
    clock.value = 11
    result = engine.step(malformed)
    assert result.events[0].reason.value == "INVALID_OBSERVATION"
    assert result.effective_parameters == BASELINE
    assert value.calls == 1
    clock.value = 12
    engine.step(observation(sequence=2, timestamp_s=12))
    assert value.calls == 2


def test_legacy_snapshot_without_activity_is_unknown_and_never_observed():
    from cyberpilot_autotune.contracts import ObservationSnapshot

    legacy = ObservationSnapshot(
        10, 1, 0, "synthetic/test-only", True, 2, 0.25, 0, None, False, False, BASELINE
    )
    engine, value, _, _ = setup()
    assert legacy.control_active is None
    result = engine.step(legacy)
    assert result.events[0].reason.value == "CONTROL_STATE_UNAVAILABLE"
    assert value.calls == 0


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), True])
def test_common_minimum_speed_policy_validated(bad):
    with pytest.raises(ValidationError):
        GateConfig(1, 3, 0.8, minimum_speed_mps=bad)


def test_gate_policy_cannot_be_weaker_than_learner_requirement():
    with pytest.raises(ValidationError):
        setup(gate_minimum=1, learner_minimum=2)


def test_policy_comparison_preserves_finite_integer_precision():
    # Synthetic numeric boundary, not a vehicle speed or proposed limit.
    with pytest.raises(ValidationError):
        setup(gate_minimum=2**53, learner_minimum=2**53 + 1)


def test_stricter_common_policy_and_explicit_synthetic_zero_are_supported():
    engine, value, _, _ = setup(gate_minimum=2, learner_minimum=1)
    assert engine.step(observation(speed_mps=1)).events[0].reason.value == "BELOW_MINIMUM_SPEED"
    assert value.calls == 0
    engine, value, _, _ = setup(gate_minimum=0, learner_minimum=0)
    engine.step(observation(speed_mps=0))
    assert value.calls == 1


@pytest.mark.parametrize(
    "active,reason", [(None, "CONTROL_STATE_UNAVAILABLE"), (False, "CONTROL_INACTIVE")]
)
def test_candidate_gate_independently_rejects_inactive_control(active, reason):
    _, _, _, gate = setup()
    result = gate.evaluate(
        observation(control_active=active),
        proposal(),
        now_s=10,
        baseline_parameters=BASELINE,
        previous_sequence=0,
        previous_timestamp_s=9,
    )
    assert not result.eligible
    assert result.reason.value == reason
