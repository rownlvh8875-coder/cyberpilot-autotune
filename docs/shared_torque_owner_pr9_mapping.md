# H4 mapping to preserved PR #9 SteeringTarget

PR #9 is unchanged at `6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5`.
Its exact ports/contracts/coordinator are indexed by the unchanged H3 source
manifest. No PR #9/application module is imported, copied or implemented here.

The reference owner is **not a drop-in SteeringTarget adapter**: its explicit
proposal/authority/Ack API models the future concrete owner underneath that port.
The mapping below defines obligations for a separately reviewed facade.

| Requirement | H4 reference definition | Remaining native status |
|---|---|---|
| coherent snapshot | immutable full triple from actual memory cell, independent of Ack | SOURCE_CHANGE_REQUIRED |
| owner identity | version/source/integration/family/context/session/epoch/token | SOURCE_CHANGE_REQUIRED |
| scope | no application scope/permission inferred by reference | STILL_BLOCKED |
| context | explicit source/context/mode/generation checks | SOURCE_CHANGE_REQUIRED |
| baseline epoch | explicit trusted BaselineRecord; restart changes epoch/session | SOURCE_CHANGE_REQUIRED |
| sample timestamp | caller monotonic read time; no revision/read-side state change | SOURCE_CHANGE_REQUIRED |
| revision | uint64-like explicit anchor, +1 install, no wrap | SOURCE_CHANGE_REQUIRED |
| expected-revision CAS | full immutable memory-port comparison/replacement | SOURCE_CHANGE_REQUIRED |
| atomic selected tuple | one complete logical install; no partial update API | SOURCE_CHANGE_REQUIRED |
| revision+1 Ack | immutable CommitAck, independent of readback | SOURCE_CHANGE_REQUIRED |
| independent readback | snapshot observation separate from mutation/Ack path | SOURCE_CHANGE_REQUIRED |
| unrelated preservation | reference owns only triple; exact offset preserved | SOURCE_CHANGE_REQUIRED |
| exclusive ownership | serialized owner boundary, active producer exclusion | SOURCE_CHANGE_REQUIRED |
| rollback | trusted original baseline, expected/pending cohort, CAS and exact readback | SOURCE_CHANGE_REQUIRED |
| deterministic failure semantics | rejection vs uncertain/foreign/fault/terminal outcomes tested | SOURCE_CHANGE_REQUIRED |
| watchdog execution | explicit tick while owner alive; native death containment not qualified | STILL_BLOCKED |

The logical semantics of each row are **PROTOCOL_DEFINED**. Source-required or
still-blocked labels are separate; protocol definition is not native implementation
proof. Snapshot's epoch/context are contained in its immutable owner identity;
source-context and optional lease are not reconstructed from Params or wire age.

## Future facade shape and transaction binding

PR #9 expects snapshot() -> TargetSnapshot and commit(expected_revision, values)
-> int. The future facade must be private to one serialized application session,
bind policy/source/context/epoch/scope, and reserve ordinary writers **before core
construction**, including its READY state. The core fixes `_expected` to its
trusted original baseline; torqued cannot silently update it between attempts.

For a forward call, a trusted per-invocation context must bind the exact already
authorized PR #9 request/sequence, qualified proposal and grant to the owner
operation. No "latest proposal" lookup, invented authority token or confidence
ranking can supply this. The owner Ack's new_revision must match expected+1, then
the core calls snapshot independently. No production facade is added in H4.

For recovery, the only permitted target is the original baseline from the known
owned/pending cohort. The facade must preserve expected revision and map a
successful reference recovery's Ack, followed by independent core readback. It
cannot give general callers an authorization-free baseline setter. A grantless
internal recovery capability is restricted to that original baseline, not a path
to install arbitrary proposals. A malformed or late recovery stays faulted even
if a later observation happens to see baseline.

Reference no-change returns None, with no revision/lease renewal. PR #9 bypasses
commit for ordinary no-change and for already-restored recovery. A facade must
not convert an unexpected None into fake expected+1. This is a compatibility
condition for a future adapter, not a signature-equivalence claim.

Reference signed-zero/canonical logical identity is stricter than ordinary Python
numeric equality. PR #9 may compare -0.0 and +0.0 equal; the concrete facade must
still preserve untuned bits/canonical identity under the approved representation.
Float32 native encoding remains REPRESENTATION_ENCODING_UNRESOLVED; no target-side
rounding after grant formation can be represented as verified exact application.

## What the reference does not duplicate

The reference does not implement observation admission, scientific qualification,
confidence/sample/speed gates, vehicle bounds/step/rate policy, request generation
or PR #9's application coordinator. Its fixed per-producer generation/sequence
high-water is the owner replay boundary. The future CyberPilot lane must use
the preserved core's session/sequence identity rather than reassigning IDs after
a core rejection. Research exports and H2 descriptors remain non-authoritative.

## Approval gates retained

Factor/friction global equivalence, identification/independent confidence, trusted
vehicle baseline, actual runtime/fingerprint, approved bounds/rates/deadlines,
native encoding and outside-process watchdog acceptance remain unresolved.
H4's logical model makes no parked/runtime acceptance or application claim.
