# Containment backend feasibility and enforcement-evidence design

2026-10-30 (Asia/Seoul). Base PR25/head
`3b1342f3e131642c6edbe3b18270a1fe1e7d216b`. Design-only follow-up to the
[synthetic checker](../../native_build_device_containment_synthetic_result.md).
The user delegated ordinary design choices; selections below are the designer's
calls, not user adoption of a kernel policy or permission to execute it.

## Intent and limits

Choose a concrete future architecture and state exactly what could establish
its claims. A successful synthetic verdict, CPU label, errno, digest, namespace
or Docker installation is not evidence of actual enforcement. Nothing here
implements or runs a collector, broker, BPF program, seccomp filter or native job.
No kernel/config/device probing, privilege request, container/image, install,
device node, Params/SubMaster/controller/schema/application/owner change.
The acquired139 files, old evidence, all existing code/tests/CI and earlier PRs
remain unchanged. PR25's deferred Unicode minor is not repaired in this task.

STRICT_NO_DEVICE_ATTEMPT remains current. Its exact-R discovery attempts still
reject even if a future backend denies them. CAPABILITY_CLOSED_DISCOVERY_PROPOSAL
remains not adopted. Neither backend qualification nor this design can adopt it.
Gate A stays BLOCKED; B/C/D are not started; all four permissions remain false.

## Approaches and selection

| Approach | Useful property | Limitation / disposition |
|---|---|---|
| Existing container/AppArmor profile plus strace | Less new trusted code | Path labels/logs do not establish object/absence binding, FD coverage or source closure; not sufficient as the chosen contract |
| Dedicated microVM with no device passthrough | Stronger host separation | Guest devices, hypervisor, image, CPU/backend and host/guest clocks introduce another cohort; not selected for this bounded design |
| Linux object-level deny + cgroup-device deny + non-CONTINUE broker + external collector | Explicit independent enforcement and request/result identity | Larger trusted control plane, feature/ABI/hook qualification required; selected conditionally |

Selected reference family: Linux x86_64 native syscall ABI only, BPF LSM MAC,
cgroup-v2 device BPF, seccomp-BPF with USER_NOTIF for mediated opens, an
unprivileged confined payload, and a separate trusted launcher/broker/observer.
No automatic AppArmor-only, rootless-container or ptrace-only fallback. Missing
mandatory features, unsupported ABI or failed attachment means NOT_SUPPORTED.

The Linux reference is torvalds/linux v6.12 commit
`adc218676eef25575469234709c2d87185ca223a`, **API/source study only**. It is not a
deployment kernel recommendation, an installed-host fingerprint, a claim of
security maintenance or a tested compatibility floor. A future host must use a
maintained, patched, explicitly approved kernel/build/config/BTF cohort and repeat
the source/hook analysis; version arithmetic or CO-RE is not compatibility proof.
[Source manifest](../../evidence/containment_backend_sources.json) binds nine
files and eighteen exact ranges. GitHub reports the reference tag unverified;
hashes establish byte identity, not upstream authenticity or a running binary.

## Trusted boundary and launch barrier

The payload is adversarial, including generated code and model pickle behavior.
Trusted launch control, broker, collector and their policy/loader inputs are
outside payload-writable storage and outside its accessible FD/namespace scope.
Broker/collector privileges are part of the attack surface, not a reason to give
the payload extra privileges. A device-free dedicated test host is a future
requirement; no such host has been selected or attested.

Before the first untrusted instruction, the future launcher must bind a live
non-root **domain** cgroup, policy/program/link identities, sealed mount inventory,
approved native ABI, interpreter/toolchain/source cohort and inherited-FD inventory.
It must activate the observer and independent deny mechanisms, install the exact
filter on the single-threaded trusted trampoline, transfer the listener through
trusted setup only, close setup/host/control FDs, drop all payload capabilities,
set no_new_privs, then exec the fixed entry. Never attach after discovery starts.
Descendants inherit the restrictions; per-exec generations and startup coverage
must still be observed. No cgroup migration/delegation/control mount is exposed.
Read-back presence, observed attachment and negative fixture behavior are separate
requirements; desired launch arguments alone cannot satisfy the barrier.

## Independent kernel denial

The selected BPF LSM design inspects resolved file/inode type and exact resource
identity, not pathname prefixes. It preserves any previous nonzero LSM denial.
Scope it to two distinct live domain-cgroup identities: payload descendants and
the broker process that performs filesystem work. Both get device/object guards;
only the external supervisor owns control maps/links. Bind each live cgroup FD
to its launch generation to prevent ID reuse. No host-wide unscoped deny policy
or unguarded privileged filesystem worker is part of this proposal. The broker
may use its exact listener/control FDs but cannot access physical resources;
payload restrictions never grant access to those control FDs.
For the payload **and broker filesystem worker**, hardware char/block access is
denied; only the four separately bound pseudo-device objects null1:3, zero1:5,
random1:8, urandom1:9 may be considered. No wildcard type/major/minor allowance.
The namespace has no physical device/sysfs/host-data mounts; a discovered hardware
object is a preflight failure, not a permitted denied-open experiment.

Separate cgroup-device BPF denies creation/read/write for other device identities.
It is not the only guard: it does not prove all O_PATH, inherited/passed FD,
ioctl/mmap or sysfs cases. The syscall policy denies unmediated async IO, sockets/
network/FD receive, hardware control paths, privilege/policy/namespace changes,
ptrace/process-memory access by the payload, handle-based open, pidfd_getfd and
new filter installation. Exact syscall-number/flag/ABI coverage is a qualification
obligation, not an allowlist supplied by this prose. Unknown routes reject.

**Source finding:** in the reference `fs/open.c`, O_PATH returns before
`security_file_open`; normal `security_file_open` precedes the driver's open
callback. Thus file_open alone is not an O_PATH guard. The initial broker profile
rejects **all payload O_PATH opens**, including regular-file ones, before any
lookup/FD injection. This conservative restriction may be incompatible with an
unmodified build; do not relax it automatically. Inherited/open-by-handle/FD-import
routes must be closed independently. No BPF hook is claimed complete just because
its declaration exists.

## Non-CONTINUE broker and object binding

For open/openat/openat2/creat, the future ABI filter routes every reachable variant
to the broker, including compatible numeric aliases or rejects that ABI outright.
The broker never sends SECCOMP_USER_NOTIF_FLAG_CONTINUE; the kernel header warns
that pointer-argument mutation makes notifier-only security policy unsafe.

Each request binds filter/listener generation + notification ID + trusted task
birth/exec generation + run/cgroup/namespace cohort. PID or notification ID alone
is insufficient. Read scalar registers and copy bounded, NUL-terminated pathname/
open_how data into broker-owned memory before decisions. A short/ambiguous copy,
unknown task/dirfd/cwd, expired request or mismatched generation rejects. Record
these as **broker-considered bytes**, not proof of what a resumed syscall would
have consumed; no such syscall is resumed. ID_VALID is not a transaction lock or
proof that pointed-to memory is immutable.

For proposed discovery request classes, refuse **without object lookup/open**
and return modeled/qualified EPERM only after trusted provenance requirements.
The receipt kind is POLICY_DENIED_NO_OBJECT, not PRIVATE_NAMESPACE_ABSENCE and
not an invented kernel ENOENT. A copied pathname is a request-class label only.
Under the current strict rule the attempt rejects the run regardless. No new
endpoint/flag set is admitted and no policy adoption is inferred from the broker.

For ordinary regular build files, use only broker-owned stable root/dir handles
and an explicit object/operation inventory. Do not copy a numeric payload dirfd
and assume it names the same object later. Initial support is bounded to known
directory handles; untracked dirfd/cwd mutations are unsupported. Path resolution
uses kernel openat2 with RESOLVE_IN_ROOT|RESOLVE_NO_MAGICLINKS; **do not combine
IN_ROOT and BENEATH**, which the source rejects. Approved sub-root profiles may
instead use BENEATH|NO_MAGICLINKS. Symlinks are permitted only where the sealed
source inventory requires them and kernel resolution remains within that root;
NO_SYMLINKS everywhere is not claimed compatible with the acquired seven symlinks.
Cross-mount behavior is explicitly inventoried; do not blindly add NO_XDEV across
approved bind mounts. EAGAIN/ambiguous resolution rejects the attempt, with no
unscoped fallback or guessed retry allowance. These flags are not object-type
checks; the independent kernel guards still apply **before** driver open.

After successful approved regular-file open, bind the resulting object/FD lineage
and exact access flags before ADDFD. Use ADDFD_FLAG_SEND for atomic injection and
reply; verify the actual result, never an expected FD number. That atomicity does
not make earlier O_CREAT/O_TRUNC writes transactional: cancellation may leave
filesystem effects. Initial harmless qualification is **read-only emulation**;
write/create/truncate and full build compatibility remain unsupported pending a
separate effect/cleanup protocol. All effects, including broker-side ones, belong
in the evidence scope; a dead requesting task cannot erase them.

## Capture, lineage, loss and independent stop

The selected observer design correlates kernel syscall entry/exit and fork/clone/
exec/exit events with broker and guard outcomes, outside payload-writable storage.
Use one explicit kernel-monotonic domain, kernel task birth identity, per-exec and
launch/cgroup generations, and notification IDs where applicable. CPU migration
and concurrent threads require causal pairing, not a guessed global timestamp sort.
Raw trace strings are not object provenance; bind authoritative guard objects or
broker no-object decisions. Exact loader/entry-stage identity requires separately
reviewed immutable closure; kernel PID/argv events do not identify Python frames.

Record all initial/duplicated/closed/injected FDs, descendants and syscall outcomes.
Use producer sequences, explicit reserve/drop/failure counters, start/end barriers
and independent lifecycle reconciliation. No guessed expected-event count, drop
tolerance or fabricated zero. An unpaired event, unknown result, observer/guard
loss, untracked exec/clone, clock ambiguity or unresolved lineage invalidates the
whole run. Durable log digests alone do not establish collector authenticity or
completeness. The trusted verifier must bind the collector build, protected
channel and policy cohort; no OBSERVED parser or trust adapter exists here.

The supervisor must retain deny links/rules independently of collector lifetime;
payload/broker cannot detach or rewrite them. Listener closure wakes outstanding
notifications with ENOSYS in the reference, **not process-tree termination**.
Failure handling requires an independent supervisor and domain-cgroup kill plus
exit/quiescence evidence. cgroup.kill is unsupported in threaded cgroups. No
shutdown latency, heartbeat threshold or watchdog execution model is invented;
those remain unqualified. Failure can never widen access, retry unconfined or
create a reviewable receipt. If the supervisor dies too, deny mechanisms must
remain in force; complete termination is not claimed without separate proof.

## Source, loader and generated-code closure

Input closure includes exact executable mode/symlinks, Python/package/native
loaders, sys.path/working directory, pyc/cache precedence, environment/preload,
ELF/interpreter/library search, generated Python/shared objects and JIT producers.
Protected input mounts and all parent directories must resist replacement,
rename, hardlinks and shadowing; read-only lowerdir, chmod or Python -B alone
are insufficient. No source directory is made generally writable for convenience.

Writable output/scratch is separate from approved executable/loader inputs.
Generated loadable output must cross a quiesced, immutable, provenance-reviewed
promotion boundary before loading; a newly computed hash alone is not semantic
approval. CPU LLVM JIT/private memory requirements are a separate review point,
not an excuse to label arbitrary mutable code as trusted input. Current compiler/
system closure, model pickle semantics and default SCons execution are unresolved.
Containment cannot establish that no Params/controller/service semantics ran.

## Feasibility verdict and future proof

DESIGN_SELECTED_CONDITIONALLY; API mechanisms exist in the reference source.
Actual host/kernel/config/BTF/program/toolchain/layout/collector bindings are
**unavailable**, not false measurements or zero counts. This task performed no
feature probe, attachment, syscall experiment or namespace setup.

[Qualification protocol](../../containment_backend_qualification_protocol.md)
defines harmless regular-file fixtures and their limits. Passing them could only
support named regular-file/lineage claims, not device-class enforcement, native
compatibility, complete closure, current-policy adoption or Gate A. Device-hook
coverage remains UNQUALIFIED until separately reviewed evidence addresses it;
no physical or stand-in device nodes are authorized by that protocol.

The [conditional implementation plan](../plans/2026-10-30-containment-backend-qualification.md)
has a hard host/scope-approval precondition and is **not executable now**. Do not
turn the absence of a host into permission to use this managed cloud instance.

Retain every scientific/runtime/application blocker from PR25, q unavailable,
NO_EMPIRICAL_ESTIMATOR_BRIDGE and all four permissions false. No earlier PR is
merged/refreshed; no external/native-fork PR or upstream policy is changed.
