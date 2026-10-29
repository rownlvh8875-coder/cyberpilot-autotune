# Offline full-native-build verification planning result

OFFLINE_FULL_NATIVE_BUILD_VERIFICATION_PLAN_READY
NATIVE_BUILD_EXECUTION_NOT_STARTED
FULL_HOST_NATIVE_BUILD_UNQUALIFIED
OFFLINE_BUILD_ARTIFACT_CLOSURE_UNAVAILABLE
IMAGE_TOOLCHAIN_INPUTS_UNPINNED

## Delivered, not executed

This task follows PR21's single recommendation: **prepare a plan**, not run a
native build. New files only: [design](native_build_verification_design.md),
[dependency inventory](native_build_dependency_inventory.md),
[future gated execution plan](superpowers/plans/2026-10-29-offline-native-build-verification.md)
and [pinned source evidence](evidence/native_build_verification_sources.json).
No new runtime/tooling/producer/validator implementation, installed source, native
patch/schema, old evidence, test, lock, dependency or CI modification.

Base is CyberPilot PR21 `efdec237947bb47eebdbecebb2680114f085c3eb`.
Branch `design/offline-native-build-verification`; stacked Draft against
`fix/native-registration-unicode-paths`, not main or a native fork. Earlier PRs
are preserved. No Ready/merge/rebase/force push.

Future selected profile: Ubuntu24.04 linux/amd64 root-default all-extras host
build, no --minimal; includes C++ cereal, model compilation, host tools and debug
Panda firmware. Gate A acquire/audit → B seal → C cold B1/B2/P1/P2 builds → D
schema/repeatability assessment. Each future stage needs explicit approval.
Current Debian host and healthy Docker daemon do not satisfy the sealed profile.

## Frozen source and drift

R `c2130730239bcdb4cbde9361ab90c8d99aa4ff55` remains primary; C
`f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3` remains comparative. Patch SHA-256
`8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac`, applied
tree `6185197d6f334f745a9c082519013b8fe0376f65` and offline synthetic recipe
commit `9957868acc7459f515f1b79e9315cf93a878d933` are unchanged; not published.

Designated `ajouatom/openpilot:carrot-wip` was re-queried and remains C unchanged.
An initial lookup used the user fork's same-named branch; that cross-repository
comparison cannot establish movement/rewind and was corrected before publication.
Evidence now binds repository and branch explicitly. No promotion, source-policy
change, branch refresh or vehicle/runtime inference.

## Important findings and verification scope

- Native-cpu CI is only a subset; pycapnp/body parity tests are not a full native
  build. Root default includes models/host tools/firmware; do not omit them.
- SCons help/dry-run is not a safe read-only check: Panda writes headers at
  configuration and modeld probes tinygrad devices. No SCons command was run.
- Source setup self-updates uv and changes host udev; do not invoke it here.
  Pinned offline source/dependency/image/LLVM/PEP517 closure is still absent.
- Twenty-five exact-R source/lock files have raw hash/Git-blob evidence. Model
  blobs have tree/size metadata only; weights were not downloaded. Full transitive
  build-action/import purity and resource sufficiency are still future gates.
- Existing core1494 and mandatory native192 tests pass, no native-suite skips;
  lint/format pass. These are preservation checks, not native-build evidence.

Exact-head independent builder/final review and hosted push/PR CI results will
be recorded in the Draft PR, not asserted before they run or inserted afterward
into an already reviewed head. Hosted CyberPilot CI does not execute gate C.

## Retained gates

FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED
NO_EMPIRICAL_ESTIMATOR_BRIDGE
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_EXECUTOR_UNQUALIFIED
APPLICATION_NOT_AUTHORIZED

q_observed remains null, consumed-source cohort incomplete, all candidate/
application/runtime/owner permissions false; H7 still rejects the instrumented
source/schema pair. No vehicle, Params, real SubMaster, service, native build,
image/container acquisition, empirical data, estimator qualification, candidate,
application/owner bridge, longitudinal or external AI integration, deployment,
native-fork/upstream PR or PR8/9 modification.

The planning skills kept configuration side effects inside future execution gates
and separated content/build repeatability from runtime/application authority.

## Recommended next SINGLE task

Gate A: acquire and freeze the complete offline native-build **input closure and
static build-action audit**. Complete source availability, pinned toolchain/image
inputs and forbidden-side-effect review must precede any native SCons execution.
This recommendation does not start acquisition, image preparation or a build.
