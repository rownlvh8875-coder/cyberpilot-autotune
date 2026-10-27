"""Synthetic mathematical invariants, not vehicle-specific limits."""

from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.safety.reasons import ReasonCode as R
from tests.unit.test_contracts import observation, proposal
from tests.unit.test_gate import evaluate


@settings(derandomize=True, deadline=None)
@given(
    st.floats(min_value=-100, max_value=100, allow_nan=False),
    st.floats(min_value=0.001, max_value=5, allow_nan=False),
)
def test_eligible_candidate_respects_bounds_step_and_rate(value, elapsed):
    candidate = proposal(proposed_value=value)
    decision = evaluate(candidate=candidate, previous_timestamp_s=10 - elapsed)
    if decision.eligible:
        assert 0 <= value <= 20
        assert abs(value - 10) <= 2
        assert abs(value - 10) <= 10 - (10 - elapsed)


@settings(derandomize=True, deadline=None)
@given(st.sampled_from([float("nan"), float("inf"), -float("inf")]))
def test_nonfinite_is_never_eligible(value):
    candidate = proposal()
    object.__setattr__(candidate, "proposed_value", value)
    decision = evaluate(candidate=candidate)
    assert not decision.eligible
    assert decision.reason is R.NON_FINITE


@settings(derandomize=True, deadline=None)
@given(st.integers(min_value=0, max_value=10000), st.integers(min_value=0, max_value=10000))
def test_reordered_sequence_is_rejected(sequence, previous):
    if sequence <= previous:
        assert (
            evaluate(snapshot=observation(sequence=sequence), previous_sequence=previous).reason
            is R.OUT_OF_ORDER
        )
