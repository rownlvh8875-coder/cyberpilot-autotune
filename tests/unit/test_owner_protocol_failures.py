"""Fault injection at trusted capability boundaries, never actual controller IO."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.owner_protocol import (
    AuthorityContext,
    ControllerMode,
    MemoryTuplePort,
    OwnerProtocolError,
    OwnerState,
    ProducerBinding,
    ProducerKind,
    ReferenceTorqueParameterOwner,
    TorqueParameterTuple,
)
from tests.unit.test_owner_protocol import evidence, grant, mode_grant, proposal, setup_owner


def uninitialized():
    old, port, clock, authority, base = setup_owner()
    return (
        ReferenceTorqueParameterOwner(old.identity, base, old.policy, clock, authority, port),
        port,
        clock,
    )


def test_explicit_initialization_validates_actual_baseline_and_no_double_initialize():
    owner, _, _ = uninitialized()
    assert owner.state is OwnerState.UNINITIALIZED
    with pytest.raises(OwnerProtocolError, match="UNINITIALIZED"):
        owner.snapshot()
    assert not owner.watchdog(evidence()).verified
    with pytest.raises(OwnerProtocolError):
        owner.rollback()
    owner.initialize()
    with pytest.raises(OwnerProtocolError, match="ALREADY_INITIALIZED"):
        owner.initialize()
    assert owner.snapshot().tuple_digest == owner.baseline.values.digest


@pytest.mark.parametrize("fault", ["foreign", "clock"])
def test_invalid_initial_baseline_or_clock_latches_fault(fault):
    owner, port, clock = uninitialized()
    if fault == "foreign":
        before = port.read()
        port.compare_and_swap(before, replace(before, revision=8))
    else:
        clock.value = float("nan")
    with pytest.raises(OwnerProtocolError, match="INITIALIZATION_FAULT"):
        owner.initialize()
    assert owner.state is OwnerState.FAULTED


@pytest.mark.parametrize(
    "field,value",
    [
        ("lat_accel_factor", float("nan")),
        ("friction", float("inf")),
        ("lat_accel_offset", True),
        ("lat_accel_factor", 1),
    ],
)
def test_incomplete_or_nonfinite_logical_values_cannot_enter_protocol(field, value):
    with pytest.raises(ValueError):
        replace(TorqueParameterTuple(0.0, 0.0, -0.0), **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("baseline_epoch", -1),
        ("session_generation", True),
        ("session_generation", 1 << 64),
        ("protocol_version", "unknown"),
        ("controller_family", ""),
        ("source_revision", "main"),
        ("vehicle_context_digest", "VIN"),
    ],
)
def test_owner_identity_does_not_accept_missing_or_ambiguous_identity(field, value):
    owner, *_ = setup_owner()
    with pytest.raises(ValueError):
        replace(owner.identity, **{field: value})


def test_policy_requires_explicit_positive_times_unique_generations_and_qualified_modes():
    owner, *_ = setup_owner()
    for changes in (
        {"maximum_lease_s": 0.0},
        {"maximum_transaction_s": -1.0},
        {"producers": ()},
        {"producers": owner.policy.producers * 2},
    ):
        with pytest.raises(ValueError):
            replace(owner.policy, **changes)
    with pytest.raises(ValueError):
        ProducerBinding(ProducerKind.CYBERPILOT, 0, frozenset({ControllerMode.UNKNOWN}))
    with pytest.raises(ValueError):
        AuthorityContext("2" * 32, "a" * 64, "b" * 64, 10.0, 10.0)


def test_port_rejects_invalid_initial_and_foreign_compare_without_mutation():
    with pytest.raises(ValueError):
        MemoryTuplePort(None)
    owner, port, *_ = setup_owner()
    initial = port.read()
    with pytest.raises(OwnerProtocolError, match="FOREIGN_STATE"):
        port.compare_and_swap(replace(initial, revision=8), initial)
    assert port.read() == initial


@pytest.mark.parametrize("corruption", ["port", "clock", "invalid_proposal"])
def test_preflight_faults_cannot_be_hidden_by_a_new_proposal(corruption):
    owner, port, clock, authority, _ = setup_owner()
    item = proposal(owner)
    auth = grant(owner, authority, item)
    if corruption == "port":
        port.read = lambda: None
    elif corruption == "clock":
        clock.value = 8.0
    with pytest.raises(OwnerProtocolError):
        owner.commit(7, None if corruption == "invalid_proposal" else item, auth)
    assert owner.state is (
        OwnerState.READY if corruption == "invalid_proposal" else OwnerState.FAULTED
    )


def test_revision_exhaustion_does_not_wrap_or_install():
    previous, _, clock, authority, base = setup_owner()
    base = replace(base, revision_anchor=(1 << 64) - 1)
    port = MemoryTuplePort(base.installed)
    owner = ReferenceTorqueParameterOwner(
        previous.identity, base, previous.policy, clock, authority, port
    )
    owner.initialize()
    item = proposal(owner)
    with pytest.raises(OwnerProtocolError, match="REVISION_EXHAUSTED"):
        owner.commit((1 << 64) - 1, item, grant(owner, authority, item))
    assert port.read().revision == (1 << 64) - 1 and owner.fault_reason == "REVISION_EXHAUSTED"


@pytest.mark.parametrize(
    "times,reason,revision",
    [
        ([10.0, 10.0, 12.0], "DEADLINE", 7),
        ([10.0, 10.0, 10.0, 12.0], "DEADLINE", 8),
        ([10.0, 10.0, 10.0, 10.0, 15.0], "DEADLINE", 8),
    ],
)
def test_pre_install_post_install_and_final_grant_expiry_are_distinct(times, reason, revision):
    owner, port, clock, authority, _ = setup_owner()
    item = proposal(owner)
    auth = grant(owner, authority, item)
    values = iter(times)
    clock.now_s = lambda: next(values)
    with pytest.raises(OwnerProtocolError, match=reason):
        owner.commit(7, item, auth)
    assert owner.state is OwnerState.FAULTED and port.read().revision == revision


def test_callback_overrun_before_commit_never_changes_tuple():
    owner, port, clock, authority, _ = setup_owner()
    item = proposal(owner)
    auth = grant(owner, authority, item)

    def approve(*args):
        clock.value = 12.0
        return True

    authority.approve = approve
    with pytest.raises(OwnerProtocolError, match="DEADLINE"):
        owner.commit(7, item, auth)
    assert port.read().revision == 7


def test_expired_lease_blocks_new_commit_then_watchdog_recovers():
    owner, _, clock, authority, base = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    next_item = proposal(owner, sequence=2)
    clock.value = 15.0
    with pytest.raises(OwnerProtocolError, match="LEASE_EXPIRED"):
        owner.commit(8, next_item, grant(owner, authority, next_item))
    assert owner.state is OwnerState.RECOVERING
    assert owner.watchdog(replace(evidence(), generated_at_s=15.0)).values == base.values


@pytest.mark.parametrize("fault", ["tuple", "revision", "deadline"])
def test_recovery_serialization_or_deadline_failure_never_claims_verified_baseline(fault):
    owner, _, clock, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    real_snapshot = owner.snapshot

    def broken_readback():
        actual = real_snapshot()
        if fault == "deadline":
            clock.value = 12.0
            return actual
        return replace(
            actual,
            **(
                {"values": item.candidate}
                if fault == "tuple"
                else {"revision": actual.revision + 1}
            ),
        )

    owner.snapshot = broken_readback
    result = owner.rollback()
    assert not result.verified and result.values is None and result.state is OwnerState.FAULTED


def test_mode_switch_rejects_bad_cas_unknown_mode_and_expired_authorization():
    owner, _, clock, authority, _ = setup_owner()
    auth = mode_grant(owner, authority, ControllerMode.NN_TORQUE, 7)
    with pytest.raises(OwnerProtocolError, match="CAS_CONFLICT"):
        owner.transition_mode(6, ControllerMode.NN_TORQUE, auth)
    with pytest.raises(OwnerProtocolError, match="UNSUPPORTED_MODE"):
        owner.transition_mode(7, ControllerMode.UNKNOWN, auth)
    same = mode_grant(owner, authority, ControllerMode.LINEAR_TORQUE, 7)
    assert owner.transition_mode(7, ControllerMode.LINEAR_TORQUE, same) is None

    def slow(*args):
        clock.value = 16.0
        return True

    authority.approve = slow
    with pytest.raises(OwnerProtocolError, match="MODE_TRANSITION_FAULT"):
        owner.transition_mode(7, ControllerMode.NN_TORQUE, auth)


def test_new_epoch_cannot_reuse_old_owner_authorization_or_producer_generation():
    old, _, clock, authority, base = setup_owner()
    old_item = proposal(old)
    old_grant = grant(old, authority, old_item)
    identity = replace(
        old.identity, baseline_epoch=5, session_generation=1, owner_instance_id="4" * 32
    )
    base = replace(base, identity=identity)
    restarted = ReferenceTorqueParameterOwner(
        identity, base, old.policy, clock, authority, MemoryTuplePort(base.installed)
    )
    restarted.initialize()
    with pytest.raises(OwnerProtocolError, match="CONTEXT"):
        restarted.commit(7, old_item, old_grant)
    item = replace(old_item, baseline_epoch=5, sequence=2, proposal_id=f"{2:032x}")
    with pytest.raises(OwnerProtocolError, match="AUTHORITY"):
        restarted.commit(7, item, old_grant)


def test_unknown_producer_binding_and_empty_fault_reason_reject():
    previous, _, clock, authority, base = setup_owner()
    policy = replace(previous.policy, producers=(previous.policy.producers[0],))
    owner = ReferenceTorqueParameterOwner(
        previous.identity, base, policy, clock, authority, MemoryTuplePort(base.installed)
    )
    owner.initialize()
    item = proposal(owner)
    with pytest.raises(OwnerProtocolError, match="PRODUCER_GENERATION"):
        owner.commit(7, item, grant(owner, authority, item))
    with pytest.raises(ValueError):
        owner.fault("")


def test_recovery_cannot_cross_a_completed_mode_transition():
    owner, _, _, authority, _ = setup_owner()
    owner.transition_mode(
        7,
        ControllerMode.CUSTOM_TORQUE,
        mode_grant(owner, authority, ControllerMode.CUSTOM_TORQUE, 7),
    )
    owner.fault("EXTERNAL_FAILURE")
    assert not owner.rollback().verified


def test_foreign_state_after_disarm_prevents_clean_stop():
    owner, port, *_ = setup_owner()
    owner.disarm()
    previous = port.read()
    port.compare_and_swap(previous, replace(previous, revision=9))
    with pytest.raises(OwnerProtocolError, match="STOP_UNVERIFIED"):
        owner.stop()


def test_healthy_watchdog_observes_actual_nonbaseline_values_without_recovery():
    owner, _, _, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    result = owner.watchdog(evidence())
    assert result.reason == "UNCHANGED" and result.values == item.candidate and result.revision == 8
    owner.fault("SYNTHETIC")
    assert not owner.watchdog(evidence()).verified


def test_expiry_during_mode_authorization_has_priority_over_mode_recovery_request():
    owner, _, clock, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    auth = mode_grant(owner, authority, ControllerMode.NN_TORQUE, 8)

    def approve(*args):
        clock.value = 15.0
        return True

    authority.approve = approve
    with pytest.raises(OwnerProtocolError, match="LEASE_EXPIRED"):
        owner.transition_mode(8, ControllerMode.NN_TORQUE, auth)


def test_transaction_deadline_in_final_post_install_check_cannot_be_hidden_by_valid_grant():
    owner, _, clock, authority, _ = setup_owner()
    item = proposal(owner)
    auth = grant(owner, authority, item)
    times = iter([10.0, 10.0, 10.0, 10.0, 11.5])
    clock.now_s = lambda: next(times)
    with pytest.raises(OwnerProtocolError, match="DEADLINE"):
        owner.commit(7, item, auth)


def test_mode_install_cannot_outlive_its_authorization_even_within_transaction_duration():
    owner, _, clock, authority, _ = setup_owner()
    auth = replace(mode_grant(owner, authority, ControllerMode.NN_TORQUE, 7), expires_at_s=10.1)
    times = iter([10.0, 10.0, 10.0, 10.2, 10.2])
    clock.now_s = lambda: next(times)
    with pytest.raises(OwnerProtocolError, match="DEADLINE"):
        owner.transition_mode(7, ControllerMode.NN_TORQUE, auth)
    assert owner.state is OwnerState.FAULTED


def test_failure_of_independent_initial_snapshot_does_not_leave_ready_state():
    owner, port, _ = uninitialized()
    actual_read = port.read
    calls = 0

    def unavailable_readback():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("initial readback unavailable")
        return actual_read()

    port.read = unavailable_readback
    with pytest.raises(OwnerProtocolError, match="INITIALIZATION_FAULT"):
        owner.initialize()
    assert owner.state is OwnerState.FAULTED


def test_restart_requires_explicit_fresh_owner_session_epoch_and_baseline():
    owner, _, _, authority, base = setup_owner()
    with pytest.raises(OwnerProtocolError, match="RESTART_REQUIRES_CLOSED_DOMAIN"):
        owner.restart(owner.identity, base, owner.policy, MemoryTuplePort(base.installed))
    old_item = proposal(owner)
    old_auth = grant(owner, authority, old_item)
    owner.stop()
    with pytest.raises(ValueError, match="fresh identity"):
        owner.restart(owner.identity, base, owner.policy, MemoryTuplePort(base.installed))
    identity = replace(
        owner.identity, session_generation=1, baseline_epoch=5, owner_instance_id="4" * 32
    )
    fresh_base = replace(base, identity=identity, captured_at_s=10.0, capture_id="5" * 32)
    restarted = owner.restart(
        identity, fresh_base, owner.policy, MemoryTuplePort(fresh_base.installed)
    )
    assert restarted.state is OwnerState.READY and owner.state is OwnerState.STOPPED
    with pytest.raises(OwnerProtocolError, match="CONTEXT"):
        restarted.commit(7, old_item, old_auth)


def test_known_actual_context_loss_cannot_be_bypassed_by_later_generic_rollback():
    owner, port, _, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    installed = port.read()
    owner.watchdog(replace(evidence(), context_digest="9" * 64))
    result = owner.rollback()
    assert not result.verified and result.values is None and port.read() == installed


def test_commit_identity_is_unique_across_producers_reusing_their_lane_sequence():
    owner, _, _, authority, _ = setup_owner()
    first = proposal(owner)
    first_ack = owner.commit(7, first, grant(owner, authority, first))
    assert owner.rollback().verified
    second = proposal(owner, producer=ProducerKind.TORQUED)
    second_ack = owner.commit(9, second, grant(owner, authority, second))
    assert first_ack.commit_id != second_ack.commit_id


def test_fresh_watchdog_input_does_not_refresh_the_active_proposals_original_age():
    owner, _, clock, authority, base = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    clock.value = 13.25  # proposal age exceeds caller policy, before proposal/grant raw expiry
    result = owner.watchdog(replace(evidence(), generated_at_s=13.25))
    assert result.verified and result.values == base.values and result.revision == 9
    assert result.state is OwnerState.FAULTED


@pytest.mark.parametrize(
    "times,revision",
    [
        ([12.9, 12.9, 13.0, 13.0, 13.0], 8),
        ([12.9, 12.9, 12.9, 13.0, 13.0], 9),
        ([12.9, 12.9, 12.9, 12.9, 13.0], 9),
    ],
)
def test_old_lease_expiry_precedes_renewal_at_every_final_install_boundary(times, revision):
    owner, port, clock, authority, base = setup_owner()
    first = proposal(owner)
    owner.commit(7, first, grant(owner, authority, first))
    second = replace(
        proposal(owner, sequence=2, candidate=TorqueParameterTuple(3.0, 0.2, -0.125)),
        generated_at_s=12.9,
        expires_at_s=20.0,
    )
    authorization = replace(grant(owner, authority, second), expires_at_s=20.0)
    samples = iter(times)
    clock.now_s = lambda: next(samples)
    with pytest.raises(OwnerProtocolError, match="LEASE_EXPIRED"):
        owner.commit(8, second, authorization)
    assert port.read().revision == revision
    clock.now_s = lambda: 13.0
    result = owner.rollback()
    assert result.verified and result.values == base.values
    assert result.revision == revision + 1
    assert owner.state is OwnerState.FAULTED


def test_mode_final_clock_cannot_hide_transaction_overrun_behind_unexpired_grant():
    owner, port, clock, authority, _ = setup_owner()
    authorization = mode_grant(owner, authority, ControllerMode.NN_TORQUE, 7)
    samples = iter([10.0, 10.0, 10.0, 10.0, 11.5])
    clock.now_s = lambda: next(samples)
    with pytest.raises(OwnerProtocolError, match="DEADLINE"):
        owner.transition_mode(7, ControllerMode.NN_TORQUE, authorization)
    assert owner.state is OwnerState.FAULTED and port.read().revision == 8


@pytest.mark.parametrize("expired", ["grant", "proposal", "proposal_age", "mode_grant"])
def test_known_expiry_at_final_pre_cas_sample_never_installs(expired):
    owner, port, clock, authority, _ = setup_owner()
    item = proposal(owner)
    if expired == "proposal":
        item = replace(item, expires_at_s=10.1)
    elif expired == "proposal_age":
        item = replace(item, generated_at_s=7.1)
    authorization = grant(owner, authority, item)
    if expired == "grant":
        authorization = replace(authorization, expires_at_s=10.1)
    if expired == "mode_grant":
        authorization = replace(
            mode_grant(owner, authority, ControllerMode.NN_TORQUE, 7), expires_at_s=10.1
        )
    samples = iter([10.0, 10.0, 10.2, 10.2, 10.2])
    clock.now_s = lambda: next(samples)
    with pytest.raises(OwnerProtocolError):
        if expired == "mode_grant":
            owner.transition_mode(7, ControllerMode.NN_TORQUE, authorization)
        else:
            owner.commit(7, item, authorization)
    assert port.read().revision == 7 and port.read().mode is ControllerMode.LINEAR_TORQUE
    assert owner.state is OwnerState.FAULTED


def test_positive_but_unrepresentable_hold_cannot_create_an_already_expired_lease():
    previous, _, clock, authority, base = setup_owner()
    policy = replace(previous.policy, maximum_lease_s=5e-324)
    port = MemoryTuplePort(base.installed)
    owner = ReferenceTorqueParameterOwner(previous.identity, base, policy, clock, authority, port)
    owner.initialize()
    item = proposal(owner)
    with pytest.raises(OwnerProtocolError, match="LEASE_DURATION"):
        owner.commit(7, item, grant(owner, authority, item))
    assert port.read().revision == 7


def test_hold_resolution_change_during_install_faults_instead_of_acknowledging_zero_hold():
    previous, _, clock, authority, base = setup_owner()
    policy = replace(previous.policy, maximum_lease_s=1e-15)
    port = MemoryTuplePort(base.installed)
    owner = ReferenceTorqueParameterOwner(previous.identity, base, policy, clock, authority, port)
    owner.initialize()
    item = replace(proposal(owner), generated_at_s=15.999999999999998, expires_at_s=20.0)
    authorization = replace(grant(owner, authority, item), expires_at_s=20.0)
    samples = iter([15.999999999999998] * 3 + [16.0, 16.0])
    clock.now_s = lambda: next(samples)
    with pytest.raises(OwnerProtocolError, match="LEASE_DURATION"):
        owner.commit(7, item, authorization)
    assert owner.state is OwnerState.FAULTED and port.read().revision == 8


def test_same_mode_no_change_cannot_mask_authority_transaction_overrun():
    owner, port, clock, authority, _ = setup_owner()
    authorization = mode_grant(owner, authority, ControllerMode.LINEAR_TORQUE, 7)

    def slow_authority(*args):
        clock.value = 12.0
        return True

    authority.approve = slow_authority
    with pytest.raises(OwnerProtocolError, match="DEADLINE"):
        owner.transition_mode(7, ControllerMode.LINEAR_TORQUE, authorization)
    assert owner.state is OwnerState.FAULTED and port.read().revision == 7


def test_mode_grant_expiry_only_at_last_clock_is_still_a_fault():
    owner, port, clock, authority, _ = setup_owner()
    authorization = replace(
        mode_grant(owner, authority, ControllerMode.NN_TORQUE, 7), expires_at_s=10.1
    )
    samples = iter([10.0, 10.0, 10.0, 10.0, 10.2])
    clock.now_s = lambda: next(samples)
    with pytest.raises(OwnerProtocolError, match="MODE_TRANSITION_FAULT"):
        owner.transition_mode(7, ControllerMode.NN_TORQUE, authorization)
    assert owner.state is OwnerState.FAULTED and port.read().revision == 8


def test_clean_stop_rejects_nonbaseline_independent_snapshot_serialization():
    owner, port, *_ = setup_owner()
    owner.disarm()
    before = port.read()
    actual = owner.snapshot()
    owner.snapshot = lambda: replace(actual, values=TorqueParameterTuple(9.0, 0.2, -0.125))
    with pytest.raises(OwnerProtocolError, match="STOP_UNVERIFIED"):
        owner.stop()
    assert owner.state is OwnerState.FAULTED and port.read() == before
