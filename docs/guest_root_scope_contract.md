# Managed-root creation-time source provenance contract

Base PR37 `06e218ca9e17af9547fc7871df70d2b9415f2cb9`. New test-only package
`tests/guest_root_scope`, complete standalone9-file Linux6.12.113 patch, fixed
static PID1 driver, asset-checked opt-in QEMU TCG runner and offline byte audit.
Old producer/serial/source/code/evidence/PRs are unchanged. Not installed in wheel.

## What changes

PID1 opens the control/read handles before arming. Only after arm it forks the
fixed managed root; that root executes the harmless memfd/dup3/F_SETFD sequence,
forks one descendant, waits, closes the file and exits. PID1 waits, stops and dumps.
No borrowed files_struct pointer, reference-owning registry, target-effect lock,
host trace, general payload, network, KVM, shared folder or passed-through device.
One vCPU,512MiB,TCG,exact fixed cases NORMAL/ROOT_BIRTH_LOSS/SMALL_BUFFER only.

| Source stage | Meaning | Not evidence of |
|---|---|---|
| TASK_ALLOC | successful dup_task_struct allocation, fresh cookie, inherited diagnostic identity cleared | successful fork, runnable task, final task lifetime |
| TABLE_NEW | successful private dup_fd result assigned in copy_files, namespace cookie and subject task linked before publication | slot inventory, atomic copy cut, inherited OFD birth |
| TASK_COMMIT | copy_process past its last failure point, before task-list publication and wake_up_new_task | first instruction executed, lifetime end or whole ownership closure |

The root scope is its new source-issued task cookie. Descendants inherit only the
scalar scope and receive distinct task cookies. Namespace/OFD/task cookies share
one atomic increasing issuer. Cookie0 means unavailable, never PID/address/hash,
actual zero identity, proof of absence or inferred pre-arm birth. PID1 is solely
the fixed command/first-fork gate; its task/namespace birth remain unknown.
The one-shot root allocation consumes the root selection even if fork later fails;
an uncommitted allocation must not be silently retried/recast as a successful root.

File/table free callbacks pass only saved scalar cookie/scope after the selected
allocator free returns, never released object dereferences. Actor is the current
live task at the hook; it can be unavailable for uninstrumented/deferred contexts.
No TASK_FREE/exit hook, complete reference/copy/exec history or late-cleanup closure.
No generic CLONE_FILES/threads/exec/unshare/root-selection/SMP/NMI support. Excluding
a source path does not count its events or losses as zero. No cookie-wrap or
authenticated boot issuer guarantee, and never pool cookies across captures.

## Separate wire / role semantics

New CPS prefix,wire version1,release `6.12.113-cpscope-v1`. Old CPL v2 is rejected,
not upgraded. Metadata: case,source release,CPU/capacity,source-declared root cookie.
Events: emission sequence,kind,scope,**actor task**,**subject task**,table,OFD,old
cookie,FD,CLOEXEC and kernel monotonic ns. Actor is current, not the new child.
Subject is available only for TASK_ALLOC/TABLE_NEW/TASK_COMMIT; bindings use actor.
`fd=-1`/`flags=-1` mean unavailable; FD0 and CLOEXEC0 remain actual values. Only
INSTALL/FLAGS/REPLACE carry actual CLOEXEC. REPLACE is a dup-write path even into
an unused destination; unavailable old cookie is not an absence witness.
Monotonic ns annotates hooks, not effect linearization or an alignment proof.

Frozen partial Capture/RawEvent records are produced by a bounded strict parser:
exact framing/completion,key sets,version/case/release/one-CPU profile,UInt64 IDs,
32-bit nonnegative FDs,stage-specific subject/table/OFD/old/FD/flag availability,
source scope and increasing unique emission sequence. Unknown bytes/stages reject.
Manual dataclass construction is not a validated producer or authority boundary.

`assess` reports only local accounting,reported local loss and whether the captured
root allocation→copied namespace→success-commit linkage is consistent. It checks
fresh cross-role cookies,duplicate stages,actor/subject separation,pre-commit actor
use,namespace ownership and unavailable root-parent context. Missing allocation,
commit or namespace record cannot be repaired with metadata/expected IDs.
Its affirmative `root_creation_observed` is a bounded **untrusted diagnostic**,
never a complete observer,causal authenticity,inventory,qualification or grant.
It deliberately becomes false on reported loss or context inconsistency.

## Accounting and authority

Preallocated128slots. Attempt ordinal increments before reservation. ROOT_BIRTH_LOSS
rejects ordinal1 (root TASK_ALLOC); SMALL_BUFFER capacity2 rejects later attempts.
Local equations: attempted=reserved+failed; reserved=committed+discarded+pending;
received=committed. Stop disables emissions then waits current emitter RCU sections.
Neither a balanced equation nor failed0 proves all-source/global losslessness,
target quiescence,all-source arm/drain,hotplug/NMI coverage or later cleanup.

All9 operational permissions remain fixed false, status BLOCKED; actual global
loss and prohibited-operation counts None. There is no estimator,application,
PR35 semantic adapter,PR30 evidence or owner-proposal bridge. No vehicle,Params,
cereal/controller/torqued changes,longitudinal,external AI or upstream PR.
Structure fields and hooks perturb layout/allocation/instructions/scheduling;
read-only evidence is not transparent or naturally timed observation.

## Byte provenance and operation

The build manifest binds source/config/patch/kernel/static driver and selected
compiler/dependency/archive/QEMU bytes. Source manifest pins7pristine/9patched
files and43exact ranges. Original complete serial and initramfs hashes are retained.
These are content identities, not authenticity,freshness,race-resistant sealing,
reproducible build or complete transitive build-input closure. Old signed Debian
evidence is preserved, not represented as a new repository-freshness verification.

Offline only: `python -m tests.guest_root_scope.audit`.
Optional source/asset checks require both source roots and `--verify-assets`;
without them the report explicitly leaves those checks false. No VM is launched.
Explicit guest only: `python -m tests.guest_root_scope.runner --execute-fixed NORMAL`.
Exactly three choices; frozen inputs verified before launch, no fallback. The
timeout preserves raw failure bytes, not a qualified watchdog. Never execute the
PID1 ELF on the host. Normal pytest/import/audit never builds or boots a kernel.
