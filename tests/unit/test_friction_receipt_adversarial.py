"""Adversarial primitive, stage, precision and causal-context contract cases."""

from dataclasses import asdict, replace

import pytest

from cyberpilot_autotune.observability import context as x
from cyberpilot_autotune.observability import contracts as c
from cyberpilot_autotune.observability import validation as v
from cyberpilot_autotune.observability.types import (
    RUNTIME,
    AlignmentMethod,
    ClockDomain,
    GeometryOrigin,
    ScalarOrigin,
    SourceOrigin,
    Stage,
    canonical,
)
from tests.fixtures.friction_receipt import complete
from tests.unit.test_friction_receipt import reasons


@pytest.mark.parametrize(
    "changes",
    [
        {"source_time_ns": None},
        {"sequence": None, "source_identity": None},
        {"origin": SourceOrigin.UNKNOWN},
        {"consumed": None},
        {"valid": None},
        {"alive": False},
    ],
)
def test_consumed_source_metadata_is_not_satisfied_by_latest_topic_presence(changes):
    receipt = complete()
    source = replace(receipt.sources[0], **changes)
    decision = v.evaluate(
        replace(receipt, sources=(source, *receipt.sources[1:])), v.ObservationPolicy()
    )
    assert decision.status.value == "REJECTED"


def test_missing_source_roles_or_unproven_complete_dependency_manifest_reject():
    receipt = complete()
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(replace(receipt, sources=receipt.sources[:1]))
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(
        replace(receipt, consumption_manifest_complete=None)
    )


@pytest.mark.parametrize("field", ["installed", "gains", "geometry", "delay"])
def test_missing_context_blocks_and_keeps_unknowns_in_content_digest(field):
    receipt = complete()
    missing = replace(receipt, context=replace(receipt.context, **{field: None}))
    assert missing.digest != receipt.digest
    assert v.evaluate(missing, v.ObservationPolicy()).status.value == "REJECTED"


def test_bad_applied_geometry_is_not_a_safe_range_policy():
    receipt = complete()
    for changes in (
        {"center_to_front_ratio": 0.0},
        {"wheelbase": 0.0},
        {"stiffness_factor": 0.0},
        {"effective_steer_ratio": 0.0},
        {"center_to_front": 1.2},
    ):
        geom = replace(receipt.context.geometry, **changes)
        assert "GEOMETRY_CONTEXT_INCONSISTENT" in reasons(
            replace(receipt, context=replace(receipt.context, geometry=geom))
        )


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"effective_delay_s": None}, "DELAY_CONTEXT_INCOMPLETE"),
        ({"effective_delay_s": -0.1}, "DELAY_CONTEXT_INCOMPLETE"),
        ({"correction_count": 2}, "DOUBLE_ALIGNMENT"),
        ({"sample_pair_id": "a" * 64}, "ALIGNMENT_METADATA_INCONSISTENT"),
        (
            {"alignment_method": AlignmentMethod.SINGLE_DOWNSTREAM_PAIR},
            "ALIGNMENT_METADATA_INCONSISTENT",
        ),
        (
            {
                "alignment_method": AlignmentMethod.CORE_VALUES_SHIFTED,
                "values_already_aligned": True,
            },
            "ALIGNMENT_NOT_RAW_CALLBACK",
        ),
    ],
)
def test_alignment_never_double_corrects_or_shifts_core_callback_values(changes, reason):
    receipt = complete()
    delay = replace(receipt.context.delay, **changes)
    assert reason in reasons(replace(receipt, context=replace(receipt.context, delay=delay)))


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"source_healthy": None}, "MISSING_LIMIT_STATE"),
        ({"source_healthy": False}, "SOURCE_UNHEALTHY"),
        ({"controller_active": False}, "CONTROLLER_INACTIVE"),
    ],
)
def test_unknown_false_health_and_false_activity_are_distinct(changes, reason):
    receipt = complete()
    assert reason in reasons(replace(receipt, limits=replace(receipt.limits, **changes)))


@pytest.mark.parametrize(
    ("field", "changes", "want"),
    [
        ("friction_threshold", {"value": 0.0}, "FRICTION_INPUT_DOMAIN_INVALID"),
        ("friction_deadzone", {"value": -0.1}, "FRICTION_INPUT_DOMAIN_INVALID"),
        ("actual_lateral_accel", {"value": None}, "MISSING_REQUIRED_SIGNAL"),
        ("desired_lateral_accel", {"cycle_digest": None}, "SOURCE_COHORT_INCOMPLETE"),
        ("desired_lateral_accel", {"captured_mono_time_ns": None}, "SOURCE_COHORT_INCOMPLETE"),
        ("desired_lateral_accel", {"captured_mono_time_ns": 0}, "TIME_ORDER_INVALID"),
        ("desired_lateral_accel", {"stage": Stage.APPLIED_TORQUE}, "WRONG_SIGNAL_STAGE"),
        ("desired_lateral_accel", {"origin": ScalarOrigin.RECONSTRUCTED}, "NONLOCAL_SIGNAL_ORIGIN"),
    ],
)
def test_each_core_value_requires_its_own_exact_stage_and_capture_binding(field, changes, want):
    receipt = complete()
    signal = replace(getattr(receipt.signals, field), **changes)
    assert want in reasons(replace(receipt, signals=replace(receipt.signals, **{field: signal})))


def test_zero_installed_factor_is_undefined_source_math_not_an_invented_F_range():
    receipt = complete()
    installed = replace(receipt.context.installed, factor_installed=0.0)
    assert "FRICTION_INPUT_DOMAIN_INVALID" in reasons(
        replace(receipt, context=replace(receipt.context, installed=installed))
    )


def test_missing_pid_components_wrong_sum_and_unlinked_downstream_reject():
    receipt = complete()
    assert "MISSING_PID_DECOMPOSITION" in reasons(
        replace(receipt, stages=replace(receipt.stages, pid_i=None))
    )
    wrong = replace(receipt.stages.pid_sum, value=0.9)
    assert "PID_STAGE_INCONSISTENT" in reasons(
        replace(receipt, stages=replace(receipt.stages, pid_sum=wrong))
    )
    assert "DOWNSTREAM_COHORT_INCOMPLETE" in reasons(
        replace(receipt, stages=replace(receipt.stages, downstream_cycle_id=None))
    )


def test_previous_ineligible_cycle_and_epoch_source_changes_do_not_create_history_state():
    previous = complete(10)
    current = complete(11)
    bad = replace(previous, signals=replace(previous.signals, q_observed=None))
    assert "PREVIOUS_RECEIPT_NOT_ELIGIBLE" in reasons(current, bad)
    assert "TIME_ORDER_INVALID" in reasons(previous, current)
    changed = replace(current, controller_mode=c.ControllerMode.CUSTOM)
    assert "MODE_CHANGED" in reasons(changed, previous)
    delay = replace(current.context.delay, effective_delay_s=0.3)
    assert "DELAY_CONTEXT_CHANGED" in reasons(
        replace(current, context=replace(current.context, delay=delay)), previous
    )
    source = replace(current.sources[0], source_identity=previous.sources[0].source_identity)
    assert "SOURCE_TIMESTAMP_MISMATCH" in reasons(
        replace(current, sources=(source, *current.sources[1:])), previous
    )


def test_unknown_schema_revision_clock_or_causal_event_order_rejects():
    receipt = complete()
    assert "UNSUPPORTED_RECEIPT_VERSION" in reasons(
        replace(receipt, receipt_schema_version="friction-observation-v2")
    )
    for changes, want in (
        ({"source_revision": "a" * 40}, "UNSUPPORTED_SOURCE_REVISION"),
        ({"source_schema_digest": "a" * 64}, "SOURCE_SCHEMA_MISMATCH"),
        ({"clock_domain": ClockDomain.SENSOR}, "WRONG_CLOCK_DOMAIN"),
        ({"receipt_complete_mono_time_ns": 0}, "TIME_ORDER_INVALID"),
    ):
        assert want in reasons(replace(receipt, cycle=replace(receipt.cycle, **changes)))


@pytest.mark.parametrize("value", [-1, 2**64, True, 1.5, None])
def test_uint64_identity_is_never_signed_float_bool_or_unknown(value):
    with pytest.raises(ValueError, match="UINT64"):
        replace(complete().cycle, controller_cycle_id=value)


def test_strict_enums_fields_and_nested_types_fail_before_content_hashing():
    receipt = complete()
    for build in (
        lambda: replace(receipt, controller_mode="STANDARD"),
        lambda: replace(receipt, cycle=None),
        lambda: replace(receipt, sources=("carState",)),
        lambda: replace(receipt, signals=replace(receipt.signals, roll=0.0)),
        lambda: replace(receipt, stages=replace(receipt.stages, pid_i=0.0)),
        lambda: replace(receipt, context=replace(receipt.context, gains={})),
        lambda: replace(receipt.context.installed, source_field="VIN"),
        lambda: replace(receipt.limits, driver_override=0),
        lambda: replace(receipt.cycle, session_id="wall-clock"),
        lambda: replace(receipt.context.delay, alignment_version="untrusted space"),
        lambda: v.ObservationPolicy(receipt_versions=("other",)),
        lambda: v.ObservationPolicy(source_revisions=("main",)),
        lambda: v.evaluate(None, v.ObservationPolicy()),
    ):
        with pytest.raises(ValueError):
            build()
    with pytest.raises(ValueError):
        canonical({"not_finite": float("nan")})
    with pytest.raises(ValueError):
        v.reconstruct_q_diagnostic(0.0, 0.0, 0.0, True)


def test_r_profile_requires_static_geometry_and_no_dynamic_field_inference():
    receipt = complete()
    cycle = replace(
        receipt.cycle, source_revision=RUNTIME, source_schema_digest=c.SOURCE_SCHEMA_DIGESTS[0][1]
    )

    def bound(value):
        return (
            replace(value, cycle_digest=cycle.digest)
            if type(value) is c.ScalarObservation
            else value
        )

    signals = c.ControllerCallbackSignals(
        **{name: bound(getattr(receipt.signals, name)) for name in asdict(receipt.signals)}
    )
    stages = c.ControllerStageDecomposition(
        **{
            name: bound(getattr(receipt.stages, name))
            for name in asdict(receipt.stages)
            if name != "downstream_cycle_id"
        },
        downstream_cycle_id=cycle.digest,
    )
    geom = replace(
        receipt.context.geometry,
        source_revision=RUNTIME,
        origin=GeometryOrigin.STATIC_CP,
        requested_center_to_front_percent=None,
        live_parameters_ratio=None,
    )
    context = replace(
        receipt.context,
        cycle_digest=cycle.digest,
        geometry=geom,
        gains=replace(receipt.context.gains, cycle_digest=cycle.digest),
    )
    stages = replace(
        stages,
        downstream_identities=tuple(
            replace(i, controller_cycle_digest=cycle.digest) for i in stages.downstream_identities
        ),
    )
    static = replace(receipt, cycle=cycle, signals=signals, stages=stages, context=context)
    assert v.evaluate(static, v.ObservationPolicy()).status.value == "ELIGIBLE"
    assert static.context.geometry.live_parameters_ratio is None


def test_partial_records_are_immutable_diagnostics_not_default_valued_measurements():
    receipt = complete()
    ctx = x.FrictionObservationContext()
    partial = replace(
        receipt,
        context=ctx,
        signals=c.ControllerCallbackSignals(),
        stages=c.ControllerStageDecomposition(),
        limits=c.LimitState(),
    )
    assert v.evaluate(partial, v.ObservationPolicy()).status.value == "REJECTED"
    assert ctx.installed is None and ctx.geometry is None


def test_speed_effective_gain_snapshot_is_captured_after_pid_speed_latch_not_before_callback():
    receipt = complete()
    gains = replace(
        receipt.context.gains,
        cycle_digest=receipt.cycle.digest,
        captured_mono_time_ns=receipt.cycle.callback_enter_mono_time_ns,
    )
    invalid = replace(receipt, context=replace(receipt.context, gains=gains))
    assert "MISSING_GAIN_COHORT" in reasons(invalid)
    gains = replace(gains, captured_mono_time_ns=receipt.cycle.control_event_mono_time_ns)
    valid = replace(receipt, context=replace(receipt.context, gains=gains))
    assert v.evaluate(valid, v.ObservationPolicy()).status.value == "ELIGIBLE"


def test_downstream_values_need_exact_command_event_lineage_not_just_a_cycle_label():
    receipt = complete()
    bad = replace(receipt, stages=replace(receipt.stages, downstream_identities=()))
    assert "DOWNSTREAM_COHORT_INCOMPLETE" in reasons(bad)
    identity = receipt.stages.downstream_identities[0]
    wrong = replace(identity, clock_domain=ClockDomain.SENSOR)
    assert "WRONG_CLOCK_DOMAIN" in reasons(
        replace(receipt, stages=replace(receipt.stages, downstream_identities=(wrong,)))
    )
    wrong = replace(identity, source_command_event_id="f" * 64)
    bad = replace(receipt, stages=replace(receipt.stages, downstream_identities=(wrong,)))
    assert "DOWNSTREAM_COHORT_INCOMPLETE" in reasons(bad)


def test_neutral_geometry_h6_projection_keeps_required_semantics_without_a_runtime_bridge():
    from cyberpilot_autotune.research.friction_model.contracts import SteeringGeometryContext

    receipt = complete()
    geo, installed, delay = (
        receipt.context.geometry,
        receipt.context.installed,
        receipt.context.delay,
    )
    h6 = SteeringGeometryContext(
        source_revision=geo.source_revision,
        vehicle_context_digest=geo.vehicle_context_digest,
        wheelbase=geo.wheelbase,
        center_to_front=geo.center_to_front,
        center_to_front_ratio=geo.center_to_front_ratio,
        steer_ratio_effective=geo.effective_steer_ratio,
        stiffness_factor=geo.stiffness_factor,
        controller_mode="LINEAR_TORQUE",
        geometry_generation=geo.generation,
        snapshot_time_ns=receipt.context.snapshot_time_ns,
        cohort=geo.applied_vm_context_id,
        geometry_source="APPLIED_VM",
        steer_ratio_rate=geo.steer_ratio_rate_raw,
        custom_sr=geo.custom_sr_raw,
        delay_source=delay.source.value,
        effective_delay_s=delay.effective_delay_s,
        custom_torque_mode=installed.custom_selector,
        factor_installed=installed.factor_installed,
        friction_installed=installed.friction_installed,
    )
    assert h6.complete and h6.center_to_front_ratio == 0.43
    assert h6.factor_installed == 2.0 and h6.friction_installed == 0.125
    assert replace(h6, center_to_front_ratio=None).complete is False


def test_one_ulp_error_change_across_deadzone_is_not_hidden_by_math_roundoff_allowance():
    import math

    receipt = complete(error=0.06, q=0.2)
    error = receipt.signals.friction_input.value
    changed = replace(receipt.signals.friction_input, value=math.nextafter(error, math.inf))
    bad = replace(receipt, signals=replace(receipt.signals, friction_input=changed))
    assert "LINEAR_INPUT_INCONSISTENT" in reasons(bad)


def test_reused_downstream_event_identity_with_changed_time_cannot_name_a_new_cycle():
    previous, current = complete(10), complete(11)
    old = previous.stages.downstream_identities[0]
    event = replace(
        current.stages.downstream_identities[0],
        source_event_id=old.source_event_id,
        source_command_event_id=old.source_event_id,
    )
    changed = replace(current, stages=replace(current.stages, downstream_identities=(event,)))
    assert "SOURCE_TIMESTAMP_MISMATCH" in reasons(changed, previous)
