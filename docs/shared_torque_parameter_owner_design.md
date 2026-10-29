# H4 Shared TorqueParameterOwner detailed design

Status: pure reference protocol, **APPLICATION_NOT_AUTHORIZED**. No Carrot adapter,
controller hook, Params access, publisher, process or thread is implemented.

## Basis

PR #12 was merged at `b0de6b4032d587c818f3d47389ae1afc37f2009c`
on 2026-10-29T04:54:31Z using merge method and the exact head guard
`040b6500aeef47d486cf11895c1bca1b1b8e2282`. Its parents are main
`66f4b79036560a11e7020af9cc214118dcbd4fba` and that H3 head. H3 is an ancestor,
and the merge/head trees are equal. The guarded prerequisites were Open/Draft,
MERGEABLE, successful push and PR runs (12 checks), no unresolved threads, and
fresh independent Critical 0 / Important 0 / Minor 0. H4 starts from the merge.

PR #9 remains `6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5` and PR #8 remains
`e4361678ed176cbd7c0bb6f838d3daa7174caf22`, Draft/Open. PR #8's merge conflict
is separate maintenance. Neither is changed, rebased, merged or fixed by H4.

Source pins and the 55-file/95-claim H3 manifest remain unchanged:
runtime `c2130730239bcdb4cbde9361ab90c8d99aa4ff55`, tree-equal integration
`7a2f051b1f3847786318900444c88c2ba7a74a67`, current carrot-wip
`f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3` (rechecked, no movement), historical
Hoya `0e9c589c1b83027146f909a9cdc306c2c665ceaf`. No runtime pin is upgraded.

## Responsibility and authority

torqued, CyberPilot and manual/custom configuration supply proposals. An injected
independent authority selects/approves an exact proposal; the owner never compares
confidence scores or chooses a scientifically superior tuple. NN/GM are explicit
alternate modes, not implied compatible parameter families. The future owner is
the sole effective writer; LatControlTorque would be its consumer.

The reference package is `cyberpilot_autotune.owner_protocol`: immutable contracts,
pure ports, one in-memory cell and ReferenceTorqueParameterOwner. Construction
takes explicit identity, baseline, policy, clock, authority and port and invokes
none of their methods. initialize() explicitly admits the supplied coherent
baseline against the actual cell and independently reads it back.

AuthorityContext binds owner digest, exact operation digest, issue/expiry and
authorization identity. Those checks do not authenticate it: a separately trusted
Authority.approve capability must return exactly True. No production allow-all
authority, grant issuer or candidate generator is supplied. Evidence digests and
synthetic compatibility policies do not confer real application authority.

## Immutable logical data

| Contract | Content |
|---|---|
| TorqueParameterTuple | complete factor/friction/preserved-offset triple; finite float values |
| OwnerIdentity | version, source/integration, controller family, context digest, session generation, baseline epoch, non-identifying instance token |
| BaselineRecord | identity, full tuple, explicit revision anchor/mode/capture time/evidence and capture ID |
| InstalledTuple | actual cell's tuple, revision, identity, mode, installation time and commit ID |
| TorqueProposal | producer/generation/sequence/ID, source/context/epoch/base revision, full candidate, generation/expiry, evidence and required mode |
| CommitAck | prior/new revision, committed digest, owner identity, commit ID/time and state; no verified flag |
| TorqueOwnerSnapshot | independent actual values/revision/identity/mode/sample time/state/optional lease; tuple digest derived from values |
| OwnerLease | installed revision, producer/proposal, issue/expiry and baseline epoch |
| RecoveryResult | observed tuple/revision or None, verification result, reason/state and optional Ack |

All nested records are frozen and constructed from immutable values. Instance IDs
are caller-supplied non-identifying 32-hex session tokens, never VIN/device IDs.
The pure reference generates no random identity or wall-clock value.

Numbers are opaque finite Python floats retained losslessly. Canonical logical
identity uses deterministic JSON with nonfinite values prohibited and distinguishes
signed zero. No epsilon, clipping, units conversion, friction fitting, scale or
Float32 quantization is performed. Zero and either finite sign have no scientific
meaning assigned by this protocol. In particular, a zero factor may be logically
representable here while being unusable by a real linear controller.

LogicalParameterTuple is not EncodedControllerTuple. Native encoding/round-trip
policy remains **REPRESENTATION_ENCODING_UNRESOLVED**. Future encoding must be
qualified before authorization/digest formation; a target cannot silently round
an authorized value. H4 does not choose BINARY32_EXACT as a production policy.

## CAS, Ack and readback

Each successful mutating install replaces one full InstalledTuple and increments
the uint64-like revision exactly once. The MemoryTuplePort models one serialized
compare-and-swap boundary. This is semantic atomicity under the single-caller,
non-reentrant trusted-capability assumption; it is not thread safety, native
atomicity, lock-free proof or a GIL guarantee.

commit(expected_revision, proposal, authority_context) validates current actual
state, timing, producer/generation, replay, context/mode, revision, full tuple and
preserved offset, independent authorization, then rechecks state/time before
installation. A producer cannot displace a different producer's active lease.
All future producer writes must enter this boundary; a bypass is
EXCLUSIVE_OWNER_NOT_ESTABLISHED.

The port's returned revision is checked for exact +1 and the owner returns a
CommitAck. **Ack is not readback.** Call snapshot() separately to observe the actual
cell; it does not echo the proposal or modify revision/state/lease. A correct Ack
can coexist with a later readback failure, and a bad Ack can coexist with a correct
installed tuple. Neither is turned into a false VERIFIED receipt.

No-change consumes its proposal identity but returns None: no install, no revision
increment, no new/extended lease. The native PR #9 mapping must handle this
explicitly rather than manufacture a revision+1 acknowledgement.

## Replay and timing

Each permitted producer has one caller-supplied generation and a sequence
high-water. Proposal IDs encode that sequence. The immutable proposal digest binds
all fields. A structured failed proposal consumes the sequence before later
validation, so editing evidence/candidate/ID cannot revive it. The cache has at
most four producer lanes, independent of runtime length. Producer identity is
the composite producer/generation/session/sequence, not an unscoped string.

PR #9 already protects its application request stream. A future facade must bind
the same CyberPilot request sequence/session rather than invent a second producer
counter or duplicate its admission algorithm. This reference's bounded lane
defense models the multi-producer owner boundary only.

All times/durations are caller-supplied, finite, nonnegative logical monotonic
times; durations are explicit positive policy inputs. There is no wall clock,
default deadline or vehicle number. Mutating operations check for clock regression
against the last operation and check deadlines before/after capabilities. Forward
transaction and rollback budgets start before the initial port read, including
no-change/same-mode paths; a slow initial read cannot reset the operation budget. snapshot
does not update a clock high-water; supplying a monotonic read clock remains a
caller obligation, and PR #9 independently checks its own observation clock.

A lease ends at the earliest of proposal expiry, original proposal generation plus
maximum proposal age, authority expiry and caller maximum hold. Fresh watchdog
samples do not refresh the original proposal's age. Rejected/no-change proposals
cannot renew it. The proposal-age deadline is exclusive. Expiry prevents a new
commit and requires a recovery watchdog tick; it cannot be masked by a mode or
new proposal event. Recovery itself has a separate caller rollback deadline.
Direct rollback/disarm/stop also check the existing lease before restoration
and after readback: verified baseline does not erase an observed expiry fault.
maximum_lease_s is a post-commit-completion hold, matching the reference lease's
issued_at_s; the installation/verification interval has its separate transaction
bound. It is not a physical exposure limit measured from first installation.
Native policy acceptance must account for both intervals and absolute deadlines.
If a positive hold cannot be represented as an expiry later than the logical
clock sample, reject/fault rather than acknowledge an already-expired lease.
This is a numeric representability check, not a vehicle minimum duration.

## Baseline, recovery and restart

Baseline is a trusted caller-supplied coherent record, never a UI default, latest
torqued message, synthetic zero or cached estimate inferred into trust. Forward
commits preserve offset exactly; a new trusted baseline requires a new epoch.
rollback() supports only that original baseline, using known expected or exact
pending state, CAS, Ack checks and independent snapshot. It refuses foreign
tuple/revision/mode/identity. Missing readback returns None/unknown and FAULTED.

An install that succeeded before an exception remains a pending cohort. Actual
snapshot matching it proves that install occurred; actual original state proves
it did not. An unknown/foreign cohort is never guessed into ownership. A faulted
domain may make one explicit proven-cohort recovery attempt and remains FAULTED
even if baseline is observed. No automatic rearm or repeated recovery loop exists.

Normal disarm/stop verifies baseline before declaring a clean terminal state.
Mode transition while OWNED enters RECOVERING without installing another mode;
the tick/recovery returns to original baseline and closes DISARMED. A separate
explicit new epoch/session is needed for the requested mode. From baseline READY,
an authorized mode metadata transition increments once and closes DISARMED.

restart() is an explicit logical handoff from a terminal domain: new instance ID,
strictly greater session generation and baseline epoch, and a trusted new record/
port/policy. It never clears the old object's fault or restores a dead controller.
After complete memory loss, an external execution owner must supply fresh identity
and baseline; no in-memory object can detect a caller reusing an old identity
without retained external evidence. No persistence/global registry is introduced.

## Status and limits

Protocol readiness is scoped to the tested reference semantics. It does not close
H3's source-unit, encoding, vehicle-policy, runtime or scientific evidence gates.
The process execution model and its unresolved native acceptance are detailed in
[process ownership](shared_torque_owner_process_ownership.md). The
[state machine](shared_torque_owner_state_machine.md),
[failure model](shared_torque_owner_failure_model.md),
[PR #9 mapping](shared_torque_owner_pr9_mapping.md) and
[source sketch](shared_torque_owner_carrot_change_sketch.md) complete the design.
