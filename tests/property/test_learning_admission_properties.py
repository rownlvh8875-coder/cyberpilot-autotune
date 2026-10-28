"""Synthetic generated thresholds and rejected-frame replay invariants."""

from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.integration.test_learning_admission import BASELINE, setup
from tests.unit.test_contracts import observation


@settings(derandomize=True, deadline=None)
@given(
    st.floats(min_value=0, max_value=100, allow_nan=False),
    st.integers(min_value=0, max_value=2**63),
    st.sampled_from([None, False]),
)
def test_repaired_rejected_sequence_with_later_timestamp_cannot_manufacture_samples(
    minimum,
    sequence,
    inactive,
):
    engine, learner, clock, _ = setup(gate_minimum=minimum, learner_minimum=minimum)
    snapshot = observation(sequence=sequence, control_active=inactive, speed_mps=minimum)
    rejected = engine.step(snapshot)
    assert rejected.effective_parameters == BASELINE
    assert learner.calls == 0
    clock.value = 11
    repaired = replace(snapshot, timestamp_s=11, control_active=True)
    replay = engine.step(repaired)
    assert replay.events[0].reason.value == "OUT_OF_ORDER"
    assert replay.effective_parameters == BASELINE
    assert learner.calls == 0
    clock.value = 12
    engine.step(replace(repaired, sequence=sequence + 1, timestamp_s=12))
    assert learner.calls == 1
    assert learner.statistics.sample_count == 1


@settings(derandomize=True, deadline=None)
@given(st.floats(min_value=0, max_value=100, allow_nan=False))
def test_exact_caller_supplied_minimum_is_admitted_once(minimum):
    engine, learner, _, _ = setup(gate_minimum=minimum, learner_minimum=minimum)
    result = engine.step(observation(speed_mps=minimum, control_active=True))
    assert learner.calls == 1
    assert result.effective_parameters == BASELINE
