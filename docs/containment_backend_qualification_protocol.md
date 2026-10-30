# Harmless backend qualification protocol (not executed)

2026-10-30 (Asia/Seoul). Binding
[design](superpowers/specs/2026-10-30-containment-backend-feasibility-design.md).
This is a proposed test protocol, not approval to exercise host security features.

## Precondition and scope

An explicitly selected dedicated device-free test host, a maintained exact kernel/
config/BTF and toolchain cohort, approved privilege/namespace/cgroup/BPF/seccomp
operations, disposable filesystem scope, and an independent recovery supervisor
are required before implementation/execution. Missing any item: STOP. Neither
the current cloud runtime status nor a caller-authored approval JSON establishes
that external operational authority. No host has been selected in this task.
Host setup/policy mutation is security-sensitive and cannot be inferred from
approval of the synthetic checker or a generic "continue".

Only owned temporary regular files, directories, symlinks and ordinary pipe/FD
fixtures are in this protocol. No physical devices, fake device nodes/mknod,
raw block/VFIO/KVM/GPU/CAN/camera/USB/GPIO, sysfs mutation, native/Carrot/model/
Params/controller/SubMaster/service/vehicle execution. No source/model artifacts
from the139-file acquisition enter a fixture. A regular file with a hardware-like
label is **not** a device and cannot test device ACL or driver hook execution.
The fixture design does not authorize replacing host /dev or loading a policy.

## Evidence envelope for a future harness

Each run has a non-identifying run_id, operational-scope reference, exact fixture/
expected-outcome digest, source/toolchain/kernel/config/BTF/runtime/program/link/
policy/mount/namespace/cgroup identities, supervisor/broker/collector revisions,
start/end barriers and one explicit clock domain. Host labels are not identities.
Do not embed hostname, VIN/dongle/route/GPS, secrets or driver data.

Each event records requested/broker-considered arguments separately from resolved
object identity or POLICY_DENIED_NO_OBJECT, task birth and exec/FD generations,
notification/filter generation, request ID, syscall ABI, result, effect and
collector/guard correlation. For regular objects include type, live object handle
binding and namespace/mount/inode generation as available; inode number alone is
not durable identity. Unknown values are null, never filled with0/false.
All broker-side effects are captured, including canceled operations; no FD/effect
count0 follows from an empty trace.

Outcomes: PASS_NAMED_HARMLESS_FIXTURE, REJECTED, NOT_SUPPORTED, or UNAVAILABLE.
No outcome is OBSERVED containment qualification, native readiness, policy
adoption or execution/application authority. Fixtures may identify a deficient
primitive; they cannot confer the authority to widen its policy.

## Required fixture inventory

These are expected future experiments, **not results**. The final observed
result/effect/guard-active fields are null for every row in the manifest.

| ID | Controlled input / perturbation | Required observation |
|---|---|---|
| HF01 | Immutable regular input, allowed read | Resolved expected object; exact read-only FD injection/result pair |
| HF02 | Change request buffer while broker is deciding | Only broker-owned copied bytes used; no CONTINUE or unmediated open |
| HF03 | Replace symlink during resolution | Resolve within approved root or reject; no prefix approval |
| HF04 | Absolute / parent traversal outside root | No outside object/FD/effect; scoped kernel rejection bound |
| HF05 | proc-fd magic link label | No magic-link traversal; no inherited FD laundering |
| HF06 | Close/reuse numeric dirfd or change cwd | Unknown generation rejects; never reuse numeric identity blindly |
| HF07 | Hardlink / rename replacement of protected input | Write/replace denied or input-cohort invalidated; no stale identity |
| HF08 | O_PATH on ordinary fixture | Rejected before lookup/injection by initial broker profile |
| HF09 | Unknown O_* bits / invalid open_how / ABI | Explicit rejection; no masked unsafe fallback |
| HF10 | IN_ROOT+BENEATH / scoped EAGAIN | Rejected; no unscoped retry |
| HF11 | Canceled notification / stale ID / PID reuse | No injection into replacement task; request/result remains paired |
| HF12 | Fork/clone/exec across fixture entry | Guard active before first untrusted instruction; no lineage gap |
| HF13 | Duplicate/reordered/unmatched/dropped capture record | Whole run invalid; no guessed drop budget |
| HF14 | Observer channel/process loss | No reviewable record; independent deny remains; stop outcome captured |
| HF15 | Broker/listener loss | ENOSYS is not a kill verdict; separate supervisor stops/reconciles tree |
| HF16 | Guard/link detachment attempt inside test scope | Denied or whole run invalid before any admission |
| HF17 | Threaded cgroup supplied | NOT_SUPPORTED before payload, not best-effort kill |
| HF18 | Extra inherited regular FD / duplicate or passed FD claim | Uninventoried lineage rejects; no conversion into device proof |
| HF19 | pyc / preload / sys.path / writable-parent drift | Input closure invalid; never repaired by recalculating target hash |
| HF20 | Generated fixture code in writable scratch | No promotion/load until quiesced immutable closure review |
| HF21 | Mode/proposed-adoption field changed by payload | No policy/state change; four permissions remain false |
| HF22 | Incomplete guard/source/result/clock evidence | UNAVAILABLE/REJECTED, never zero or false evidence |
| HF23 | Plain-file label resembles kfd/sysfs/control endpoint | Model/path classification only; device enforcement remains UNQUALIFIED |
| HF24 | Read-only broker asked to create/truncate/write | NOT_SUPPORTED; no filesystem side effect or widened profile |

Some rows require controlled fault injection in an approved isolated harness, not
an actual attacker or a host-wide policy change. Exact failures/branch coverage
must be recorded rather than "all tests passed" from an unrelated Python model.
Any unexpected effect/handle, untracked child or unknown evidence invalidates the
run; do not continue to native code because the fixture payload only computes CPU.

## What this cannot qualify

Character/block-device hook reachability, hardware ioctl/mmap/driver callbacks,
real device cgroup denial, actual inherited hardware handles, host escape resistance,
full syscall mediation/trace completeness, generated native-loader/JIT behavior,
watchdog latency and native-build compatibility remain separately UNQUALIFIED.
An emulated denial demonstrates the emulator path, not the real driver boundary.
No actual device-class experiment is authorized or specified here.

The source study identifies O_PATH's hook bypass and cgroup.kill's threaded-mode
failure; harmless tests can pin these interfaces only in their approved scope.
They cannot prove that a selected maintained deployment kernel retains every
reference behavior. A differing kernel needs fresh provenance/hook review.

## Exit rule

Publish a rejected/partial receipt on any missing proof, preserving all unknowns.
Only named fixture claims may be supported after real authorized tests; never
upgrade PR25's SYNTHETIC cases to trusted OBSERVED records or feed an estimator.
Actual device containment remains unqualified and Gate A blocked even if every
harmless fixture passes. Policy adoption and exact-R execution require separate
decisions; this document is neither.
