> Frozen original design-time specification. Current implementation/test results are recorded separately; design-only wording below is historical, not this branch's execution verdict.

# H preparation read-only capture boundary — design v1

2026-11-04 KST. Exact base7422a868a5802ab49b496429448795e88c4de074,
tree14154790b5379280c2b24cdd50cde6e9a7a35229. PR61's diagnostic mapper IS implemented.
THIS pack is a new,not-implemented capture design. Do not confuse the two dates/scopes.
No current source/ref/PR/index/config/workflow changes and no collection or H execution.

## Intent and completion boundary

For each of the existing132 gaps,identify who could observe it,at what boundary,
which context and evidence must accompany it,and what remains unavailable now.
There are130 H value slots and2 producer streams,not132 currently measured values.
The target's other142 rows are static schema/registry configuration,not observations.
All132 remain unfilled by this task. This catalog is NOT a record with nulls stuffed
into required fields. No PreparationProfileRecord or H DTO is constructed.

Existing supplied-claim comparator and preflight mapper stay separate and unchanged.
Neither can obtain actual provider ownership,enforcement,consumed-source provenance
or capture atomicity by matching supplied strings,booleans,hashes or synthetic tests.

## Approaches — author's delegated choice

1. Expand saved preflight/posthoc topic joins:reject. Source process facts and job IDs
   do not identify an H workload;there is no actual consumed-source or ownership cohort.
2. Put all capture in an outside polling sidecar:insufficient as primary source.
   It may read diagnostics but cannot know the exact applied context or pre-release gate.
3. SELECTED:provider/supervisor-local capture at the actual consumption/control boundary,
   emitting a coherent evidence packet to a separate read-only offline inspector.
   This accesses owned generation-bound contexts and records before/after events together.
   Cost:couples capture to a reviewed future provider/bootstrap/supervisor;none exists now.

Read-only means the observer does not configure limits,move processes,release the gate,
launch/kill/reap,install/fetch,write subjects or authorize anything. The future provider
owns such operations under separate reviewed scope. Observation outputs stay in memory;
any bounded evidence transport/persistence is separate,not an application writer.
No polling loop,thread,global singleton,background service or generic plugin API is proposed.

## Source families and current availability

| Family | Target slots | Required primary source |
| --- | ---: | --- |
| H run identity | 1 | provider-owned H attempt identity,not Actions run ID |
| prepared artifact contents | 11 | complete prepared content plus independent review binding |
| installed policy content | 1 | exact canonical policy bytes actually consumed |
| consumed O/D and command cohorts | 10 | trusted source/bootstrap consumption receipts |
| batch/command boundary context | 21 | retained provider-owned handle identity/generation/domain |
| approved AND applied limits | 54 | reviewed policy + applied readback + enforcement witness |
| monotonic command timing | 18 | actual supervisor command events in one explicit clock domain |
| control observations | 14 | specific measured control/review evidence + execution-context binding |
| producer status streams | 2 | this producer's actual success/error/unavailable reporting path |

Catalog132rows and closed witness roles are normative. The metadata-only future slice
has273 required witness slots:132 baseline+11 artifact review+108 extra limit witnesses
+14 control context witnesses+8 additional per-command O/D consumption bindings.
This is a coverage requirement,not273 executed tests
or proven effects. No current H values or witness payloads are supplied.

## Capture architecture and phase semantics

PREPARED_BINDING:bind exact existing content/review records to this attempted cohort.
The original artifact may predate H;the binding event is not its creation timestamp.
Do not replace unavailable complete toolchain/dependency/syscall/collection/expectation
inventories with current files,pyproject ranges,S-only source hashes or AST import lists.

BOUNDARY_READY and LIMITS_APPLIED:after a separately authorized provider has prepared
an exclusive batch/command boundary,capture actual retained-handle references and readback.
The observer cannot create an ownership generation from path/PID/inode/W_OK equivalence.
Zero generation can be real data;unknown is None. Same-UID/ABA/kernel attacks remain open.

PRE_RELEASE:record placement,outer bootstrap boundary and effective FD/control context
before any historical payload/import/plugin. The supervisor,not this observer,owns the
release decision. A gap or known contradiction must not be converted to an observed True.

COMMAND_START/COMMAND_FINISH:actual trusted supervisor events bind command/cohort/attempt,
consumed inputs,run/policy generation and monotonic start/deadline semantics. A wall timestamp,
API log date,source-local timeout or observer's later clock sample is not a substitute.
Deadline uses checked actual_start+approved_duration in the same domain,not double correction.

CONTROL_WITNESS/BATCH_FINISH/PRODUCER_STATUS:bind effect and cleanup evidence to the same
owned epoch and attempt. Retain the first error and later cleanup uncertainty together.
No global process scan,numeric-PID fallback,or observer-initiated cleanup is permitted.

These phase names classify future observations,not an implemented execution state machine
or automatic transition mechanism. A memory-only receipt is one coherent packet,not a claim
that all kernel/topic reads were physically simultaneous. Record the complete capture window,
source sequences and immutable source-packet identities;atomicity remains NOT_ESTABLISHED.

## Context and source identity

Run ID is a32lowerhex opaque H run token supplied by the future provider. It is never
generated from branch,wall clock,Actions metadata,Python object ID or memory address.
Policy SHA256 identifies exact canonical installed content,not authorization or authenticity.
Each command attempt has its own registered command ID,UInt64 attempt,boundary digest and
generation. Source IDs identify producer instances;event IDs identify immutable source packets;
sequence/timestamp identify exactly consumed events,not merely latest-seen messages.
One source event is a single-context logical event. A multi-context provider packet
requires separately registered subevent identities/sequences and unambiguous parent
packet binding;the validator never invents or splits them from a caller's label.

An event reused for multiple witness roles must have identical source ID/sequence/event ID,
timestamp,stage,context and packet digest. Different metadata at the same source+sequence,
or one event ID aliasing different source events,is a contradiction. Repeated target+role
is malformed even if identical. Different sources may have independent sequences.
None never equals zero/False/empty;known negative/error claims survive missing context.
Known peer run/policy/domain contradictions reject even if the root epoch is unavailable.
Shared event IDs compare each known identity/context/content component;one missing
component never conceals a different proven conflict. Window/source-time/stage ordering
only compares known matching clock domains;unknown stays unavailable and different
known domains reject as clock mismatches,not invented elapsed-time failures. Root
begin/end still describe one asserted window,so its known reversed order is invalid.

No cross-run,policy,command,attempt,boundary-generation or clock-domain pooling.
Prepared material gets an explicit current consumption binding;do not assert that its
original preparation and runtime observation were one atomic transaction.

## Limits and controls — values are not guessed

Each54limit slot needs APPROVED_LIMIT,APPLIED_LIMIT and ENFORCEMENT_WITNESS evidence.
These do not assert policy equals observed hard enforcement without the mechanism witness.
CPU quota/period is not lifetime CPU usage. CPU accounting needs independently justified
latency/overshoot semantics. Scratch bytes AND inodes and combined retained output need
aggregate mechanisms,not per-process RLIMIT substitutes. All numeric H budgets stay absent.

For each control,catalog names the specific required effect. In particular W_OK=False,
NNP/Seccomp flags,native API presence or S toy results cannot fill H controls.
toolchain_closure_reviewed and expected_inventory_separately_frozen require real separately
reviewed content plus binding to what H consumed;the observer cannot self-certify them.
provider_guard_compatible requires the actual credential-free guard configuration and
observed compatible provider behavior,without reading,dumping or hashing secrets.

producer_errors/unavailable require the producer's real reporting stream;absence of a log
does not become an empty successful tuple. A lost/failed channel stays unavailable/failed.
The current target's coarse producer codes cannot encode all detailed source provenance.
A separate evidence packet is therefore required;no wire-v1 semantics are reinterpreted.

## Privacy and trust

No VIN,dongle/route/GPS/driver identity,raw CAN/images/model output,hostnames,credentials,
raw environment,cgroup paths,raw PID/UID/GID/FD numbers or model/vehicle inference.
Opaque non-identifying content/context digests only. Digests can still be linkable;
they are not anonymization,authenticity,independent custody or blanket DLP guarantees.
Any future local handle reader needs a separately reviewed bounded API;none is added now.

## Buildable next slice versus blocked runtime producer

The architecture requires future provider/bootstrap/supervisor source hooks whose exact
implementation bytes do not exist. No source range or working kernel producer is invented.
Full effectful H producer implementation remains BLOCKED by the inherited policy/content/
inventory/budget/provider/ownership/guard/authority prerequisites.

The narrow next software slice is only a pure supplied-provenance bundle validator,
defined in capture-contract.json and implementation-plan.md. It checks closed catalog
coverage,event/cohort consistency and explicit missing/negative metadata. It has no source
reader,H-target constructor,application import,collector,clock,thread,IO or release capability.
Even a complete result is COHORT_METADATA_CONSISTENT,never observed or H-qualified.
This is intentionally not marketed as implementation of the capture producer.

Future scope is proposed10new/2modified paths from this exact head;old helper bytes,
rawrange/untracked checks and frozen inventories remain independently checked. No scope
change occurs in this design task. Details are in scope-proposal.json.

## Status and non-goals

H_PREPARATION_CAPTURE_BOUNDARY_DESIGN_READY is a design-only verdict subject to builder check.
H_PREPARATION_RUNTIME_PRODUCER_NOT_IMPLEMENTED and H_PREPARATION_RUNTIME_POLICY_UNAVAILABLE
remain. All9permissionsfalse;content_identity_only=true;H_executed/integrated_admission=false;
source_capture_atomicity=NOT_ESTABLISHED. All inherited blockers from current registration,
including operationalI1/original-hostGit-config equality and APPLICATION_NOT_AUTHORIZED,remain.
No actual collection/H/O/D execution,vehicle,Params,controller,cereal/schema,estimator,
candidate/application/owner/longitudinal/upstream work,privileged fallback or infrastructure purchase.
