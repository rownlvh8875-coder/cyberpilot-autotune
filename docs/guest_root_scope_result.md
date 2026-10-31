# Managed-root creation-time provenance — result

Base PR37 `06e218ca9e17af9547fc7871df70d2b9415f2cb9`.
Branch `feat/guest-managed-root-provenance`; own append-only stacked Draft only.
[Contract and exact limits](guest_root_scope_contract.md).

## Actual observations

Compiled a fixed static PID1 and actually booted it on the unchanged PR37 kernel:
missing `/proc/cpscope` returned errno2; no CPS source frame was accepted (RED).
Fresh source extracted from the same pinned Linux6.12.113 archive, complete9-file
patch built in a new owned prefix with GCC14.2.0/binutils2.44 and unchanged prepared
dependencies. No host package/kernel/policy changes. No new dependency downloads.

Actual frozen-runner fresh512MiB/one-vCPU TCG guests:

| Case | Own-buffer attempts | Received records | Own-buffer reservation failures | Recorded root creation linkage |
|---|---:|---:|---:|---|
| NORMAL |18|18|0|observed, unqualified |
| ROOT_BIRTH_LOSS |18|17|1|not observed |
| SMALL_BUFFER |18|2|16|not observed |

37 original raw records retained. Local counters balance in all three; root
allocation omission remains visible even with balanced counters and source root
metadata. No global-zero or lossless claim. Complete original serial, initramfs,
kernel/driver/config/source/patch/tool byte records are committed separately.

Normal source sequence:

1. PID1 armer actor unknown → TASK_ALLOC task1/scope1.
2. TABLE_NEW namespace2/subjecttask1/oldparentnamespace unknown.
3. TASK_COMMIT task1/namespace2, before first root workload operation.
4. Root actor1 creates OFD3, installsFD5, dup-writesFD40,sets CLOEXEC,replacesFD40.
5. Actor1 allocates distinct childtask4/copiesnamespace5from2/commitschild4.
6. Actor4 closesFD5/40; namespace5 allocator free emits saved scalars.
7. Actor1 closesFD5/40; OFD3 and namespace2 allocator frees emit saved scalars.

Root/task creation identity no longer depends on a borrowed pre-existing PID1
namespace pointer. PID1 identity,inherited stdio/proc OFD births,copy slot history,
task final-free and complete source/owner/loss closure remain unavailable.
Boot-relative cookie1/2/etc are not portable IDs or authenticity witnesses.

Prepared new assets: `/workspace/scratch/root-scope-producer.wggKv4`.
Kernel SHA256 `fb06e73c11ee893e5d3bf0e02263362f2893863cb670becff8246bcd91562b7b`.
Driver SHA256 `ffcc3b280edf1c645a8605e5ce46648ab61c4c9873664fc3bb3e590a6b2d7627`.
Old PR37 prepared assets and all earlier captures remain unchanged. Binaries not
committed. No source/kernel/tool substitution or host execution of guest ELF.

## Verification record

Baseline3014passed36.22s. New parser tests missing API RED→GREEN; image/runner9
missing-API cases RED→GREEN;25 byte-audit cases missing API RED→GREEN. Author
root-parent namespace invention regression RED→GREEN. Explicit mypy re-export
correction after2attribute errors; no runtime semantics change,source hashes
refreshed and all three guests recaptured through the final frozen runner.
After the review fix,71 focused tests pass,including2architecture guards. Pure
model/image149statements,46branches100/100%,no exclusions. This is Python coverage,
not kernel correctness.
Optional local source/asset audit passed7pristine/9patched files/43ranges and all
recorded selected prepared inputs/QEMU cohort. Default audit never claims those
optional checks were performed. Post-fix full3085passed35.63s;ruff/format,mypy71installed+
5prototype modules,sdist/wheel build pass. Fresh isolated wheel outside checkout:
all installed modules,replay,Carrot contract,knowledge,owner,science,H6/H7 smokes
pass; tests/compatibility/NumPy absent before research extra;research smokes pass
after explicit extra installation. All prior source/history/offline/PR37 audits
and192passive native cases pass. CRLF/exact-head CI/independent review are recorded
in the own PR handoff after observation,not inferred from an earlier head.

One fresh independent review on `6513170ae3c1af0eb0dfa00054aa080e63379304`:
C0/I1/M0. Reviewer independently ran3082tests and verified source/assets/original
serial/images; no kernel compile or guest execution was repeated independently.
I1: a non-root creation triplet with unavailable creator skipped parent/namespace
checks. Author reproduced3balanced-counter variants (old namespace unknown,actual,
substituted),all RED,then required a non-root creator and made them GREEN in one
fix pass. All three fixed guests were recaptured through refreshed frozen Python
source bindings; kernel/driver/source patch bytes unchanged. Old pre-review serial
and images remain in the new producer's `pre-review` directory and previous Git
evidence. The full post-fix suite,audits,coverage,wheel and type/lint checks reran.
No second independent review: final fix head differs from the reviewed head;
report both,do not label the final head independently C0/I0 reviewed.

The guest reported TSC calibration failure; timestamps stay hook annotations,
not accurate timing or effect-order evidence. General workloads/shared namespaces,
SMP/NMI/wrap,task final-free/late cleanup,copy inventory/complete ownership/global
closure,authenticity/cross-boot identity/reproducibility/sealing,portable asset
execution and manual dataclass input validation remain expressly unqualified.

## Status / retained blockers

BOUNDED_MANAGED_ROOT_CREATION_PROVENANCE_IMPLEMENTED.
BOUNDED_MANAGED_ROOT_CREATION_OBSERVATIONS_CAPTURED.
QUALIFIED_LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED.
LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN.
COPY_CUT_PROOF_UNAVAILABLE.
LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED.
OBSERVER_PERTURBATION_UNQUANTIFIED.
CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED.
NO_PR35_SEMANTIC_ADAPTER.
NO_PR30_QUALIFIED_BRIDGE.

FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED (FD telemetry is not controller friction).
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED.
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED.
RUNTIME_FINGERPRINT_UNCONFIRMED.
WATCHDOG_EXECUTION_MODEL_UNRESOLVED.
EXTERNAL_EXECUTOR_UNQUALIFIED.
APPLICATION_NOT_AUTHORIZED.

All9 permissions false; actual global loss/prohibited counts None. Prior PR34M1
and PR33M1/M2/M3 remain deferred unchanged. Earlier PRs,main,installed runtime,
compatibility,CI,tests/fixtures,experiments and all old evidence/code unchanged.

## Next single task

**Fixed managed-root fork-copy evidence design**: define per-slot read/copy source
witnesses and their non-atomicity/unknown inherited-OFD limits in this exact source
profile, before attempting an inventory adapter. Creation linkage alone cannot
answer which FD bindings were inherited. No automatic general observer,PR35/PR30
bridge,device,vehicle or application qualification.
