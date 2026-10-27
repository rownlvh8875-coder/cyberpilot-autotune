"""Synthetic research streams only; no relationship to vehicle tuning values."""

from dataclasses import FrozenInstanceError, replace
from importlib import import_module

import pytest

from cyberpilot_autotune.contracts import ValidationError
from tests.unit.test_contracts import observation, spec


def config(**changes):
    values = dict(
        alpha=0.5,
        minimum_samples=3,
        maximum_samples=8,
        maximum_source_age_s=1.0,
        maximum_sample_gap_s=2.0,
        maximum_state_age_s=10.0,
        maximum_absolute_residual_inv_m=1.0,
        consistency_scale_inv_m=0.5,
        mean_deadband_inv_m=0.01,
        parameter_delta_per_inv_m=2.0,
    )
    values.update(changes)
    return import_module("cyberpilot_autotune.core.residual").ResidualStatisticsConfig(**values)


def learner(**changes):
    return import_module("cyberpilot_autotune.core.residual").ResidualStatisticsLearner(
        spec(),
        config(**changes),
    )


def sample(index, residual=0.25, **changes):
    values = dict(
        timestamp_s=10.0 + index,
        sequence=index,
        desired_curvature_inv_m=residual,
        measured_curvature_inv_m=0.0,
    )
    values.update(changes)
    return observation(**values)


def warm(value):
    for index in range(3):
        output = value.observe(sample(index))
    return output


def test_constant_residual_waits_for_samples_then_proposes_from_original_baseline():
    value = learner()
    assert value.statistics is None
    assert value.observe(sample(0)) == ()
    assert value.statistics.sample_count == 1
    assert value.statistics.confidence == pytest.approx(1 / 3)
    assert value.observe(sample(1)) == ()
    (proposal,) = value.observe(sample(2))
    assert proposal.parameter_id == "synthetic.test_only"
    assert proposal.baseline_value == 10.0
    assert proposal.proposed_value == 10.5
    assert proposal.sample_count == 3
    assert proposal.confidence == 1.0
    assert proposal.timestamp_s == 12.0
    assert proposal.context_key == "synthetic/test-only"
    assert proposal.learner_version == "residual-ewma-v1"
    assert proposal.evidence_summary
    (later,) = value.observe(sample(3))
    assert later.proposed_value == 10.5  # No accumulation from previous proposal.


def test_ewma_and_innovation_confidence_match_hand_calculated_values():
    value = learner(minimum_samples=2)
    value.observe(sample(0, residual=0.25))
    (proposal,) = value.observe(sample(1, residual=0.5))
    assert value.statistics.mean_residual_inv_m == 0.375
    assert value.statistics.mean_absolute_innovation_inv_m == 0.125
    assert proposal.confidence == 0.75  # 1 * (1 - .125/.5)
    assert proposal.proposed_value == 10.75


@pytest.mark.parametrize("coefficient,expected", [(2, 10.5), (-2, 9.5)])
def test_conversion_sign_is_explicit(coefficient, expected):
    (proposal,) = warm(learner(parameter_delta_per_inv_m=coefficient))
    assert proposal.proposed_value == expected


def test_measured_curvature_is_subtracted_and_deadband_is_inclusive():
    value = learner(minimum_samples=2)
    value.observe(sample(0, residual=0.25, measured_curvature_inv_m=0.25))
    assert value.observe(sample(1, residual=0.25, measured_curvature_inv_m=0.25)) == ()
    assert value.statistics.mean_residual_inv_m == 0
    value = learner(minimum_samples=2, mean_deadband_inv_m=0.25)
    value.observe(sample(0))
    assert value.observe(sample(1)) == ()


def test_learner_does_not_clip_to_parameter_bounds_or_step():
    (proposal,) = warm(learner(parameter_delta_per_inv_m=100.0))
    assert proposal.proposed_value == 35.0  # Gate owns synthetic upper bound 20.


@pytest.mark.parametrize(
    "changes",
    [
        {"source_valid": False},
        {"speed_mps": None},
        {"desired_curvature_inv_m": None},
        {"measured_curvature_inv_m": None},
        {"driver_override": True},
        {"driver_override": None},
        {"controller_saturated": True},
        {"controller_saturated": None},
        {"source_age_s": 1.1},
        {"baseline_parameters": {}},
    ],
)
def test_excluded_sample_clears_warm_evidence(changes):
    value = learner()
    warm(value)
    assert value.observe(sample(3, **changes)) == ()
    assert value.statistics is None
    assert value.observe(sample(4)) == ()
    assert value.statistics.sample_count == 1


def test_unavailable_optional_acceleration_does_not_block_learning():
    (proposal,) = warm(learner())
    assert proposal.confidence == 1


def test_outlier_is_excluded_without_clipping_and_requires_fresh_samples():
    value = learner()
    warm(value)
    assert value.observe(sample(3, residual=1.01)) == ()
    assert value.statistics is None
    assert value.observe(sample(4)) == ()
    assert value.statistics.mean_residual_inv_m == 0.25


@pytest.mark.parametrize(
    "changes",
    [
        {"context_key": "synthetic/other"},
        {"baseline_parameters": {"synthetic.test_only": 11.0}},
        {"timestamp_s": 15.0},
    ],
)
def test_context_baseline_or_gap_change_restarts_with_current_sample(changes):
    value = learner()
    warm(value)
    assert value.observe(sample(3, **changes)) == ()
    assert value.statistics.sample_count == 1


def test_total_window_age_expires_even_with_fresh_short_gaps():
    value = learner(maximum_sample_gap_s=1, maximum_state_age_s=3)
    for index in range(4):
        value.observe(sample(index))
    assert value.statistics.sample_count == 4  # Exact age boundary is admitted.
    assert value.observe(sample(4)) == ()
    assert value.statistics.sample_count == 1


def test_exact_source_age_and_gap_boundaries_are_admitted():
    value = learner(minimum_samples=2)
    value.observe(sample(0, source_age_s=1))
    assert value.observe(sample(1, timestamp_s=12, source_age_s=1))


@pytest.mark.parametrize(
    "index,changes", [(2, {}), (3, {"timestamp_s": 12}), (1, {"timestamp_s": 13})]
)
def test_reordered_input_clears_evidence_without_resetting_high_water(index, changes):
    value = learner()
    warm(value)
    assert value.observe(sample(index, **changes)) == ()
    assert value.statistics is None
    assert value.observe(sample(2)) == ()
    assert value.statistics is None
    assert value.observe(sample(4)) == ()
    assert value.statistics.sample_count == 1


def test_reset_preserves_cursor_and_statistics_snapshot_is_immutable():
    value = learner()
    warm(value)
    statistics = value.statistics
    with pytest.raises(FrozenInstanceError):
        statistics.sample_count = 100
    value.reset()
    assert value.statistics is None
    assert value.observe(sample(2)) == ()
    assert value.statistics is None
    value.observe(sample(3))
    assert statistics.sample_count == 3
    assert value.statistics.sample_count == 1


def test_count_is_capped_and_context_cache_is_not_retained():
    value = learner(maximum_samples=3, maximum_state_age_s=100)
    for index in range(30):
        value.observe(sample(index))
    assert value.statistics.sample_count == 3
    value.observe(sample(30, context_key="synthetic/new"))
    assert value.statistics.sample_count == 1
    value.observe(sample(31))
    assert value.statistics.sample_count == 1


@pytest.mark.parametrize(
    "field,bad",
    [
        ("speed_mps", float("nan")),
        ("sequence", -1),
        ("baseline_parameters", {"synthetic.test_only": float("inf")}),
    ],
)
def test_corrupted_contract_raises_validation_error_after_clearing_evidence(field, bad):
    value = learner()
    warm(value)
    snapshot = sample(3)
    object.__setattr__(snapshot, field, bad)
    with pytest.raises(ValidationError):
        value.observe(snapshot)
    assert value.statistics is None


def test_malformed_observation_raises_typed_error():
    with pytest.raises(ValidationError):
        learner().observe(None)


def test_extreme_residual_subtraction_and_candidate_overflow_emit_nothing():
    value = learner()
    warm(value)
    assert value.observe(sample(3, residual=1e308, measured_curvature_inv_m=-1e308)) == ()
    assert value.statistics is None
    value = learner(
        parameter_delta_per_inv_m=1e308, maximum_absolute_residual_inv_m=10, mean_deadband_inv_m=0
    )
    for index in range(3):
        assert value.observe(sample(index, residual=10)) == ()
    assert value.statistics is None


def test_noise_reduces_confidence_without_claiming_physical_quality():
    value = learner(minimum_samples=2, alpha=1, consistency_scale_inv_m=0.25)
    value.observe(sample(0, residual=0.25))
    (proposal,) = value.observe(sample(1, residual=-0.25))
    assert proposal.confidence == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"alpha": 0},
        {"alpha": 1.1},
        {"alpha": float("nan")},
        {"alpha": True},
        {"minimum_samples": 1},
        {"minimum_samples": True},
        {"maximum_samples": 2},
        {"maximum_source_age_s": -1},
        {"maximum_sample_gap_s": 0},
        {"maximum_state_age_s": 1},
        {"maximum_absolute_residual_inv_m": 0},
        {"consistency_scale_inv_m": 0},
        {"mean_deadband_inv_m": -1},
        {"mean_deadband_inv_m": 1},
        {"parameter_delta_per_inv_m": 0},
        {"parameter_delta_per_inv_m": float("inf")},
    ],
)
def test_configuration_rejects_unsafe_or_ambiguous_values(changes):
    with pytest.raises(ValidationError):
        config(**changes)


def test_configuration_is_frozen_and_invalid_constructor_inputs_are_visible():
    configuration = config()
    with pytest.raises(FrozenInstanceError):
        configuration.alpha = 0.9
    module = import_module("cyberpilot_autotune.core.residual")
    with pytest.raises(ValidationError):
        module.ResidualStatisticsLearner(None, configuration)
    with pytest.raises(ValidationError):
        module.ResidualStatisticsLearner(spec(), None)
    value = learner()
    value.observe(sample(0))
    with pytest.raises(ValidationError):
        replace(value.statistics, confidence=float("nan"))


def test_subprecision_delta_does_not_emit_unchanged_proposal():
    assert warm(learner(parameter_delta_per_inv_m=5e-324)) == ()


def test_unrepresentable_innovation_clears_evidence():
    value = learner(
        alpha=1,
        minimum_samples=2,
        maximum_absolute_residual_inv_m=1e308,
        parameter_delta_per_inv_m=1e-308,
        mean_deadband_inv_m=0,
    )
    value.observe(sample(0, residual=1e308))
    assert value.observe(sample(1, residual=-1e308)) == ()
    assert value.statistics is None


def test_uninitialized_snapshot_clears_evidence_with_typed_error():
    from cyberpilot_autotune.contracts import ObservationSnapshot

    value = learner()
    warm(value)
    with pytest.raises(ValidationError):
        value.observe(object.__new__(ObservationSnapshot))
    assert value.statistics is None
