"""Synthetic steering contracts only; no numbers here are vehicle policies."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError, replace

import pytest

from cyberpilot_autotune.contracts import ParameterSpec, ValidationError


def api():
    assert importlib.util.find_spec("cyberpilot_autotune.application") is not None, (
        "separate steering application contracts are not implemented"
    )
    return importlib.import_module("cyberpilot_autotune.application.contracts")


def policy(**changes):
    a = api()
    values = dict(
        scope=a.ApplicationScope.SYNTHETIC_TEST_ONLY,
        owner_id="synthetic-owner",
        source_revision="a" * 40,
        context_digest="b" * 64,
        observation_context="synthetic-steering-only",
        baseline_epoch=0,
        session_token="c" * 32,
        parameters=(
            ParameterSpec(
                "lat_accel_factor",
                "synthetic.units.not_for_vehicle",
                0.0,
                20.0,
                2.0,
                1.0,
                "test-only",
                False,
            ),
        ),
        minimum_samples=2,
        minimum_confidence=0.5,
        minimum_speed_mps=0.0,
        maximum_source_age_s=1.0,
        maximum_target_age_s=1.0,
        maximum_evidence_age_s=5.0,
        maximum_authorization_age_s=1.0,
        maximum_transaction_s=0.25,
        maximum_rollback_s=0.25,
        maximum_hold_s=2.0,
        maximum_consumed_proposals=2,
    )
    values.update(changes)
    return a.SteeringPolicy(**values)


def test_policy_is_immutable_and_digest_is_deterministic():
    p = policy()
    assert p.digest == replace(p).digest and len(p.digest) == 64
    with pytest.raises(FrozenInstanceError):
        p.owner_id = "other"
    assert replace(p, baseline_epoch=1).digest != p.digest


@pytest.mark.parametrize(
    "field,value",
    [
        ("scope", "OWNER_REVIEWED_STEERING"),
        ("minimum_samples", True),
        ("minimum_samples", 0),
        ("minimum_confidence", 1.1),
        ("minimum_speed_mps", -1),
        ("maximum_source_age_s", float("nan")),
        ("maximum_target_age_s", -1),
        ("maximum_evidence_age_s", float("inf")),
        ("maximum_authorization_age_s", 0),
        ("maximum_transaction_s", 0),
        ("maximum_hold_s", 0),
        ("maximum_consumed_proposals", 0),
        ("source_revision", "main"),
        ("context_digest", "bad"),
        ("session_token", "VIN"),
        ("baseline_epoch", -1),
    ],
)
def test_incomplete_or_invalid_policy_is_rejected(field, value):
    with pytest.raises(ValidationError):
        policy(**{field: value})


@pytest.mark.parametrize(
    "identifier,persistence",
    [
        ("safety.accel_max", False),
        ("steer_max", False),
        ("lat_accel_offset", False),
        ("friction", True),
    ],
)
def test_longitudinal_safety_offset_and_persistence_are_not_tunable(identifier, persistence):
    spec = ParameterSpec(identifier, "synthetic", 0, 10, 1, 1, "test-only", persistence)
    with pytest.raises(ValidationError):
        policy(parameters=(spec,))


def test_empty_or_duplicate_registry_is_rejected():
    p = policy()
    for specs in ((), (p.parameters[0],) * 2):
        with pytest.raises(ValidationError):
            replace(p, parameters=specs)


def test_target_snapshot_defensive_copy_and_no_longitudinal_state():
    a = api()
    values = {"lat_accel_factor": 10.0, "lat_accel_offset": 0.0}
    state = a.TargetSnapshot(
        0, 0.0, "synthetic-owner", "b" * 64, 0, a.ApplicationScope.SYNTHETIC_TEST_ONLY, values
    )
    values["lat_accel_factor"] = 999
    assert state.values["lat_accel_factor"] == 10.0
    with pytest.raises(TypeError):
        state.values["lat_accel_factor"] = 11
    with pytest.raises(ValidationError):
        replace(state, values={"longitudinal_gain": 1})
    with pytest.raises(ValidationError):
        replace(state, values={"lat_accel_factor": float("nan")})


def test_grants_require_complete_bindings_and_ordered_finite_times():
    a = api()
    grant = a.AuthorizationGrant("d" * 32, "a" * 64, "b" * 64, "c" * 64, 1.0, 2.0)
    assert replace(grant) == grant
    for changes in (
        {"expires_at_s": 1.0},
        {"issued_at_s": float("nan")},
        {"request_sha256": "bad"},
        {"authorization_id": ""},
    ):
        with pytest.raises(ValidationError):
            replace(grant, **changes)


def test_typed_nested_boundaries_reject_shape_coercion():
    a = api()
    from tests.fixtures.steering_application import baseline, request

    p = policy()
    item = request(p)
    for name in ("proposal", "observation", "evidence"):
        with pytest.raises(ValidationError):
            replace(item, **{name: None})
    with pytest.raises(ValidationError):
        replace(p, parameters=(object(),))
    with pytest.raises(ValidationError):
        replace(p, maximum_rollback_s=0)
    with pytest.raises(ValidationError):
        replace(baseline(p), scope="SYNTHETIC_TEST_ONLY")
    with pytest.raises(ValidationError):
        replace(item.evidence, quality="INDEPENDENTLY_QUALIFIED")
    receipt = a.ApplicationReceipt(
        a.ApplicationReason.DISARMED,
        a.ApplicationState.DISARMED,
        None,
        baseline(p).values,
        None,
        None,
        None,
    )
    with pytest.raises(ValidationError):
        replace(receipt, reason="VERIFIED")
    with pytest.raises(ValidationError):
        replace(receipt, recovery_reason="ROLLBACK_FAILED")
