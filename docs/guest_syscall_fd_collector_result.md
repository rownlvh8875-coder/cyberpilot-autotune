# Guest syscall/task/exec/FD collector

2026-10-30 (Asia/Seoul). Base PR27 head
`1b2ff21ac83a8ea9d7c04850c8e2f7e92d06425d`.

## Scope and interpretation

This implements the user's approved next recommendation: a separate collector
for the **same fixed harmless software guest**, not a Carrot/vehicle/native
execution permission. Ordinary architecture decisions were delegated to the
author. Existing fixture binary, read-only broker, LSM/cgroup guard, old checker,
old evidence, installed source and existing CI are unchanged.

The new evidence kind is `UNTRUSTED_CAPTURE_REPORT`. `capture_complete` means the
observed native-x86_64 syscall entry/return-or-abort, task birth/exec/exit ledger
closed for this declared window. `fd_profile_complete` additionally reconciles
stopped-task FD tables and the supported acquisition/duplication/close/exec/
notification profile. Neither flag authenticates the collector or qualifies
general containment, complete source/loader closure, watchdog behavior, device
enforcement, native compatibility, empirical identification or application.

Global prohibited-handle/effect counts remain **null**, never0. Every runtime,
device, policy-adoption, candidate, application and owner permission stays false.
STRICT_NO_DEVICE_ATTEMPT remains; discovery proposal not adopted; Gate A BLOCKED,
B/C/D not started. PR27's six UNAVAILABLE/fifteen REJECTED/three NOT_SUPPORTED
reports are immutable historical reports and are not upgraded to PASS.

## Why ptrace rather than a syscall tracepoint

Actual Debian `linux-source-6.12` version `6.12.113-1` shows, in
`kernel/entry/common.c:28–76`, ptrace entry **before seccomp**, then
`trace_sys_enter`. A seccomp ERRNO denial can skip that tracepoint. Therefore a
BPF enter/exit tracepoint alone cannot prove every attempted syscall here.

The selected C17 collector uses PTRACE_SYSCALL/PTRACE_GET_SYSCALL_INFO, fork/
vfork/clone/exec/exit events, TRACESYSGOOD and EXITKILL. It never writes registers,
arguments, memory, results or seccomp state. It does not use suspend-seccomp,
SYSEMU, CONTINUE, syscall substitution or unscoped retry. Increased scheduling
perturbation is acceptable for synthetic capture, not vehicle timing evidence.

## Actual execution boundary

Unchanged original VM cohort:
`d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c`.
QEMU10.0.13 TCG, q35/qemu64, one vCPU/768MiB, kernel
`6.12.113+deb13-cloud-amd64`. No KVM, NIC, shared host filesystem, persistent disk,
QMP, extra telemetry device or hardware passthrough. Same serial stdout channel.
The derived image adds only the fixed collector and its scope marker. Every
selected fixture gets a fresh diskless guest; no implicit all-fixtures option.

The frozen old 4,307-input manifest and original 5,501-entry VM tree are verified
before launching the fixed recipe. New source/build input hashes are additional
content identities. Missing/drifted inputs fail closed, with no install/download,
other kernel, outer-host tracing or fallback to the old uncollected harness.
Rootless outer-host compilation only; all actual ptrace/procfs/cgroup/BPF/security
operations execute inside the guest. Signed source tar component was matched to
the already authenticated Debian package before source review/load. No package
postinst, host service or host kernel policy changed.

## Identity, lifecycle and termination

The collector starts before fixed `/harmless-fixtures HFxx` exec. Task identity
is capture content plus monotonic birth generation, never PID alone. Successful
exec increments a task's image generation. Child stops are held until the exact
parent fork event binds them; kernel source wakes the child before notifying the
parent, so wait-event arrival order must not be mistaken for missing ancestry.

Seed/child fork completions are explicit boundary returns, not invented entry
pairs. Normal nonreturning exit and signal-killed pending calls have ABORT plus
PRE_EXIT/actual wait EXIT, rather than fake successful syscall returns. All born
tasks must reconcile with terminal counters. Listener ENOSYS is not termination;
the original supervisor's subsequent stop/reap remains separately observable.
EXITKILL and outer QEMU termination are recovery boundaries, not a qualified
watchdog or proof against supervisor/host compromise.

CLONE_UNTRACED can suppress birth tracing; shared FD tables and nonleader thread
exec exceed this profile. The collector aborts before executing unsupported
untraced/shared/thread clones, emitting incomplete/error evidence rather than a
fabricated return. This is not an unperturbed observation of those programs.
The neutral evaluator independently checks flags from parent syscall entry,
not just the birth record. Successful clone3 cannot qualify the FD profile:
numeric args contain a pointer, not separately observed clone_args flags.
Successful x32 is unsupported; actually rejected x32 attempts remain observable.

## FD and request provenance

At stopped-task boundaries, procfs supplies sorted FD number, actual flags,
device/inode/type and mount id. Kernel fdinfo source holds file-table lock and a
temporary file reference, including per-FD O_CLOEXEC. The collector never retains
duplicates of target pipe FDs; doing so would change EOF. FD0 is a valid result.

Initial FD tables are seed checkpoints, not proof of pre-window acquisition or
complete open-file-description deduplication. Later lifetime/generation follows
observed return, close, dup, fork and exec. Inode alone is not durable identity.
Pidfds bind the observed birth generation at creation; later numeric PID reuse
cannot retarget them. Unknown acquisition, unexplained mutation, rights-passing,
async io_uring and unknown ioctl semantics invalidate FD profile completeness,
even if a negative return or unchanged snapshot appears reassuring.
Unknown/OFD-mutating fcntl commands are likewise unsupported. A successful dup2/
dup3 rebinds source provenance even for an occupied target with identical inode
and flags; F_SETFD preserves OFD origin while verifying the actual cloexec bit.
Scalar acquisition cannot change unrelated existing FDs. Duplication must match
the requested destination, source object and exact per-FD flags. Post-call/exec
checkpoints bind the exact call once; later tables cannot replace that evidence.

Typed USER_NOTIF RECV/ADDFD/SEND input/output receipts bind actual request ID,
listener origin, notified task generation, currently pending syscall and source
FD generation. Older identical calls are not selected by a latest/PID heuristic.
An ADDFD delivery additionally requires atomic SEND flags, actual source FD,
ioctl return, target return and target FD snapshot; a stale/canceled request or
similar inode cannot substitute. Listener-loss interpretation checks the alias
state at the target return, not the fact that all processes eventually exited.
The supported ADDFD profile requires atomic SEND, zero ignored requested newfd,
only zero/O_CLOEXEC newfd_flags, and matching actual target file flags.

Six raw numeric syscall arguments are retained exactly, including unsigned
register bits and signed return/error. Pointer numbers are **not general pointee
memory or consumed-path-byte receipts**, nor identities. The typed notification
structures are read at stopped trusted-broker boundaries; raw caller and broker
open arguments remain separate. Whole memory/source/loader closure is unqualified.

## Transport, validation and faults

Version `guest-syscall-fd-v1`; exact integer JSON records and canonical content
digest. Clock domain `GUEST_TRACER_OBSERVATION_MONOTONIC_NS` is observation time,
not kernel execution time or absolute clock authentication. Ordering is checked
between observations; no vehicle-delay/performance inference follows.

The collector alone writes capture records. Fixture stdout/stderr are piped and
demultiplexed separately, preventing their bytes from becoming capture frames.
Actual kernel console output can still be adjacent to a **complete** JSON object
on the unchanged serial channel. Only a complete object followed by a timestamped
kernel diagnostic is demultiplexed; its occurrence count enters the capture and
raw bytes are retained losslessly. Unknown trailing data, duplicate keys, NaN/Inf,
truncated or internally interleaved JSON, missing/reordered/duplicate sequences,
wrong clocks/generations/counters and missing reaps reject. No event or data byte
is repaired, filled, or inferred from a success summary.

Observed RED→GREEN diagnoses include:

- Empty/missing collector can return process0 but no capture: parser rejects.
- Raw Linux PTRACE_PEEKDATA writes via its data pointer, unlike libc's wrapper:
  initial real EFAULT fixed against exact source, not an access-policy bypass.
- Child SIGSTOP before parent fork notification: held-stop queue with exact
  parent binding; no guessed birth from PID.
- Kernel CRNG console message adjacent to complete JSON: strict framing above;
  bytes inside a JSON object still invalidate it.
- Synthetic adversarial tests: identical older syscall, stale request, missing
  source FD, wrong donation result, PID reuse, live-listener ENOSYS, missing birth,
  exec/cloexec drift, capture truncation and unsupported async/rights/ioctl paths.

Resource bounds (64tasks, 4,096FDs/task, 1,000,000events, 180s/QEMU) reject overflow
or unavailable evidence. These are implementation limits, not empirical/safety
admission thresholds. The original fixture timeout is not bypassed or qualified.

## Evidence and regression

Actual final run: **24/24 capture ledgers, 24/24 named FD profiles and 24/24
unchanged harmless assertions reconcile**. Across the24 independent guests:
136,933 events,81 observed task lifetimes,66,562 entry/return pairs,80 explicit
terminal/aborted calls,25 successful exec events,3,520 observed FD-table
transitions,14 notification receipts and4 successful donations. There was1
adjacent kernel diagnostic outside a complete JSON frame. FD-transition counts
exclude seed/inheritance and implicit terminal cleanup; they are not global
successful-handle/effect counts.

| Case | Events | Task lifetimes | Execs | Notifications | Donations |
|---|---:|---:|---:|---:|---:|
| HF01 read-only injection | 7,177 | 4 | 1 | 1 | 1 |
| HF09 rejected flags/x32 | 7,163 | 4 | 1 | 1 | 0 |
| HF11 canceled request | 5,051 | 3 | 1 | 1 | 0 |
| HF12 nested fork/exec | 3,780 | 4 | 2 | 0 | 0 |
| HF14 inner observer loss | 3,011 | 4 | 1 | 0 | 0 |
| HF15 listener loss then stop | 5,054 | 3 | 1 | 1 | 0 |
| HF22 missing inner end marker | 2,897 | 3 | 1 | 0 | 0 |

Actual final measurements and exact verification counts are in
[the machine-readable result](evidence/guest_collector_results.json).
[Source/range hashes](evidence/guest_collector_sources.json) and
[build/input hashes](../compatibility/containment_guest_collector/guest/build_manifest.json)
bind the declared content, never authenticity or operational authority.
Verification before independent review: full1,962 tests, focused107; global
ruff check/format, strict mypy (installed source + new package), `-Werror` C build,
sdist/wheel and fresh isolated wheel imports/replay/knowledge/owner/science/
friction/receipt smokes pass, including base and optional-research variants.
Historical source/history audits and passive offline native192 pass. New-package
pure/replay combined statement+branch coverage83.24%; no C/BPF line-coverage claim.
Source study:8 exact Debian files/12 ranges. Original fixture sources, installed
package and CI compare unchanged against the base.
The new package stays outside the wheel and ordinary CI guest execution. Default
pytest tests pure contracts, replayed committed captures and architecture only.
Actual guest runs are opt-in. Existing replay goldens and scientific/runtime/
application blockers remain unchanged. Final independent review and exact-head
push/PR CI are recorded on the new Draft, not claimed by a producer bool.

Post-review author fix pass: **2,004 full tests /149 focused tests pass**;
new-package coverage is86.70% statements /80.14% branches (combined84.34%),
including pure replay but not guest C/BPF line instrumentation. Full lint,
format, strict mypy, source/history audits and passive offline native192 pass.
The installed-source coverage run before the fix was98.52%; installed source
remains byte-identical. Build and freshly isolated vanilla/research wheel smokes
pass. An initial rerun reused a research-installed venv and correctly failed the
vanilla NumPy absence check; a new empty venv resolved test-environment pollution,
without product or dependency changes.

Independent review at exact8f1ac2995d89bb7cc5ba5c4b955768bb6d88c4f8 found
**C0/I6/M0**. All six Important issues reproduced RED, then were fixed in one
author TDD pass and the full suite rerun. The fix head was **not independently
re-reviewed**; no C0/I0 verdict is claimed for it. All24 original raw captures,
digests and metrics still match. See the exhaustive
[review/fix/ruling record](guest_syscall_fd_collector_review.md).
Deferred minors: none.

No Params, controller, writer, SubMaster, Carrot/native/model/service/vehicle,
longitudinal, external AI integration, upstream PR or prior PR modification.
No empirical estimator bridge. No device-class or deployment qualification.

Retained exact statuses:

```text
GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED
FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED
NO_EMPIRICAL_ESTIMATOR_BRIDGE
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_EXECUTOR_UNQUALIFIED
APPLICATION_NOT_AUTHORIZED
```

Recommended next single task: a **guest-only immutable source/toolchain/loader
closure verifier** for these fixed harmless runs. Complete capture does not seal
all build/loader inputs or authenticate the collector; hashes alone do neither.
This recommendation does not authorize Carrot-native build/execution or actual
device qualification. Do not auto-start it after this handoff.
