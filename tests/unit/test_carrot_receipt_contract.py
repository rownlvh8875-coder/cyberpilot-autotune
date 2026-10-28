"""Literal contract outcomes, not an openpilot adapter test."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cyberpilot_autotune.adapters.carrot_receipt_contract import evaluate
from cyberpilot_autotune.contracts.validation import ValidationError
from tests.fixtures.carrot_v2 import (
    BASELINE,
    actuators,
    complete,
    context,
    measurement_change,
    stamp,
)


def test_complete_join_and_age_at_apply_excludes_evaluation_delay():
    attempt, policy = complete()
    decision = evaluate(attempt, policy, BASELINE)
    assert decision.reason.value == "ACCEPTED"
    snapshot = decision.snapshot
    assert snapshot.source_valid is True
    assert snapshot.timestamp_s == 10.0 and snapshot.source_age_s == 0.1
    assert snapshot.control_active is True and snapshot.controller_saturated is False
    assert snapshot.driver_override is False and snapshot.lateral_acceleration_mps2 is None
    assert snapshot.speed_mps == 2.0
    assert snapshot.desired_curvature_inv_m == snapshot.measured_curvature_inv_m == 0.0
    assert snapshot.baseline_parameters == BASELINE
    assert decision.cohort_key == (9_980_000_000, 10_000_000_000)
    assert evaluate(attempt, policy, BASELINE) == decision


@pytest.mark.parametrize(
    "field,reason",
    [
        ("source_command", "MISSING_SOURCE_COMMAND"),
        ("source_car_state", "MISSING_SOURCE_CAR_STATE"),
    ],
)
def test_missing_exact_sources_never_use_latest(field, reason):
    attempt, policy = complete()
    result = evaluate(replace(attempt, **{field: None}), policy, BASELINE)
    assert result.snapshot is None and result.reason.value == reason


def test_latest_command_substitution_rejects():
    attempt, policy = complete()
    latest = replace(attempt.source_command, event_time=stamp(9_990_000_000))
    assert evaluate(replace(attempt, source_command=latest), policy, BASELINE).reason.value == (
        "MISSING_SOURCE_COMMAND"
    )


@pytest.mark.parametrize(
    "instant,output,expected",
    [
        ("limited", "notLimited", True),
        ("notLimited", "limited", True),
        ("limited", "limited", True),
        ("notLimited", "notLimited", False),
    ],
)
def test_independent_limits(instant, output, expected):
    attempt, policy = complete()
    command = replace(attempt.source_command, instantaneous_limit=instant)
    receipt = replace(attempt.receipt, instantaneous_limit=instant, output_limit=output)
    result = evaluate(replace(attempt, receipt=receipt, source_command=command), policy, BASELINE)
    assert result.snapshot.controller_saturated is expected


@pytest.mark.parametrize(
    "host,safety,expected",
    [
        ("active", "allowed", True),
        ("inactive", "allowed", False),
        ("active", "disallowed", False),
        ("active", "unavailable", None),
    ],
)
def test_activity_is_host_admission_and_observed_permission(host, safety, expected):
    attempt, policy = complete()
    receipt = replace(attempt.receipt, host_activity=host, safety_permission=safety)
    result = evaluate(replace(attempt, receipt=receipt), policy, BASELINE)
    assert result.control_active is expected
    if host == "inactive" or safety == "unavailable":
        assert result.snapshot is None
    elif safety == "disallowed":
        assert result.snapshot.source_valid and result.snapshot.control_active is False


def test_optional_numeric_is_not_inferred_zero():
    attempt, policy = complete()
    result = evaluate(measurement_change(attempt, measured_curvature_inv_m=None), policy, BASELINE)
    assert result.snapshot is None and result.reason.value == "INVALID_MEASUREMENT"


def test_baseline_is_defensively_copied_and_immutable():
    attempt, policy = complete()
    supplied = dict(BASELINE)
    attempt = replace(attempt, baseline_parameters=supplied)
    decision = evaluate(attempt, policy, supplied)
    supplied["synthetic.test_only"] = 99
    assert decision.snapshot.baseline_parameters == BASELINE
    with pytest.raises(TypeError):
        decision.snapshot.baseline_parameters["synthetic.test_only"] = 88
    with pytest.raises(FrozenInstanceError):
        attempt.sequence = 4


def test_actual_inactive_v2_has_no_nested_measurement_but_proves_inactivity():
    attempt, policy = complete()
    command = replace(
        attempt.source_command,
        lat_active=False,
        instantaneous_limit="unavailable",
        measurement=replace(attempt.source_command.measurement, version=0),
    )
    receipt = replace(attempt.receipt, host_activity="inactive", instantaneous_limit="unavailable")
    decision = evaluate(replace(attempt, receipt=receipt, source_command=command), policy, BASELINE)
    assert decision.control_active is False
    assert decision.controller_saturated is None and decision.snapshot is None


def test_inactive_receipt_retains_false_without_inventing_a_source_car_state():
    attempt, policy = complete()
    command = replace(attempt.source_command, lat_active=False, instantaneous_limit="unavailable")
    receipt = replace(attempt.receipt, host_activity="inactive", instantaneous_limit="unavailable")
    result = evaluate(
        replace(attempt, receipt=receipt, source_command=command, source_car_state=None),
        policy,
        BASELINE,
    )
    assert result.control_active is False
    assert result.snapshot is None and result.reason.value == "UNAVAILABLE_LIMIT"


@pytest.mark.parametrize(
    "name,value",
    [
        ("maximum_receipt_age_s", -1),
        ("maximum_source_skew_s", float("nan")),
        ("maximum_safety_state_age_s", True),
        ("supported_receipt_versions", (True,)),
        ("supported_observation_versions", (1, 2)),
        ("supported_measurement_versions", (0,)),
        ("allowed_controller_kinds", ()),
        ("allowed_controller_kinds", ("unknown",)),
        ("allowed_controller_kinds", ("pid", "pid")),
        ("static_context_digest", "x" * 64),
        ("static_context_digest", "0"),
        ("baseline_epoch", True),
    ],
)
def test_caller_policy_is_complete_known_finite_and_has_no_vehicle_defaults(name, value):
    _, policy = complete()
    with pytest.raises(ValidationError):
        replace(policy, **{name: value})


@pytest.mark.parametrize(
    "name,value",
    [
        ("mass", 0),
        ("rotational_inertia", float("inf")),
        ("center_to_front", 3),
        ("source_revision", "uninspected"),
        ("observation_schema_revision", "v3"),
        ("steer_control_type", "unknown"),
        ("brand", "device-serial"),
        ("flags", -1),
    ],
)
def test_static_context_rejects_invalid_or_unpinned_geometry(name, value):
    with pytest.raises(ValidationError):
        replace(context(), **{name: value})


def test_static_context_digest_is_canonical_and_includes_branching_and_geometry():
    original = context()
    assert original.digest == "9cfeba0c38bb2151c49c157760d2774e7734fdcc977c183f81fded65b4d2df2a"
    assert replace(original, mass=1000).digest == original.digest
    assert replace(original, mass=1001).digest != original.digest
    assert context("angle").controller_kind == "angle"
    assert context("pid").controller_kind == "pid"
    assert context("mebCurvature").controller_kind == "mebCurvature"
    assert context("mebCurvature").digest != original.digest


@pytest.mark.parametrize("kind", ["pid", "angle", "mebCurvature"])
def test_each_supported_controller_uses_the_same_contract(kind):
    attempt, policy = complete(kind)
    result = evaluate(attempt, policy, BASELINE)
    assert result.snapshot.source_valid and result.snapshot.controller_saturated is False
    assert f"/o2/{kind}/" in result.snapshot.context_key


def test_no_retained_input_is_mutated_and_no_limits_recomputed_using_measurement_speed():
    attempt, policy = complete("mebCurvature")
    requested = actuators(curvature=0.25)
    command = replace(attempt.source_command, requested_actuators=requested)
    receipt = replace(
        attempt.receipt,
        final_requested_actuators=requested,
        controller_output_actuators=actuators(curvature=0),
        output_limit="notLimited",
    )
    result = evaluate(replace(attempt, receipt=receipt, source_command=command), policy, BASELINE)
    # Producer used card's apply-boundary speed, not the measurement's inputSpeedMps.
    assert result.snapshot.controller_saturated is False
    requested["curvature"] = 99
    assert (
        command.requested_actuators["curvature"]
        == receipt.final_requested_actuators["curvature"]
        == 0.25
    )


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda a: replace(a, sequence=True), "INVALID_INPUT"),
        (lambda a: replace(a, receipt=replace(a.receipt, version=True)), "UNSUPPORTED_VERSION"),
        (
            lambda a: replace(a, receipt=replace(a.receipt, host_apply_time=stamp(0))),
            "MISSING_TIMESTAMP",
        ),
        (
            lambda a: replace(a, receipt=replace(a.receipt, host_apply_time=stamp(2**64))),
            "MISSING_TIMESTAMP",
        ),
        (
            lambda a: replace(
                a, source_command=replace(a.source_command, requested_actuators=None)
            ),
            "INVALID_ACTUATORS",
        ),
        (
            lambda a: replace(
                a, receipt=replace(a.receipt, controller_output_actuators=actuators(extra=0))
            ),
            "INVALID_ACTUATORS",
        ),
        (
            lambda a: replace(a, source_car_state=replace(a.source_car_state, can_valid=False)),
            "INVALID_SOURCE_CAR_STATE",
        ),
    ],
)
def test_malformed_evidence_fails_closed(mutator, reason):
    attempt, policy = complete()
    result = evaluate(mutator(attempt), policy, BASELINE)
    assert result.reason.value == reason and result.snapshot is None


def test_missing_policy_and_corrupted_configuration_fail_closed():
    attempt, policy = complete()
    assert evaluate(attempt, None, BASELINE).snapshot is None
    object.__setattr__(policy, "maximum_receipt_age_s", float("inf"))
    assert evaluate(attempt, policy, BASELINE).reason.value == "INVALID_INPUT"


def test_policy_and_consumed_identifiers_defensively_copy_lists():
    attempt, policy = complete()
    versions, kinds, keys = [1], ["torque"], [[9_980_000_000, 10_000_000_000]]
    copied = replace(policy, supported_receipt_versions=versions, allowed_controller_kinds=kinds)
    attempt = replace(attempt, consumed_cohorts=keys)
    versions.clear()
    kinds.clear()
    keys[0].clear()
    assert copied.supported_receipt_versions == (1,) and copied.allowed_controller_kinds == (
        "torque",
    )
    assert evaluate(attempt, copied, BASELINE).reason.value == "DUPLICATE_COHORT"
