# Guest syscall/task/exec/FD collector design

Base `1b2ff21ac83a8ea9d7c04850c8e2f7e92d06425d` (PR27). User requests the
previously recommended next implementation and has delegated ordinary design
choices/inline execution. This is a designer-selected architecture, not a claim
that the user chose its mechanism. No repeated design interview is required.

## Intent and boundary

Capture actual kernel syscall stops, task birth/exec/exit and FD transitions for
the same fixed harmless guest fixtures. Close PR27's missing observation layer,
not its device, source-closure, watchdog or application qualification blockers.
No old receipt/evidence/checker is promoted or rewritten. A capture is UNTRUSTED
until externally bound; even complete capture of a named profile grants nothing.

Use the already approved QEMU10.0.13 TCG guest, Debian
`6.12.113+deb13-cloud-amd64`, source `6.12.113-1`, original VM digest
`d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c`.
Rootless host compilation only; ptrace/procfs/cgroup/BPF operations only in the
derived device-free guest. Same fixed regular-file payloads, no arbitrary command,
native/model/Carrot/controller/Params/service/vehicle, network or passthrough.
Guest console/null bootstrap nodes remain bootstrap metadata, not device tests.

STRICT_NO_DEVICE_ATTEMPT. Gate A BLOCKED; B/C/D not started. All runtime/device/
policy/candidate/application/owner permissions false. Global prohibited-handle/
effect counts remain unknown: syscall/FD recording alone proves neither complete
filesystem effects nor absence of all device acquisition. No estimator bridge.

## Approaches considered

1. BPF syscall enter/exit plus lifecycle hooks: low perturbation, but actual
   `kernel/entry/common.c:28–74` puts seccomp before trace_sys_enter. ERRNO
   rejections can skip that hook. It cannot be the complete entry observer.
2. **Selected:** independent C17 ptrace collector, PTRACE_SYSCALL and
   PTRACE_GET_SYSCALL_INFO, fork/vfork/clone/exec/exit events, stopped-task procfs
   FD snapshots and typed USER_NOTIF ioctl receipts. Ptrace entry precedes seccomp
   in this exact source. PTRACE_O_EXITKILL plus the existing outer QEMU boundary
   provides recovery, not a qualified watchdog. More scheduling perturbation is
   acceptable for synthetic observations, never a vehicle timing measurement.
3. Userspace preload/string-log tracing: cannot cover static/direct syscalls and
   does not provide typed FD/request provenance. Rejected.

Existing independent LSM/cgroup guard and old immutable fixture binary remain
unchanged. The collector starts a fixed `/harmless-fixtures HFxx` under tracing
before exec and follows all children. It never changes registers, syscall
arguments/results, seccomp policy or filter generation. It records signal
delivery rather than interpreting ENOSYS as termination.

## Capture contract

New repository-only `compatibility/containment_guest_collector/`. Pure immutable
events/evaluator separate from opt-in runner and guest C. No imports from the
installed package, application or owner code. Existing PR27 files are frozen.

Wire version `guest-syscall-fd-v1`; one named fixture per capture. Records have
strict keys `kind,seq,mono_ns,task,tid,image,values`. Values are immutable integer
tuples with kind-specific lengths/ranges; no floats, arbitrary mappings, NaN or
implicit defaults. Prefix `TRACE_EVENT `; explicit TRACE_BEGIN and TRACE_END
envelopes bind version/fixture and observation clock. Observation timestamps are
`GUEST_TRACER_OBSERVATION_MONOTONIC_NS`, **not kernel execution timestamps**.

Kinds: BIRTH(parent generation, clone flags), ENTER(call id, audit arch, syscall
nr, six args), RETURN(call id, signed result), ABORT(call id, signal), EXEC(old
tid), FDS(call id, count, repeated fd/flags/dev/inode/mode/mount-id), NOTIFY_RECV
(call id, request id, target tid, flags, nr, arch, listener fd, six args), ADDFD
(call id, request id, flags, source fd, requested new fd, new-fd flags, result),
NOTIFY_SEND(call id, request id, value, errno, flags, result), SIGNAL(sig, code),
PRE_EXIT(raw status), EXIT(raw wait status), ERROR(errno, phase).

Task identity is capture content identity plus monotonic birth generation, not
PID alone. Exec generation increments only on actual PTRACE_EVENT_EXEC. All live
TIDs must be unique. Fork/clone events bind a child before its first execution.
Initial trusted SIGSTOP/tgkill completion is an explicit seed boundary, outside
the first measured entry. Fork child return without a child entry is an explicit
birth completion, not a fabricated pair. Successful exit syscalls and killed
blocked calls have explicit terminal/abort semantics, not invented returns.

FD0 is valid. Sorted actual FD tables include flags, type, device, inode and
mount id, with lifetime/generation derived from acquisition/close/dup/fork/exec
events. Inode alone is not durable identity. Unsupported shared FD tables,
nonleader exec, syscall ABI, acquisition or unexplained mutations reject FD
profile completeness. Unknown is not zero. Do not retain duplicated pipe FDs in
the collector: that would alter EOF and the experiment.

Capture actual USER_NOTIF RECV/ADDFD/SEND ioctl input/output and IDs; join with the
target generation and pending syscall. Successful donation must match the source
FD generation and target returned FD/table; stale/canceled requests cannot become
deliveries. Original caller arguments and broker-private copied/open arguments
remain separate. No CONTINUE or unscoped retry may be added.

## Evaluation and completeness

`parse_capture(raw: str) -> Capture` validates and defensively freezes records.
`evaluate_capture(capture: Capture) -> CaptureAssessment` independently checks
sequence, clock ordering, birth/exec generations, call pairs/aborts, terminal
closure, FD transitions and notification pairing. `capture_digest` is canonical
content identity only. `capture_complete` and `fd_profile_complete` are separate;
complete means only this declared native-x86_64, independent-file-table, named
fixture profile and capture window. Unsupported/unknown evidence rejects rather
than silently excluding a task or syscall. Shared-thread/general hostile-payload
proof is not implied. External collector authenticity remains unqualified.

Begin/end counters must reconcile with parsed events, all born tasks actually
reaped and no live or pending task/call remains. Duplicate/dropped/reordered,
future clock, wrong result/exec generation, missing terminal and FD reuse tests
must reject. Collector loss produces incomplete capture, never a zero verdict.
Original HF raw assertion checks remain separate and must still pass.

## Assets, publishing, non-goals

Reuse immutable prior inputs by verifying their manifest/cohort. New fixed guest
image/runner pins only the new collector and frozen fixture assets. No host
fallback, runtime downloads, implicit all-fixtures or arbitrary payload argument.
Default pytest/CI performs pure tests only; fresh wheel excludes this package.
Exact source/package/range hashes and build recipe are recorded before guest load.

Exercise all24 HF fixtures and added synthetic adversarial capture mutations.
Publish actual per-case capture summaries plus lossless raw capture artifact,
retaining incomplete reasons. Do not overwrite PR27 evidence or convert it to
PASS. Full pytest, lint/format/mypy, build/fresh wheel, historical source audits
and passive offline native regression, then one independent final review.
Append-only new branch/Draft stacked on PR27; no merge/rebase/force push or prior
PR edits. Stop after handoff; no device or native execution automatically follows.
