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
    OffsetSource,
    ScalarOrigin,
    SourceOrigin,
    SourceRole,
    Stage,
    canonical,
)
from tests.fixtures.friction_receipt import complete
from tests.unit.test_friction_receipt import reasons


@pytest.mark.parametrize(
    ("role", "origin"),
    [
        (SourceRole.CAR_CONTROL, SourceOrigin.WIRE_EVENT),
        (SourceRole.CAR_STATE, SourceOrigin.LOCAL_CYCLE_OBJECT),
    ],
)
def test_pinned_consumed_source_role_cannot_be_relabelled_with_another_origin(role, origin):
    receipt = complete()
    changed = replace(
        receipt,
        sources=tuple(replace(s, origin=origin) if s.role == role else s for s in receipt.sources),
    )
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(changed)


@pytest.mark.parametrize("with_previous", [False, True])
def test_prior_cycle_local_builder_is_not_a_consumed_source_of_this_cycle(with_previous):
    previous, current = complete(10), complete(11)
    old = next(s for s in previous.sources if s.role == SourceRole.CAR_CONTROL)
    changed = replace(
        current,
        sources=tuple(old if s.role == SourceRole.CAR_CONTROL else s for s in current.sources),
    )
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(changed, previous if with_previous else None)


@pytest.mark.parametrize("binding", [None, "f" * 64])
def test_consumed_local_object_requires_explicit_current_cycle_binding(binding):
    receipt = complete()
    changed = replace(
        receipt,
        sources=tuple(
            replace(s, controller_cycle_digest=binding) if s.role == SourceRole.CAR_CONTROL else s
            for s in receipt.sources
        ),
    )
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(changed)


@pytest.mark.parametrize("reused", ["source_identity", "sequence"])
def test_local_object_identity_or_sequence_cannot_be_reused_even_after_cycle_rebinding(reused):
    previous, current = complete(10), complete(11)
    old = next(s for s in previous.sources if s.role == SourceRole.CAR_CONTROL)
    changed = replace(
        current,
        sources=tuple(
            replace(s, **{reused: getattr(old, reused)}) if s.role == SourceRole.CAR_CONTROL else s
            for s in current.sources
        ),
    )
    assert "SOURCE_TIMESTAMP_MISMATCH" in reasons(changed, previous)


def test_identical_local_object_metadata_cannot_be_reused_with_only_a_new_cycle_label():
    previous, current = complete(10), complete(11)
    old = next(s for s in previous.sources if s.role == SourceRole.CAR_CONTROL)
    rebound = replace(old, controller_cycle_digest=current.cycle.digest)
    changed = replace(
        current,
        sources=tuple(rebound if s.role == SourceRole.CAR_CONTROL else s for s in current.sources),
    )
    assert "SOURCE_TIMESTAMP_MISMATCH" in reasons(changed, previous)


@pytest.mark.parametrize(
    ("error", "q"),
    [(0.5, 1.0000000000000002), (-0.5, -1.0000000000000002), (0.01, 5e-324)],
)
def test_exact_helper_zero_and_clip_states_are_not_relaxed_by_algebraic_roundoff(error, q):
    receipt = complete(error=error, q=q)
    assert "Q_SEMANTICS_INCONSISTENT" in reasons(receipt)


def test_pinned_threshold_constant_is_exact_not_a_roundoff_derived_value():
    receipt = complete()
    threshold = replace(receipt.signals.friction_threshold, value=0.30000000000000004)
    changed = replace(receipt, signals=replace(receipt.signals, friction_threshold=threshold))
    assert "FRICTION_INPUT_DOMAIN_INVALID" in reasons(changed)


@pytest.mark.parametrize(
    ("origin", "field"),
    [
        (OffsetSource.UNAVAILABLE, None),
        (OffsetSource.FILTERED_LIVE, "liveTorqueParameters.latAccelOffsetRaw"),
        (OffsetSource.RAW_LIVE, "liveTorqueParameters.latAccelOffsetFiltered"),
        (OffsetSource.INSTALLED_UNUSED_LINEAR, None),
    ],
)
def test_available_offset_cannot_claim_unknown_or_contradictory_field_provenance(origin, field):
    receipt = complete()
    installed = replace(receipt.context.installed, offset_source=origin, source_field=field)
    changed = replace(receipt, context=replace(receipt.context, installed=installed))
    assert "INSTALLED_CONTEXT_INCOMPLETE" in reasons(changed)


@pytest.mark.parametrize(
    ("origin", "field", "value"),
    [
        (OffsetSource.FILTERED_LIVE, "liveTorqueParameters.latAccelOffsetFiltered", 0.0),
        (OffsetSource.RAW_LIVE, "liveTorqueParameters.latAccelOffsetRaw", 0.0),
        (OffsetSource.UNAVAILABLE, None, None),
    ],
)
def test_offset_field_provenance_can_be_preserved_without_adding_a_regressor(origin, field, value):
    receipt = complete()
    installed = replace(
        receipt.context.installed, offset_source=origin, source_field=field, offset_installed=value
    )
    assert reasons(replace(receipt, context=replace(receipt.context, installed=installed))) == set()


def test_unchanged_wire_sample_can_be_consumed_across_successive_cycles():
    previous, current = complete(10), complete(11)
    old = next(s for s in previous.sources if s.role == SourceRole.CAR_STATE)
    changed = replace(
        current,
        sources=tuple(old if s.role == SourceRole.CAR_STATE else s for s in current.sources),
    )
    assert reasons(changed, previous) == set()


def test_source_specific_local_live_parameters_fallback_requires_current_cycle_binding():
    receipt = complete()
    sources = tuple(
        replace(
            s, origin=SourceOrigin.LOCAL_CYCLE_OBJECT, controller_cycle_digest=receipt.cycle.digest
        )
        if s.role == SourceRole.LIVE_PARAMETERS
        else s
        for s in receipt.sources
    )
    assert reasons(replace(receipt, sources=sources)) == set()


@pytest.mark.parametrize("declare_unused", [False, True])
def test_model_input_read_even_on_linear_cannot_be_omitted_or_declared_unused(declare_unused):
    receipt = complete()
    other = tuple(s for s in receipt.sources if s.role != SourceRole.MODEL)
    unused = c.ConsumedSourceIdentity(role=SourceRole.MODEL, consumed=False)
    sources = (*other, unused) if declare_unused else other
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(replace(receipt, sources=sources))


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"valid": False}, "SOURCE_UNHEALTHY"),
        ({"alive": False}, "SOURCE_UNHEALTHY"),
        ({"clock_domain": ClockDomain.UNKNOWN}, "WRONG_CLOCK_DOMAIN"),
        ({"source_identity": None, "sequence": None}, "SOURCE_COHORT_INCOMPLETE"),
    ],
)
def test_required_model_identity_health_and_domain_checks_cannot_be_bypassed(changes, reason):
    receipt = complete()
    sources = tuple(
        replace(s, **changes) if s.role == SourceRole.MODEL else s for s in receipt.sources
    )
    assert reason in reasons(replace(receipt, sources=sources))


def test_pinned_model_argument_is_wire_origin_not_a_new_local_object():
    receipt = complete()
    other = tuple(s for s in receipt.sources if s.role != SourceRole.MODEL)
    local = c.ConsumedSourceIdentity(
        role=SourceRole.MODEL,
        consumed=True,
        source_time_ns=receipt.cycle.context_capture_mono_time_ns,
        clock_domain=ClockDomain.MONOTONIC,
        sequence=receipt.cycle.controller_cycle_id,
        source_identity="d" * 64,
        origin=SourceOrigin.LOCAL_CYCLE_OBJECT,
        controller_cycle_digest=receipt.cycle.digest,
        valid=True,
        alive=True,
    )
    assert "SOURCE_COHORT_INCOMPLETE" in reasons(replace(receipt, sources=(*other, local)))


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
    sources = tuple(
        replace(s, controller_cycle_digest=cycle.digest)
        if s.origin == SourceOrigin.LOCAL_CYCLE_OBJECT
        else s
        for s in receipt.sources
    )
    static = replace(
        receipt, cycle=cycle, signals=signals, stages=stages, context=context, sources=sources
    )
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


def test_requested_command_event_cannot_precede_actual_control_event_publication():
    receipt = complete()
    early = receipt.cycle.callback_exit_mono_time_ns
    stages = replace(
        receipt.stages,
        requested_torque=replace(receipt.stages.requested_torque, captured_mono_time_ns=early),
        downstream_identities=(
            replace(receipt.stages.downstream_identities[0], source_time_ns=early),
        ),
    )
    assert "DOWNSTREAM_COHORT_INCOMPLETE" in reasons(replace(receipt, stages=stages))


def test_control_and_command_events_remain_distinct_with_causally_ordered_timestamps():
    receipt = complete()
    later = receipt.cycle.control_event_mono_time_ns + 1
    stages = replace(
        receipt.stages,
        requested_torque=replace(receipt.stages.requested_torque, captured_mono_time_ns=later),
        downstream_identities=(
            replace(receipt.stages.downstream_identities[0], source_time_ns=later),
        ),
    )
    assert reasons(replace(receipt, stages=stages)) == set()


@pytest.mark.parametrize("name", ["pid_p", "pid_i", "pid_d", "pid_f", "pid_sum", "post_pid_output"])
def test_pid_decomposition_must_be_captured_before_control_event_publication(name):
    receipt = complete()
    changed = replace(
        getattr(receipt.stages, name),
        captured_mono_time_ns=receipt.cycle.control_event_mono_time_ns + 1,
    )
    assert "TIME_ORDER_INVALID" in reasons(
        replace(receipt, stages=replace(receipt.stages, **{name: changed}))
    )


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
