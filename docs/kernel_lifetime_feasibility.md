# Kernel lifetime observer feasibility — source design only

Base PR35 `a982d1bec759916013981f9cbc76ced6679c71ea`. This is the approved
read-only source feasibility spike, not an observer, kernel patch, attach script,
VM experiment, qualified receipt adapter or permission grant.

## Decision

**NO_GO_CURRENT_PROFILE**: the unchanged inspected source plus existing diagnostic
captures does not supply the evidence required by PR35's serialized, source-complete
lifetime profile. This is a qualification decision, **not** a theorem that Linux
cannot be instrumented or that every tracing facility has been exhaustively ruled
out. Generic syscall/scheduler events and agreeing inventories do not close the gaps.

**CONDITIONAL_DESIGN_ONLY**: explicit, source-pinned instrumentation in a separately
built disposable guest kernel is the preferred route to a narrow raw-event prototype.
It must preserve raw operation intervals and observable interventions. A later
assembler may admit only operations with independently demonstrated cuts. Do not
add a global lock around kernel effects just to manufacture PR35-compatible history:
that changes the execution being observed. Neither instrumentation nor quiescence
is transparent by default. No such kernel is built, patched, booted or observed here.

Source cohort: Debian `linux-source-6.12_6.12.113-1_all.deb`,153094996 bytes,
SHA256 `6ad4a0316ddefced87cef8cd9a25a268e0cdfe0a10adc5148401f49f90b336b5`;
inner archive SHA256
`ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33`.
The preserved previously authenticated package/archive were rehashed;10 selected
files and26 exact ranges were freshly extracted/read and verified. No fresh Debian
signature verification or running-kernel equivalence is claimed. Whole file size,
SHA256, Git-blobSHA1 and exact rangeSHA256 are in
[source manifest](evidence/kernel_lifetime_feasibility_sources.json).
The `claim` IDs below resolve to path/start/end/hash in that manifest.

## Hook-site feasibility matrix

| Obligation / exact source claims | Candidate semantic capture point (future) | Why existing evidence is insufficient |
|---|---|---|
| Namespace `NS_LAYOUT,NS_COPY,NS_END,NS_RESIZE` | successful files_struct initialization before publication; exact owner switch/detach; terminal before allocator reuse | fdtable backing replacement is not namespace allocation; boot/static `init_files`, failed copies and outside-scope references need distinct handling |
| OFD `OFD_ALLOC,OFD_BACKING,OFD_FREE,OFD_FPUT` | successful initialized struct file lifetime and its actual terminal boundary | noaccount/backing variants and initialization failures differ; final fput may use task/delayed work; syscall exit is not terminal |
| Binding `FD_INSTALL,FD_CLOSE,FD_REPLACE,FD_FLAGS` | actual slot publication/removal/replacement/flag effect plus operation provenance | fd_install alone misses replacement/close/flags; syscall return is not exact slot/OFD identity; inspected points are not a complete effect-path audit |
| Fork/unshare `FORK_FILES,UNSHARE,NS_COPY` | actual old/new namespace result and each copy read/reference | CLONE_FILES shares; copying depends on real references; holding file_lock does not exclude in-flight lockless installs |
| Exec `EXEC_EFFECT,EXEC_CLOSE,EXEC_EVENT` | actual unshare result and complete individual CLOEXEC effects, then successful image transition | exec success is later than the effects; close loop unlocks/relocks; partial/failing paths cannot be reconstructed from a success event |
| Task/scope `SCHED_TASK,SCHED_FORK,SCHED_EXEC,FORK_EVENT` | allocation-scoped task identity, ownership switches and scope entry/exit | trace payload PID/comm/path is not lifetime cookie, files_struct generation or closed owner set; raw tracepoint arguments alone also need a qualified issuer/coverage |
| Delivery `RING_RESERVE,RING_COMMIT,RING_DOC` | independent accounting before every attempted emission, terminal disposition and consumer delivery | reservation can fail; discard is skipped; busy records defer later delivery; ring counters count bytes/reservations, not all attempted semantic effects |
| Arm/drain/CPU `TRACE_UNREGISTER,CPU_COHORT,RING_DOC` | explicit all-source arm cut, producer quiescence and complete CPU/source drain | synchronize_unregister waits probe readers, not target-mutator quiescence or all queued records; hotplug synchronization is not source-wide atomic enable |
| Perturbation `NS_COPY,UNSHARE,OFD_FPUT,CPU_COHORT` | record observer references, stopping/scheduling and hotplug interventions | extra references can change copy/free behavior; new locks/hooks affect timing; read-only access does not prove natural unobserved execution |

The machine-readable [decision matrix](evidence/kernel_lifetime_feasibility_matrix.json)
keeps9 obligations individually blocked and all9 permissions false. Hook candidates
are **source locations**, not claims of exported tracepoints, BTF availability,
fentry/fexit/kprobe attachability or safe callback context. Static/inline functions,
compiler optimization, configuration, recursion and allocator safety must be checked
against the exact future binary. No BPF load, privilege change or host tracing occurs.

## Reproducible non-atomic copy witness

`NS_COPY` explicitly allows fd_install racing with its ascending array walk despite
file_lock. `FD_INSTALL` has a normal lockless RCU publication path. Consider two slots
whose reservation bits were set **before** copying; no resize or new reservation is
needed during the critical section. Both slots initially contain no struct file.

| Step | Action | Source published presence `(fd0,fd1)` | Copied value |
|---|---|---|---|
|0|both slots reserved, unpopulated|`(0,0)`|—|
|1|copy reads fd0|`(0,0)`|fd0 absent; child's open bit cleared|
|2|another sharer publishes fd0|`(1,0)`|—|
|3|that sharer publishes fd1|`(1,1)`|—|
|4|copy reads fd1|`(1,1)`|fd1 present|

The child's copied published bindings `(0,1)` never existed together in the source.
All6 merges preserving reader and writer program order are enumerated by the small
test-only witness; this1 merge lacks even a matching presence state. These are
synthetic schedules, **not** six observed runs, probabilities, actual Linux traces,
or a complete memory-model proof. A presence match in the other5 is necessary only,
not sufficient proof of exact atomic geometry/flags/reference/source context.

PR35 intentionally excludes reserved-but-unpopulated slots and demands a serialized
cut. This witness is a reason to prove/enforce that premise **before admission**, not
a bug fix to PR35, a new admitted kernel profile, or grounds to silently coalesce a
racing copy. Stopping one PID, file_lock, KCMP_FILES equality or an event sequence
does not prove absence of all shared mutators and previously started installs.

Two future options: demonstrate true scope-wide quiescence without claiming it was
uninfluenced execution; or design a different per-slot/interleaved raw schema.
The preferred prototype retains raw evidence first; no automatic PR35 bridge.

## Delivery/loss feasibility

`RING_RESERVE` can returnNULL for size/space and NMI try-lock failure; `RING_DOC`
explicitly notes NMI failure even with free space. No NMI exposure of the chosen
future lifecycle hooks is asserted here: each hook's actual context needs proof.
`RING_COMMIT` clears busy and can set discard. Reservation ordering is not effect
ordering: a reservation before an effect can be delayed, and emission after an
effect can be overtaken. A global event number does not linearize multi-slot copy.

A future source accounting design needs independent, synchronized counters:

`attempted = reserve_failed + reserved`

`reserved = committed + discarded + pending`

`received = committed` at a **proven closed** source/drain boundary.

These are proposed event-count equations, not built-in BPF byte counters. Counters
must count every required source attempt before any fallible reservation, distinguish
CPU/source/generation, handle recursion/NMI and fail closed on overflow/reset/gaps.
The counter/arm/drain mechanism itself needs qualification; another lossy event cannot
be its only witness. Discarded semantic events and nonzero failures/pending invalidate
this proposed lossless profile. Aborting a capture after a lost effect is evidence
invalidation, **not** prevention or rollback of the target effect.

The pure synthetic ledger checker rejects unknown/bool/float/negative/overflowing
counts, failed reservations, discard/pending, equation/delivery mismatch, missing or
duplicate CPUs, and unproven synthetic arm/drain premises. A mutually consistent
fabrication, wholly omitted hook, or omission before attempted++ remains undetectable.
Empty balanced ledgers mean only consistent no-activity premises, not liveness.
Actual dropped-event and global prohibited-operation counts remain **None**.

## Implementation boundary and alternatives

1. Userspace proc/ptrace/pidfd/kcmp: retain PR34's point diagnostics; cannot infer
   allocation generations or complete source delivery. No new implementation.
2. Generic tracing/eBPF: useful exploratory visibility, not current qualification.
   Need exact binary/hook/effect-path and loss evidence; no “eBPF is lossless” premise.
3. Explicit guest-source instrumentation: **selected conditional architecture**.
   Design source-issued cookies with no wire pointers, avoid extra file/table refs
   for identity, log raw effects without serializing them artificially, separately
   account intervention/loss and reject unsupported interleavings. No hook set yet
   satisfies these obligations; read [implementation gates](kernel_lifetime_implementation_gates.md).

The source review is bounded to declared files/ranges. Uninspected paths (including
SCM_RIGHTS/receive_fd/pidfd_getfd/io_uring and kernel-only references) are not declared
absent or covered. Support them in a later whole-path audit or prove actual pre-effect
exclusion. Declared scope policies/caller booleans are not such exclusion evidence.
No new timers, collector, persistence, network, production dependencies, runtime
decoder, application/owner imports or H6 estimator bridge are added.
