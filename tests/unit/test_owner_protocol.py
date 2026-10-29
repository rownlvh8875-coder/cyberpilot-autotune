"""Vehicle-independent owner behavior; synthetic values are not vehicle policy."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.owner_protocol import (
    AuthorityContext,
    BaselineRecord,
    ControllerMode,
    MemoryTuplePort,
    OwnerIdentity,
    OwnerPolicy,
    OwnerProtocolError,
    OwnerState,
    ProducerBinding,
    ProducerKind,
    ReferenceTorqueParameterOwner,
    TorqueParameterTuple,
    TorqueProposal,
    WatchdogInput,
)


class Clock:
    def __init__(self):
        self.value = 10.0

    def now_s(self):
        return self.value


class Authority:
    def __init__(self):
        self.accepted = set()

    def approve(self, grant, now_s):
        return grant.operation_digest in self.accepted


def setup_owner(port_type=MemoryTuplePort):
    identity = OwnerIdentity(
        "torque-owner-v1", "a" * 40, "b" * 40, "synthetic", "c" * 64, 0, 4, "d" * 32
    )
    baseline = BaselineRecord(
        identity,
        TorqueParameterTuple(2.0, 0.2, -0.125),
        7,
        ControllerMode.LINEAR_TORQUE,
        9.0,
        "e" * 64,
        "f" * 32,
    )
    bindings = tuple(
        ProducerBinding(p, 0, frozenset({ControllerMode.LINEAR_TORQUE})) for p in ProducerKind
    )
    policy = OwnerPolicy(3.0, 2.0, 8.0, 1.0, 1.0, bindings)
    clock, authority = Clock(), Authority()
    port = port_type(baseline.installed)
    owner = ReferenceTorqueParameterOwner(identity, baseline, policy, clock, authority, port)
    owner.initialize()
    return owner, port, clock, authority, baseline


def proposal(owner, sequence=1, candidate=None, producer=ProducerKind.CYBERPILOT):
    snap = owner.snapshot()
    return TorqueProposal(
        producer,
        sequence,
        f"{sequence:032x}",
        0,
        "a" * 40,
        "c" * 64,
        4,
        snap.revision,
        candidate or TorqueParameterTuple(2.5, 0.2, -0.125),
        10.0,
        15.0,
        "1" * 64,
        ControllerMode.LINEAR_TORQUE,
    )


def grant(owner, authority, item):
    authority.accepted.add(item.digest)
    return AuthorityContext("2" * 32, owner.identity.digest, item.digest, 9.0, 16.0)


def evidence():
    return WatchdogInput("a" * 40, "c" * 64, 4, ControllerMode.LINEAR_TORQUE, True, True, 10.0)


def test_cas_ack_and_independent_snapshot_keep_offset_and_exact_revision():
    owner, port, clock, authority, base = setup_owner()
    item = proposal(owner)
    ack = owner.commit(7, item, grant(owner, authority, item))
    assert (ack.prior_revision, ack.new_revision) == (7, 8)
    snap = owner.snapshot()
    assert snap.values == item.candidate
    assert snap.values.lat_accel_offset == -0.125
    assert snap.revision == 8 and snap.state is OwnerState.OWNED
    assert snap.values.digest == ack.committed_digest


def test_no_change_does_not_increment_or_create_lease_and_consumes_identity():
    owner, _, _, authority, base = setup_owner()
    item = proposal(owner, candidate=base.values)
    assert owner.commit(7, item, grant(owner, authority, item)) is None
    assert owner.snapshot().revision == 7 and owner.snapshot().lease is None
    with pytest.raises(OwnerProtocolError, match="REPLAY"):
        owner.commit(7, item, grant(owner, authority, item))


def test_rejected_authorization_cannot_be_mutated_and_reused():
    owner, _, _, authority, _ = setup_owner()
    item = proposal(owner)
    denied = AuthorityContext("2" * 32, owner.identity.digest, item.digest, 9.0, 16.0)
    with pytest.raises(OwnerProtocolError, match="AUTHORITY"):
        owner.commit(7, item, denied)
    with pytest.raises(OwnerProtocolError, match="REPLAY"):
        owner.commit(7, replace(item, evidence_digest="3" * 64), grant(owner, authority, item))
    assert owner.snapshot().revision == 7


def test_lease_expiry_rolls_back_then_faults_without_hiding_the_deadline():
    owner, _, clock, authority, base = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    clock.value = 15.0
    result = owner.watchdog(replace(evidence(), generated_at_s=15.0))
    assert result.verified and result.values == base.values and result.revision == 9
    assert owner.state is OwnerState.FAULTED
    with pytest.raises(OwnerProtocolError):
        owner.commit(9, proposal(owner, sequence=2), grant(owner, authority, item))


def test_snapshot_never_changes_revision_state_or_lease():
    owner, _, clock, _, _ = setup_owner()
    first = owner.snapshot()
    clock.value = 10.25
    second = owner.snapshot()
    assert second.timestamp_s == 10.25 and first.timestamp_s == 10.0
    assert (second.revision, second.state, second.lease) == (7, OwnerState.READY, None)


def test_different_producer_cannot_replace_an_active_lease_even_with_own_grant():
    owner, _, _, authority, _ = setup_owner()
    first = proposal(owner)
    owner.commit(7, first, grant(owner, authority, first))
    contender = proposal(owner, producer=ProducerKind.TORQUED)
    with pytest.raises(OwnerProtocolError, match="PRODUCER_BUSY"):
        owner.commit(8, contender, grant(owner, authority, contender))
    assert owner.snapshot().revision == 8


def test_a_normal_recovery_does_not_disable_next_lease_expiry_recovery():
    owner, _, clock, authority, base = setup_owner()
    first = proposal(owner)
    owner.commit(7, first, grant(owner, authority, first))
    assert owner.rollback().verified
    second = proposal(owner, sequence=2)
    owner.commit(9, second, grant(owner, authority, second))
    clock.value = 15.0
    result = owner.watchdog(replace(evidence(), generated_at_s=15.0))
    assert result.verified and result.values == base.values and result.revision == 11


def test_clock_regression_after_install_latches_uncertain_domain():
    class RegressingPort(MemoryTuplePort):
        def compare_and_swap(self, expected, update):
            result = super().compare_and_swap(expected, update)
            clock.value = 8.0
            return result

    owner, _, clock, authority, _ = setup_owner(RegressingPort)
    item = proposal(owner)
    with pytest.raises(OwnerProtocolError):
        owner.commit(7, item, grant(owner, authority, item))
    assert owner.state is OwnerState.FAULTED


class OneShotFaultPort(MemoryTuplePort):
    fault = "none"

    def compare_and_swap(self, expected, update):
        kind, self.fault = self.fault, "none"
        if kind == "before":
            raise RuntimeError("before install")
        result = super().compare_and_swap(expected, update)
        if kind == "after":
            raise RuntimeError("after install")
        return result + 1 if kind == "ack" else result


@pytest.mark.parametrize(
    "failure, observed_revision, recovered_revision",
    [
        ("before", 7, 7),
        ("after", 8, 9),
        ("ack", 8, 9),
    ],
)
def test_uncertain_commit_requires_actual_cohort_and_verified_recovery(
    failure, observed_revision, recovered_revision
):
    owner, port, _, authority, base = setup_owner(OneShotFaultPort)
    port.fault = failure
    item = proposal(owner)
    with pytest.raises(OwnerProtocolError):
        owner.commit(7, item, grant(owner, authority, item))
    assert owner.snapshot().revision == observed_revision
    result = owner.rollback()
    assert (
        result.verified and result.revision == recovered_revision and result.values == base.values
    )
    assert result.state is OwnerState.FAULTED
    with pytest.raises(OwnerProtocolError, match="RECOVERY_UNAVAILABLE"):
        owner.rollback()


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("observed_revision", 6, "CAS_CONFLICT"),
        ("source_revision", "9" * 40, "CONTEXT"),
        ("context_digest", "9" * 64, "CONTEXT"),
        ("baseline_epoch", 3, "CONTEXT"),
        ("producer_generation", 1, "PRODUCER_GENERATION"),
        ("required_mode", ControllerMode.NN_TORQUE, "UNSUPPORTED_MODE"),
        ("generated_at_s", 11.0, "PROPOSAL_EXPIRED"),
        ("expires_at_s", 9.5, "PROPOSAL_EXPIRED"),
        ("proposal_id", "f" * 32, "REPLAY"),
        ("candidate", TorqueParameterTuple(2.5, 0.3, 0.0), "OFFSET_PRESERVATION"),
    ],
)
def test_invalid_or_stale_proposal_rejects_without_tuple_mutation(field, value, reason):
    owner, _, _, authority, base = setup_owner()
    item = proposal(owner)
    if field == "expires_at_s":
        item = replace(item, generated_at_s=9.0)
    item = replace(item, **{field: value})
    with pytest.raises(OwnerProtocolError, match=reason):
        owner.commit(7, item, grant(owner, authority, item))
    assert owner.snapshot().values == base.values and owner.snapshot().revision == 7


@pytest.mark.parametrize(
    "kind", ["owner", "operation", "future", "expired", "exception", "nonbool"]
)
def test_grant_binding_and_independent_authority_cannot_be_replaced_by_a_digest(kind):
    owner, _, _, authority, _ = setup_owner()
    item = proposal(owner)
    authorization = grant(owner, authority, item)
    if kind == "owner":
        authorization = replace(authorization, owner_digest="3" * 64)
    elif kind == "operation":
        authorization = replace(authorization, operation_digest="3" * 64)
    elif kind == "future":
        authorization = replace(authorization, issued_at_s=11.0)
    elif kind == "expired":
        authorization = replace(authorization, expires_at_s=10.0)
    elif kind == "exception":

        def approve(*args):
            raise RuntimeError("authority unavailable")

        authority.approve = approve
    else:
        authority.approve = lambda *args: 1
    with pytest.raises(OwnerProtocolError, match="AUTHORITY"):
        owner.commit(7, item, authorization)
    assert owner.snapshot().revision == 7


@pytest.mark.parametrize("damage", ["revision", "tuple", "mode", "identity"])
def test_foreign_state_is_never_overwritten_even_when_lease_expired(damage):
    owner, port, clock, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    before = port.read()
    foreign = replace(
        before,
        **{
            "revision": {"revision": 99},
            "tuple": {"values": TorqueParameterTuple(9.0, 0.3, -0.5)},
            "mode": {"mode": ControllerMode.NN_TORQUE},
            "identity": {"identity_digest": "9" * 64},
        }[damage],
    )
    port.compare_and_swap(before, foreign)
    clock.value = 20.0
    with pytest.raises(OwnerProtocolError, match="FOREIGN_STATE"):
        owner.snapshot()
    result = owner.watchdog(evidence())
    assert not result.verified and result.values is None and result.revision is None
    assert owner.state is OwnerState.FAULTED and port.read() == foreign
    assert not owner.rollback().verified and port.read() == foreign


@pytest.mark.parametrize("change", ["source", "context", "mode", "epoch", "owner"])
def test_changed_actual_context_or_dead_owner_prevents_guessed_baseline_recovery(change):
    owner, port, _, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    before = port.read()
    observed = replace(
        evidence(),
        **{
            "source": {"source_revision": "9" * 40},
            "context": {"context_digest": "9" * 64},
            "mode": {"controller_mode": ControllerMode.NN_TORQUE},
            "epoch": {"baseline_epoch": 5},
            "owner": {"owner_alive": False},
        }[change],
    )
    result = owner.watchdog(observed)
    assert not result.verified and result.values is None and port.read() == before
    assert result.state is OwnerState.FAULTED


@pytest.mark.parametrize("change", ["stale", "future", "dead"])
def test_watchdog_veto_recovers_only_known_owned_cohort(change):
    owner, _, _, authority, base = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    observed = replace(
        evidence(),
        **{
            "stale": {"generated_at_s": 1.0},
            "future": {"generated_at_s": 11.0},
            "dead": {"active_producer_alive": False},
        }[change],
    )
    result = owner.watchdog(observed)
    assert result.verified and result.values == base.values and result.revision == 9
    assert result.state is OwnerState.FAULTED


def mode_grant(owner, authority, mode, revision):
    operation = owner.mode_transition_digest(mode, revision)
    authority.accepted.add(operation)
    return AuthorityContext("2" * 32, owner.identity.digest, operation, 9.0, 16.0)


def test_explicit_custom_transition_closes_old_epoch_and_ack_names_final_state():
    owner, _, _, authority, base = setup_owner()
    ack = owner.transition_mode(
        7,
        ControllerMode.CUSTOM_TORQUE,
        mode_grant(owner, authority, ControllerMode.CUSTOM_TORQUE, 7),
    )
    snap = owner.snapshot()
    assert snap.values == base.values and snap.revision == 8
    assert snap.controller_mode is ControllerMode.CUSTOM_TORQUE
    assert snap.state is ack.state is OwnerState.DISARMED
    with pytest.raises(OwnerProtocolError):
        item = proposal(owner)
        owner.commit(8, item, grant(owner, authority, item))


def test_active_mode_request_recovers_before_any_new_mode_or_new_epoch():
    owner, _, _, authority, base = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    with pytest.raises(OwnerProtocolError, match="RECOVERY_REQUIRED"):
        owner.transition_mode(
            8, ControllerMode.NN_TORQUE, mode_grant(owner, authority, ControllerMode.NN_TORQUE, 8)
        )
    result = owner.watchdog(evidence())
    assert result.verified and result.values == base.values and result.revision == 9
    assert owner.state is OwnerState.DISARMED
    assert owner.snapshot().controller_mode is ControllerMode.LINEAR_TORQUE


@pytest.mark.parametrize("operation", ["disarm", "stop"])
def test_shutdown_requires_verified_baseline_and_is_terminal(operation):
    owner, _, _, authority, base = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    result = getattr(owner, operation)()
    assert result.verified and result.values == base.values and result.revision == 9
    assert owner.state is (OwnerState.DISARMED if operation == "disarm" else OwnerState.STOPPED)
    with pytest.raises(OwnerProtocolError):
        owner.commit(9, item, grant(owner, authority, item))
    if operation == "disarm":
        assert owner.stop().verified and owner.state is OwnerState.STOPPED


def test_failed_rollback_cannot_be_reported_as_clean_stop():
    owner, port, _, authority, _ = setup_owner(OneShotFaultPort)
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    port.fault = "after"
    result = owner.stop()
    assert not result.verified and result.values is None and owner.state is OwnerState.FAULTED


def test_no_change_on_active_lease_never_extends_it():
    owner, _, clock, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    original = owner.snapshot().lease
    clock.value = 10.5
    unchanged = proposal(owner, sequence=2, candidate=item.candidate)
    assert owner.commit(8, unchanged, grant(owner, authority, unchanged)) is None
    assert owner.snapshot().lease == original and owner.snapshot().revision == 8


def test_signed_zero_and_float64_precision_remain_lossless_logical_values():
    assert TorqueParameterTuple(0.0, 0.1, -0.0).digest != TorqueParameterTuple(0.0, 0.1, 0.0).digest
    owner, _, _, authority, _ = setup_owner()
    value = 1.0 + 2.0**-40  # deliberately not a binary32 value; not a vehicle proposal
    item = proposal(owner, candidate=TorqueParameterTuple(value, 0.1, -0.125))
    owner.commit(7, item, grant(owner, authority, item))
    assert owner.snapshot().values.lat_accel_factor == value
