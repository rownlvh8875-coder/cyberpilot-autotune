"""Sequence invariants of the actual reference owner, not vehicle qualification."""

from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.owner_protocol import (
    MemoryTuplePort,
    OwnerProtocolError,
    OwnerState,
    ReferenceTorqueParameterOwner,
    TorqueParameterTuple,
)
from tests.unit.test_owner_protocol import evidence, grant, proposal, setup_owner


@given(
    st.lists(
        st.sampled_from(["commit", "reject", "read", "rollback", "disarm", "fault"]),
        min_size=1,
        max_size=35,
    )
)
@settings(max_examples=100)
def test_revision_rejection_replay_and_terminal_invariants_across_sequences(operations):
    owner, _, _, authority, base = setup_owner()
    for sequence, operation in enumerate(operations, 1):
        before = owner.snapshot()
        if operation in {"commit", "reject"}:
            item = proposal(
                owner,
                sequence=sequence,
                candidate=TorqueParameterTuple(
                    3.0 if before.values.lat_accel_factor == 2.0 else 2.0, 0.2, -0.125
                ),
            )
            if operation == "reject":
                item = replace(item, observed_revision=before.revision + 1)
            try:
                ack = owner.commit(before.revision, item, grant(owner, authority, item))
            except OwnerProtocolError:
                after = owner.snapshot()
                assert (
                    after.revision == before.revision
                    and after.values.digest == before.values.digest
                )
            else:
                assert operation == "commit" and ack.new_revision == before.revision + 1
                try:
                    owner.commit(ack.new_revision, item, grant(owner, authority, item))
                except OwnerProtocolError:
                    pass
                else:
                    raise AssertionError("consumed proposal was reapplied")
        elif operation == "read":
            assert owner.snapshot() == before
        elif operation == "fault":
            owner.fault("SYNTHETIC_FAULT")
        else:
            try:
                recovery = getattr(owner, operation)()
            except OwnerProtocolError:
                pass
            else:
                if recovery.verified:
                    assert recovery.values.digest == base.values.digest
        after = owner.snapshot()
        assert after.revision >= before.revision
        assert after.values.lat_accel_offset == -0.125
        if before.state is OwnerState.FAULTED:
            assert after.state is OwnerState.FAULTED
        assert after.revision - before.revision in (0, 1)


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
)
def test_opaque_finite_logical_tuples_are_lossless(factor, friction, offset):
    original, _, clock, authority, base = setup_owner()
    base = replace(base, values=TorqueParameterTuple(2.0, 0.2, offset))
    owner = ReferenceTorqueParameterOwner(
        original.identity, base, original.policy, clock, authority, MemoryTuplePort(base.installed)
    )
    owner.initialize()
    item = proposal(owner, candidate=TorqueParameterTuple(factor, friction, offset))
    ack = owner.commit(7, item, grant(owner, authority, item))
    assert owner.snapshot().values.digest == item.candidate.digest
    assert owner.snapshot().revision == (7 if item.candidate.digest == base.values.digest else 8)
    if ack:
        result = owner.rollback()
        assert (
            result.verified and result.values.digest == base.values.digest and result.revision == 9
        )


@given(st.booleans())
def test_expiry_plus_foreign_context_never_claims_or_overwrites_baseline(owner_alive):
    owner, port, clock, authority, _ = setup_owner()
    item = proposal(owner)
    owner.commit(7, item, grant(owner, authority, item))
    installed = port.read()
    clock.value = 15.0
    result = owner.watchdog(
        replace(evidence(), context_digest="9" * 64, owner_alive=owner_alive, generated_at_s=15.0)
    )
    assert result.values is None and not result.verified
    assert port.read() == installed and owner.state is OwnerState.FAULTED
