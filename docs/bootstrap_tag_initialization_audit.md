# Bootstrap tag initialization / reuse boundary source audit

## Verdict and exact basis

**BOOTSTRAP_TAG_INITIALIZATION_SOURCE_AUDIT_COMPLETE**
**BOOTSTRAP_TAG_REUSE_PUBLICATION_BOUNDARIES_DOCUMENTED**

This is selected static source analysis,not C semantic verification,complete
allocation coverage,actual reuse testing or qualified identity history. Every
runtime qualification and operational permission remains false. No producer,
kernel patch,controller,schema,actual log or installed src changed in this audit.

Basis:PR42 exact `37c0e614f01e13b5e6078178b3712c0ec6ba4495`,not a Linux Git
revision. Exact Debian6.12.113 archive SHA256
`ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33`
plus unchanged PR42 patch SHA256
`3eed09131f6ce03dc4a489dfe161cd3d48576ba760abf0978d8846fd3edfc848`.
The new source manifest records9pristine/11patched full-file hashes and33inclusive
line ranges with SHA256/Base64. Git-blob SHA1 identifies bytes,not an upstream
commit or authenticity. Four unchanged repository artifacts bind the PR42 patch,
build,actual captures and source manifest.

## Selected path matrix

Claim IDs below resolve to exact path/start/end/hash/source bytes in
`docs/evidence/bootstrap_tag_initialization_sources.json`.

| Subject | Selected source relationship | What it does not establish |
|---|---|---|
| TASK | x86 duplicates task bytes;post-dup hook clears tag/copy fields before its active/clone gate | pre-hook failure coverage,final task destruction,general clone coverage |
| NAMESPACE | private constructor explicitly clears tags then assigns allocation origin before completion | shared/unshare coverage,fallback origin,backing-fdtable identity |
| OFD | normal zero-allocation/init precedes tag assignment;alternative allocators differ | complete allocator coverage,RCU lifetime identity,atomic tag publication |
| SEED | zero/tag-state checks preserve admitted aliases;abort retains partial assigned tags | protected all-mutator cut,complete allocation history |
| ISSUER | monotonic CAS issuer has a terminal zero-return guard;nonce is local annotation | execution at exhaustion/concurrency,authenticated unique boot identity |

### TASK — copy,reset,early failure and destruction

TASK_X86_DUP:`arch/x86/kernel/process.c:93-108` uses memcpy/memcpy_and_pad.
TASK_DUP_FAILURES:`kernel/fork.c:1126-1236` can free a copied task before
returning to the caller. TASK_ALLOC_CALL:`2254-2258` calls `cpl_task_alloc` only
after successful dup. TASK_RESET_GATE:`fs/proc/cplife.c:78-126` clears task
identity,scope,epoch,origin and copy bookkeeping before checking active/unsupported
clone flags. A supported managed child gets a fresh allocation tag;seeded PID1
does not become the managed root through its seed tag.

TASK_LATE_ABORT:`kernel/fork.c:2594-2726` distinguishes the pre-publication commit
call from later cleanup labels and scalar copy-finalization. This is a manual
control-path interpretation of pinned source,not proof from line ordering alone.
TASK_FREE:`596-624` finally frees task storage;it is not a CPB task-destruction
producer. TASK_FINALIZE means copy/task construction outcome,not final lifetime
destruction. Pre-hook dup failures are outside the new tag hook's observation.

STATIC_INIT_TASK:`init/init_task.c:65-222` is a static aggregate;new omitted
members have C static-zero initialization. TASK_LAYOUT pins the added fields.
That language property does not prove every dynamic task route is initialized,
nor prove compiler layout,publication,or concurrent-reader safety.

### NAMESPACE — object vs storage and unsupported context changes

NS_CONSTRUCTOR:`fs/file.c:315-445` allocates nonzeroed cache storage,explicitly
clears the four namespace tag fields,and invokes `cpc_allocated` after selected
constructor setup. NS_CPC_ALLOCATED assigns allocation origin before bitmap/FD
copy succeeds. An allocation tag is not constructor success or published namespace
birth. The final `fdt` pointer is separate from the files_struct object's tag.
The same range pins the ordinary `dup_fd(...,NULL)` context wrapper.

NS_ATTACH:`fs/proc/cplife.c:108-118` can fill a missing cookie and scope but does
not itself assign cpb_epoch/cpb_origin or issue a CPB origin witness. In PR42's
supported private path the earlier constructor hook already supplies them. Do
not generalize that to a qualified fallback or ignore an exhausted/missing tag.

NS_SHARED:`kernel/fork.c:1802-1831` shares the existing object for CLONE_FILES.
NS_UNSHARE:`3296-3310` calls ordinary dup_fd;NS_UNSHARE_EFFECT:`3458-3474`
changes the current task's files pointer. These are not an admitted CPB transition
protocol. Unsupported child-task scope reset does not erase the shared object's
existing tag or magically qualify its readers. NS_LAYOUT pins object fields,not
an identity for replaceable backing fdtable storage. Full resize/replacement and
all callers are not audited here.

NS_FREE:`fs/file.c:479-492` saves scalar identity/scope before releasing storage
and calls the legacy callback afterward. NS_STATIC_INIT pins the static zero
aggregate. Legacy CPL shadow callbacks are not newly exported CPB end-of-lifetime
receipts and cannot be silently joined into complete CPB history.

### OFD — allocation variants and the publication gap

OFD_INIT:`fs/file_table.c:175-206`;OFD_NORMAL_ALLOC:`218-258`:the normal route
uses kmem_cache_zalloc,initializes the file,and calls cpl_file_birth before return.
The claim is about these selected source calls,not a complete allocator/config
proof. The f_count-last comment applies within init_file;tag assignment is later.
It must not be read as publication of an atomic cookie/scope/epoch/origin tuple.

OFD_NOACCOUNT:`261-284` and OFD_BACKING:`295-326` use zero allocation but do not
call the same birth hook. Their comments restrict these routes to kernel-internal
use and say the files must not be installed in file tables. This is a source
coverage distinction,**not evidence that PR42 captured an untagged user FD through
these routes**,nor evidence that the fixed driver exercises them.

OFD_FREE:`88-102` saves scalar fields before free and calls afterward without
passing the freed target pointer. That selected callback relationship does not
give CPB complete destruction or reuse coverage. OFD_LAYOUT pins changed fields
and OFD_CACHE pins the SLAB_TYPESAFE_BY_RCU cache/freeptr offset. Old cacheline
comments are not measured post-patch ABI/layout results;perturbation remains open.

RCU_REUSE_WARNING:`include/linux/slab.h:91-142` explicitly says object storage can
be reused within the same grace period. OFD_RCU_REVALIDATE:`fs/file.c:888-928`
uses a reference and pointer revalidation for that kernel reader. This audit does
not add those operations to CPB. ORIGIN_READ/COPY_RAW_READ pin CPB's separate raw
tag scalar reads. RCU or one CPU is not an object-lifetime/atomic-tuple proof.
Release/acquire in the record buffer or issuer does not publish the target tuple
as one atomic value. A safe generalized read protocol is still missing.

### SEED and ISSUER — partial state is not complete history

SEED_WALK:`fs/proc/cpcopy.c:113-191` requires empty tag context,checks actual
pointer/tag state,accepts an already admitted FIRST_OBSERVED alias,and rejects
other tag state rather than overwriting allocation provenance. These checks and
file_lock do not exclude every external mutator/outstanding install.
SEED_ABORT:`187-191` unlocks/emits failure without rolling back assigned tags.
Those partial tags must not be reused as evidence of a successful full seed or
allocation history. One-shot/reseed restrictions do not prove a protected cut.

COOKIE_STORAGE/COOKIE_CAS:`fs/proc/cplife.c:26-48` pin static zero counter and
CAS issuance. At all-ones the function returns0 without intentional wrap/reuse.
The last nonzero issuance,all call sites' exhaustion behavior,concurrent ordering
and compiler/architecture arithmetic semantics were not dynamically tested by
this task. Zero is unavailable,not an authenticated identity or a system-level
proof of safe failure. Serialization of numbers does not stabilize object storage.

COHORT_NONCE:`fs/proc/cpcopy.c:32-71` pins random local nonce generation and
one-shot mode preparation. Neither random bits nor content hashes prove unique
boots,freshness,authenticity,anti-replay or cross-boot identity. Cookie0/epoch0
cannot be silently replaced with a default valid identity.

## Exactly thirteen retained source-boundary obligations

TASK:PRE_HOOK_DUP_FAILURES_UNOBSERVED;TASK_FINAL_DESTRUCTION_UNOBSERVED;
UNSUPPORTED_CLONE_SCOPE_UNQUALIFIED.

NAMESPACE:UNSHARE_AND_SHARED_CONTEXT_UNQUALIFIED;
FALLBACK_NAMESPACE_ORIGIN_INCOMPLETE;
BACKING_FDT_REPLACEMENT_NOT_NAMESPACE_IDENTITY.

OFD:NONSTANDARD_ALLOCATOR_HOOK_COVERAGE_INCOMPLETE;
RCU_OBJECT_REUSE_IDENTITY_UNQUALIFIED;TAG_TUPLE_PUBLICATION_UNQUALIFIED.

SEED:ALL_MUTATOR_SEED_CUT_UNPROVEN;ABORTED_SEED_TAGS_RETAINED_NO_HISTORY.

ISSUER:ISSUER_WRAP_EXHAUSTION_RUNTIME_UNTESTED;COHORT_NONCE_AUTHENTICITY_UNQUALIFIED.

## What the verifier actually verifies

`python -m tests.bootstrap_tag_audit.audit` checks frozen metadata,embedded
excerpt bytes/claimed line counts,closed citation/obligation cohorts and unchanged
PR42 repository artifact bytes. It does not check external full kernel files.
It does not parse/execute C,prove the prose,validate package freshness or qualify
any runtime. `external_source_bytes_verified` is false in this mode.

Explicit paired source roots additionally verify9pristine/11patched full-file
sizes/SHA256/Git-blob SHA1 and actual selected range locations/bytes:

```sh
python -m tests.bootstrap_tag_audit.audit \
  --pristine-root /workspace/scratch/bootstrap-tag-reference.TFNmZc/linux-source-6.12 \
  --patched-root /workspace/scratch/guest-bootstrap-producer.O8Npmg/linux-source-6.12
```

Even when external bytes match,all13obligations remain open. The pure `assess`
factory is the validated construction API;it defensively copies rows into frozen
tuples. Direct unchecked dataclass construction is not an admission API. Report
digests identify content only. No collector/writer/network/process/build/VM is
implemented. This task ran no new guests and did not reclassify any old actual
capture as static or synthetic evidence.
