# Fixed guest per-slot fork-copy prototype

Base PR39 `4a04a5a38a68970624380c10113c97a752af4aa8`. Implement the approved next
prototype,not a qualified observer/inventory/estimator/application bridge. Preserve
all previous source,tests,evidence,PRs,compiled assets and main. Work on a new branch
and a fresh source/build prefix;never modify the preserved PR38 source checkout.

## Scope and architecture

Author's choice under standing autonomous inline execution: explicit diagnostic
copy context from copy_files to a task-aware dup_fd wrapper;ordinary other dup_fd
callers retain their original wrapper path. Issue a constructor allocation cookie
before the selected walk and retain it at post-copy TABLE_NEW;do not move the
successful-birth event early or issue a second cookie. Source task fields retain
only scalar copy-attempt/source/destination/local-ordinal context,not extra refs.
Clear inherited diagnostic fields at task allocation.

Read actual source-local f,existing get_file or clear-open,and destination store.
Capture actual copied new_fdt open/CLOEXEC words before per-slot reads. Preserve
unknown PRESENT cookies vs NULL and stale NULL CLOEXEC. No reread-as-consumed input,
no extra target refs or global effect lock. Saved scalar post-free evidence only.
Task-finalize COMMITTED is after last copy_process failure point;ABORTED at cleanup
before task destruction,using saved context even after its files were released.

New test-only `tests/guest_fork_copy`:pure observed wire codec/diagnostic,explicit
fixed VM runner,image builder,static PID1,complete standalone source patch/config,
offline original-byte/source/build auditor. No changes to installed src,old tests,
compatibility,CI,old evidence or PR39's SYNTHETIC_ONLY oracle. Do not relabel actual
records SYNTHETIC_ONLY or connect to that evaluator/PR35/PR30. Neutral actual
decoder uses its own source-bound semantics and preserves OBSERVED_UNTRUSTED class.

One vCPU,512MiB,QEMU TCG,no KVM/network/shared filesystem/passthrough/device or
arbitrary payload. Existing fixed root memfd/dup3/F_SETFD/nested-fork/close workload;
PID1 arms before root creation,waits,stops and dumps. Two copy attempts per guest.
Separate existing128 lifecycle diagnostic buffer and new512-slot preallocated copy
buffer,derived above2×196=392 normal copy records. Capacity is not qualification.

## Six fixed fresh-guest modes

NORMAL;READ_LOSS;SMALL_BUFFER;CONSTRUCTOR_FAIL;TASK_FAIL;ALLOC_FAIL.
READ_LOSS deliberately loses copy2local18 (FD5 READ) after attempted accounting.
SMALL_BUFFER limits copy buffer to128;it does not modify the lifecycle buffer.
CONSTRUCTOR_FAIL injects ENOMEM on copy2 after initialized allocation/BEGIN and
before bitmap copy,unlocks and actually frees constructor,records scalar ALLOC_FREE,
failed return and task abort. TASK_FAIL injects EAGAIN after copy_files success,
uses original cleanup path and records later task abort,not a committed child.
ALLOC_FAIL injects ENOMEM before copy2 allocator call,no destination ID/no BEGIN;
failed return and task abort remain explicit. These are operation-changing **fault
injections**,not natural error frequencies or passive/unperturbed runs. Driver checks
the expected syscall error and only then reports success. NORMAL has no injected
operation failure;instrumentation still perturbs layout/instructions/scheduling.

Expected source-derived normal copy records392;READ_LOSS391/1own failure;
SMALL_BUFFER128/264;CONSTRUCTOR_FAIL196+4=200;TASK_FAIL392;ALLOC_FAIL196+2=198.
Verify actual results,do not manufacture/patch logs to these expectations.

## Observed wire contract

New CPC prefix/version1/release6.12.113-cpcopy-v1,path/proc/cpcopy;old CPSv1 not
silently upgraded. Source frame metadata:case,release,CPU,copycapacity,copyattempt
count. Counter fields attempted,reserved,committed,failed,discarded,pending.
Events common fields n(global copy emission ordinal),copy(attemptID),local(percopy
attempted ordinal),kind,scope,actor,task,source,dest. IDs UInt64,0unavailable except
positive ordinals/copy/scope/subject. Field order irrelevant,exact closed key sets.

Payloads: BEGIN scan_bound/capacity;BITMAPS rawUInt64 open_fds/cloexec words;READ
fd/presence(PRESENT/NULL)/ofd;REFERENCE andCLEAR_OPEN fd/read_ordinal;STORE adds
presence/ofd;COPY_RETURN result(SUCCESS/FAILED),tail_zeroed(-1unknown/0/1),reason;
TASK_FINALIZE result(COMMITTED/ABORTED),reason;ALLOC_FREE reason (post-allocator,
saved context only). Root parent actor/source remain unavailable;nonroot creator
must be known. Per-attempt context cannot change between records. No pointers/PID/
wallclock/object-address identity. Separate lifecycle and copy ordinals are NOT a
unified effect order. No TSC accuracy claim or atomic copy inference.

Full successful grammar196records is the prior READ/ref-or-clear/STORE design,
now observed. Failure-before-BEGIN/partial/late-abort paths stay reasoned diagnostic,
not reconstructed child inventories. Source stop/RCU waits emitter sections only,
not all-source/global quiescence. Local balanced equations never imply global0.
Frozen partial captures and decisions;own-buffer counters numeric when observed,
global loss/prohibited counts None,all9permissions false,statusBLOCKED,atomic cut
and runtime qualification false. Unknown IDs/flags stay None,never0/false defaults.

## Verification and deliverables

TDD codec/runner/audit adversaries first. Compile new static driver and actually
boot old PR38 frozen kernel as missing/proc/cpcopy RED before new source hooks.
Fresh extract/build exact Linux6.12.113 archive with existing recorded tools/deps;
no host package/kernel/security changes. Actual six guests,complete original serial,
kernel/driver/config/patch/source/tools/image hashes,source ranges and offline replay.
Normal tests/audit never build or boot VM;only explicit fixed --execute-fixed cases.
Finite malformed/stage/cohort/role/NULL/unknown/pairing/sequence/loss/failure/width
tests,architecture guards,pure coverage98/95minimum,aim100/100,full old regressions,
ruff/format,mypy,build/freshwheel,CRLF,one fresh exact-head review,own stacked Draft
and both exact-head push/PR CI. At most one authorC/I TDDfixpass,no re-review.

Retain source/hook/owner/copy-cut/loss/perturbation/consumer/frozen-artifact/factor/
vehicle-bounds/runtime-fingerprint/watchdog/external-executor/application blockers
and prior4minors. No real vehicle,Params,cereal/controller/torqued,H6 estimator,
candidate,owner/application bridge,longitudinal,externalAI or upstream PR. Recommend
one next task,not automatic qualification or real application execution.
