# Fixed harmless guest input object seal prototype

Base PR31: `ae7b3644984cd5ecc8fbb23532f5ec7e0da3998f`.
Branch: `feat/guest-input-seal-prototype`; stacked Draft, not an old PR merge.

## Delivered scope

Pure immutable contracts, strict bounded physical-LF/CRLF frames, canonical
content-only digest and eight fixed-scenario diagnostic checks. Separate static
C parent driver and opt-in diskless software guest runner. Python compatibility
package is outside the wheel. No second workload tracer, PR30 seal witness,
build-receipt bridge, real compiler target, Carrot/runtime/controller/vehicle or
host security-policy change. All previous packages/evidence/CI remain exact.

The host only compiles the harmless static C probe; it never executes that ELF.
Actual operations run inside QEMU10.0.13 TCG q35/qemu64,1CPU/768MiB,
Linux6.12.113+deb13-cloud-amd64. No KVM, network, disk, host share, QMP or device
passthrough. Existing prepared VM/input cohort is byte checked, not repaired or
downloaded. The180s timeout is bounded recovery, not a qualified watchdog.

Probe ELF:773512 bytes, SHA256
`1b879e954be351ec57ff9d68723242dadc2b1c8d363c108da93b9b37da45b4f7`.
Prepared asset `/workspace/scratch/input-seal-producer.HKE6j9/input-seal-probe`
is separate from temporary verification logs. Missing assets fail closed; normal
CI replays committed captures and never starts a VM or rebuilds the probe.
Manifest source/build-command identity is not compiler/header consumption
closure, historical build sealing, authenticity or authority.

## Seal semantics and fixed diagnostics

`MFD_CLOEXEC|MFD_ALLOW_SEALING|MFD_NOEXEC_SEAL` initializes EXEC seal32 and
non-executable mode0666. Adding WRITE8/GROW4/SHRINK2/SEAL1 gives47. EXEC seals
mode bits; no claim that it prohibits every executable mapping or arbitrary
execution. Full sealing belongs to the retained inode, not its pathname.

| Case | Diagnostic being checked | Expected full-sealed read binding |
| --- | --- | --- |
| IS01 | full seal, original/dup/reopened writable-FD writes, grow/shrink and shared-write mmap denied EPERM | yes |
| IS02 | writable shared map makes seal attempt1 EBUSY/no partial mask; backing mutation; explicit unmap/restore, attempt2 succeeds | yes, attempt2 only |
| IS03 | FUTURE_WRITE-only mask55 blocks new writes but existing mapping mutates backing | no |
| IS04 | two identical sealed objects; FD0 reused for wrong inode despite same hash/mask | no |
| IS05 | chmod0444; drop groups/uid/gid65534, no_new_privs; existing writable descriptor still writes | no |
| IS06 | actual initial symlink→sealed-object BIND+SNAP; alias replacement returns different object/bytes while original stays unchanged | no |
| IS07 | private COW mutation succeeds; backing bytes unchanged | yes, not private-memory immutability |
| IS08 | read-only shared map from writable descriptor retains MAYWRITE; EBUSY until explicit unmap | yes, attempt2 only |

The initial assumption that ordinary files would return EINVAL was rejected by
actual evidence: this guest's rootfs is tmpfs. Ordinary files start with seal1
(SEAL only), which is not a write seal. Unavailable seals are represented as
`None` plus errno and tested synthetically, never coerced to zero. No backend
fallback, downgrade or hidden retry. Named lifecycle attempts are separate
ordered events; later success cannot retroactively seal the failed epoch.

Actual final-source captures matched all8 fixed diagnostics:4 scoped sealed
object/read observations and4 unsafe/substitution controls. Record counts for
IS01..IS08:14,13,11,9,10,12,9,10. Raw serial bytes are stored losslessly as base64
inside deterministic gzip; no stdout repair, successful-flag inference or
synthetic replacement of raw evidence. Kernel6files/12ranges passed exact
file/blob/range hashes against the authenticated Linux6.12.113-1 source archive.

All snapshots hash actual17-byte pread buffers and record local fstat dev/inode,
mode and actual seal mask/errno. Expected and actual FD0 object identity are
recorded while both descriptors pin their objects. Device/inode is not durable
identity beyond this window; hash, pathname and FD number alone do not bind an
object. Driver MONOTONIC time is the explicit fixed schema clock domain, not a
kernel-event timestamp. OP reports libc result/errno, not raw syscall returns;
`map_shared` specifically reports normalized mmap status0/-1, never a pointer
identity. The actual expected mmap-denial result is-1/EPERM in both cases.
Private LOCAL bytes do not become backing-object bytes.

The trusted parent driver generates these diagnostics. It is not an independent
adversarial workload observer, collector authenticity proof, or comprehensive
all-FD/effect/kernel-read ledger. No global zero prohibited-operation count:
counts remain unavailable. Capture digest is content identity only.

## Verification checkpoint

Baseline2454 tests passed. Post-review pure contracts/wire/evaluation:
176/176 statements,82/82 branches (100%/100%); C/native line/branch coverage is
not claimed. Shared strict guest-envelope validation requires exact unique
LF-terminated markers (CRLF accepted), rejects malformed/conflicting markers,
and enforces kernel→capture BEGIN/END→exit0→DONE ordering.
Installed source aggregate coverage98.52% (4350 statements/1192 branches,
2548-test post-review coverage run). Pre-review full2531/focused77 and fresh
exact d3549ab CRLF2531 passed. Post-review full2548 and focused94 passed; source,
all8 actual guests, -Werror static build, lint/format437,mypy71+7 and fresh
vanilla+research wheel/replay/smokes/native192 reran green. Post-review CRLF and
remote CI are recorded at the final checkpoint, not inferred from earlier heads.

Independent review at exact `d3549abbff5b7873cf899ad5a24652cea3ed4891`:
**C0/I2/M0**. Initial pathname binding and strict execution-envelope findings
were reproduced RED, then fixed in one author TDD pass. No independent fix-head
re-review or C0/I0 claim. See [review and retained boundaries](guest_input_seal_prototype_review.md).

Source/native regressions: H2/H3/H4/H5/H6/H7 source/history validators,
observation-v2, unchanged PR31 captures and192 passive native patch tests passed.
Passive source compatibility is not execution/Carrot qualification. Ruff/format,
mypy71 installed source files and7 new modules passed at this checkpoint.
Build and fresh wheel import outside checkout passed; compatibility and NumPy
absent in vanilla wheel. Replay goldens, Carrot-contract, knowledge, owner,
H7 receipt and optional-dependency/research science+friction smokes passed.

## Status and remaining blockers

Overall `BLOCKED`. All9 build/promotion/runtime/device/policy/candidate/
application/owner permissions remain false. Scoped `object_seal_observed` is
only fixed diagnostic recognition, not an input-seal qualification predicate.

- GUEST_INPUT_OBJECT_SEAL_PROTOTYPE_IMPLEMENTED
- INPUT_SEAL_BACKEND_UNQUALIFIED
- NO_PR30_QUALIFIED_SEAL_WITNESS_BRIDGE
- FULL_BUILD_INPUT_CLOSURE_UNQUALIFIED
- EXECUTOR_UNQUALIFIED / EXTERNAL_EXECUTOR_UNQUALIFIED
- OUTPUT_PROMOTION_UNQUALIFIED
- FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED
- FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
- FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
- FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
- VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
- RUNTIME_FINGERPRINT_UNCONFIRMED
- REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED
- WATCHDOG_EXECUTION_MODEL_UNRESOLVED
- APPLICATION_NOT_AUTHORIZED

Existing Gate A BLOCKED, B/C/D not started, PHASE_8B_2B parked/runtime
qualification not completed. No application/approved baseline/owner proposal,
external AI, longitudinal, upstream PR, or modification/merge of PR8/9 or other
prior PR. Full namespace, hostile external writers, complete compiler/sysroot
input set, VM/host/hypervisor and output promotion remain outside proven scope.

## Next single task

Design an immutable **guest input namespace/descriptor handoff contract** that
binds the declared complete object set, sealed-object generation and actual
consumer FD lifetime before any build starts. This is the missing connection
between isolated sealed objects and PR31's consumption observations. Start with
design and counterexamples; do not automatically elevate these diagnostics into
PR30's qualified input seal witness or authorize a real build/device run.

## Final local checkpoint

Post-fix source `f4b2e7ba610b9dc47882fe329a0ffc63d186e9fd`:
full2548 (coverage99.74s), focused94, pure176/176 statements and82/82 branches,
installed src aggregate98.52%. Fresh core.autocrlf=true clone at this exact
source head: full2548 passed36.33s. All8 actual final-source guests and kernel
6files/12ranges audit reran green; final binary773512 bytes/hash above.
Ruff/format437, mypy71+7, build/fresh vanilla+research wheel/replay/smokes,
historical source validators/native192 all green. Working tree clean after
append-only commits; no old PR or protected runtime/schema/evidence edits.

This final documentation checkpoint changes no tested runtime/producer source,
manifest or raw captures. Final exact-head push/PR CI identities, PR state,
remaining external-gate completion and full author rulings are recorded in the
[Draft PR32 handoff](https://github.com/rownlvh8875-coder/cyberpilot-autotune/pull/32),
not inferred from the successful pre-fix d3549ab CI. No merge or next real build.
