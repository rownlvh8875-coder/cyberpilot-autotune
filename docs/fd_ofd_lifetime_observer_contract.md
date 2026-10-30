# FD-table/OFD lifetime observation qualification contract — design only

Version `fd-ofd-lifetime-design-v1`; base PR34
`3a831fdd423aa98638082eba126519db19f432d6`. This document describes obligations
for a **future** qualified lifetime observer. None is implemented or qualified.
The companion pure test oracle accepts only **SYNTHETIC_ONLY** model graphs.
Its success means internal consistency of simulated claims, not empirical proof,
runtime admission, executor authority or trusted coverage. All9 permissions false,
overallBLOCKED, actual dropped/global prohibited-operation counts unavailable.

## Identities: five different notions, not one counter

| Identity | Meaning | Not evidence for it |
|---|---|---|
| table key `[cookie,generation]` | allocation lifetime of **files_struct**, the descriptor namespace shared by CLONE_FILES tasks | PID, fdtable address, current KCMP_FILES equality, enumeration digest |
| table mutation epoch | observer-local ordinal per admitted serialized semantic transaction | allocation generation, backing storage resize, clock tick |
| `(table key,FD,slot generation)` | binding incarnation; initial0, increment on rebind/replacement, retained across close | FD number alone, CLOEXEC-only change |
| OFD key `[cookie,generation]` | struct file allocation lifetime, potentially shared across tables/tasks | device/inode, bytes/hash, pathname, file offset, normalized flags |
| task key + local exec ordinal | actual task birth lifetime and actual exec transitions | recycled PID, intended argv, executable hash alone |

Observer pin keys have a separate reference lifetime. Identical numeric cookies
in different resource classes are distinct namespaces. Cookies are backend-issued
opaque identifiers scoped by boot/session/source/scope; raw addresses are not wire
identities. Generation0 is valid, None is unavailable. Reusing a cookie requires
explicit prior lifetime end and exactly the next generation, never inferred from
a source change, FD close, exec call or repeated snapshot.

Linux's **fdtable backing storage** may expand/replace under the *same* files_struct.
This oracle deliberately does not assign a physical backing-storage generation;
it remains unavailable/out of scope. KCMP_FILES compares files_struct, not fdt.
No source pointer is exposed, and resizing must not spuriously invent a new
descriptor namespace. A future storage observer needs separate source evidence.

## Selected proposed profile

`PROPOSED_KERNEL_SERIALIZED_LIFETIME_V1`: a proposed kernel-assisted lifecycle
source with verified protected cuts and loss accounting. It is a **proposal**,
not an existing tracepoint/eBPF implementation or qualified kernel modification.
Userspace ptrace/proc/pidfd/kcmp snapshots remain useful diagnostics but cannot
establish allocation/destruction history, closed scope or complete mutation coverage.

The graph models **complete, serialized semantic transitions**, not syscall entry
and return logs. A producer may coalesce an operation only after proving its raw
effects, causal source cut and absence of conflicting overlapping mutations.
It must retain raw operation/linearization provenance for audit. Failed/no-effect
calls cause no lifecycle delta; their separate syscall accounting is not modeled.
Unknown effectful operations are not silently treated as no-ops. Overlap or an
unrepresentable copy/exec/teardown is unavailable/blocked, not repaired or reordered.

Source warning: dup_fd explicitly permits races with lockless fd_install even
while file_lock is held. A single lock-held snapshot is therefore **not** proof of
a linearizable whole-table copy. Quiescence of every relevant mutator (including
shared/external owners and outstanding installs), or finer-grained copy evidence,
must be proved before this serialized profile can qualify. The latter needs a
different/extended contract; this oracle is not a concurrent Linux simulator.

## Synthetic envelope and coverage

Exact fields: `schema,evidence_class,context,events,coverage`. No runtime wire
decoder is provided. Python graph inputs are finite, bounded, strict JSON-like
values; no Bool/Float impersonation of kernel integers, NaN/Inf, custom objects
or unknown fields. Evaluation copies canonical JSON before checking and never
mutates caller input. Canonical sorted-key SHA256 gives content identity only:
no authenticity, freshness, anti-replay, safety approval or authority.

Context fields: `session_id,boot_scope,source_revision,source_digest,scope_digest,
profile,clock_domain,cpus`. Source revision is an exact40hex Git revision, digests
64hex; source/cohort changes alter digest, not automatically schema version.
Session/boot are non-identifying local tokens, not VIN/dongle/route/GPS/driver IDs.
Version changes on semantic/unit/cohort/order changes, not merely a new source SHA.

Every event has `seq,time_ns,cpu,cpu_seq,context_digest,kind,data`:

- `seq`: contiguous proposed-source linearization order, not host arrival order.
- `cpu_seq`: contiguous per-CPU source order; `cpu` must belong to declared cohort.
- `time_ns`: exact UInt64 observer/source-clock value, not an ordering substitute.
  Cross-CPU arrival/clock order is not sorted into causal order; clock domain is
  explicitly SYNTHETIC_KERNEL_MONOTONIC_NS in this design oracle.
- `context_digest`: binds this frame to the whole context; mixed frames reject.
- `kind/data`: closed kind and exact ordered semantic fields, cataloged separately.

Coverage has `start_fence=0,end_fence=event_count+1,cpus`. Each declared CPU,
including idle ones, has exactly one ordered row: `cpu,armed,drained,emitted,
last_source_seq,dropped`. Simulated armed/drained must be true, emitted/source
watermarks must equal the graph's per-CPU count, and dropped must be known0.
Unknown/missing CPU, holes, mismatched watermarks/fences and loss reject consistency.
These are **simulated claims**, not verified capture facts: the result's actual
drop/global counts stay None even when the synthetic row says0. A future producer
must prove arm-before-creation, source-wide drain, all-CPU membership/hotplug policy,
rollback/reservation holes, delivery/loss counters and raw-to-canonical completeness.

The model cannot detect mutually consistent fabrication or an omitted effect with
all counters coherently forged. It rejects detectable contradictions only. Digest,
boolean metadata or counter agreement is not proof that any backend exists.

## Transition contract

References below are exact resource keys, not names or source timestamps. Table
epoch checks compare the consumed before-state. FD0, generation0 and empty
inventories are actual synthetic zero/empty values, never unavailable defaults.
FD bindings carry slot generation, OFD key and per-descriptor CLOEXEC. Object digest
on OFD_NEW is CONTEXT_ONLY; equal digests do not merge OFDs.

| Event | Required interpretation |
|---|---|
| TABLE_NEW(table) | root namespace allocation witness, empty, epoch0; not a late empty registration |
| TASK_START(task,table) | sole managed root birth, local exec0, initial inventory barrier |
| OFD_NEW(task,exec,ofd,object_digest) | explicit file allocation in this task/exec context; does not imply consumed bytes or installed FD |
| INSTALL(task,table,epoch,fd,slot,ofd,cloexec) | FD absent; live OFD; first slot0 or prior binding+1; epoch+1 |
| DUP(task,table,epoch,src_fd,src_slot,dst_fd,dst_slot,method,cloexec) | exact source binding; distinct destination, replace/rebind increments destination slot incarnation; epoch+1; DUP/DUP2/F_DUPFD clear CLOEXEC, F_DUPFD_CLOEXEC sets, DUP3 explicitly supplies it |
| CLOEXEC(task,table,epoch,fd,slot,old,new) | exact existing flag changes; binding/OFD identity and slot generation unchanged; epoch+1 |
| CLOSE(task,table,epoch,fd,slot,ofd) | exact consumed binding removed; slot history retained; epoch+1; not OFD destruction |
| FORK(parent,table,epoch,child,child_table,share) | share=true requires identical namespace; copy requires explicitly fresh different table key, exact OFDs/flags, new slots0/epoch0; child local exec0 |
| UNSHARE(task,table,epoch,after_table) | actual same/new key supplied, never inferred. Same only if not shared by tracked tasks; copy preserves OFDs/flags in a new lifetime/slots0/epoch0 |
| EXEC(task,table,epoch,after_table,before_exec,after_exec,closed) | actual same/new table witness; shared table cannot be modified in-place; exact next local exec ordinal; complete post-copy CLOEXEC close delta, no other slot loss |
| PIN(pin,ofd) / UNPIN(pin,ofd) | explicit actual-reference acquisition/release hypotheses, exact live OFD and pin lifetime; not intended pinning |
| INVENTORY(task,exec,table,epoch,entries) | exact canonical full stopped/protected-cut inventory; must match derived state; clears required initial/post-transition barrier |
| DETACH(task,exec,table,epoch) | explicit exit_files/task ownership removal, not task reap or table destruction |
| REAP(task,exec) | actual terminal task hypothesis only after detach; not OFD/table end |
| TABLE_FREE(table,epoch,closed) | actual namespace destruction hypothesis, no tracked task owner; complete remaining close delta, no inferred early free |
| OFD_FREE(ofd) | explicit actual final destruction hypothesis, no remaining tracked bindings/pins; never inferred merely from known reference count0 |
| END(tasks,tables,ofds,pins) | exact **synthetic allocation counts**, all modeled lifetimes closed; no global operation counts |

Canonical entries/close deltas: ordered `[fd,slot,[ofd_cookie,ofd_generation],cloexec]`
rows, ascending unique FD. Exact UInt/Bool types required even in nested vectors.
Fork/copy does not copy old slot history: current inherited bindings start0 in the
new table. Shared-table changes are visible to every owner; independent copies
retain the same OFDs but have independent FD flags/slot history/epochs.

Exec with same table does not advance its allocation generation. Exec copy records
a fresh explicit table key; post-copy close entries refer to the **new** table's
slot generation0. The close transaction advances mutation epoch once if nonempty;
empty close delta preserves epoch. This is a semantic transaction ordinal, not an
assertion that Linux closes all FD slots in one atomic instruction/lock section.
Former unowned tables must still have explicit destruction evidence. Same-table
exec with one tracked owner is allowed; new-table copy with one owner is also
expressible because kernel references are not deducible from task count alone.

Initial birth and fork/unshare/exec require an exact inventory before any modeled
mutation through that namespace. This deliberate barrier profile rejects
unrepresentable overlap. Snapshots alone still do not prove continuous coverage.
Task-local exec ordinal does not attest executable bytes: that remains a separate
actual executed-image receipt obligation, with no PR30/33/34 adapter in this work.

## Limits and retained blockers

Resource bounds:32 task allocations,32 table allocations,64 OFD/pin allocations,
64 FD slots,2048 events,8 CPUs, bounded canonical depth/strings. These are parser/
model resource limits, not empirical or safety thresholds.
Aggregate copy limits are100000 visited JSON nodes (including keys and repeated
references),4MiB total string characters, and4MiB final canonical bytes. Individual
keys obey the same4096-character bound as string values; cycles/deep graphs reject.

Actual backend must cover or prove pre-effect exclusion for all relevant mutation
routes: open/close/dup/fcntl/close_range, fork/clone/CLONE_FILES/unshare/exec/exit,
pidfd_getfd/receive_fd/SCM_RIGHTS, io_uring fixed files, asynchronous references,
external sharers and kernel transient references. Pathnames/mmap/content consumption,
program/loader/compiler/sysroot closure, executor/watchdog/application authority
remain separate. An unknown route or incomplete exclusion is a blocker, not0.

Current PR34's local OFD pins/comparisons and point FD inventories cannot fill
the proposed lifecycle keys or coverage claims automatically. Its unavailable
table/storage generations remain unavailable. No observed→synthetic relabeling,
no qualified handoff/consumption/application bridge and no producer implementation.
PR34 M1 and PR33 M1/M2/M3 remain explicitly deferred and unchanged.

No vehicle, host/guest target execution, Params/controller/cereal changes, real
compiler/source build, estimator qualification, candidates, application/owner
proposal, longitudinal, external AI, upstream PR or old PR modification.
