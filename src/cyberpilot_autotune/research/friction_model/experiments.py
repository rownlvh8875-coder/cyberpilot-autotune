"""Frozen H6 synthetic comparisons. Returns data only; no persistence or authority."""

import json
from dataclasses import asdict, replace

from .candidates import factor_sensitivity, fit, select_model
from .contracts import CURRENT, POLICY_SHA256, digest, require
from .contracts import SteeringGeometryContext as Context
from .geometry import vehicle_diagnostic
from .synthetic import Scenario, generate


def toy_context() -> Context:
    """Explicit preregistered mathematical fixture, not an inferred vehicle default."""
    return Context(
        source_revision=CURRENT,
        vehicle_context_digest=digest({"synthetic_fixture": "H6", "not_vehicle_data": True}),
        wheelbase=2.73,
        center_to_front=1.1739,
        center_to_front_ratio=0.43,
        steer_ratio_effective=14.7,
        stiffness_factor=0.95,
        controller_mode="LINEAR_TORQUE",
        geometry_generation=1,
        snapshot_time_ns=100,
        cohort="h6-synthetic-fixture-only",
        geometry_source="APPLIED_VM",
        steer_ratio_rate=100.0,
        custom_sr=0.0,
        delay_source="LIVE_DELAY",
        effective_delay_s=0.2,
        custom_torque_mode=0,
        factor_installed=2.4,
        friction_installed=0.17,
    )


def _geometry_comparison() -> dict[str, object]:
    baseline = vehicle_diagnostic(0.43)
    base_rows = generate(Scenario(count=200), toy_context(), baseline.acceleration_series)
    comparisons = []
    for ratio in (0.43, 0.44, 0.51):
        diagnostic = vehicle_diagnostic(ratio)
        # Deliberately unbound negative control, NOT admitted observations of changed geometry.
        wrong = tuple(
            replace(row, acceleration=a)
            for row, a in zip(base_rows, diagnostic.acceleration_series, strict=True)
        )
        naive = fit(wrong, "controller")
        comparisons.append(
            {
                "ratio": ratio,
                "center_to_front_m": diagnostic.center_to_front,
                "front_stiffness": diagnostic.front_stiffness,
                "rear_stiffness": diagnostic.rear_stiffness,
                "steady_curvature_inv_m": diagnostic.curvature,
                "steady_acceleration_mps2": diagnostic.curvature * 18.0**2,
                "roll_compensation_inv_m": diagnostic.roll_compensation,
                "transient_yaw_rate_rad_s": diagnostic.yaw_rate,
                "transient_lateral_velocity_mps": diagnostic.lateral_velocity,
                "max_transient_acceleration_delta_mps2": max(
                    abs(a - b)
                    for a, b in zip(
                        diagnostic.acceleration_series, baseline.acceleration_series, strict=True
                    )
                ),
                "naive_wrong_cohort_factor": naive.factor,
                "naive_wrong_cohort_friction": naive.estimate,
                "naive_fit_claim": "UNADMITTED_GEOMETRY_MISMATCH_NEGATIVE_CONTROL",
            }
        )
    invariant = all(
        abs(d["steady_curvature_inv_m"] - baseline.curvature) <= 1e-9  # type: ignore[operator]
        for d in comparisons
    )
    material = any(
        d["max_transient_acceleration_delta_mps2"] > 1e-9  # type: ignore[operator]
        for d in comparisons
    )
    return {
        "verdict": "GEOMETRY_CONTEXT_MATERIAL"
        if material
        else "GEOMETRY_CONTEXT_NEGLIGIBLE_UNDER_MODEL",
        "scope": "GENERIC_COHERENT_BICYCLE_TRANSIENT_NOT_VEHICLE_QUALIFICATION",
        "coherent_steady_invariant": invariant,
        "comparisons": comparisons,
        "mixed_epoch_status": fit(
            generate(Scenario(context_change="geometry"), toy_context()), "controller"
        ).status,
        "vehicle_safe_range_claim": False,
    }


def run_experiments(policy_json: str) -> dict[str, object]:
    policy = json.loads(policy_json)
    require(digest(policy) == POLICY_SHA256, "POLICY_MUTATION")
    overrides = {
        "zero_friction": Scenario(friction=0),
        "symmetric": Scenario(),
        "asymmetric_occupancy": Scenario(state="asymmetric"),
        "directional_asymmetry": Scenario(negative_friction=0.27),
        "deadzone_only": Scenario(state="deadzone"),
        "transition_only": Scenario(state="transition"),
        "single_sign": Scenario(state="positive"),
        "collinear_design": Scenario(state="collinear"),
        "compensation_disabled": Scenario(compensation=False),
        "known_factor": Scenario(state="correlated"),
        "wrong_factor": Scenario(state="correlated"),
        "joint_factor": Scenario(state="correlated"),
        "factor_interval": Scenario(state="correlated"),
        "pid_contamination": Scenario(pid_gain=1),
        "feedforward_only": Scenario(pid_gain=1),
        "pid_subtracted": Scenario(pid_gain=1),
        "x_noise": Scenario(u_noise=0.08),
        "a_noise": Scenario(a_noise=0.08),
        "q_noise": Scenario(q_noise=0.08),
        "total_noise": Scenario(u_noise=0.08, a_noise=0.08, q_noise=0.08),
        "delay_mismatch": Scenario(delay_samples=3),
        "roll_mismatch": Scenario(roll_mismatch=0.12),
        "geometry_change": Scenario(context_change="geometry"),
        "mode_change": Scenario(context_change="mode"),
        "saturation": Scenario(saturated=True),
        "driver_override": Scenario(override=True),
    }
    require(set(overrides) == set(policy["synthetic"]["scenarios"]), "SCENARIO_SET")
    scenarios = []
    import numpy as np

    for name in policy["synthetic"]["scenarios"]:
        scenario = overrides[name]
        rows = generate(scenario, toy_context())
        f = 2.4 if name == "known_factor" else (3.0 if name == "wrong_factor" else None)
        target = (
            "total"
            if name == "pid_contamination"
            else ("pid_subtracted" if name == "pid_subtracted" else "callback")
        )
        points = np.array([(r.total, r.acceleration) for r in rows])
        centered = points - points.mean(axis=0)
        _, _, vectors = np.linalg.svd(centered, full_matrices=False)
        k = float(1.5 * np.std(centered @ vectors[-1]))
        scenarios.append(
            {
                "scenario": name,
                "truth": asdict(scenario),
                "input_sha256": digest([asdict(r) for r in rows]),
                "sample_count": len(rows),
                "target": target,
                "supplied_factor_synthetic_only": f,
                "K_native_spread_diagnostic_not_C": k,
                "models": {
                    model: asdict(fit(rows, model, factor=f, target=target))
                    for model in ("controller", "inverse", "branch", "explicit")
                },
                "factor_sensitivity": asdict(factor_sensitivity(rows, (2.1, 2.7)))
                if name == "factor_interval"
                else None,
            }
        )
    return {
        "schema": "friction-model-synthetic-v1",
        "scope": "OFFLINE_SYNTHETIC_ONLY_NO_EMPIRICAL_QUALIFICATION",
        "policy_sha256": POLICY_SHA256,
        "selected_model": select_model(required_signals_complete=False, independent_response=False),
        "selection_reason": "CURRENT_CALLBACK_TARGET_Q_AND_APPLIED_CONTEXT_COHORT_NOT_PUBLISHED",
        "geometry": _geometry_comparison(),
        "scenarios": scenarios,
        "factor_qualification": (
            "FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE"
        ),
        "frozen_artifact": "FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE",
        "authority": {
            name: False
            for name in (
                "empirical_qualified",
                "candidate_generation_allowed",
                "bounds_qualified",
                "runtime_accepted",
                "encoding_qualified",
                "watchdog_qualified",
                "external_executor_qualified",
                "owner_proposal_allowed",
                "application_authorized",
            )
        },
    }
