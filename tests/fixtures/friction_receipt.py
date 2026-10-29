"""Hand-checked mathematical receipts only: no vehicle or live producer data."""

from cyberpilot_autotune.observability import context as x
from cyberpilot_autotune.observability import contracts as c
from cyberpilot_autotune.observability.types import (
    CURRENT,
    AlignmentMethod,
    CallbackFamily,
    CallbackFunction,
    CallbackSite,
    CallbackStage,
    ClockDomain,
    ControllerMode,
    DelaySource,
    GeometryOrigin,
    OffsetSource,
    Precision,
    ScalarOrigin,
    Signal,
    SourceOrigin,
    SourceRole,
    Stage,
)


def cycle(number=10, **changes):
    fields = dict(
        session_id="1" * 64,
        controller_cycle_id=number,
        context_capture_mono_time_ns=10000 + number * 1000,
        callback_enter_mono_time_ns=10010 + number * 1000,
        callback_exit_mono_time_ns=10020 + number * 1000,
        control_event_mono_time_ns=10030 + number * 1000,
        receipt_complete_mono_time_ns=10040 + number * 1000,
        source_revision=CURRENT,
        source_schema_digest=c.SOURCE_SCHEMA_DIGESTS[1][1],
        vehicle_context_digest="2" * 64,
        controller_instance_generation=1,
        installed_parameter_generation=2,
        geometry_generation=3,
        callback_invocation_index=2,
        clock_domain=ClockDomain.MONOTONIC,
    )
    fields.update(changes)
    return c.CycleIdentity(**fields)


def scalar(
    identity, signal, value, stage=Stage.CALLBACK_INPUT, origin=ScalarOrigin.LOCAL_DIRECT, **changes
):
    fields = dict(
        signal=signal,
        value=value,
        stage=stage,
        origin=origin,
        precision=Precision.BINARY64,
        cycle_digest=identity.digest,
        captured_mono_time_ns=identity.callback_exit_mono_time_ns,
    )
    if stage not in (Stage.CALLBACK_INPUT, Stage.HELPER_Q, Stage.RAW_CALLBACK):
        fields["captured_mono_time_ns"] = identity.control_event_mono_time_ns
    fields.update(changes)
    return c.ScalarObservation(**fields)


def complete(number=10, *, error=0.5, q=1.0, compensation=True):
    identity = cycle(number)
    desired = 1.0 if error == 0.5 else 0.0
    actual = desired - error
    raw = desired / 2.0 + 0.125 * q
    f = raw * 0.5
    total = 0.02 + 0.01 + 0.0 + f
    sources = tuple(
        c.ConsumedSourceIdentity(
            role=role,
            source_time_ns=identity.context_capture_mono_time_ns - 10,
            clock_domain=ClockDomain.MONOTONIC,
            sequence=number,
            source_identity=f"{number * 100 + i:064x}",
            consumed=role is not SourceRole.LIVE_POSE,
            valid=True,
            alive=True,
            origin=SourceOrigin.LOCAL_CYCLE_OBJECT
            if role is SourceRole.CAR_CONTROL
            else SourceOrigin.WIRE_EVENT,
        )
        for i, role in enumerate(
            (
                SourceRole.CAR_STATE,
                SourceRole.LIVE_POSE,
                SourceRole.LIVE_PARAMETERS,
                SourceRole.CAR_CONTROL,
            ),
            start=10,
        )
    )
    signals = c.ControllerCallbackSignals(
        desired_lateral_accel=scalar(identity, Signal.DESIRED_ACCEL, desired),
        actual_lateral_accel=scalar(identity, Signal.ACTUAL_ACCEL, actual),
        roll=scalar(identity, Signal.ROLL, 0.0),
        roll_compensation=scalar(identity, Signal.ROLL_COMPENSATION, 0.0),
        callback_acceleration=scalar(identity, Signal.CALLBACK_ACCEL, desired),
        friction_input=scalar(identity, Signal.FRICTION_INPUT, error),
        friction_deadzone=scalar(identity, Signal.DEADZONE, 0.06),
        friction_threshold=scalar(identity, Signal.THRESHOLD, 0.3),
        q_observed=scalar(
            identity, Signal.Q_OBSERVED, q, Stage.HELPER_Q, ScalarOrigin.HELPER_OBSERVED
        ),
        friction_compensation_enabled=compensation,
        gravity_adjusted=True,
    )
    stages = c.ControllerStageDecomposition(
        downstream_cycle_id=identity.digest,
        downstream_identities=(
            c.DownstreamStageIdentity(
                stage=Stage.REQUESTED_TORQUE,
                source_event_id=f"{number * 100 + 99:064x}",
                source_command_event_id=f"{number * 100 + 99:064x}",
                source_time_ns=identity.control_event_mono_time_ns,
                clock_domain=ClockDomain.MONOTONIC,
                controller_cycle_digest=identity.digest,
                exact_source_command_reference=True,
                source_valid=True,
                source_transport_healthy=True,
            ),
        ),
        callback_output_raw=scalar(identity, Signal.CALLBACK_OUTPUT, raw, Stage.RAW_CALLBACK),
        pid_p=scalar(identity, Signal.PID_P, 0.02, Stage.PID_P),
        pid_i=scalar(identity, Signal.PID_I, 0.01, Stage.PID_I),
        pid_d=scalar(identity, Signal.PID_D, 0.0, Stage.PID_D),
        pid_f=scalar(identity, Signal.PID_F, f, Stage.PID_F),
        pid_sum=scalar(identity, Signal.PID_SUM, total, Stage.PID_SUM),
        post_pid_output=scalar(identity, Signal.PID_OUTPUT, total, Stage.PID_CLIPPED),
        requested_torque=scalar(
            identity,
            Signal.REQUESTED_TORQUE,
            -total,
            Stage.REQUESTED_TORQUE,
            ScalarOrigin.DOWNSTREAM,
        ),
    )
    installed = x.InstalledParameters(
        generation=2,
        factor_installed=2.0,
        friction_installed=0.125,
        offset_installed=0.0,
        offset_source=OffsetSource.INSTALLED_UNUSED_LINEAR,
        source_field="torque_params.latAccelOffset",
        precision=Precision.BINARY64,
        custom_selector=0,
    )
    gains = x.GainSnapshot(
        generation=2,
        k_p=0.2,
        k_i=0.05,
        k_d=0.0,
        k_f=0.5,
        precision=Precision.BINARY64,
        cycle_digest=identity.digest,
        captured_mono_time_ns=identity.control_event_mono_time_ns,
    )
    geom = x.AppliedGeometryContext(
        source_revision=CURRENT,
        vehicle_context_digest="2" * 64,
        generation=3,
        applied_vm_context_id="3" * 64,
        origin=GeometryOrigin.APPLIED_VM,
        wheelbase=2.73,
        center_to_front=1.1739,
        center_to_front_ratio=0.43,
        stiffness_factor=0.95,
        effective_steer_ratio=14.7,
        steer_ratio_rate_raw=100.0,
        steer_ratio_rate_effective=1.0,
        custom_sr_raw=0.0,
        custom_sr_effective=0.0,
        precision=Precision.BINARY64,
        requested_center_to_front_percent=0,
        live_parameters_ratio=0.43,
    )
    delay = x.DelayContext(
        effective_delay_s=0.2,
        source=DelaySource.LIVE_DELAY,
        alignment_method=AlignmentMethod.NONE,
        alignment_version="raw-callback-v1",
        correction_count=0,
        values_already_aligned=False,
    )
    context = x.FrictionObservationContext(
        cycle_digest=identity.digest,
        snapshot_time_ns=identity.context_capture_mono_time_ns,
        installed=installed,
        gains=gains,
        geometry=geom,
        delay=delay,
    )
    limits = c.LimitState(
        controller_active=True,
        source_healthy=True,
        steering_pressed=False,
        driver_override=False,
        timer_saturated=False,
        instantaneous_controller_limited=False,
        curvature_limited=False,
        steer_limited_by_controls=False,
        vehicle_actuator_limited=False,
    )
    return c.LateralTorqueIdentificationReceipt(
        consumption_manifest_complete=True,
        cycle=identity,
        callback_stage=CallbackStage.LINEAR_CALLBACK_PRE_PID,
        controller_mode=ControllerMode.STANDARD,
        callback_family=CallbackFamily.LINEAR,
        callback_function=CallbackFunction.BASE_LINEAR,
        callback_site=CallbackSite.FEEDFORWARD,
        sources=sources,
        signals=signals,
        stages=stages,
        context=context,
        limits=limits,
    )
