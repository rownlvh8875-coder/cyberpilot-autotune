# Offline Full-Native-Build Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Obtain an honest, reproducible offline full-host native build comparison
of exact R and its unchanged passive friction observation patch, without runtime
or vehicle qualification.

**Architecture:** Acquire/audit inputs, then seal an isolated Ubuntu24.04 amd64
image, then build cold baseline/patch trees and assess only compile/schema
evidence. Each stage has an explicit stop/approval gate; this planning task
executes none of them.

**Tech Stack:** Git, uv/Python3.12, SCons4.11.1, C/C++/Cap'n Proto, tinygrad
CPU:LLVM, locked ARM GCC, offline unprivileged container.

**Spec:** [design](../../native_build_verification_design.md),
[dependency inventory](../../native_build_dependency_inventory.md).

## Global Constraints

- R `c2130730239bcdb4cbde9361ab90c8d99aa4ff55`; patch SHA-256 `8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac`.
- Patched tree `6185197d6f334f745a9c082519013b8fe0376f65`; C/current branch never auto-promoted.
- Profile `PC_X86_64_ROOT_DEFAULT`: Ubuntu24.04 linux/amd64, Python `>=3.12.3,<3.13`, locked all-extras, root default extras enabled, no --minimal.
- Actual full native build, dependency installation, image acquisition and containers have NOT started. Approve each future gate explicitly.
- No native source/lock/patch edits, native-fork PR/publication, merge, deploy, device/vehicle, real Params/SubMaster, service launch, empirical data, estimator/application bridge or authority changes.
- Final build is offline with isolated inputs/caches/outputs; preserve TLS/proxy/CA/signature checks during separately approved preparation.
- No image tag/version placeholders may pass the seal gate; unresolved input means BLOCKED, not permission to guess.

## Review Focus

1. Offline cache appears populated but a VCS/PEP517/native archive is absent: missing-input check must fail before SCons; never retry online.
2. SCons help/configuration touches state: audit and sandbox it as execution, not a preflight read-only command.
3. A successful subset or stale generated object is mislabeled full: reject non-root/minimal/stale profiles; require default-target and cold-cache evidence.
4. Different image/CPU/path/dependency inputs masquerade as patch effects: B/P equality checks must reject changed cohort inputs.
5. Debug firmware/model/codegen artifacts escape quarantine: denied-action checks must block services, flashing, Params/transport/device and uploads.

---

All steps below are unchecked future work. Operational verification steps replace
feature TDD where no program is being changed. If future receipt/probe tooling is
implemented, write its negative tests before implementation and keep it outside
the installed neutral package/native patch.

### Task 1 (gate A): Acquire and audit immutable input closure

**Files:** Create `docs/evidence/offline_native_build_inputs.json` and
`docs/offline_native_build_input_acquisition_result.md`; temporary artifacts live
outside the repository in a newly allocated task directory. No native tracked edits.

**Interfaces:** Consumes the design/source evidence and existing
`docs/evidence/carrot_passive_native_registration.json`. Produces an
`offline-native-build-inputs-v1` candidate manifest with the inventory's required
fields; `seal_status=UNSEALED` until Task2 succeeds.

- [ ] Obtain explicit acquisition/audit authorization; record task directory and
  allowed downloads, sandboxed package hooks, trust inputs and storage budget.
- [ ] Verify R and all source blobs/modes offline; reconstruct patch and compare
  complete trees and exactly seven changed entries to committed registration.
  Missing objects, patch byte drift or a fetch of synthetic995… must reject.
- [ ] Enumerate all selected all-extras lock/PEP517/VCS/native/system/model inputs.
  Acquire by immutable identity with TLS/signature/hash checks; do not execute
  upstream setup or alter lock/source. Record unavailable artifacts as blockers.
- [ ] Audit transitive configuration/import/action IO, including codegen, Panda,
  tinygrad CPU discovery, hardware/model catalog and package hooks. Record allowed
  subprocesses/write paths; real Params/SubMaster/service/device needs BLOCKED.
- [ ] Check negative cases: omit one required source blob, VCS build artifact or
  model payload from a temporary manifest/closure copy; each must fail validation.
  No network fallback or SCons invocation is allowed by this validation check.
- [ ] Publish acquisition inventory/log digests and remaining gaps. Commit only
  new manifests/docs, not downloaded binaries, keys or native source.

### Task 2 (gate B): Seal toolchain image and offline environment

**Files:** Create external preparation recipe and
`docs/evidence/offline_native_build_seal.json`; update Task1 manifest's seal status
only after validation. Document exact recipe path/hash in the seal; no Dockerfile
is introduced by the current planning task.

**Interfaces:** Consumes Task1's complete closure/audit. Produces a digest-pinned
image plus immutable source/dependency inputs and an environment/write/action
allowlist, identified as `offline-native-build-seal-v1`.

- [ ] Obtain separate preparation authorization and select exact Ubuntu image,
  Python3.12 patch, uv, compiler/binutils/LLVM and system-package snapshot.
- [ ] Build only in disposable preparation isolation. Preserve session proxy/CA
  via secret trust mounts; never put credentials in layers, copy a host home,
  mount Docker socket/devices or invoke host udev/setup. Audit package hooks first.
- [ ] Reinstall native all-extras from sealed inputs with
  `uv sync --locked --offline --all-extras` in a fresh isolated tree. Validate
  manifest/lock immutability and exact installed versions/ABI. No root SCons yet.
- [ ] Verify seal rejection for mutated image digest, uv binary, lock, Python ABI,
  LLVM/native archive or missing input. Record observed CPU/backend capability
  without spoofing source architecture or performing model/controller execution.
- [ ] Budget full input/image/vfs storage, four cold builds and artifact retention;
  measure/record limits. Unresolved capacity or forbidden import/action blocks C.
- [ ] Freeze image/config/artifact digests, allowlists and receipts; fresh review
  must confirm no unresolved gate before build authorization. Commit seal docs.

### Task 3 (gate C): Four cold full-host builds

**Files:** Create `docs/evidence/offline_native_build_runs.json`; raw logs/artifacts
stay in the task evidence store with hashes, not the Git repository.

**Interfaces:** Consumes Task2 seal and complete R/patched trees. Produces B1/B2/P1/P2
run records: seal digest, source tree, environment/CPU/backend, exact command,
exit status, target inventory, compiler commands, write/denial logs and artifact
path/size/SHA-256. No runtime readiness or authorization field can be true.

- [ ] Obtain explicit native-build authorization. Validate every seal/input and
  the action audit before any SCons command, including -h/-n. Reject subset,
  --minimal, inherited generated files or nonempty shared caches.
- [ ] Allocate each sandbox with source at `/work/native`, separate task-specific
  caches/outputs, fixed dependencies and network disabled. Run serially; keep the
  same CPU feature exposure/path/environment for all four. Never overwrite an
  earlier run. Unset inherited compiler/GPU/model/RELEASE/CERT/DEBUG/cache-lock
  overrides; set only the reviewed environment allowlist and SOURCE_DATE_EPOCH.
- [ ] In each sandbox run `.venv/bin/scons -j2 --verbose` from root. Capture full
  exit/log/target evidence; stop on build/configuration failure, non-CPU backend,
  forbidden side effect or attempted network. Do not skip models/firmware/host
  tools, relax Werror/link whitelist or patch the source to pass.
- [ ] Verify B/P cohort equality and cold-cache proof. Negative receipt checks
  must reject a changed image, CPU exposure, path, lock, cache or command profile.
- [ ] Quarantine all executable/model/firmware outputs. Assert no runtime entry
  point, blanket native pytest, Params/SubMaster, flashing or deployment occurred.
  Commit only new run manifests/report, preserving failed-run evidence too.

### Task 4 (gate D): Schema/repeatability assessment and handoff

**Files:** Create `docs/offline_native_build_verification_result.md` and
`docs/evidence/offline_native_build_assessment.json`; schema probe source/tests
belong to the external task evidence store, with their content hashes recorded.

**Interfaces:** Consumes four complete Task3 run records and generated cereal
C++ artifacts. Produces separate compile, schema probe and repeatability verdicts,
explicit blockers and a content-only evidence digest.

- [ ] Confirm D authorization covers only standalone schema inspection/probe,
  never launching built services. Inspect generated C++ schema symbols/types/
  ordinals against existing wire map/compiled-schema interoperability tests.
- [ ] Write failing negative probe cases first: wrong Float32/raw stage,
  unavailable→zero substitution, incompatible schema or missing generated type.
  Compile/run only the synthetic schema-only probe (cereal/KJ/Cap'n Proto), with
  no common/controller/service imports, sockets, Params or vehicle inputs.
- [ ] Compare B1↔B2 and P1↔P2 raw artifact hashes, including models/debug firmware;
  inventory B↔P propagation and every unexplained variance. No arbitrary byte
  normalization or blanket binary-equality claim. Exit0 alone is compile only.
- [ ] Report FULL_HOST_NATIVE_BUILD_PASS only if all four complete default builds
  pass, the C++ schema probe passes, and target/closure integrity is proven.
  Report repeatability separately; unresolved raw variance keeps it unqualified.
- [ ] Run preserved CyberPilot core/native/source audits and exact-head fresh
  independent review. Publish only a CyberPilot Draft PR/evidence report; no
  native-fork/upstream PR, merge or authority/schema-policy update.
- [ ] Retain all runtime/source-registration/empirical/application blockers and
  false permissions. Recommend exactly one next task and stop; no auto execution.
