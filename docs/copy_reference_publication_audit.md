# Copy-local reference and tag publication source audit

## Scope and evidence level

Exact CyberPilot base PR45 `5581049957088b348498eb5ef0b1061f76d19b7c`.
Exact source is Debian linux6.12.113-1 with unchanged PR42 patch
`3eed09131f6ce03dc4a489dfe161cd3d48576ba760abf0978d8846fd3edfc848` and PR45 delta
`78bada7bb59500a6c25d9d5e691867eccb27a3e7e5f10b9e958d8e2a308777f2`.
Archive SHA256 `ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33`.
No source patch,old contract/decoder,actual capture or qualification is changed.

The source catalog embeds31exact byte ranges across12kernel/source-document
files and3cited repository files,plus3repository provenance references. File
SHA256/Git-blob IDs and range SHA256 identify bytes,not C semantics,authenticity,
freshness or a complete build. Citations below use catalog claim IDs.

All conclusions are STATIC_SOURCE_AUDIT_ONLY/BLOCKED. The11source facts/conditional
arguments and19retained duties are reviewed metadata,not results of a C parser,
LKMM checker,compiler proof or actual-record admission engine.

## 1. Caller,slot and existing reference

```text
copy_files: current->files → oldf
  → copy_fd_for_context(oldf,tsk)
  → oldf->file_lock; old_fdt loaded/reloaded under that lock
  → local f = rcu_dereference_raw(*old_fds++)
  → pointer-presence marker only
  → existing get_file(f)
  → saved = cpt_take(f)
  → destination rcu_assign_pointer(...,f)
  → emit saved scalars by value
```

CALLER_COPY_FILES (`kernel/fork.c:1802-1832`) supplies current's table to the
private-copy path. CLONE_FILES takes a different shared-table branch. This is a
source fact,not a runtime attestation of table ownership or supported actor scope.
ACTOR_SCOPE_GATE independently restricts diagnostic tagging;passing through an
ordinary VFS function is not proof that every diagnostic route is supported.

COPY_LOCK_RELOAD and FDTABLE_LOOKUP show the existing old-table lock and fdtable
lookup. The resize path drops the lock during allocation,then reacquires it and
reloads the fdtable/bound. It does not keep the old pointer across that unlocked
window. COPY_LOCAL_REFERENCE (`fs/file.c:398-440`) shows the *same consumed local
f* passed to get_file,cpt_take and destination STORE:there is no cookie lookup,
replacement observer reference or pointer reconstruction.

The ordinary VFS argument is conditional on a live owned old table,valid slot,
correct lock and ordinary refcount invariants. The loop's own comment says
existing files cannot disappear while the lock is held,although lockless
fd_install can add a pointer during the walk. FD_REMOVE_LOCK and FD_REPLACE_LOCK
show selected removal/replacement paths under that lock;TABLE_RELEASE shows a
different final table-release path tied to table refcount ownership. These are
supporting source routes,not an exhaustive proof of every remover or table owner.

GET_FILE_RELAXED (`include/linux/fs.h:1125-1130`) uses
atomic_long_fetch_inc_relaxed and warns on prior zero. It is not an
increment-unless-zero/revalidate operation or a standalone acquire-publication
barrier. It relies on a valid existing object at the call site. RCU_REF_REVALIDATE
and VFS_REFERENCE_RULES describe a *different* lockless lookup/reuse protocol
with ref/pointer revalidation. Its guarantees must not be borrowed for this loop,
nor does this audit prescribe substituting it into the existing copy operation.

Thus the source-local pointer/reference window is visible,with ordinary VFS
protection conditional on its invariants. No actual receipt carries an attested
old-table/lock/reference lifetime witness;source_binding_qualified stays false.

## 2. Initialization/publication is a separate question

| Route | Conditional source argument | What is still needed |
|---|---|---|
| Normal pre-install file | zalloc/init plus active-scope birth writes precede return;matching fd_install publishes pointer | exact publication/read dependency,valid object,no later unguarded writers |
| Seeded already-published file,same namespace lock | seed writes before unlock,then copy acquires the exact same lock | actual same-lock/namespace identity,writer completion and exclusion |
| Alias/other namespace or other writer | no all-writer guard established by this audit | separate binding/ordering/exclusion witness;no automatic handoff |

NORMAL_ALLOCATION and NORMAL_TAG_WRITER show alloc_empty_file's zero allocation,
initialization and scope-gated tag writes. FD_INSTALL_PUBLICATION uses
rcu_assign_pointer;RCU_PUBLISH documents ordering for initialization *before*
that store. RCU_RAW_LOAD and RCU_DEPENDENCY_RULES describe pointer-load address/
data dependencies and compiler restrictions. These support a conditional
pre-install argument,not proof that the entire instrumented writer/read path
preserves every required dependency or that tags remain stable forever.

SEED_WRITER updates tags of files already in a table. An earlier pointer release
cannot retroactively order later tag writes. A different argument may apply:
SAME_LOCK_HANDOFF documents visibility across release/acquire of the *same lock*.
If seed writes complete under exactly the lock subsequently acquired by copy,
that lock handoff is relevant. Namespace cookie equality alone does not attest
lock-object identity,exclude ABA,or order writers through another alias/table.

PID1,single userspace thread,files count1,one CPU,seed walk completion and emitter
drain are not all-alias/all-mutator closure proofs. Seed writes remain separate
from historical allocation;aborted seed tags and unsupported allocation routes
retain their prior obligations. OFD_NOACCOUNT_ROUTE explicitly warns its kernel
internal objects must not be installed;it is scope counterevidence,not permission
to declare complete allocation-hook coverage.

All-tag-writer closure,exact after-publication guards,alias exclusion and compiled
dependency preservation remain open. publication_qualified stays false.

## 3. Capture,transfer and membership are distinct

COPY_LOCAL_REFERENCE and SNAPSHOT_RAW_HELPER show capture after the existing
reference call and before destination transfer. SNAPSHOT_EMITTER consumes the
saved structure by value after STORE;it does not re-read f tags. This source
stage separation is supported,not a proof of atomic tuple sampling,compiler
behavior or temporal/runtime witness completeness. COPY_CONTEXT_FIELDS and
PR45_FIXED_PROOF_FLAGS show why operation IDs/available source joins are not
measured lifetime/publication/membership witnesses.

An object reference protects a different concept from its membership in a
namespace/FD slot. OFD_CACHE_REUSE and RCU_REF_REVALIDATE explain why address or
refcount observations cannot substitute for reuse/generation evidence. An
OFD's seeded raw scope0 also must not be overwritten conceptually with a later
managed task's nonzero scope. Cookie issuance/nonce are not identity
authentication. Membership generation and exact source witnesses stay unavailable.

## 4. Object→saved→buffer→wire→decoder type flow

| Field | Object declaration | Saved / buffer | printf | Decoder | Probe's fake object |
|---|---|---|---|---|---|
| raw_cookie | u64 | u64 / u64 | %llu | UInt64 | u64 |
| raw_scope | u64 | u64 / u64 | %llu | UInt64 | u64 |
| raw_epoch | **u64** | **unsigned int / unsigned int** | %u | UInt64 | **unsigned int** |
| raw_origin | u8 | unsigned int / unsigned int | %u | enum0/1/2 | unsigned int |

OFD_TAG_LAYOUT (`include/linux/fs.h:1075-1082`),SNAPSHOT_RAW_HELPER
(`include/linux/cptagread.h:1-20`),BUFFER_TAG_TYPES,WIRE_OUTPUT,
PR45_DECODER_EPOCH and PR45_STANDIN_EPOCH pin each boundary.

The source object's cpb_epoch is u64. Initializing the saved unsigned-int member
can narrow it before later by-value buffering or %u output. On the fixed x86_64
ABI's32-bit unsigned-int model,a hypothetical object epoch2^32 would become0.
This is a conditional language/representation illustration,not a measured guest
value,a new compiler/layout proof or evidence of actual capture corruption.

The selected source assignments use0/1 and PR45's recorded observed epochs fit
that domain. This audit does not parse/reclassify those records. It does not prove
that every allocator/reuse/writer path enforces the closed domain. Therefore the
audit identifies possible source-to-saved narrowing and leaves actual_epoch_loss
None and epoch_range_invariant_proven false.

The previous native scalar unit's stand-in file already declares cpb_epoch as
unsigned int. It tests scalar copy/retention for that stand-in;it cannot detect
the real object's u64→unsigned-int boundary. Its passing result was never a
Linux-layout/type-fidelity proof. Separately,PR45's deferred minor allows the
decoder to accept UInt64 epochs impossible for the current unsigned-int/%u
producer. Tightening the decoder alone cannot recover bits lost before emission.

Cookie/scope have a declared u64 width-preserving chain;origin is declared
widened from u8 before enum checks. Neither fact establishes actual atomicity,
all-writer invariants,valid logical identity or runtime admission.

## Verification and next prerequisite

`python -m tests.copy_reference_audit.audit` checks embedded ranges and repository
refs. Optional `--source-root /exact/PR45/patched/tree` additionally checks all12
selected full kernel/source-document files and their ranges. Default external
verification is false. Hash checking never proves the reviewed source meanings.

Existing regressions,including their unchanged controlled-layout native unit,
and Python wheel checks may run their ordinary temporary tooling. No new kernel/
producer build,compiler type probe,guest/device/vehicle execution or old-file fix
is performed by this source audit. All nine permissions/proofs remain false,
global counts and actual epoch loss None,all prior blockers/minors retained.

Next single task:**lossless raw-epoch representation correction design**. Specify
the source/saved/buffer/wire/decoder domains and required versioning before a
separate producer patch. It must not silently reinterpret CPRv1,repair old captures
from expectations,or qualify lifetime/publication. No such design/patch starts here.
