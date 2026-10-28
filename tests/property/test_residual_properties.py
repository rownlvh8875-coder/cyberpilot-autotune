"""Generated synthetic evidence for finite, bounded and deterministic statistics."""

import math
import sys

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.unit.test_residual import learner, sample


@settings(derandomize=True, deadline=None)
@given(
    st.lists(st.floats(min_value=-1, max_value=1, allow_nan=False), max_size=40),
    st.floats(min_value=0.01, max_value=1, allow_nan=False),
)
def test_generated_streams_are_deterministic_bounded_and_do_not_mutate_baseline(values, alpha):
    def run():
        value = learner(
            alpha=alpha, mean_deadband_inv_m=0, maximum_samples=5, maximum_state_age_s=100
        )
        results = []
        for index, residual in enumerate(values):
            snapshot = sample(index, residual=residual)
            proposals = value.observe(snapshot)
            assert snapshot.baseline_parameters == {"synthetic.test_only": 10}
            statistics = value.statistics
            assert 1 <= statistics.sample_count <= 5
            assert -1 <= statistics.mean_residual_inv_m <= 1
            assert 0 <= statistics.mean_absolute_innovation_inv_m <= 2
            assert 0 <= statistics.confidence <= 1
            for proposal in proposals:
                assert math.isfinite(proposal.proposed_value)
                assert proposal.baseline_value == 10
                assert proposal.sample_count >= 3
            results.append((statistics, proposals))
        return results

    assert run() == run()


@settings(derandomize=True, deadline=None)
@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda value: value != 0),
)
def test_extreme_finite_signals_never_produce_nonfinite_statistics_or_proposals(
    desired,
    measured,
    coefficient,
):
    value = learner(
        minimum_samples=2,
        maximum_absolute_residual_inv_m=sys.float_info.max,
        mean_deadband_inv_m=0,
        parameter_delta_per_inv_m=coefficient,
    )
    for index, sign in enumerate([1, -1, 1]):
        for proposal in value.observe(
            sample(index, residual=desired * sign, measured_curvature_inv_m=measured * sign)
        ):
            assert math.isfinite(proposal.proposed_value)
            assert 0 <= proposal.confidence <= 1
        if value.statistics is not None:
            assert math.isfinite(value.statistics.mean_residual_inv_m)
            assert math.isfinite(value.statistics.mean_absolute_innovation_inv_m)
