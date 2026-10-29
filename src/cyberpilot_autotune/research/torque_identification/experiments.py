"""Frozen mathematical sensitivity catalog; no observed development values."""

from dataclasses import dataclass, replace
from math import sin

from .cluster_stats import FitDiagnostic, diagnostic
from .synthetic import SyntheticScenario, generate
from .trajectories import FROZEN_SINE_COMMANDS


@dataclass(frozen=True, slots=True)
class SyntheticCaseResult:
    name: str
    scenario_digest: str
    true_factor: float
    true_controller_friction: float
    x_noise_std: float
    y_noise_std: float
    point_count: int
    numerical: FitDiagnostic
    factor_absolute_bias: float | None
    native_coefficient_absolute_bias: float | None
    native_coefficient_relative_bias: float | None
    verdict: str


def catalog() -> tuple[SyntheticScenario, ...]:
    commands = (-0.4, -0.4, -0.2, -0.2, 0.2, 0.2, 0.4, 0.4) * 10
    base = SyntheticScenario(
        "ideal_factor",
        2.0,
        0.0,
        0.0,
        commands,
        (0.0,) * 80,
        0.0,
        0.3,
        0.0,
        0.0,
        0,
        0,
        (0.0,) * 80,
        0.0,
        20,
        17,
    )
    balanced = replace(base, controller_friction=0.1, errors=(-0.3, 0.3) * 40)
    sine = FROZEN_SINE_COMMANDS
    lag = replace(
        base,
        commands=sine,
        errors=(0.0,) * 240,
        roll_bias_rad=(0.0,) * 240,
        lag_steps=2,
        alignment_steps=2,
    )
    primary = (
        base,
        replace(base, name="factor_offset", offset=0.125),
        replace(balanced, name="symmetric_friction"),
        replace(balanced, name="multiple_friction", controller_friction=0.05),
        replace(base, name="x_noise", x_noise_std=0.02),
        replace(base, name="y_noise", y_noise_std=0.02),
        replace(base, name="both_noise", x_noise_std=0.02, y_noise_std=0.02),
        replace(balanced, name="unbalanced_excitation", commands=(-0.4,) * 10 + (0.2,) * 70),
        replace(lag, name="lag_error", alignment_steps=1),
        replace(base, name="roll_bias", roll_bias_rad=(0.01,) * 80),
        replace(balanced, name="deadzone", errors=(-0.05, 0.05) * 40, deadzone=0.1),
        replace(balanced, name="threshold_transition", errors=(-0.05, 0.05) * 40),
        replace(base, name="low_excitation", commands=(-1e-4, 1e-4) * 40),
        replace(base, name="degenerate", commands=(0.2,) * 80),
        replace(base, name="mild_nonlinearity", nonlinear_gain=0.2),
    )
    extra = []
    for factor in (0.5, 1.0, 2.0, 4.0):
        extra.append(replace(base, name=f"factor_axis_{factor}", factor=factor))
        extra.append(replace(balanced, name=f"friction_factor_axis_{factor}", factor=factor))
    for friction in (0.0, 0.01, 0.05, 0.1):
        extra.append(
            replace(balanced, name=f"friction_axis_{friction}", controller_friction=friction)
        )
    for offset in (-0.125, 0.0, 0.125):
        extra.append(replace(base, name=f"offset_axis_{offset}", offset=offset))
    for size in (80, 160, 240):
        extra.append(
            replace(
                base,
                name=f"count_axis_{size}",
                commands=commands * (size // 80),
                errors=(0.0,) * size,
                roll_bias_rad=(0.0,) * size,
            )
        )
    extra.extend(
        (
            replace(balanced, name="occupancy_constant_positive", errors=(0.3,) * 80),
            replace(balanced, name="occupancy_zero", errors=(0.0,) * 80),
            replace(
                balanced, name="excitation_half_amplitude", commands=tuple(x / 2 for x in commands)
            ),
            replace(balanced, name="friction_and_x_noise", x_noise_std=0.02),
            replace(balanced, name="friction_and_y_noise", y_noise_std=0.02),
            replace(balanced, name="friction_and_both_noise", x_noise_std=0.02, y_noise_std=0.02),
            replace(
                balanced,
                name="threshold_saturated",
                errors=(-0.05, 0.05) * 40,
                friction_threshold=0.01,
            ),
            replace(lag, name="delay_correct"),
            replace(lag, name="delay_positive", alignment_steps=3),
            replace(base, name="roll_varying", roll_bias_rad=(0.01, 0.01, -0.01, 0.01) * 20),
        )
    )
    return primary + tuple(extra)


def run_synthetic_suite() -> tuple[SyntheticCaseResult, ...]:
    results = []
    for case in catalog():
        data = generate(case)
        observed = diagnostic(data.points)
        fit = observed.fit
        ideal = (
            case.controller_friction == 0.0
            and case.x_noise_std == 0.0
            and case.y_noise_std == 0.0
            and case.nonlinear_gain == 0.0
            and case.lag_steps == case.alignment_steps
            and len(set(case.roll_bias_rad)) == 1
        )
        verdict = "SENSITIVITY_DIAGNOSTIC"
        if case.name == "degenerate":
            verdict = "EXPECTED_DEGENERACY" if fit is None else "ANALYTIC_SYNTHETIC_MISMATCH"
        elif ideal:
            expected_offset = case.offset - 9.81 * sin(case.roll_bias_rad[0])
            matches = fit is not None and (
                abs(fit.linear_mode_tls_lat_accel_slope - case.factor) <= 2e-12
                and abs(fit.lat_accel_offset_mps2 - expected_offset) <= 2e-12
                and fit.native_residual_spread_coefficient <= 2e-12
            )
            verdict = "IDEAL_AFFINE_RECOVERY_PASS" if matches else "ANALYTIC_SYNTHETIC_MISMATCH"
        results.append(
            SyntheticCaseResult(
                case.name,
                data.scenario_digest,
                case.factor,
                case.controller_friction,
                case.x_noise_std,
                case.y_noise_std,
                len(data.points),
                observed,
                abs(fit.linear_mode_tls_lat_accel_slope - case.factor) if fit else None,
                abs(fit.native_residual_spread_coefficient - case.controller_friction)
                if fit
                else None,
                (fit.native_residual_spread_coefficient - case.controller_friction)
                / case.controller_friction
                if fit and case.controller_friction
                else None,
                verdict,
            )
        )
    return tuple(results)
