"""Synthetic input failures cannot manufacture a usable source sample."""

from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from cyberpilot_autotune.adapters.carrot_receipt_contract import evaluate
from tests.fixtures.carrot_v2 import BASELINE, complete, measurement_change, stamp


@given(st.sampled_from([float("nan"), float("inf"), -float("inf"), True, None]))
def test_unavailable_or_nonfinite_never_becomes_measured_zero(value):
    attempt, policy = complete()
    result = evaluate(measurement_change(attempt, measured_curvature_inv_m=value), policy, BASELINE)
    assert result.snapshot is None
    assert result.reason.value == "INVALID_MEASUREMENT"
    assert attempt.baseline_parameters == BASELINE


@given(st.integers(min_value=1, max_value=2**63))
def test_timestamp_substitution_never_matches_a_different_source(offset):
    attempt, policy = complete()
    command = replace(
        attempt.source_command,
        event_time=stamp(attempt.receipt.source_command_time.value_ns + offset),
    )
    result = evaluate(replace(attempt, source_command=command), policy, BASELINE)
    assert result.snapshot is None and result.reason.value == "MISSING_SOURCE_COMMAND"


@given(st.integers(min_value=0, max_value=200_000_000))
def test_evaluation_delay_is_separate_from_age_at_apply(delay):
    attempt, policy = complete()
    attempt = replace(attempt, evaluation_time=stamp(10_000_000_000 + delay))
    result = evaluate(attempt, policy, BASELINE)
    assert result.snapshot.source_age_s == 0.1
    assert result.snapshot.timestamp_s == 10.0
    assert evaluate(attempt, policy, BASELINE) == result


@given(st.one_of(st.none(), st.text(), st.integers(), st.lists(st.integers())))
def test_malformed_boundary_never_raises(value):
    _, policy = complete()
    result = evaluate(value, policy, BASELINE)
    assert result.snapshot is None and result.reason.value == "INVALID_INPUT"
