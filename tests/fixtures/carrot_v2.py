"""Synthetic software evidence only; unrelated to vehicle tuning values."""

from dataclasses import replace

from cyberpilot_autotune.adapters.carrot_receipt_contract import (
    CarrotSnapshotPolicy,
    MappingAttempt,
    MeasurementEvidence,
    ReceiptEvidence,
    SourceCarStateEvidence,
    SourceCommandEvidence,
    StaticVehicleContext,
    TimestampEvidence,
)

BASELINE = {"synthetic.test_only": 10.0}


def stamp(value, domain="monotonic"):
    return TimestampEvidence(value, domain)


def context(kind="torque"):
    return StaticVehicleContext(
        mass=1000.0,
        rotational_inertia=1000.0,
        wheelbase=2.0,
        center_to_front=1.0,
        steer_ratio_rear=0.0,
        tire_stiffness_front=1000.0,
        tire_stiffness_rear=1000.0,
        initial_steer_ratio=10.0,
        brand="volkswagen" if kind == "mebCurvature" else "mock",
        flags=16 if kind == "mebCurvature" else 0,
        steer_control_type="angle" if kind in {"angle", "mebCurvature"} else "torque",
        lateral_tuning_kind=kind if kind in {"pid", "torque"} else "pid",
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        observation_schema_revision="observation-v2-measurement-v1",
    )


def actuators(**changes):
    values = dict.fromkeys(
        (
            "gas",
            "brake",
            "torque",
            "steeringAngleDeg",
            "accel",
            "speed",
            "curvature",
            "torqueOutputCan",
            "jerk",
            "aTarget",
        ),
        0.0,
    )
    values.update(changes)
    return values


def complete(kind="torque"):
    ctx = context(kind)
    measurement = MeasurementEvidence(
        version=1,
        mode="vehicleModelLive",
        validity="valid",
        car_state_health="valid",
        live_parameters_health="valid",
        car_state_time=stamp(9_940_000_000),
        live_parameters_time=stamp(9_900_000_000),
        calculation_time=stamp(9_960_000_000),
        measured_curvature_inv_m=0.0,
        input_speed_mps=2.0,
        input_steering_angle_deg=0.0,
        effective_stiffness_factor=1.0,
        effective_steer_ratio=10.0,
        effective_angle_offset_deg=0.0,
        effective_roll_rad=0.0,
    )
    command = SourceCommandEvidence(
        event_time=stamp(9_980_000_000),
        event_valid=True,
        observation_version=2,
        controller_kind=kind,
        instantaneous_limit="notLimited",
        lat_active=True,
        measurement=measurement,
        desired_target_state="available",
        desired_target_curvature_inv_m=0.0,
        requested_actuators=actuators(),
        static_context_digest=ctx.digest,
    )
    receipt = ReceiptEvidence(
        version=1,
        source_command_time=command.event_time,
        host_apply_time=stamp(10_000_000_000),
        host_activity="active",
        safety_permission="allowed",
        safety_state_time=stamp(19_970_000_000, "bootTime"),
        safety_observation_time=stamp(20_000_000_000, "bootTime"),
        controller_kind=kind,
        instantaneous_limit="notLimited",
        output_limit="notLimited",
        controller_output_returned=True,
        final_requested_actuators=actuators(),
        controller_output_actuators=actuators(),
    )
    source_cs = SourceCarStateEvidence(
        event_time=measurement.car_state_time,
        event_valid=True,
        can_valid=True,
        steering_pressed=False,
        steering_pressed_supported=True,
        speed_mps=2.0,
        steering_angle_deg=0.0,
    )
    attempt = MappingAttempt(
        receipt=receipt,
        source_command=command,
        source_car_state=source_cs,
        static_context=ctx,
        baseline_parameters=BASELINE,
        baseline_epoch=1,
        evaluation_time=stamp(10_010_000_000),
        sequence=0,
        previous_sequence=None,
        previous_host_apply_ns=None,
        consumed_cohorts=(),
        exact_lookup_unambiguous=True,
        car_output_transport_healthy=True,
        outer_car_output_valid=True,
    )
    policy = CarrotSnapshotPolicy(
        maximum_receipt_age_s=0.2,
        maximum_command_to_apply_delay_s=0.2,
        maximum_car_state_age_s=0.2,
        maximum_live_parameters_age_s=0.2,
        maximum_calculation_age_s=0.2,
        maximum_safety_state_age_s=0.2,
        maximum_source_skew_s=0.2,
        supported_receipt_versions=(1,),
        supported_observation_versions=(2,),
        supported_measurement_versions=(1,),
        allowed_controller_kinds=(kind,),
        static_context_digest=ctx.digest,
        baseline_epoch=1,
    )
    return attempt, policy


def measurement_change(attempt, **changes):
    return replace(
        attempt,
        source_command=replace(
            attempt.source_command,
            measurement=replace(attempt.source_command.measurement, **changes),
        ),
    )
