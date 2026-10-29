"""Wrong stages, unknowns and causal provenance never become empirical permission."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cyberpilot_autotune.observability import validation as v
from cyberpilot_autotune.observability.types import (
    CallbackFamily,
    CallbackFunction,
    CallbackSite,
    CallbackStage,
    ClockDomain,
    ControllerMode,
    GeometryOrigin,
    Precision,
    ScalarOrigin,
    Signal,
    Stage,
)
from tests.fixtures.friction_receipt import complete, scalar


def reasons(receipt, previous=None):
    return {r.value for r in v.evaluate(receipt, v.ObservationPolicy(), previous=previous).reasons}


def test_full_linear_receipt_is_only_structurally_eligible_and_immutable():
    receipt = complete()
    decision = v.evaluate(receipt, v.ObservationPolicy())
    assert decision.status.value == "ELIGIBLE"
    assert decision.reasons == ()
    assert not any(
        getattr(decision, field)
        for field in (
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "owner_proposal_allowed",
        )
    )
    assert not hasattr(receipt, "friction_identifiable")
    assert not hasattr(receipt, "approved_target")
    assert decision.receipt_digest == receipt.digest
    for field in (
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        with pytest.raises(ValueError):
            replace(decision, **{field: True})
    with pytest.raises(FrozenInstanceError):
        receipt.receipt_schema_version = "other"


def test_missing_q_is_not_reconstructed_or_derived_from_installed_C():
    receipt = complete()
    missing = replace(receipt, signals=replace(receipt.signals, q_observed=None))
    assert "MISSING_Q" in reasons(missing)
    assert v.evaluate(missing, v.ObservationPolicy()).status.value == "REJECTED"
    for origin in (ScalarOrigin.RECONSTRUCTED, ScalarOrigin.INSTALLED_C_DERIVED):
        bad_q = replace(receipt.signals.q_observed, origin=origin)
        assert "Q_NOT_INDEPENDENTLY_OBSERVED" in reasons(
            replace(receipt, signals=replace(receipt.signals, q_observed=bad_q))
        )


def test_raw_output_missing_or_applied_torque_substituted_even_when_numbers_equal():
    receipt = complete()
    assert "MISSING_RAW_CALLBACK_OUTPUT" in reasons(
        replace(receipt, stages=replace(receipt.stages, callback_output_raw=None))
    )
    applied = scalar(
        receipt.cycle, Signal.APPLIED_TORQUE, 0.625, Stage.APPLIED_TORQUE, ScalarOrigin.DOWNSTREAM
    )
    swapped = replace(receipt, stages=replace(receipt.stages, callback_output_raw=applied))
    assert "WRONG_CALLBACK_STAGE" in reasons(swapped)
    assert v.evaluate(swapped, v.ObservationPolicy()).status.value == "REJECTED"


@pytest.mark.parametrize(
    ("error", "q", "enabled"),
    [(0.01, 0.0, True), (0.06, 0.2, True), (-0.06, -0.2, True), (0.5, 0.0, False)],
)
def test_zero_q_deadzone_boundary_and_disabled_compensation_are_valid_observations(
    error, q, enabled
):
    receipt = complete(error=error, q=q, compensation=enabled)
    decision = v.evaluate(receipt, v.ObservationPolicy())
    assert decision.status.value == ("ELIGIBLE" if enabled else "REJECTED")
    assert "Q_SEMANTICS_INCONSISTENT" not in {r.value for r in decision.reasons}


@pytest.mark.parametrize(
    ("stage", "family", "function"),
    [
        (
            CallbackStage.NN_LITE_CALLBACK_PRE_PID,
            CallbackFamily.NN_LITE,
            CallbackFunction.BASE_LINEAR,
        ),
        (CallbackStage.NN_CALLBACK_PRE_PID, CallbackFamily.NN, CallbackFunction.NN_MODEL),
        (
            CallbackStage.GM_SIGLIN_CALLBACK_PRE_PID,
            CallbackFamily.GM_SIGLIN,
            CallbackFunction.GM_SIGLIN,
        ),
        (CallbackStage.OTHER_UNSUPPORTED, CallbackFamily.OTHER, CallbackFunction.OTHER),
    ],
)
def test_other_callback_families_are_diagnostic_only(stage, family, function):
    receipt = replace(
        complete(), callback_stage=stage, callback_family=family, callback_function=function
    )
    assert "IDENTIFICATION_MODEL_UNSUPPORTED" in reasons(receipt)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("steering_pressed", "DRIVER_OVERRIDE"),
        ("driver_override", "DRIVER_OVERRIDE"),
        ("timer_saturated", "SATURATED"),
        ("instantaneous_controller_limited", "CONTROLLER_LIMITED"),
        ("curvature_limited", "CONTROLLER_LIMITED"),
        ("steer_limited_by_controls", "CONTROLLER_LIMITED"),
        ("vehicle_actuator_limited", "VEHICLE_ACTUATOR_LIMITED"),
    ],
)
def test_limits_keep_instantaneous_and_timer_saturation_distinct(field, reason):
    receipt = complete()
    assert reason in reasons(replace(receipt, limits=replace(receipt.limits, **{field: True})))


def test_missing_gain_cohort_cannot_be_replaced_by_published_components():
    receipt = complete()
    assert "MISSING_GAIN_COHORT" in reasons(
        replace(receipt, context=replace(receipt.context, gains=None))
    )
    assert "MISSING_GAIN_COHORT" in reasons(
        replace(
            receipt,
            context=replace(receipt.context, gains=replace(receipt.context.gains, generation=999)),
        )
    )


def test_partial_geometry_and_requested_zero_do_not_invent_applied_context():
    receipt = complete()
    geom = replace(receipt.context.geometry, center_to_front_ratio=None)
    assert geom.center_to_front_ratio is None
    assert geom.requested_center_to_front_percent == 0
    assert "GEOMETRY_CONTEXT_INCOMPLETE" in reasons(
        replace(receipt, context=replace(receipt.context, geometry=geom))
    )
    requested = replace(receipt.context.geometry, origin=GeometryOrigin.REQUESTED)
    assert "GEOMETRY_NOT_ACTUALLY_APPLIED" in reasons(
        replace(receipt, context=replace(receipt.context, geometry=requested))
    )


def test_float32_only_existing_mapping_is_not_exact_raw_local_evidence():
    receipt = complete()
    raw = replace(
        receipt.stages.callback_output_raw,
        precision=Precision.FLOAT32,
        origin=ScalarOrigin.LEGACY_PUBLISHED,
    )
    assert "RAW_PRECISION_UNAVAILABLE" in reasons(
        replace(receipt, stages=replace(receipt.stages, callback_output_raw=raw))
    )


def test_exact_source_times_and_domains_reject_future_wrong_clock_and_latest_seen():
    receipt = complete()
    for changes, want in (
        ({"source_time_ns": receipt.cycle.callback_exit_mono_time_ns + 1}, "TIME_ORDER_INVALID"),
        ({"clock_domain": ClockDomain.UNKNOWN}, "WRONG_CLOCK_DOMAIN"),
        ({"consumed": False}, "SOURCE_COHORT_INCOMPLETE"),
    ):
        source = replace(receipt.sources[0], **changes)
        assert want in reasons(replace(receipt, sources=(source, *receipt.sources[1:])))


def test_duplicate_cycles_and_context_drift_cannot_pool():
    previous = complete(10)
    assert "DUPLICATE_CONTROLLER_CYCLE" in reasons(previous, previous)
    current = complete(11)
    assert reasons(current, previous) == set()
    for field, value in (("factor_installed", 2.1), ("friction_installed", 0.15)):
        installed = replace(current.context.installed, **{field: value})
        changed = replace(current, context=replace(current.context, installed=installed))
        assert "INSTALLED_PARAMETER_CONTEXT_CHANGED" in reasons(changed, previous)
    geometry = replace(current.context.geometry, generation=4)
    changed = replace(current, context=replace(current.context, geometry=geometry))
    assert "GEOMETRY_CONTEXT_CHANGED" in reasons(changed, previous)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), True, 10**1000])
def test_nonfinite_or_non_numeric_raw_values_are_rejected_structurally(value):
    with pytest.raises(ValueError, match="NONFINITE_INPUT"):
        scalar(complete().cycle, Signal.CALLBACK_OUTPUT, value, Stage.RAW_CALLBACK)


def test_defensive_source_copy_and_duplicate_source_identity_rejection():
    receipt = complete()
    inputs = list(receipt.sources)
    copied = replace(receipt, sources=inputs)
    inputs.clear()
    assert len(copied.sources) == 5
    with pytest.raises(ValueError, match="DUPLICATE_CONSUMED_SOURCE"):
        replace(receipt, sources=receipt.sources + receipt.sources[:1])


def test_custom_selector_is_not_a_callback_family_and_other_call_sites_reject():
    receipt = complete()
    custom = replace(
        receipt,
        controller_mode=ControllerMode.CUSTOM,
        context=replace(
            receipt.context, installed=replace(receipt.context.installed, custom_selector=1)
        ),
    )
    assert v.evaluate(custom, v.ObservationPolicy()).status.value == "ELIGIBLE"
    assert "MODE_IDENTITY_INCOMPLETE" in reasons(
        replace(receipt, controller_mode=ControllerMode.CUSTOM)
    )
    assert "WRONG_CALLBACK_STAGE" in reasons(replace(receipt, callback_site=CallbackSite.SETPOINT))


def test_signal_equations_use_source_callback_inputs_not_achieved_accel():
    receipt = complete()
    wrong = replace(receipt.signals.callback_acceleration, value=0.5)
    assert "LINEAR_INPUT_INCONSISTENT" in reasons(
        replace(receipt, signals=replace(receipt.signals, callback_acceleration=wrong))
    )
    wrongq = replace(receipt.signals.q_observed, value=0.25)
    assert "Q_SEMANTICS_INCONSISTENT" in reasons(
        replace(receipt, signals=replace(receipt.signals, q_observed=wrongq))
    )
