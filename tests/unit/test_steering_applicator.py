"""Synthetic, host-only transaction behavior; no controller or vehicle objects."""

import importlib
import importlib.util
from dataclasses import replace

import pytest

from cyberpilot_autotune.application.contracts import (
    ApplicationReason as R,
)
from cyberpilot_autotune.application.contracts import (
    ApplicationState as S,
)
from cyberpilot_autotune.application.contracts import (
    EvidenceQuality,
)
from tests.fixtures.steering_application import (
    Authority,
    Clock,
    MemoryTarget,
    baseline,
    policy,
    request,
)


def setup(**changes):
    assert importlib.util.find_spec("cyberpilot_autotune.application.coordinator") is not None, (
        "bounded steering transaction coordinator is not implemented"
    )
    module = importlib.import_module("cyberpilot_autotune.application.coordinator")
    p = policy(**changes)
    clock = Clock()
    target = MemoryTarget(clock, baseline(p))
    authority = Authority()
    app = module.BoundedSteeringApplicator(p, baseline(p), target, authority, clock)
    return p, clock, target, authority, app


def test_explicit_commit_and_readback_preserve_coupled_untuned_values():
    p, _, target, authority, app = setup()
    assert target.reads == len(target.writes) == authority.calls == 0
    result = app.process(request(p))
    assert result.reason is R.VERIFIED and result.state is S.ACTIVE
    assert result.effective_parameters == target.current.values
    assert result.effective_parameters["lat_accel_factor"] == 11.0
    assert result.effective_parameters["lat_accel_offset"] == 0.0
    assert result.effective_parameters["friction"] == 0.5
    assert result.baseline_parameters["lat_accel_factor"] == 10.0
    assert result.verified_revision == 1 and len(target.writes) == 1
    with pytest.raises(TypeError):
        result.effective_parameters["friction"] = 999


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("source_valid", False, R.SOURCE_INVALID),
        ("control_active", None, R.CONTROL_INACTIVE),
        ("control_active", False, R.CONTROL_INACTIVE),
        ("driver_override", True, R.OVERRIDE),
        ("driver_override", None, R.OVERRIDE),
        ("controller_saturated", True, R.SATURATED),
        ("controller_saturated", None, R.SATURATED),
        ("speed_mps", None, R.SOURCE_INVALID),
        ("source_age_s", 2.0, R.STALE_SOURCE),
        ("context_key", "other", R.POLICY_MISMATCH),
    ],
)
def test_rejected_source_never_reaches_authority_or_writer(field, value, reason):
    p, _, target, authority, app = setup()
    item = request(p)
    item = replace(item, observation=replace(item.observation, **{field: value}))
    result = app.process(item)
    assert result.reason is reason and result.effective_parameters is None
    assert not target.writes and authority.calls == 0


@pytest.mark.parametrize(
    "value,reason", [(21.0, R.OUT_OF_BOUNDS), (13.0, R.STEP_LIMIT), (11.5, R.RATE_LIMIT)]
)
def test_hard_step_and_actual_elapsed_rate_limits(value, reason):
    p, _, target, _, app = setup()
    assert app.process(request(p, value=value)).reason is reason
    assert not target.writes


def test_research_output_cannot_be_promoted_by_confidence_or_authority():
    p, _, target, authority, app = setup()
    result = app.process(request(p, quality=EvidenceQuality.RESEARCH_ONLY))
    assert result.reason is R.UNQUALIFIED_EVIDENCE
    assert authority.calls == 0 and not target.writes


def test_missing_owner_authorization_cannot_apply():
    p, _, target, authority, app = setup()
    authority.reject = True
    assert app.process(request(p)).reason is R.AUTHORIZATION_DENIED
    assert not target.writes


def test_rejected_attempt_cannot_be_repaired_even_after_id_eviction():
    p, clock, target, _, app = setup(maximum_consumed_proposals=1)
    rejected = request(p, quality=EvidenceQuality.RESEARCH_ONLY)
    assert app.process(rejected).reason is R.UNQUALIFIED_EVIDENCE
    clock.time = 2.0
    assert app.process(request(p, sequence=1, now=2.0, value=10.0)).reason is R.UNCHANGED
    assert app.process(request(p)).reason is R.REPLAYED
    assert not target.writes


def test_sequence_and_distinct_id_replay_both_fail_closed():
    p, clock, target, _, app = setup()
    first = request(p, value=10.0)
    assert app.process(first).reason is R.UNCHANGED
    clock.time = 2.0
    second = replace(request(p, sequence=1, now=2.0), proposal_id=first.proposal_id)
    assert app.process(second).reason is R.REPLAYED
    assert not target.writes


def test_successive_update_rate_is_relative_to_verified_current_value_and_commit_time():
    p, clock, target, _, app = setup()
    assert app.process(request(p)).reason is R.VERIFIED
    clock.time = 1.1
    result = app.process(request(p, sequence=1, now=1.1, revision=1, value=11.5))
    assert result.reason is R.RATE_LIMIT
    assert result.effective_parameters == baseline(p).values  # rejection restores baseline
    assert target.current.values == baseline(p).values


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("driver_override", True, R.OVERRIDE),
        ("controller_saturated", True, R.SATURATED),
        ("source_valid", False, R.SOURCE_INVALID),
    ],
)
def test_safety_veto_restores_baseline_in_same_call(field, value, reason):
    p, clock, target, _, app = setup()
    app.process(request(p))
    clock.time = 1.1
    obs = replace(request(p, sequence=1, now=1.1, revision=1).observation, **{field: value})
    result = app.watchdog(obs)
    assert result.reason is reason and result.state is S.READY
    assert result.effective_parameters == target.current.values == baseline(p).values
    assert len(target.writes) == 2


def test_expired_hold_restores_and_latches_then_never_rearms_itself():
    p, clock, target, authority, app = setup()
    app.process(request(p))
    clock.time = 2.0
    result = app.watchdog(request(p, sequence=1, now=2.0, revision=1).observation)
    assert result.reason is R.HOLD_EXPIRED and result.state is S.FAULTED
    assert result.effective_parameters == baseline(p).values
    reads, writes, calls = target.reads, len(target.writes), authority.calls
    assert app.process(request(p, sequence=2, now=2.0, revision=2)).reason is R.FAULT_LATCHED
    assert (target.reads, len(target.writes), authority.calls) == (reads, writes, calls)


def test_disarm_restores_baseline_and_requires_new_instance_to_rearm():
    p, _, target, _, app = setup()
    app.process(request(p))
    result = app.disarm()
    assert result.state is S.DISARMED and result.effective_parameters == baseline(p).values
    writes = len(target.writes)
    assert app.process(request(p)).reason is R.DISARMED
    assert len(target.writes) == writes


@pytest.mark.parametrize("failure", ["before_write", "after_write", "bad_ack", "slow"])
def test_failed_uncertain_or_late_commit_is_faulted_and_verified_back_at_baseline(failure):
    p, _, target, _, app = setup()
    target.failure = failure
    result = app.process(request(p))
    assert result.state is S.FAULTED
    assert result.effective_parameters == target.current.values == baseline(p).values
    assert result.reason in {R.TARGET_FAULT, R.TRANSACTION_TIMEOUT}


@pytest.mark.parametrize("failure", ["read", "partial", "post_read"])
def test_unknown_output_or_ownership_never_claims_baseline(failure):
    p, _, target, _, app = setup()
    target.failure = failure
    result = app.process(request(p))
    assert result.state is S.FAULTED and result.effective_parameters is None
    assert result.reason in {R.TARGET_FAULT, R.ROLLBACK_FAILED}


def test_foreign_revision_is_not_overwritten_even_to_restore_baseline():
    p, _, target, _, app = setup()
    app.process(request(p))
    target.current = replace(target.current, revision=99)
    result = app.disarm()
    assert result.reason is R.ROLLBACK_FAILED and result.effective_parameters is None
    assert len(target.writes) == 1


def test_clock_regression_restores_owned_state_and_latches():
    p, clock, target, _, app = setup()
    app.process(request(p))
    clock.time = 0.5
    result = app.process(request(p, sequence=1, now=0.5, revision=1))
    assert result.state is S.FAULTED and result.reason is R.CLOCK_FAULT
    assert target.current.values == result.effective_parameters == baseline(p).values


def test_fresh_proposal_cannot_bypass_an_expired_active_hold():
    p, clock, target, authority, app = setup()
    app.process(request(p))
    clock.time = 2.0
    result = app.process(request(p, sequence=1, now=2.0, revision=1, value=11.0))
    assert result.reason is R.HOLD_EXPIRED and result.state is S.FAULTED
    assert result.effective_parameters == baseline(p).values
    assert authority.calls == 1 and len(target.writes) == 2


def test_no_change_still_checks_target_after_authorizer_work():
    p, _, target, authority, app = setup()
    original = authority.authorize

    def conflict(item, policy, now):
        authority.callback = None
        grant = original(item, policy, now)
        target.current = replace(target.current, revision=99)
        return grant

    authority.callback = conflict
    result = app.process(request(p, value=10.0))
    assert result.reason is R.TARGET_CONFLICT and result.state is S.FAULTED
    assert result.effective_parameters is None and not target.writes


def test_future_baseline_anchor_is_a_clock_fault_even_for_unchanged_value():
    p, clock, target, authority, app = setup()
    app = type(app)(p, replace(baseline(p), timestamp_s=2.0), target, authority, clock)
    result = app.process(request(p, value=10.0))
    assert result.reason is R.CLOCK_FAULT and result.state is S.FAULTED
    assert not target.writes and authority.calls == 0


def test_rejected_source_also_consumes_timestamp_high_water():
    p, clock, target, _, app = setup()
    first = request(p)
    app.process(replace(first, observation=replace(first.observation, source_valid=False)))
    clock.time = 1.1
    result = app.process(request(p, sequence=1, now=1.0, value=10.0))
    assert result.reason is R.ORDERING and not target.writes


def test_rollback_deadline_is_reported_even_when_baseline_is_observed():
    p, _, target, _, app = setup(maximum_rollback_s=0.25)
    app.process(request(p))
    target.failure = "slow"
    result = app.watchdog(replace(request(p, sequence=1).observation, driver_override=True))
    assert result.reason is R.OVERRIDE and result.state is S.FAULTED
    assert result.effective_parameters == baseline(p).values
    assert result.recovery_reason.value == "ROLLBACK_TIMEOUT"


def test_rollback_exception_cannot_be_hidden_by_successful_baseline_readback():
    p, _, target, _, app = setup()
    app.process(request(p))
    target.failure = "after_write"
    result = app.disarm()
    assert result.state is S.FAULTED and result.effective_parameters == baseline(p).values
    assert result.recovery_reason is R.TARGET_FAULT


def test_rollback_failure_is_sticky_and_not_automatically_retried():
    p, _, target, _, app = setup()
    app.process(request(p))
    target.failure = "before_write"
    result = app.disarm()
    assert result.reason is R.ROLLBACK_FAILED and result.effective_parameters is None
    writes = len(target.writes)
    assert app.disarm().reason is R.FAULT_LATCHED
    assert app.watchdog(request(p).observation).reason is R.FAULT_LATCHED
    assert len(target.writes) == writes
