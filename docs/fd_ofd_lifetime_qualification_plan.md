# Future lifetime observer qualification obligations — not a grant

This checklist defines what a separate future qualification would have to prove.
No item is satisfied merely by the companion SYNTHETIC oracle accepting a graph.
No producer, device run, kernel patch, actual guest experiment or qualified bridge
is implemented in this work. Actual global/drop counts remain unavailable.

## Evidence gates (all mandatory before a future scoped qualification)

| Gate | Required exact evidence | Current status |
|---|---|---|
| Q1 source/runtime cohort | exact kernel binary/config/BTF/source/hook/collector build identity, boot/session/scope; representation version and encoding compatibility | UNQUALIFIED |
| Q2 lifecycle issuers | actual files_struct, task and struct file allocation/end hooks, cookie reuse and generation proofs, no address/PID/inode/hash substitution | NOT_IMPLEMENTED |
| Q3 mutation/alias coverage | every supported install/replace/dup/flag/close/fork/share/unshare/exec/exit path and external sharer, or independently enforced pre-effect exclusions | UNPROVEN |
| Q4 protected cuts | initial root after source arm, exact inventories and complete raw-to-semantic operation cuts including lockless fd_install/racing dup_fd | COPY_CUT_PROOF_UNAVAILABLE |
| Q5 delivery/loss | source reservation/commit/rollback accounting, per-CPU sequences/fences/watermarks, idle CPUs/hotplug, bounded drain, overflow/termination losses | UNQUALIFIED |
| Q6 actual terminals | detached task vs reaped task, namespace end vs internal storage, delayed fput/last struct file reference, observer pins/interventions | UNQUALIFIED |
| Q7 perturbation/fail-closed behavior | observed pin/count/scheduling effects, safe hook context/reentrancy and resource bounds, actual abort before disallowed effects; no timeout-as-watchdog inference | UNQUALIFIED |
| Q8 independent adversarial validation | exact-head source/artifacts and fresh independent tests/review across all admitted/cohort-specific cases | NOT_RUN |
| Q9 authority separation | observation+qualification != execution/application authority, approved bounds, owner baseline, trusted complete input/output closure | BLOCKED |

Qualified lifetime observation, even if eventually established for a declared
profile, would be a scientific/causal prerequisite only. It would not by itself
qualify compiler/source builds, full namespaces, byte consumption, a watchdog,
Carrot/vehicle execution, estimator candidates or application.

## Future tests to run only in a separately approved bounded implementation

1. Actual root creation after arm; initial inherited/empty descriptor histories,
   missing initial allocation, late observer attach, PID/namespace reuse and boot
   reset. Never relabel a late empty table as a newly allocated table.
2. Same files_struct storage resize versus real new namespace; pointer/address
   reuse after terminal, duplicate/missing allocation/free events and dangling keys.
3. Shared CLONE_FILES mutations seen by all owners; fork copy exact OFDs/flags;
   per-descriptor flags independent in copied tables; aliases do not merge by hash.
4. dup2/dup3/F_DUPFD replacement, FD0 and repeated reuse; same-FD/no-effect calls
   versus actual lifecycle deltas; unsupported operations must not create fake events.
5. Conditional same/new table on unshare/exec, exact post-copy slot cohort/CLOEXEC
   close deltas, failed/overlapping exec, source-before/after binding and image proof.
6. Delayed final fput, exit_files before reap, table reference retention, multiple
   observer pins, registered/transient/kernel references and release ordering.
7. fd_install during dup_fd, reserved-but-unpopulated slots, concurrent install/
   close/dup/exec across sharers and source emission reentrancy. Demonstrate actual
   quiescence or reject the unrepresentable semantic cut; locks alone do not pass.
8. Every delivery failure boundary: arm race, partial source enable, CPU gaps,
   CPU hotplug, buffer overflow, per-CPU/global mismatch, missing commit/abort,
   source crash, early stop, failed drain, truncated/interleaved/duplicate transport.
   Unknown is not0; absence of a visible event is not absence of a prohibited effect.
9. Effects via SCM_RIGHTS/receive_fd/pidfd_getfd/io_uring/epoll, mmap/async IO and
   outside scope owners. Either complete declared support or actual pre-effect
   exclusion; this design oracle does not implement or enforce those paths.
10. Independent actual returned bytes/content stage binding is separate from
    lifetime graph consistency; do not treat file lifetimes as evidence of full read.

No empirical thresholds, safety cutoffs, vehicle bounds, sample/excitation counts
or performance limits are invented. Resource parser bounds in the semantic model
are not scientific admissions. Unknown runtime fingerprints and execution models
stay blockers. No device/model inference from the user's vehicle name.

## What the current design tests can establish

The current43 SYNTHETIC graphs (12 internally consistent,31 rejected) exercise
shared/copy namespaces, conditional exec/unshare, slot/OFD/table/task generation,
independent same-object OFDs, pin lifetime, exact close deltas, CPU/fence/loss and
content/context/type contradictions. They test the contract's internal reasoning,
not whether any runtime producer supplies complete or authentic facts.

The generated semantic catalog includes generic event envelope/context/coverage,
per-CPU rows, binding vectors, all event fields and exact numeric metadata types.
Source manifests bind4 exact base Git blobs and9 Debian files/26 ranges. Source
reference verification is read-only/offline; no host sealing or hostile-checkout
security boundary is claimed. Real kernel equivalence remains unavailable.

## Next single task

A **source-pinned, read-only kernel-hook/copy-cut/loss-accounting feasibility
design spike**: determine whether actual lifecycle publication/terminal points and
quiescence can satisfy Q2/Q4/Q5 without changing target semantics invisibly.
Do not start a production observer, generic workload runner, PR30 adapter or
vehicle qualification from a synthetic consistency success.
