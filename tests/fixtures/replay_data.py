"""Synthetic JSON contracts, not vehicle observations or tuning values."""


def replay_event(index=0, residual=0.25, **changes):
    observation = dict(
        timestamp_s=10.0 + index,
        sequence=index,
        source_age_s=0.0,
        context_key="synthetic/a",
        source_valid=True,
        control_active=True,
        speed_mps=2.0,
        desired_curvature_inv_m=residual,
        measured_curvature_inv_m=0.0,
        lateral_acceleration_mps2=None,
        controller_saturated=False,
        driver_override=False,
        baseline_parameters={"synthetic.test_only": 10.0},
    )
    observation.update(changes)
    return {
        "clock_before_s": 10.0 + index,
        "clock_after_s": 10.0 + index,
        "observation": observation,
    }


def replay_document():
    return {
        "schema_version": 1,
        "scope": "SYNTHETIC_TEST_ONLY",
        "learner_version": "residual-ewma-v1",
        "time_domain": "synthetic.monotonic.v1",
        "monotonic_origin_s": 0.0,
        "units": {
            "timestamp_s": "s",
            "source_age_s": "s",
            "speed_mps": "m/s",
            "desired_curvature_inv_m": "1/m",
            "measured_curvature_inv_m": "1/m",
            "lateral_acceleration_mps2": "m/s^2",
        },
        "baseline_parameters": {"synthetic.test_only": 10.0},
        "parameter_spec": {
            "parameter_id": "synthetic.test_only",
            "units": "synthetic_unit",
            "lower_bound": 0.0,
            "upper_bound": 20.0,
            "maximum_step": 2.0,
            "maximum_rate_per_second": 1.0,
            "description": "Test only; not for vehicle use",
            "persistence_eligible": False,
            "out_of_range_policy": "REJECT",
        },
        "gate_config": {
            "maximum_observation_age_s": 1.0,
            "minimum_samples": 3,
            "minimum_confidence": 0.8,
            "minimum_speed_mps": 1.0,
        },
        "learner_config": {
            "alpha": 0.5,
            "minimum_samples": 3,
            "maximum_samples": 8,
            "maximum_source_age_s": 1.0,
            "maximum_sample_gap_s": 2.0,
            "maximum_state_age_s": 10.0,
            "maximum_absolute_residual_inv_m": 1.0,
            "consistency_scale_inv_m": 0.5,
            "mean_deadband_inv_m": 0.01,
            "parameter_delta_per_inv_m": 2.0,
            "minimum_speed_mps": 1.0,
        },
        "events": [replay_event(index) for index in range(3)],
    }
