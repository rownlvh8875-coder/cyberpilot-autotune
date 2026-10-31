# Bounded observed per-slot fork-copy contract

This is a test-only disposable-guest prototype, not a qualified lifetime producer,
atomic inventory or controller/friction receipt. Base PR39
`4a04a5a38a68970624380c10113c97a752af4aa8`; no old source/evidence is changed.
Actual records remain `OBSERVED_UNTRUSTED`, never passed to the prior
`SYNTHETIC_ONLY` copy oracle. No PR35 semantic adapter or PR30 qualified bridge.

## Capture and source semantics

The standalone ten-file patch targets exact Debian Linux6.12.113. A task-aware
`dup_fd_for_task` wrapper is used only by private `copy_files`; ordinary callers
retain the non-observed wrapper. A constructor cookie is assigned after allocation
initialization and before the selected walk. Successful `TABLE_NEW` retains that
cookie later; failed construction never emits a successful namespace birth.

After the final source-table lock reacquisition, record `BEGIN`, the actual copied
destination open/CLOEXEC bitmap words, and each actual local pointer read, existing
`get_file` or clear-open branch, and destination store. No observer reference or
new global target-effect lock. Tail memset and callback return are separate from
later task commit after the last `copy_process` failure point. Failure records
use saved scalars after actual allocator free and before task destruction. New
task allocation clears inherited diagnostic context. No pointer/PID identity.

The selected one-vCPU512MiB TCG guest runs only the fixed memfd/dup3/F_SETFD/
nested-fork/close driver. No network, KVM, shared filesystem, passthrough, vehicle,
host tracing or arbitrary workload. PID1 opens its control/read descriptors before
arming, waits for root, stops and dumps. Stop plus RCU drains emitter sections,
not all-source/global activity. Instructions/layout/scheduling are perturbed.

## CPC v1 wire

Release `6.12.113-cpcopy-v1`, `/proc/cpcopy`, CPC prefix/version1. A completed frame
contains driver/meta/count/event/end/exit rows. Closed keys, UInt64 bounds, UTF-8,
2MiB original bytes, at most512 copy records, exactly2 copy attempts; unknown
version/stage/profile rejects. Field order is irrelevant. CPS lifecycle output is
retained in original serial but belongs to a different event/counter domain.

Common event fields: global **copy emission** ordinal `n`, copy-attempt ID `copy`,
per-copy attempted ordinal `local`, scope/actor/task/source/destination cookies,
and stage. These are not kernel-effect linearization or a unified CPS/CPC order.
No timestamps are emitted in CPC. Root parent/source are unavailable, not inferred.

| Stage | Exact payload |
|---|---|
| BEGIN | scan_bound, capacity |
| BITMAPS | raw UInt64 open_fds, cloexec |
| READ | fd, PRESENT/NULL, OFD cookie |
| REFERENCE / CLEAR_OPEN | fd, paired read_ordinal |
| STORE | fd, paired read_ordinal, presence, OFD cookie |
| COPY_RETURN | SUCCESS/FAILED, tail_zeroed, reason |
| TASK_FINALIZE | COMMITTED/ABORTED, reason |
| ALLOC_FREE | reason; saved scalar context after allocator free |

Wire cookie0 means unavailable, decoded `None`, never an actual ID. PRESENT with
unknown OFD is distinct from NULL. NULL cannot have a known OFD. Raw stale CLOEXEC
bits for NULL slots survive; effective binding CLOEXEC is `None`. Tail `-1` means
unavailable, distinct from observed0/1. Tasks/namespaces/OFD roles cannot collide.
Copy context is immutable, non-root creator source must match the previous
committed task's recorded namespace. Missing/gapped sequences are not reconstructed.

## Diagnostic meaning and loss

`parse_serial` returns frozen immutable values; `assess` reports complete recorded
mechanical sequences and slots, not complete object identity or ownership.
The fixed196-record complete grammar is BEGIN/BITMAPS,64×READ/branch/STORE,
successful tail/return, then task-finalize. Abort/partial/lost sequences stay
diagnostic; no resulting child inventory is admitted.

Attempted = reserved + failed; reserved = committed + discarded + pending.
All are copy-buffer-local. Emission ordinals are attempted before fallible
reservation. Balanced equations do not erase gaps or prove global zero loss.
Separate512-copy/128-lifecycle buffers; SMALL_BUFFER limits only copy to128.
All decisions remain BLOCKED, atomic_cut_proven/runtime_qualified false,
actual_global_drops/actual_prohibited_operations `None`, all9permissions false.

## Deliberate modes and evidence

NORMAL has no injected operation error. READ_LOSS drops copy2local18 (FD5 READ)
after attempted accounting, not the target read. SMALL_BUFFER is real own-buffer
exhaustion. CONSTRUCTOR_FAIL injects ENOMEM after initialized allocation/BEGIN,
before bitmap copy, and really unlocks/frees. TASK_FAIL injects EAGAIN after
successful copy_files, then takes original cleanup with task abort. ALLOC_FAIL
injects ENOMEM **before allocator call**, not a natural allocator-returned failure.
Driver checks expected errors. No passive/transparency or error-frequency claim.

Audit binds original serial base64/size/hash, independent pre-hook literal raw-wire
goldens, six images, frozen build/source inputs, selected file/blob/range hashes.
Digest is byte/content identity, not authenticity or authority. Default audit
does not run guests/build/network; explicit source roots verify57 selected ranges
in7pristine/10patched files, not whole-source or hook-coverage proof. Explicit
asset verification checks prepared binaries/archive/package/tools/deps/QEMU;
distribution signatures/freshness are inherited prior preparation, not re-proven.
Runner execution is an explicit fixed-case opt-in only.

No schema/controller/Params/estimator/application changes, owner proposals, candidate
generation, external AI, longitudinal changes or upstream PR. No new threshold,
vehicle fingerprint, trusted baseline or operational permission follows.
