"""Known truths are generated from the controller equation, never a fitted line."""

from dataclasses import replace
from math import isclose, sin, sqrt

import pytest


def scenario(**changes):
    from cyberpilot_autotune.research.torque_identification.synthetic import SyntheticScenario

    commands = changes.get("commands", tuple(v for _ in range(20) for v in (-0.4, -0.2, 0.2, 0.4)))
    return replace(
        SyntheticScenario(
            name="oracle",
            factor=2.0,
            controller_friction=0.0,
            offset=0.0,
            commands=commands,
            errors=tuple(0.0 for _ in commands),
            deadzone=0.0,
            friction_threshold=0.3,
            x_noise_std=0.0,
            y_noise_std=0.0,
            lag_steps=0,
            alignment_steps=0,
            roll_bias_rad=tuple(0.0 for _ in commands),
            nonlinear_gain=0.0,
            sample_group_size=20,
            seed=17,
        ),
        **changes,
    )


def measured(case):
    from cyberpilot_autotune.research.torque_identification.estimator import fit_raw
    from cyberpilot_autotune.research.torque_identification.synthetic import generate

    return fit_raw(generate(case).points)


@pytest.mark.parametrize("factor", [0.5, 1.0, 2.0, 4.0])
@pytest.mark.parametrize("offset", [-0.125, 0.0, 0.125])
def test_noise_free_affine_factor_and_offset_are_recovered(factor, offset):
    fit = measured(scenario(factor=factor, offset=offset))
    assert fit.linear_mode_tls_lat_accel_slope == pytest.approx(factor, abs=2e-12)
    assert fit.lat_accel_offset_mps2 == pytest.approx(offset, abs=2e-12)
    assert fit.native_residual_spread_coefficient < 2e-12


@pytest.mark.parametrize(
    "error,expected",
    [
        (-0.5, -1.0),
        (-0.3, -1.0),
        (-0.1, -1 / 3),
        (-0.099, 0.0),
        (0.0, 0.0),
        (0.099, 0.0),
        (0.1, 1 / 3),
        (0.3, 1.0),
        (0.5, 1.0),
    ],
)
def test_actual_center_deadzone_does_not_subtract_its_width(error, expected):
    from cyberpilot_autotune.research.torque_identification.analytic import friction_shape

    assert friction_shape(error, 0.1, 0.3) == pytest.approx(expected)


def test_inverse_generator_uses_minus_factor_times_controller_friction():
    from cyberpilot_autotune.research.torque_identification.synthetic import generate

    case = scenario(controller_friction=0.1, errors=(0.3,) * 80, offset=0.125)
    points = generate(case).points
    assert points[0].lateral_accel_mps2 == pytest.approx(-0.875)
    fit = measured(case)
    assert fit.linear_mode_tls_lat_accel_slope == pytest.approx(2.0)
    assert fit.lat_accel_offset_mps2 == pytest.approx(-0.075)
    assert fit.native_residual_spread_coefficient < 2e-12


@pytest.mark.parametrize("friction", [0.01, 0.05, 0.1])
def test_symmetric_friction_cloud_matches_uncentered_native_svd_prediction(friction):
    from cyberpilot_autotune.research.torque_identification.analytic import symmetric_tls_prediction

    commands = tuple(v for _ in range(40) for v in (-0.4, -0.4, 0.4, 0.4))
    errors = (-0.3, 0.3, -0.3, 0.3) * 40
    fit = measured(scenario(commands=commands, errors=errors, controller_friction=friction))
    slope, coefficient = symmetric_tls_prediction(2.0, friction, 0.16, 1.0)
    assert fit.linear_mode_tls_lat_accel_slope == pytest.approx(slope, abs=2e-12)
    assert fit.native_residual_spread_coefficient == pytest.approx(coefficient, abs=2e-12)
    assert slope > 2.0  # even independent friction-state spread biases raw TLS
    assert not isclose(coefficient, friction, rel_tol=1e-3)


def test_true_projection_spread_is_not_a_controller_friction_identity():
    from cyberpilot_autotune.research.torque_identification.analytic import projected_coefficient

    assert projected_coefficient(2.0, 0.1, 1.0, 0.0) == pytest.approx(0.3 / sqrt(5.0))
    assert projected_coefficient(2.0, 0.1, 0.0, 0.0) == 0.0
    assert projected_coefficient(2.0, 0.0, 1.0, 0.04) == pytest.approx(0.3 / sqrt(5.0))


@pytest.mark.parametrize("axis", ["x", "y", "both"])
def test_no_friction_truth_with_measurement_noise_has_positive_native_spread(axis):
    fit = measured(
        scenario(x_noise_std=0.02 if axis != "y" else 0.0, y_noise_std=0.02 if axis != "x" else 0.0)
    )
    assert fit.native_residual_spread_coefficient > 0.001


def test_unbalanced_excitation_is_not_silently_rebalanced():
    from cyberpilot_autotune.research.torque_identification.synthetic import generate

    case = scenario(commands=(-0.4,) * 10 + (0.2,) * 70)
    data = generate(case)
    assert sum(p.normalized_command < 0 for p in data.points) == 10
    assert measured(case).linear_mode_tls_lat_accel_slope == pytest.approx(2.0)


@pytest.mark.parametrize("alignment", [1, 3])
def test_positive_and_negative_delay_mismatch_are_diagnostic_not_reapplied(alignment):
    case = scenario(
        commands=tuple(0.4 * sin(i * 0.4) for i in range(240)), lag_steps=2, alignment_steps=2
    )
    assert measured(case).linear_mode_tls_lat_accel_slope == pytest.approx(2.0)
    wrong = measured(replace(case, alignment_steps=alignment))
    assert wrong.residual_rmse_mps2 > 0.1


def test_constant_roll_bias_maps_to_observation_offset_not_friction():
    fit = measured(scenario(roll_bias_rad=(0.01,) * 80))
    assert fit.lat_accel_offset_mps2 == pytest.approx(-9.81 * sin(0.01))
    assert fit.linear_mode_tls_lat_accel_slope == pytest.approx(2.0)
    assert fit.native_residual_spread_coefficient < 2e-12


def test_varying_roll_bias_contaminates_spread_without_any_friction():
    fit = measured(scenario(roll_bias_rad=(0.01, 0.01, -0.01, 0.01) * 20))
    assert fit.native_residual_spread_coefficient > 0.001


def test_deadzone_and_threshold_change_friction_occupancy_not_its_truth():
    case = scenario(controller_friction=0.1, errors=(-0.05, 0.05, -0.05, 0.05) * 20)
    inside = measured(replace(case, deadzone=0.1))
    outside = measured(case)
    saturated = measured(replace(case, friction_threshold=0.01))
    assert inside.native_residual_spread_coefficient < 2e-12
    assert outside.native_residual_spread_coefficient > 0.0
    assert saturated.native_residual_spread_coefficient > outside.native_residual_spread_coefficient


def test_degenerate_and_low_excitation_are_distinct():
    from cyberpilot_autotune.research.torque_identification.estimator import fit_raw
    from cyberpilot_autotune.research.torque_identification.synthetic import generate

    with pytest.raises(ValueError, match="DEGENERATE_TLS"):
        fit_raw(generate(scenario(commands=(0.2,) * 80)).points)
    fit = measured(scenario(commands=(-1e-4, 1e-4) * 40))
    assert fit.linear_mode_tls_lat_accel_slope == pytest.approx(2.0)


def test_nonlinear_distortion_is_visible_even_when_affine_fit_is_stable():
    fit = measured(scenario(nonlinear_gain=0.2))
    assert fit.residual_rmse_mps2 > 0.0
    assert not isclose(fit.linear_mode_tls_lat_accel_slope, 2.0, abs_tol=1e-6)


def test_generator_and_estimator_are_deterministic_with_explicit_groups_and_seed():
    from cyberpilot_autotune.research.torque_identification.synthetic import generate

    case = scenario(x_noise_std=0.02, y_noise_std=0.02)
    assert generate(case) == generate(case)
    assert len(set(generate(case).groups)) == 4
    assert measured(case) == measured(case)
