# Bounded inherited-OFD provenance design

Base PR40 `21a542eba9e889323b2cb1b7d7c75d9c9cab1025`. Approved next task is
**design**, not another source producer implementation. Preserve all prior files,
actual captures, compiled/source assets, old PRs and main. New branch
`design/inherited-ofd-provenance`; new test-only pure premise checker and audit,
semantic schema/cases/source manifests and design/result documents only.

## Intent and selected approach (author's choice under standing delegation)

PR40 records per-slot copy effects but root-parent and pre-arm OFDs have no observed
birth. Distinguish identity continuity from allocation-history completeness.
Alternatives: always-on boot lifecycle instrumentation could witness selected
births but widens hook/boot/overhead scope and still needs coverage proof; retaining
all unknowns is honest but gives no future bounded continuity design. Select a
**separate, explicitly FIRST_OBSERVED pre-arm bootstrap** plus later consumed-copy
links, never retroactive allocation birth. Neither rejected alternative is built.

Future architecture: after the fixed PID1 driver opens all control/stdio inputs,
before first managed fork, issue typed first-observation handles for actual parent
task, source files_struct and observed struct file objects. This is NOT TASK_ALLOC,
TABLE_NEW or FILE_NEW. Object-local diagnostic tags with immutable origin and
boot/issuer epoch avoid a pointer-address identity map; aliases reference the
same object tag, distinct opens stay distinct. Existing allocation-issued handles
must not be replaced. No extra observer references. Tag initialization/reuse,
publication synchronization and all-mutator exclusions are prerequisites, not
proven here. file_lock, one CPU and PID1 identity do not prove quiescence.

Bootstrap issuer identity is separate from managed-root scope: seeding PID1 must
not accidentally enroll it as the managed root/descendant in PR40's existing
scope gate. New wire/profile and explicit root-selection logic are required.
No patch, wire tags, new buffer size, bootstrap records or empirical claims now.

## Pure executable premises

`tests/inherited_ofd_design/model.py`: `evaluate(data:object)->Decision` accepts
only `inherited-ofd-provenance-design-v1`, `SYNTHETIC_ONLY` JSON-like values.
Frozen defensive results; canonical content digest only, no authority/authenticity.
Top fields schema,evidence_class,context,objects,copy. Context source_profile,
source_revision,source_manifest_sha256,boot_scope,issuer_epoch,record_domain.
Exact source pin/base above, proposed profile `PR40_PRIVATE64_BOOTSTRAP_DESIGN`,
record domain `PROPOSED_LINEAGE_V1`; source manifest binds PR40 selected sources.
Non-identifying boot/issuer tokens1..64 ASCII alnum/underscore/hyphen.

Objects (max68): cookie,role(TASK/NAMESPACE/OFD),generation(only0),origin
(FIRST_OBSERVED/ALLOCATION),stage(PRE_ARM_SEED/POST_INIT_ALLOC),ordinal,
boot_scope,issuer_epoch. Positive UInt64 unique global cookies; duplicate/reused
or role-colliding handles reject. Seeds precede arm; allocations after arm and
before copy begin. One origin per handle; seed is never promoted to birth.
These are synthetic declared witness stages, not verification of real allocation.

Copy: parent_task,source_namespace (each optional),child_task,destination_namespace
(destination optional only for failed construction),arm,begin,returned,finalized,
return_result,return_reason,task_result,task_reason,bindings. Strict same-domain
ordinals arm<begin<returned<finalized; ordinals are proposed program-record ordering,
not global effect linearization or a merge of old CPS/CPC domains. Referenced
handles must have the right role and precede consumption. All four task/namespace
handles distinct when available. Positive IDs required; unavailable is None,not0.
New fork child and available private destination require ALLOCATION/POST_INIT_ALLOC;
PRE_ARM_SEED is allowed only for pre-existing parent/source/OFD references.

Bindings max64,ascending unique fd0..63,closed fields fd,presence,source_ofd,
destination_ofd,read,branch,branch_ordinal,branch_read,store,store_read. Local
begin<read<branch_ordinal<store<returned; strict sequential nonoverlap between rows.
Branch/store reference exact read ordinal. PRESENT needs REFERENCE; NULL needs
CLEAR_OPEN and no OFD. Known source/destination OFDs must be equal and declared
OFD role; missing values remain unavailable,never filled from the other side.
Aliases may use the same OFD. Distinct OFDs stay distinct even for equal file data.
No inode/path/PID/address/content identity fields. Binding list is a partial
synthetic lineage example,not full inventory/bitmap/flags/copy receipt proof.

SUCCESS requires reasonNONE; COMMITTED requires successful return and reasonNONE.
ABORTED after success requires TASK_INJECTED/TASK_FAILED; failed construction
requires ALLOC_INJECTED/CONSTRUCTOR_INJECTED/NATURAL_ALLOC and aborted COPY_FAILED,
with no bindings. Aborted/failed examples never produce committed links.

Decision: premises_consistent,reasons,unavailable,origins,linked_fds,digest.
Links only for committed successful copy, known parent/source and equal known OFDs;
all are **synthetic conditional links**, never observed admission. Origins preserve
FIRST_OBSERVED even when linked. Fixed evidence_classSYNTHETIC_ONLY/statusBLOCKED,
allocation_history_complete=false,runtime_producer_implemented=false,
actual_global_drops/actual_prohibited_operations=None,all9permissions=false.
Empty/unknown examples may be consistent but never prove execution or completeness.
Coherent fabricated premises remain undetectable; no cross-receipt state machine.

## Evidence, source and verification

New semantic schema and finite adversarial catalog; audit pins canonical manifests,
repository/source file/blob/range hashes. Default offline, optional explicit source
root checks selected PR40 source bytes only. Never ingest/relabel PR40 actual
captures, alter prior decoders, build/boot VM, install host packages or trace host.
TDD unknown/seed/birth/alias/different-OFD/NULL/cross-role/cohort/generation/reuse/
pairing/ordering/abort/Bool/Float/resource/class/authority attacks. Pure coverage
98%statement/95%branch minimum,aim100. Full regressions,old audits/native192,
ruff/format/mypy/build/freshwheel/CRLF,one fresh independent final review,one author
C/I RED→GREEN pass maximum,no re-review;own stacked Draft and exact-head push/PR CI.

No change to PR35 lifetime admission/PR30 bridge or current seed-unaware CPCv1.
Retain identity-history/hookcoverage/copycut/loss/perturbation/consumer/friction/
artifact/factor/vehicle/runtime/watchdog/executor/application blockers and all9false.
Prior4minors unchanged. No vehicle,Params,controller/cereal,estimator,candidate,
application/owner,longitudinal,externalAI,upstreamPR or oldPR modifications.
