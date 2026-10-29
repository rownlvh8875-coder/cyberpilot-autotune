# CPU-only native-build device containment design

Design date:2026-10-30 (Asia/Seoul). Base PR23:
`86ae36c5077ea6b69eab73e74a4f843159705a21`.

## Intent, authority and current state

Design a future exact-R build boundary that permits CPU computation and ordinary
build files without giving the payload access to physical/accelerator devices.
This is **design only**, not permission to implement or exercise the boundary.
No runner, policy deployment, new dependency, image/container, namespace, kernel
probe, SCons invocation, native import/hook, device, model or vehicle execution.

PR23 remains an accurate rejected/incomplete acquisition audit. Do not edit its
input receipt, status, old plan, native source/patch, installed package, tests,
CI, source allowlist or earlier PRs. Gate A stays BLOCKED; B/C/D are not started.
All candidate/application/runtime/owner permissions stay false.

R remains `c2130730239bcdb4cbde9361ab90c8d99aa4ff55`; comparative C remains
`f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3`. Patch SHA-256 remains
`8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac`; applied tree
`6185197d6f334f745a9c082519013b8fe0376f65`. Offline synthetic995… is not published.
The acquired139 files remain quarantined; no new acquisition is needed here.

Current ajouatom/openpilot:carrot-wip was re-read as
`1fbce2fe7869fda285ee860f7172743e04f6022f`, two commits ahead of C. Compare metadata
includes log.capnp/modeld.py changes. This does not promote that revision, alter
the exact-R contract or establish a runtime/device fingerprint.

## Goals and anti-goals

Separate three assertions that are not interchangeable:

1. No hardware operation was attempted.
2. Hardware requests were denied before any capability/effect was acquired.
3. A CPU backend was selected.

R can satisfy neither1 nor2 merely by printing CPU. Its discovery constructs
backends and suppresses exceptions. DEV=CPU does not filter that enumeration.
The contract must fail on unknown evidence, source/context drift, inherited device
FDs, monitor gaps, successful prohibited operations and attempted control writes.
It must not pretend that a shell flag, errno string, empty GPU list, digest,
successful compilation or synthetic unit test proves kernel containment.

CPU computation (including private-memory LLVM JIT when later authorized) and
exact allowlisted OS pseudo-devices are not physical-device authority. No camera,
CAN, USB, GPIO, raw block, GPU, VFIO/KVM or vehicle interfaces are allowed. This is
not a sandbox-escape proof, controller qualification or a safe-unpickle design.

## Approaches considered — designer's proposal, not adopted policy

| Approach | Tradeoff | Disposition |
|---|---|---|
| DEV=CPU / empty device flags | Small, but R still enumerates constructors; no enforcement or trace completeness | Rejected as containment |
| Modify R to skip/filter discovery | Can remove attempts, but changes the exact source/tree and needs a new source review/registration | Outside this task |
| Full microVM boundary | Stronger host/device separation; introduces image/hypervisor/CPU/trace qualification and a different reproducibility cohort | Possible future alternative, not selected here |
| Layered kernel-deny boundary plus trusted external observer | Retains R; needs demonstrated MAC/device/namespace/syscall enforcement and complete provenance | Preferred future architecture |

The preferred architecture is a design recommendation. Docker availability is not
evidence that its required controls exist or work. A backend that cannot implement
the normative properties must reject, not substitute an unconfined container.

## Keep strict policy; propose a separate discovery-denial policy

`STRICT_NO_DEVICE_ATTEMPT` remains the current acceptance meaning: every hardware
attempt rejects, including a failed one. Exact R's discovered path therefore stays
blocked. This document does not silently amend the prior plan's stop-on-denial rule.

`CAPABILITY_CLOSED_DISCOVERY_PROPOSAL` is a **not-adopted** future policy. It could
classify a narrowly defined discovery open that was prevented before any hardware
FD/effect as diagnostic evidence, provided the full boundary and trace are proven.
It requires separate explicit policy approval, implementation review and runtime
qualification before use. Approval of this design alone cannot adopt it.

Even under that proposal, sysfs enable/unbind, VFIO, device ioctl/mmap, raw block,
GPIO/CAN/camera/USB control, network and privilege attempts are fatal whether they
succeed or fail. No blanket "EPERM means safe" exception. Unknown/ambiguous events
reject. Compatibility of unmodified R with the proposal is not yet demonstrated.

## Preferred future architecture

Trusted launcher/control plane → enforced sandbox → untrusted build payload.
Trusted observer is outside the payload and records every descendant from before
the first untrusted instruction. Enforcement remains active independently of the
observer; observer loss kills the whole payload tree and invalidates the receipt.

The future backend must combine all of the following:

- Private mount/PID/IPC/network views; no host home, /data, Docker socket, secrets,
  agents, displays or hardware/sysfs mounts. Private device namespace with only
  four exact pseudo-device identities: null1:3, zero1:5, random1:8, urandom1:9.
  No tty, fuse, kvm, raw block or broad major/minor wildcard allowance.
- Non-root payload, zero effective/permitted/inheritable/ambient capabilities,
  no_new_privs, no setuid/file-cap escalation and no payload ability to change
  namespaces, mounts, device rules, MAC or tracing. No privileged/host-network mode.
- Mandatory kernel access control (MAC; AppArmor/SELinux-equivalent semantics),
  device access denial and syscall restrictions. Desired launch arguments alone
  are insufficient: record and independently verify observed enforcement.
- Deny raw hardware handles and sysfs controls across aliases, hardlinks, proc-fd
  paths, inherited/passed FDs and all descendants. Deny socket creation/FD passing,
  ptrace, bpf/perf, mount/setns/unshare, mknod and unmediated io_uring paths.
  Ordinary fork/threads/CPU memory are possible only with complete coverage.
- Read-only image/dependencies and immutable tracked source/loader inputs; exact
  generated-output/cache/scratch write rules, not a blanket writable source tree.
  Overlay lowerdir, chmod, sticky directories, -B or read-only rootfs alone do not
  prevent source replacement, rename, import shadowing, stale pyc or preload drift.
  Generated loadable code needs reviewed producer/output provenance before use.
- Complete observer coverage of process/exec/FD/resource/syscall outcomes, outside
  writable payload storage. A ptrace-style recorder may be a capture component,
  not the safety boundary or proof that path strings resolve as recorded.

These are backend requirements, **not deployed AppArmor/seccomp rules**. Exact
runtime/image/kernel/profile versions, label/device-rule verification, output
allowlist and authoritative event-correlation backend remain implementation and
qualification gates. No host policy is loaded, changed or probed in this task.

## Audit integrity and path/FD races

Capture requested arguments separately from kernel-resolved resources. A copied
pathname and errno in strace/stdout are not authoritative object provenance: cwd,
dirfd, symlinks, mutable argument memory, other threads and mount changes matter.
Require kernel-bound resolution/denial evidence or a separately qualified broker
that denies before any operation, with no unsafe syscall CONTINUE on mutable
arguments. Missing-target evidence must bind the immutable private namespace; an
ENOENT string is not proof of absence. A backend lacking that binding rejects.

Do not infer successful-device-handle count0 from an empty log. Capture inherited
FDs and every fork/clone/exec, FD receive/dup/reopen, attempt and result, with
monotonic sequence/clock domains and complete coverage. Source/argv/stage labels
from the payload are untrusted. Correlate them using the trusted launcher, immutable
code/dependency cohort, process lineage/exec generation and observed kernel state.

No guessed expected-event count, tolerance for dropped events or empirical safety
threshold. Lost/reordered/duplicate/unmatched events, unknown results, incomplete
closure, missing checks or any successful prohibited capability reject.

## Feasibility limits and gates

The current environment's MAC, device ACL, monitor/path-binding and immutable-source
enforcement have not been tested. Namespace isolation alone does not establish
these requirements. Existing model-pickle loading and remaining transitive actions
still require review; containment cannot prove that no Params/controller/service
semantics were executed. No vehicle or scientific/application authority follows.

First implement only the pure synthetic receipt evaluator, if separately approved.
Then separately design/qualify a concrete backend using harmless filesystem and
syscall fixtures, not native code or physical-device tests. Only afterward could
an independently authorized exact-R discovery qualification be considered. These
are separate tasks, not a bundle authorized by "proceed" on this design.

Normative fields/decisions: [contract](../../native_build_device_containment_contract.md).
Future pure-validator plan: [plan](../plans/2026-10-30-cpu-device-containment-validation.md).
