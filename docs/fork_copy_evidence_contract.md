# Fork-copy per-slot evidence contract — synthetic design only

Base PR38 `420538d7c20edcfca3eadf136b30b622ca2bede9`. No producer,wire decoder,
kernel patch/build/boot or inventory adapter is delivered. The pure oracle lives
only in `tests/fork_copy_design`. Its records are **SYNTHETIC_ONLY** and are never
reconstructed from PR38's37actual CPS records. Source/schema/case manifests are
separate from actual cereal or kernel wire schemas.

## Question and source profile

For one private copy,which local pointer did each loop iteration read,reference
or clear,and store? This is narrower than asking for an atomic source-table
snapshot,complete object ownership,an installed child inventory or a qualified
observer. A matching final table does not recover the inputs actually consumed.

Exact profile: PR38 patched Debian Linux6.12.113,x86_64,BITS_PER_LONG64,private
copy through copy_files→dup_fd with no punch_hole and64destination slots. A private
copy result does not prove the source files_struct had no other sharers. Larger
tables,resize execution,CLONE_FILES result,unshare,exec and general kernel profiles
are not admitted by this finite oracle. Their effects are unknown,not absent.

[Source references](evidence/fork_copy_design_sources.json) bind3pristine and
4patched files,36ranges,whole-file SHA256,Git blob SHA1,archive/package hashes and
the exact base. Optional source verification reports patched and pristine checks
separately; without roots it does not claim their local bytes were checked.

## Exact distinctions

- ROUNDED_SCAN_BOUND: sane_fdtable_size rounds the exclusive FD bound to a machine
  word. Empty returns NR_OPEN_DEFAULT=64,not0. The loop counts i down but reads
  FD0..63 up.64 is a range,not the count of open descriptors.
- BITMAP_COPY: open/CLOEXEC bitmaps copy before per-slot pointers. NULL_CLEAR_NOT_CLOEXEC
  clears open/full bits only. A NULL slot may retain a raw copied CLOEXEC bit1;
  it has no live binding CLOEXEC flag. Tail bitmap clearing and pointer clearing
  are different source operations.
- ASCENDING_READ_REFERENCE_CLEAR_STORE: PRESENT requires existing get_file before
  its store; NULL requires clear-open before its NULL store. REFERENCE records
  the kernel's existing copy reference,not an extra observer pin.
- LOCKLESS_INSTALL: holding file_lock excludes the inspected close/replace/flag
  paths,not already-reserved lockless fd_install. Reserved true+NULL is valid;
  a later publication can change a later copy read. Bitmap false+PRESENT contradicts
  this selected locked-bitmap/inspected-mutator model,not a universal memory theorem.
- TASK_LAST_FAILURE_BEFORE_COMMIT: constructor return is before later copy_process
  failure points. A complete tentative copy can still belong to an aborted task.

| Pointer observation | Lifetime cookie | Destination open bit | Effective binding CLOEXEC |
|---|---|---|---|
| PRESENT,known | positive source cookie | copied open bit,unknown preserved | copied CLOEXEC only when open bit known true |
| PRESENT,unknown | None,not absence | copied open bit,unknown preserved | known/None,never evidence of object identity |
| NULL | None,actual absent pointer | false after observed CLEAR_OPEN | None,even if copied raw CLOEXEC bittrue |
| UNAVAILABLE | None | not derived | not derived |

None==None is not lifetime equality. The local read ordinal pairs a STORE with
its consumed read; it is not a new OFD identity. No identity from FD,PID,pointer,
memory address,matching values,fixture expectations or post-hoc table hashes.

## Neutral synthetic envelope

Closed fields: schema,evidence_class,context,events,accounting.
Schema `fork-copy-evidence-design-v1`,class `SYNTHETIC_ONLY`. Exact field/type/unit/
availability semantics are in [neutral schema](evidence/fork_copy_design_schema.json).
No actual tag numbers or producer are provided. Future wire should preserve
UInt64 identities/ordinals,UInt32 FDs/bounds,enums,presence and explicit nullable
Bool/identity fields. Never use zero to fill missing source-issued identities.

Context includes exact source/profile/boot-scope labels,source-issued scope,
copy-attempt,actor task,child subject,source/destination namespace IDs,root/private
branch identity. Copy-attempt has its own ID namespace. Other lifetime cookie
roles cannot collide; repeated OFD across several FDs is valid aliasing. The root
may have unavailable armer/source namespace,which remains diagnostic. A non-root
creator cannot be erased. Local boot labels are not authenticated cross-boot IDs.
Synthetic IDs are symbolic premises,not issuer attestation or a complete allocation
history;the oracle does not infer historical chronology from their numeric magnitude.

Each event has source-local attempted emission ordinal n,not wallclock or a global
kernel-effect position. The successful finite grammar is:

BEGIN → BITMAPS → 64×(READ → REFERENCE-or-CLEAR_OPEN → STORE) → COPY_RETURN → TASK_FINALIZE

That is196proposed records,including196even for an empty source. Exact key sets,
stage order,ascending FDs,read pairing,pointer values,bitmap availability and
source/cohort checks reject substitutions. An unavailable read never chooses a
default branch. Missing/partial/aborted records stay diagnostic,never repaired
from expected event counts. Constructor failures before a full walk cannot pass
this successful-copy grammar; a future producer must retain their own explicit
attempt/failure records instead of treating them as no-effects.

COPY_RETURN SUCCESS/FAILED and TASK_FINALIZE COMMITTED/ABORTED/UNAVAILABLE are
separate. A returned copy is not task publication. Slots returned in a rejected
diagnostic,including abort/unknown accounting/unknown OFD,are **tentative synthetic
constructor data**,not an installed inventory. Even a consistent synthetic result
is not runtime evidence and cannot feed a PR35/PR30 adapter.

## Accounting and current evidence gap

attempted=reserved+failed;reserved=committed+discarded+pending;received=committed.
All counters UInt64-or-None. Explicit zero differs from unknown. Nonzero failure,
pending/discard,inconsistent equations,unknown counters or missing ordinals reject
consistency. Balanced local counts cannot detect a wholly omitted hook or coherent
fabrication. Actual global loss/prohibited-operation counts remainNone.

The current128buffer cannot hold even one196-record proposal. Two copies plus
separate18CPS records would be410before extra framing/failure metadata. This is a
derived design budget,not an observed count,safety threshold or permission to
enlarge a buffer. No transport change or losslessness qualification occurs here.

PR38 has task/root/namespace creation and18normal lifecycle attempts,not BITMAPS,
READ,REFERENCE,CLEAR_OPEN,STORE,copy-attempt IDs or task-abort receipts. Do not adapt
its TABLE_NEW or TASK_COMMIT into invented per-slot evidence. The semantic wire
version is separate; current CPSv1 is not silently upgraded.

## Pure evaluator and limits

`evaluate(data: object) -> Decision` validates strict bounded JSON-like premises,
defensively copies,returns frozen decisions and a tuple of frozen slot diagnostics.
Unknown fields,nonfinite/bool-as-int/float-as-int/overflow identities,unsupported
profiles and malformed stages reject with reasons. Sorted canonical digest gives
content identity only; it is not authentic,anti-replay,sealed,qualified or authorized.

Always: status BLOCKED,atomic_cut_proven=False,runtime_producer_implemented=False,
9operational permissions false,actual global countsNone. No collection,background
process,network,application/owner/estimator import or installed runtime dependency.
The reused6abstract reader/writer schedules include1copy with no matching source
presence state. The other5 do not prove atomicity; neither schedules nor outcomes
are observed Linux runs,probabilities or a complete memory-model simulator.

Offline: `python -m tests.fork_copy_design.audit`.
Optional read-only sources: `--kernel-source <patched-root> --pristine-source <root>`.
No audit/test/import builds or boots a kernel. All prior blockers and PRs remain.
