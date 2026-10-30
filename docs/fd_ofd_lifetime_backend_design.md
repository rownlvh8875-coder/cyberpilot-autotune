# Lifetime observer backend alternatives and source feasibility

Design only; no backend, guest/kernel patch or qualified observer is produced.
Contract: [serialized synthetic lifecycle semantics](fd_ofd_lifetime_observer_contract.md).
All source claims are exact base Git/Debian file/blob/range content references in
`docs/evidence/fd_ofd_lifetime_design_sources.json`. They do not establish a running
kernel fingerprint, installed hook set, BTF equivalence or capture completeness.

## Alternatives

| Approach | Useful evidence | Missing qualification obligations | Decision |
|---|---|---|---|
| Userspace ptrace + proc inventories + pidfd_getfd/kcmp | stopped target FD flags/object, held local OFD equivalence, observed exec/slot reuse | allocation/destruction history, hidden sharers, lockless mutations, all effect paths, source-wide loss/fences | retain PR34 as diagnostic only; do not synthesize generations |
| Generic syscall/tracepoint/eBPF stream | possible effect-class visibility with low integration coupling | syscall return is not file/table identity; incomplete generic hooks, pointer ABA, terminal deferred release, semantic cuts, CPU delivery/loss and permission availability | insufficient as a generic qualified backend by name alone |
| Source-pinned kernel-assisted lifecycle source plus verified quiescent semantic cuts | can be designed around actual files_struct/struct file allocation/publication/destruction and source effects | must prove exact hook coverage, root/scope closure, quiescence including lockless installs, reference perturbation, watermarks/loss and safe emission | **preferred future architecture**, conditional and unimplemented |

The choice is not “kernel implies trusted.” It selects where the missing evidence
could be captured, not proof that those hooks currently exist or can safely supply
the desired semantics. Privilege, verifier acceptance, tracing API availability,
CO-RE loading, signed modules or a successful attach would not individually qualify
it. No actual instrumentation, policy change, network collector or execution occurs.

## Source findings that constrain the design

- `include/linux/fdtable.h`: files_struct owns replaceable fdtable storage. `fs/file.c`
  expand_fdtable swaps fdt under the same namespace; KCMP_FILES compares files_struct.
  Namespace lifetime key and backing storage generation must not be conflated.
- `kernel/fork.c copy_files`: CLONE_FILES shares the namespace/reference count;
  ordinary fork invokes dup_fd, retaining the same struct file OFDs in a new table.
- `fs/file.c dup_fd`: even holding file_lock does **not** exclude lockless fd_install.
  Copy walks slots, some reserved but not yet populated. A claimed atomic old-state
  snapshot can be false. This is a concrete **COPY_CUT_PROOF_UNAVAILABLE** blocker.
- `fs/file.c fd_install`: ordinary publication can proceed under sched-RCU without
  file_lock except during resize. Global source sequence alone cannot turn a
  non-linearizable multi-slot copy into a linearizable cut.
- `kernel/fork.c unshare_fd/unshare_files`: copy is conditional on actual count;
  exec does not invariably allocate a new namespace. Tracked task count is not the
  complete kernel reference count, so copy outcome must be observed explicitly.
- `fs/exec.c`: unshare precedes close-on-exec. `do_close_on_exec` releases/reacquires
  file_lock around close work. The oracle's close delta is an admitted complete
  semantic transaction, not a claim of one physical atomic kernel close operation.
- `fs/file.c exit_files/put_files_struct`: task detaches its namespace, final table
  reference may close files/free the namespace. Task reap and namespace terminal
  lifetime are different observations and need not be simultaneous.
- `fs/file_table.c fput/__fput/file_free`: final reference cleanup can be deferred
  through task work/delayed work; last known FD close is not actual OFD destruction.
  Physical terminal witness must be emitted explicitly, not inferred from counters.
- `kernel/kcmp.c`: current FILE/FILES pointer relation comparisons with permission
  checks establish a local relation, not persistent cookie/generation or coverage.
- `kernel/pid.c`: pidfd_getfd receives a real referenced file with CLOEXEC in the
  observer. Its successful reference is useful but changes reference lifetime.
- `fs/proc/fd.c`: target fdinfo exposes current file flags plus close_on_exec, not
  source-complete allocation/mutation/destruction provenance.

Source-pinned PR34 shows actual9 fixed guest cases and local equivalence only;
its result's FD-table generation and global counts remain None. No adapter here
converts that evidence into the hypothetical new lifecycle graph. Deferred HH03
diagnostic field defect and old PR33 minors are preserved, not silently corrected.

## Preferred capture architecture — future only

```text
source-pinned lifecycle/effect hooks + closed managed scope
           + verified quiescence/copy-cut provenance
           + source/CPU sequence, arm/drain/loss proofs
                              |
                raw immutable operation evidence
                              |
        checked semantic assembler (reject overlap/gaps/unknowns)
                              |
          lifecycle observation receipt + separate qualification
```

No component of this runtime chain is implemented by the pure SYNTHETIC oracle.
The future assembler must retain raw-to-semantic links and operation intervals,
not just post-hoc snapshots or caller “complete=true”. Incomplete/coalescing-racy
operations remain unavailable. The serialized profile may prove quiescence only
if **all** relevant mutators, shared owners and in-flight installs are controlled;
stopping one task or holding file_lock alone is insufficient. Finer-grained
interleaved copy receipts require a separate schema/profile, not silent fallback.

Allocation cookies must be issued at source lifecycle points with independently
auditable generation/reuse handling and boot/observer/source scope. A user-space
map keyed by raw address without complete allocation/destruction evidence is not
that backend. TASK/EXEC, table keys, slot incarnations, OFD keys and held references
remain separate. Source revisions and collection generations must be explicit.

## Observation perturbs reference lifetimes

Read-only data access does **not** mean an unperturbed target. Retaining struct
file references delays final fput/free; retaining files_struct references can
increase the count that controls unshare/copy. Ptrace/quiescence changes scheduling.
Observer pin records must describe these actual interventions and their releases.
Never infer that an observed copy/destruction time is the unobserved natural one.

Prefer source-lifecycle cookies without keeping tables alive merely to avoid ABA;
source hook safety, memory ordering and loss behavior still require proof. If a
backend does hold table references, its qualification must include induced copy
behavior, not claim transparency. Performance/perturbation bounds require measured,
source/vehicle-independent justification later; no numbers are invented here.

## Wire/compatibility boundary

The semantic schema is not cereal, Cap'n Proto tags, a binary codec or a runtime
decoder. Proposed future primitive encoding: opaque ResourceKey of2 UInt64 values,
UInt64 source ordinals/ns/epochs, UInt32 CPU, explicit Bool flags, typed enums,
ordered binding vectors, explicit availability/status. No raw pointer wire IDs.
Unknown required lifetime/coverage is unavailable/rejected, never default0/false.
Schema version changes on field/stage/ordering/unit meaning; source SHA is separate.

Actual transport framing, duplicate-key/record handling, raw arrival preservation,
bounded verified reassembly and canonicalization require a separate implementation
contract and adversarial tests. The Python oracle is not a loss-detecting decoder.
Its graph-level digest is content identity only, never authenticity or authority.

## Retained blockers

LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED; LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN;
COPY_CUT_PROOF_UNAVAILABLE; LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED;
OBSERVER_PERTURBATION_UNQUANTIFIED; FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED;
CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED; NO_PR30_QUALIFIED_BRIDGE.
All executor/watchdog/frozen-development/vehicle/application blockers remain.
