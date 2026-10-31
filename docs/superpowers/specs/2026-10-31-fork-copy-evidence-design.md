# Managed-root fork-copy evidence — design and synthetic contract

Base PR38 `420538d7c20edcfca3eadf136b30b622ca2bede9`. The approved next task is
**design**, not a producer patch/build/guest experiment or an inventory adapter.
Answer what source records would identify each copied FD, without pretending the
whole namespace was copied at a single instant. Preserve every previous artifact.

## Selected approach

Author's choice under standing autonomy/question opt-out: retain source-local
bitmap/read/reference-or-clear/store witnesses in a new test-only synthetic
contract. Post-copy summaries cannot recover consumed reads; userspace joins cannot
recover them either. A future explicit copy context passed from copy_files into
the selected dup_fd walk is preferred. No such C/API/producer change this turn.
Inline implementation and one fresh final reviewer; own stacked Draft only.

The source is the exact PR38 patched Linux6.12.113 cohort, with pristine comparison:
fs/file.c,kernel/fork.c,include/linux/fdtable.h,fs/proc/cplife.c. Bind full bytes,
Git blob SHA1,ranges SHA256,archive/package and base source provenance. Existing
CPS records and assets are read-only references; they contain no per-slot receipt.

## Exact source semantics and future capture point

- sane_fdtable_size returns a BITS_PER_LONG-aligned exclusive scan bound; even
  an empty source returns NR_OPEN_DEFAULT=64 in this x86_64 profile. It is not the
  number of open FDs. dup_fd reads FDs ascending although its loop i counts down.
- Bitmap copy precedes individual pointer reads; copy_fd_bitmaps copies open and
  CLOEXEC bitmaps and clears the extension. File pointers are copied separately.
- file_lock excludes inspected close/replace/flag paths, not already-reserved
  lockless fd_install publications. Source namespace need not be unshared merely
  because the new operation makes a private copy. No atomic-cut claim.
- Each non-NULL read has get_file then destination store. NULL has clear-open-bit
  then destination NULL store. Clearing open_fds does NOT clear CLOEXEC bitmap.
  A stale copied CLOEXEC bit on NULL is not a live binding flag.
- Present with unavailable lifetime cookie is not NULL. Do not generate an OFD
  identity from FD,read ordinal,PID,pointer,expected fixture or matching None values.
- Remaining pointer tail is zeroed before result return. Selected64-slot/64-capacity
  contract has an empty tail; larger/resize/punch-hole profiles stay unsupported.
- Constructor completion is distinct from subsequent task commit or failure.
  Partial/failing/unpublished copies never become an installed child inventory.

Future copy context must carry a new source-issued copy-attempt ID,scope,actor,
child subject and old/new namespace identities. Child task allocation is before
copy_files; PR38 assigns the new namespace cookie only AFTER dup_fd. Thus a future
patch must deliberately issue/link a constructor cookie before the walk and retain
the same identity at completion,not invent a pre-walk identity after return. Failed
constructors and task aborts need terminal accounting. No added observer references,
global effect lock,probe attachment or code patch is provided here.

## Synthetic semantic envelope v1

New `tests/fork_copy_design/{model,audit}.py`; not installed or wired to old code.
Top-level closed fields: schema,evidence_class,context,events,accounting.
schema=fork-copy-evidence-design-v1;evidence_class=SYNTHETIC_ONLY.

Context closed fields: source_profile,source_sha256,fork_sha256,fdtable_sha256,
boot_scope,scope_id,copy_attempt_id,actor_task_id,subject_task_id,source_table_id,
destination_table_id,root_copy,clone_mode. Pinned source hashes; private-copy mode
only. Positive UInt64 identities,except unavailable actor/source table only for
the root-copy diagnostic; subject equals scope only for root. Non-root creator
must be present and differ from subject; namespaces differ. Task/table/OFD cookie
roles cannot collide; repeated OFD across FDs is valid aliasing. Copy-attempt ID
has its own namespace and is not a lifetime cookie or globally authenticated ID.

Events carry positive source-local **attempted emission ordinal** n, not wallclock
or kernel-effect ordering. Each stage has an exact closed field set:

| kind | extra fields | meaning |
|---|---|---|
| BEGIN | scan_bound,capacity |64/64 source walk declaration |
| BITMAPS | open_fds,cloexec |64 raw Bool-or-None entries each,actual copied bitmaps |
| READ | fd,presence,ofd |actual local pointer read;presence PRESENT/NULL/UNAVAILABLE |
| REFERENCE | fd,read_ordinal |existing get_file completed for that read,not an observer pin |
| CLEAR_OPEN | fd,read_ordinal |destination open bit cleared for NULL read |
| STORE | fd,read_ordinal,presence,ofd |actual destination pointer store,paired to consumed read |
| COPY_RETURN | result,tail_zeroed |SUCCESS/FAILED;Bool-or-None completion witness |
| TASK_FINALIZE | result |COMMITTED/ABORTED/UNAVAILABLE,distinct from copy success |

For a complete selected copy: BEGIN,BITMAPS,64 ascending READ→REFERENCE/CLEAR_OPEN→
STORE triples,COPY_RETURN,TASK_FINALIZE:196proposed records. n is unique/increasing;
gaps and loss never silently repaired. Empty source still scans64 slots. A source
open bit false with PRESENT read contradicts the selected locked bitmap profile;
reserved-but-unpopulated true+NULL is allowed and clears the child open bit.
NULL has no OFD,REFERENCE is forbidden; PRESENT may have None cookie but requires
REFERENCE. STORE must match read role/value; None==None never establishes object
lifetime equality. Raw CLOEXEC bitmap is kept; effective flag for NULL is None.

Accounting closed fields: attempted,reserved,committed,failed,discarded,pending,
each UInt64-or-None. Local equations plus received event count check consistency
only. The existing128-record buffer cannot fit even one196-record proposed copy;
two such copies plus separate18CPS records would be410 BEFORE extra framing or
failure records. No capacity change/empirical threshold/transport qualification.

`evaluate(data: object) -> Decision` uses strict bounded JSON-like validation and
defensive copy. Result frozen,slots tuple of frozen per-slot diagnostics. Unknown
is not zero/false/NULL. Complete known synthetic premises may be consistent;
missing/unknown/out-of-order/conflicting stages,cohort/role changes,abort or losses
produce reasons,not fabricated state. Canonical sorted-field digest is content
identity only. All output status BLOCKED,9permissions fixed false,global counts
None,atomic_cut_proven=False,runtime_producer_implemented=False.

## Deliverables and acceptance

Contract,capture architecture,result docs; neutral schema/source/case manifests;
pure evaluator and offline audit. Catalog explicitly SYNTHETIC_ONLY,never inferred
from PR38's37actual records. Reuse immutable6-schedule/1-no-cut presence witness
from PR36,which is a finite counterexample,not a kernel simulator/probability/proof.
Test complete/unknown/root/alias/reserved-NULL/stale-CLOEXEC,missing/swapped stages,
wrong read-store pairing,role collisions,source changes,task abort,loss/128buffer,
Bool/Float/overflow/unknown fields,digest/defensive-copy/no authority boundaries.

Run baseline/full regressions,pure coverage,ruff/format,mypy,build/fresh wheel,
CRLF,prior source/history/native audits,source optional checks,one fresh final
review and both exact-head CI events. Preserve src,compatibility,CI,all previous
tests/evidence/PRs and old4minors. No actual producer,kernel edits/build/boot,host
tracing,device,vehicle,Params,cereal/controller,estimator,candidate,application,
PR35/PR30 bridge,longitudinal,external AI or upstream PR. All existing blockers
remain. Recommend exactly one next task; this design does not qualify runtime.
