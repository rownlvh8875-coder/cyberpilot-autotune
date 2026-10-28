"""Synthetic rejection/fault matrix; authority is never defaulted in production."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.application.contracts import (
    ApplicationReason as R,
)
from cyberpilot_autotune.application.contracts import (
    ApplicationScope,
    AuthorizationGrant,
)
from cyberpilot_autotune.application.contracts import (
    ApplicationState as S,
)
from cyberpilot_autotune.application.coordinator import BoundedSteeringApplicator
from cyberpilot_autotune.contracts import ValidationError
from tests.fixtures.steering_application import (
    Authority,
    Clock,
    MemoryTarget,
    baseline,
    policy,
    request,
)


def system():
    p, clock, authority = policy(), Clock(), Authority()
    target = MemoryTarget(clock, baseline(p))
    return (
        p,
        clock,
        target,
        authority,
        BoundedSteeringApplicator(p, baseline(p), target, authority, clock),
    )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("session_token", "0" * 32, R.SESSION_MISMATCH),
        ("policy_sha256", "0" * 64, R.POLICY_MISMATCH),
        ("expected_revision", 1, R.TARGET_CONFLICT),
    ],
)
def test_request_bindings_are_enforced_before_write(field, value, reason):
    p, _, target, _, app = system()
    result = app.process(replace(request(p), **{field: value}))
    assert result.reason is reason and not target.writes


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("source_revision", "0" * 40, R.POLICY_MISMATCH),
        ("context_digest", "0" * 64, R.POLICY_MISMATCH),
        ("generated_at_s", 2.0, R.UNQUALIFIED_EVIDENCE),
        ("target_revision", 1, R.TARGET_CONFLICT),
    ],
)
def test_evidence_context_and_causality_are_enforced(field, value, reason):
    p, _, target, authority, app = system()
    item = request(p)
    result = app.process(replace(item, evidence=replace(item.evidence, **{field: value})))
    assert result.reason is reason and not target.writes and authority.calls == 0


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("confidence", 0.1, R.CONFIDENCE),
        ("sample_count", 1, R.SAMPLES),
        ("baseline_value", 9.0, R.BASELINE_MISMATCH),
        ("context_key", "other", R.POLICY_MISMATCH),
        ("timestamp_s", 0.9, R.POLICY_MISMATCH),
        ("parameter_id", "friction", R.BASELINE_MISMATCH),
    ],
)
def test_proposal_contract_is_independently_rechecked(field, value, reason):
    p, _, target, authority, app = system()
    item = request(p)
    result = app.process(replace(item, proposal=replace(item.proposal, **{field: value})))
    assert result.reason is reason and not target.writes and authority.calls == 0


@pytest.mark.parametrize(
    "change",
    [
        {"request_sha256": "0" * 64},
        {"policy_sha256": "0" * 64},
        {"evidence_sha256": "0" * 64},
        {"issued_at_s": 1.1},
        {"issued_at_s": 0.0, "expires_at_s": 0.5},
    ],
)
def test_grant_hash_or_time_mismatch_is_a_fault(change):
    p, _, target, authority, app = system()

    def grant(item, policy, now):
        original = AuthorizationGrant(
            "d" * 32, item.digest, policy.digest, item.evidence.digest, now, now + 0.5
        )
        return replace(original, **change)

    authority.callback = grant
    result = app.process(request(p))
    assert result.reason is R.AUTHORIZATION_INVALID and result.state is S.FAULTED
    assert not target.writes and result.effective_parameters is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("owner_id", "foreign"),
        ("context_digest", "0" * 64),
        ("baseline_epoch", 1),
        ("scope", ApplicationScope.OWNER_REVIEWED_STEERING),
        ("values", {"lat_accel_factor": 10}),
    ],
)
def test_foreign_target_is_not_modified(field, value):
    p, _, target, _, app = system()
    target.current = replace(target.current, **{field: value})
    result = app.process(request(p))
    assert result.state is S.FAULTED and result.effective_parameters is None
    assert not target.writes


@pytest.mark.parametrize("stamp", [0.0, 2.0])
def test_target_snapshot_is_current_and_in_same_clock_domain(stamp):
    p, clock, target, _, app = system()
    clock.time = 1.1
    target.snapshot = lambda: replace(target.current, timestamp_s=stamp)
    assert app.process(request(p, now=1.1)).reason is R.TARGET_CONFLICT
    assert not target.writes


@pytest.mark.parametrize("bad", [None, {}, [], "raw", 1, True, float("nan")])
def test_malformed_external_request_never_escapes_or_writes(bad):
    _, _, target, authority, app = system()
    assert app.process(bad).reason is R.INVALID_INPUT
    assert not target.writes and authority.calls == 0


def test_unknown_registry_parameter_cannot_become_a_writer():
    p, _, target, _, app = system()
    item = request(p)
    candidate = replace(
        item.proposal, parameter_id="friction", baseline_value=0.5, proposed_value=0.6
    )
    assert app.process(replace(item, proposal=candidate)).reason is R.POLICY_MISMATCH
    assert not target.writes


def test_evicted_proposal_id_cannot_be_reused_with_a_new_sequence():
    p, clock, target, _, app = system()
    for seq in range(3):
        clock.time = 1.0 + seq
        assert (
            app.process(request(p, sequence=seq, now=clock.time, value=10.0)).reason is R.UNCHANGED
        )
    clock.time = 4.0
    recycled = replace(request(p, sequence=3, now=4.0), proposal_id="0" * 32)
    assert app.process(recycled).reason is R.REPLAYED
    assert not target.writes


def test_disarm_without_owned_application_does_not_claim_baseline_readback():
    _, _, target, _, app = system()
    result = app.disarm()
    assert result.reason is R.DISARMED and result.state is S.DISARMED
    assert result.effective_parameters is None and target.reads == 0


def test_authorizer_exception_is_sanitized_and_identified():
    p, _, target, authority, app = system()

    def failed(*args):
        raise RuntimeError("SECRET_AUTHORITY")

    authority.callback = failed
    result = app.process(request(p))
    assert result.reason is R.AUTHORIZATION_INVALID and result.state is S.FAULTED
    assert not target.writes and "SECRET" not in repr(result)


def test_forged_nested_request_validation_is_an_input_rejection_and_consumed():
    p, _, target, _, app = system()
    item = request(p)
    object.__setattr__(item.proposal, "proposed_value", float("nan"))
    assert app.process(item).reason is R.INVALID_INPUT
    assert app.process(request(p)).reason is R.REPLAYED
    assert not target.writes


@pytest.mark.parametrize("phase", ["authority", "commit"])
def test_known_deadline_fault_is_not_masked_by_later_source_staleness(phase):
    p, clock, target, authority, app = system()
    if phase == "authority":

        def slow_authority(item, policy, now):
            clock.time += 2.0
            return AuthorizationGrant(
                "d" * 32, item.digest, policy.digest, item.evidence.digest, now, now + 10.0
            )

        authority.callback = slow_authority
    else:
        commit = target.commit

        def slow_commit(revision, values):
            result = commit(revision, values)
            clock.time += 2.0
            return result

        target.commit = slow_commit
    result = app.process(request(p))
    assert result.reason is R.TRANSACTION_TIMEOUT and result.state is S.FAULTED
    if phase == "commit":
        assert result.effective_parameters == baseline(p).values
    else:
        assert not target.writes


def test_existing_hold_expiring_during_authorization_requires_baseline_recovery():
    p, clock, target, authority, _ = system()
    p = replace(p, maximum_hold_s=0.05)
    app = BoundedSteeringApplicator(p, baseline(p), target, authority, clock)
    app.process(request(p))
    clock.time = 1.01

    def slow(item, policy, now):
        clock.time += 0.1
        return AuthorizationGrant(
            "d" * 32, item.digest, policy.digest, item.evidence.digest, now, now + 0.5
        )

    authority.callback = slow
    result = app.process(request(p, sequence=1, now=1.01, revision=1, value=11.0))
    assert result.reason is R.HOLD_EXPIRED and result.state is S.FAULTED
    assert result.effective_parameters == baseline(p).values


def test_invalid_structured_sequence_requires_a_new_owner_session():
    p, _, target, _, app = system()
    invalid = request(p)
    object.__setattr__(invalid, "sequence", True)
    result = app.process(invalid)
    assert result.reason is R.INVALID_INPUT and result.state is S.FAULTED
    assert app.process(request(p)).reason is R.FAULT_LATCHED
    assert not target.writes


@pytest.mark.parametrize("mode", ["wrong_type", "forged"])
def test_malformed_grant_is_an_authority_fault(mode):
    p, _, target, authority, app = system()

    def malformed(item, policy, now):
        if mode == "wrong_type":
            return True
        grant = AuthorizationGrant(
            "d" * 32, item.digest, policy.digest, item.evidence.digest, now, now + 0.5
        )
        object.__setattr__(grant, "issued_at_s", float("nan"))
        return grant

    authority.callback = malformed
    result = app.process(request(p))
    assert result.reason is R.AUTHORIZATION_INVALID and result.state is S.FAULTED
    assert not target.writes


@pytest.mark.parametrize("bad_policy,bad_baseline", [(None, None), ("policy", None)])
def test_constructor_rejects_untyped_configuration(bad_policy, bad_baseline):
    with pytest.raises(ValidationError):
        BoundedSteeringApplicator(bad_policy, bad_baseline, None, None, None)


@pytest.mark.parametrize("values", [{"friction": 0.5}, {"lat_accel_factor": 30.0}])
def test_baseline_must_have_registered_bounded_values(values):
    p, clock, target, authority, _ = system()
    with pytest.raises(ValidationError):
        BoundedSteeringApplicator(p, replace(baseline(p), values=values), target, authority, clock)
    assert target.reads == 0


@pytest.mark.parametrize("mode", ["healthy", "foreign", "broken", "unavailable"])
def test_watchdog_checks_coherent_owner_state_and_invalid_input(mode):
    p, _, target, _, app = system()
    if mode == "foreign":
        target.current = replace(target.current, revision=99)
    elif mode == "broken":
        target.snapshot = lambda: object()
    result = app.watchdog(None if mode == "unavailable" else request(p).observation)
    assert (
        result.reason
        is {
            "healthy": R.UNCHANGED,
            "foreign": R.TARGET_CONFLICT,
            "broken": R.TARGET_FAULT,
            "unavailable": R.INVALID_INPUT,
        }[mode]
    )
    assert not target.writes


def test_clock_failure_while_holding_a_value_restores_if_owner_readback_is_available():
    p, clock, target, _, app = system()
    app.process(request(p))

    def bad_clock():
        raise RuntimeError("SECRET_CLOCK")

    clock.now_s = bad_clock
    result = app.watchdog(request(p).observation)
    assert result.reason is R.CLOCK_FAULT and result.state is S.FAULTED
    assert result.effective_parameters == baseline(p).values
    assert result.recovery_reason is R.CLOCK_FAULT


@pytest.mark.parametrize(
    "mode,reason",
    [("baseline", R.BASELINE_MISMATCH), ("future", R.ORDERING), ("revision", R.TARGET_CONFLICT)],
)
def test_actual_baseline_source_time_and_target_revision_are_not_inferred(mode, reason):
    p, _, target, authority, app = system()
    item = request(p)
    if mode == "baseline":
        obs = replace(item.observation, baseline_parameters={"lat_accel_factor": 9.0})
        item = replace(item, observation=obs)
    elif mode == "future":
        item = replace(item, observation=replace(item.observation, timestamp_s=2.0))
    else:
        target.current = replace(target.current, revision=1)
    result = app.process(item)
    assert result.reason is reason and result.state is S.FAULTED
    assert authority.calls == 0 and not target.writes


@pytest.mark.parametrize("missing", ["target", "authority", "clock"])
def test_no_target_authority_or_clock_capability_is_defaulted(missing):
    p, clock, target, authority, _ = system()
    with pytest.raises(ValidationError):
        BoundedSteeringApplicator(
            p,
            baseline(p),
            None if missing == "target" else target,
            None if missing == "authority" else authority,
            None if missing == "clock" else clock,
        )
    assert target.reads == authority.calls == 0
