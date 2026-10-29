"""Exercise the installed reference protocol outside checkout with Python -I."""

from cyberpilot_autotune.owner_protocol import (
    AuthorityContext,
    BaselineRecord,
    ControllerMode,
    MemoryTuplePort,
    OwnerIdentity,
    OwnerPolicy,
    ProducerBinding,
    ProducerKind,
    ReferenceTorqueParameterOwner,
    TorqueParameterTuple,
    TorqueProposal,
)


class SyntheticClock:
    def now_s(self):
        return 10.0


class SyntheticAuthority:
    def approve(self, grant, now_s):
        return grant.operation_digest == item.digest and grant.owner_digest == identity.digest


identity = OwnerIdentity(
    "torque-owner-v1", "a" * 40, "b" * 40, "synthetic-only", "c" * 64, 0, 4, "d" * 32
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
policy = OwnerPolicy(
    3.0,
    2.0,
    8.0,
    1.0,
    1.0,
    (ProducerBinding(ProducerKind.CYBERPILOT, 0, frozenset({ControllerMode.LINEAR_TORQUE})),),
)
owner = ReferenceTorqueParameterOwner(
    identity,
    baseline,
    policy,
    SyntheticClock(),
    SyntheticAuthority(),
    MemoryTuplePort(baseline.installed),
)
owner.initialize()
item = TorqueProposal(
    ProducerKind.CYBERPILOT,
    1,
    f"{1:032x}",
    0,
    "a" * 40,
    "c" * 64,
    4,
    7,
    TorqueParameterTuple(1.0 + 2.0**-40, 0.2, -0.125),
    10.0,
    15.0,
    "1" * 64,
    ControllerMode.LINEAR_TORQUE,
)
authorization = AuthorityContext("2" * 32, identity.digest, item.digest, 9.0, 16.0)
ack = owner.commit(7, item, authorization)
actual = owner.snapshot()
assert ack.new_revision == actual.revision == 8
assert actual.tuple_digest == item.candidate.digest
result = owner.rollback()
assert result.verified and result.values == baseline.values and result.revision == 9
assert owner.stop().verified
print("OWNER_REFERENCE_WHEEL_PASS: CAS / independent readback / preserved offset / rollback / stop")
