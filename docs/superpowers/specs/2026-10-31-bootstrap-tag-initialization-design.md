# Bounded bootstrap tag initialization / reuse source audit

## Intent and authority

Audit PR42 exact `37c0e614f01e13b5e6078178b3712c0ec6ba4495` without
changing its source,producer,decoder,actual captures or qualification. The user
approved the previous next single recommendation and delegated inline execution
without routine question/approval gates. Implementation choices below are the
author's calls,not user-supplied requirements.

Answer which selected source paths initialize,inherit,assign and retain tags,and
which reuse/publication/exhaustion obligations remain open. A source hash or a
source-level observation is not a lifetime/identity/safety proof.

## Approaches and selected scope

1. Prose-only audit: smallest,but source drift/citation mixups are not checked.
2. Frozen source/citation matrix plus offline read-only validator: selected;
   machine-check exact provenance and conservative report without runtime changes.
3. New kernel hooks and reuse stress guests: supplies additional dynamic evidence
   but changes the producer and exceeds this audit's boundary. Not selected.

Use existing Python3.12 test-only architecture. No new installed package or
dependency. No fresh kernel build or VM execution: no kernel/runtime input changes.
This costs no new dynamic reuse/race/exhaustion evidence.

## Source and observation boundaries

Exact Debian6.12.113 archive SHA256
`ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33`
plus unchanged PR42 patch SHA256
`3eed09131f6ce03dc4a489dfe161cd3d48576ba760abf0978d8846fd3edfc848`.
Read patched source `/workspace/scratch/guest-bootstrap-producer.O8Npmg/linux-source-6.12`.
Extract only nine selected pristine files into a fresh durable reference prefix;
never edit existing producer assets or another plan's workspace.

Selected pristine files:fs/file.c,fs/file_table.c,kernel/fork.c,include/linux/fs.h,
include/linux/fdtable.h,include/linux/sched.h,init/init_task.c,
arch/x86/kernel/process.c,include/linux/slab.h. Patched source adds
fs/proc/cplife.c and fs/proc/cpcopy.c. No complete-tree/hook-closure claim.

Freeze full-file size/SHA256/Git-blob SHA1 and exact inclusive line range/SHA256/
Base64 excerpts. Default offline audit checks embedded bytes and frozen catalog;
only explicit paired pristine/patched paths check external source bytes. Neither
mode executes,compiles,parses C semantically or proves the prose interpretations.
Repository records bind PR42 patch/build/actual/source manifests unchanged.

Prior actual records remain OBSERVED_UNTRUSTED and are never reclassified as
STATIC_SOURCE_AUDIT_ONLY or SYNTHETIC_ONLY. This new report describes source
analysis only;PR42's ten runs are not fresh runs for this task.

## Five subject groups and thirteen retained obligations

- TASK: x86/weak shallow copy,dup failures,post-dup reset before gate,late failure,
  final destruction,static initialization. Retain PRE_HOOK_DUP_FAILURES_UNOBSERVED,
  TASK_FINAL_DESTRUCTION_UNOBSERVED,UNSUPPORTED_CLONE_SCOPE_UNQUALIFIED.
- NAMESPACE: explicit constructor reset,allocation tag before completion,private
  attach/fallback,shared/unshare,free/static init. Retain
  UNSHARE_AND_SHARED_CONTEXT_UNQUALIFIED,FALLBACK_NAMESPACE_ORIGIN_INCOMPLETE,
  BACKING_FDT_REPLACEMENT_NOT_NAMESPACE_IDENTITY.
- OFD: init_file and normal zero-alloc/tag order,noaccount/backing alternatives,
  scalar free,cache layout,RCU identity revalidation warning. Retain
  NONSTANDARD_ALLOCATOR_HOOK_COVERAGE_INCOMPLETE,RCU_OBJECT_REUSE_IDENTITY_UNQUALIFIED,
  TAG_TUPLE_PUBLICATION_UNQUALIFIED.
- SEED: zero/tag-state guard,alias reuse,abort retention,raw tag reads. Retain
  ALL_MUTATOR_SEED_CUT_UNPROVEN,ABORTED_SEED_TAGS_RETAINED_NO_HISTORY.
- ISSUER: static counter,exhaustion guard/CAS and direct nonce/cohort capture. Retain
  ISSUER_WRAP_EXHAUSTION_RUNTIME_UNTESTED,COHORT_NONCE_AUTHENTICITY_UNQUALIFIED.

The exact citation sets are defined in the implementation plan and closed model.
Catalog rows use subject,citations,open_obligations only. Missing/extra/duplicate/
cross-subject citations or obligations reject,never silently produce a complete
report. Valid source references do not close any obligation.

## Pure model and offline audit

`tests/bootstrap_tag_audit/model.py`:
`assess(rows: Any, available_claims: frozenset[str]) -> BoundaryAudit`.
Frozen defensive-copy subject/citation/obligation tuples;no I/O. Fixed
STATIC_SOURCE_AUDIT_ONLY/BLOCKED;initialization_qualified,reuse_qualified,
publication_qualified,issuer_runtime_qualified,allocation_history_complete,
atomic_cut_proven,runtime_qualified and all nine permissions false. Global
drops/prohibited None. A report digest is content identity,not authority.

`tests/bootstrap_tag_audit/audit.py`:
`validate(pristine_root: Path|None=None,patched_root: Path|None=None) -> dict`.
Closed finite manifests,duplicate/nonfinite JSON rejection,canonical digests,
embedded range checks,paired optional external bounded file reads,repository
byte verification and report rendering. No writer/network/process/build/VM.

New docs/evidence/bootstrap_tag_initialization_{sources,result}.json and
docs/bootstrap_tag_initialization_{audit,result}.md. No old file edits except
two narrow .gitattributes rules for new exact-byte files.

## Verification and publication

TDD before each model/audit implementation. Source tamper,range swap,wrong blob,
rehashed catalog changes,missing/extra/duplicate/cross-cohort citations,malformed
types,authority flags and partial source roots are negative cases. Frozen output
cannot mutate if caller changes input lists. Default audit requires no local
kernel/assets. Explicit audit verifies paired selected source files.

Full pytest,old source/history/input/lifetime/PR42 audits,native192,replay4,
ruff/format/mypy/build/fresh vanilla/research wheel and CRLF clone. Aim pure
model statement/branch100/100,minimum98/95. Source/C runtime coverage not claimed.
One fresh whole-branch independent review,one author C/I RED→GREEN fix pass;
defer minors and publish all rulings/costs. Own stacked Draft PR against
feat/guest-first-observed-bootstrap,append-only commits,exact-head push/PR CI.
Preserve all29existing Open/Draft PRs and maina5d3514f. No merge/shared writes.

## Non-goals / retained blockers

No kernel/source/producer/schema/controller mutation,VM/device/vehicle execution,
host probes,Params,estimator qualification,candidate/application/owner bridge,
PR8/9 modification,longitudinal,external AI or upstream PR. Existing lifetime,
hook closure,cut,loss,perturbation,inventory,PR35/30,frozen development artifact,
vehicle bounds,runtime fingerprint,watchdog,executor and application blockers
remain. Prior deferred five minors remain unchanged.
