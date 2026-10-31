# Managed-root creation-time provenance — bounded guest extension

Build on PR37 exact `06e218ca9e17af9547fc7871df70d2b9415f2cb9`, without modifying
its code, captures, PR or any earlier runtime/compatibility/evidence. The question
is whether a fixed managed root's task allocation, copied namespace construction
and successful task creation can be observed before its first workload operation.
This is not a general lifetime observer, inventory, copy-cut proof or qualification.

## Approach and boundary

Author's choice under the user's standing autonomous-execution instruction:
arm in fixed PID1, then fork a managed root; use task_struct source cookies, not
a borrowed root files_struct pointer. Root forks one descendant and runs the
previous harmless memfd/dup3/flags/close sequence. PID1 waits, stops and dumps.
The alternatives — relabeling PID1's pre-arm namespace, or implementing a general
reference-owning registry — respectively invent birth provenance or greatly expand
scope. No design/implementation approval menu is needed under the standing opt-out.

New test-only package `tests/guest_root_scope`, complete standalone kernel patch,
static fixed PID1 and explicit asset-checked QEMU runner. Existing dedicated clean
checkout is reused on a new branch; no linked worktree or dependency installation.
New prepared assets go in a fresh owned scratch prefix, never the old producer.

## Source contract

Exactly one vCPU,512MiB,TCG, no network/KVM/shared filesystem/passthrough/arbitrary
payload. Exactly NORMAL, ROOT_BIRTH_LOSS, SMALL_BUFFER in separate fresh guests.
Arm precedes managed-root creation. PID1 is solely a control/first-fork gate,
not task identity. It gets no invented birth cookie. No persistent pointer scope
registry, retained target references or target-effect locks.

After successful dup_task_struct, clear inherited diagnostic task/scope fields;
assign a new experiment-local allocation cookie to an admitted child. TASK_ALLOC
means allocation only, not successful fork. Root scope cookie equals its newly
issued task cookie; descendants inherit that scalar scope, never the task cookie.
In copy_files, after successful dup_fd and before task publication, assign a new
namespace cookie and emit TABLE_NEW linking it to the subject task. No CLONE_FILES,
threads, exec/unshare or arbitrary root lifecycle support is asserted. TASK_COMMIT
is emitted after copy_process's last failure point and before publication/runnable
execution. An allocation without commit is not a successful task birth.

Wire uses a new CPS prefix/version1, not silent conversion of CPL v2. Every event
has emission sequence, kind, scope, actor task, subject task, table/OFD/old cookie,
FD, flags and monotonic annotation. Actor is current at hook; subject is the child
for TASK_ALLOC/TABLE_NEW/TASK_COMMIT only. Root's armer actor and old namespace are
unavailable, not zero identities or absence proofs. File/table frees carry saved
scalar scope/cookie after allocator free; no post-free dereference. Task final
free/exit observation remains unimplemented. No authenticated boot or cookie wrap
guarantee; no pooling across captures. Emission order is not effect linearization.

Raw stage/width/scope/unknown validation is separate from a pure diagnostic of
local counters and recorded root allocation→namespace→commit linkage. Missing
creation records, lost root allocation, wrong actor/subject/namespace or identity
collisions cannot qualify provenance. Balanced local counters do not imply global
completeness. All9 permissions fixed false, global loss/prohibited counts unknown.
Pre-arm/inherited files, copy slot reads/owners, whole hook coverage, later cleanup,
SMP/NMI and instrumentation perturbation remain unqualified.

## Evidence, tests and non-goals

Before source implementation, run synthetic contract failures and actually boot
the old PR37 kernel with the new driver: missing CPS creation contract must fail.
Build from the exact preserved Linux6.12.113 archive in a new prefix with the
recorded compiler/dependencies; never change host kernel, packages or policy.
Capture all three cases; expected normal18 attempts,18/17/2 records and0/1/16
own-buffer failures (integration observations, not safety thresholds). Preserve
complete original serial and byte identities. Offline audit/test never boots VM.
Source files/ranges are byte-pinned, optional local source/assets verify separately.
Hash identity is not authenticity, authority, build closure or reproducibility.

Test malformed/stale wire, unavailable vs actual zero, actor/subject confusion,
root namespace substitutions, cloned task identity, lost allocation/commit,
duplicate/cross-role cookies, local loss/counter mismatch, exact runner recipe,
source/evidence drift and architecture separation. Run full regression, lint,
format,mypy,build,fresh wheel,CRLF,prior audits and one fresh final review.

No changes to src,compatibility,CI,old tests/evidence,PR8/9/37 or any earlier PR;
no merge,host tracing,device,vehicle,Params,cereal,controller,estimator,candidate,
application,external AI,longitudinal or upstream PR. One own stacked Draft only.
Retain prior blockers and four deferred minors. Recommend one next task; do not
claim general consumer/FD inventory/PR35 or PR30 bridge readiness.
