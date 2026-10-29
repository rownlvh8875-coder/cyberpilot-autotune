# CPU-only device-containment contract design result

CPU_DEVICE_CONTAINMENT_CONTRACT_DESIGN_READY
CPU_DEVICE_CONTAINMENT_POLICY_PROPOSAL_NOT_ADOPTED
DEVICE_CONTAINMENT_IMPLEMENTATION_NOT_PRESENT
DEVICE_CONTAINMENT_RUNTIME_UNQUALIFIED
GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED
NATIVE_BUILD_EXECUTION_NOT_STARTED

## Delivered and preserved

New design/semantic contract/future pure-validation plan only:

- [Design and approaches](superpowers/specs/2026-10-30-cpu-device-containment-design.md).
- [Normative evidence/decision contract](native_build_device_containment_contract.md).
- [Semantic manifest](evidence/native_build_device_containment_contract.json).
- [Future synthetic-checker plan](superpowers/plans/2026-10-30-cpu-device-containment-validation.md).

Base PR23 `86ae36c5077ea6b69eab73e74a4f843159705a21`, branch
`design/cpu-device-containment`, stacked Draft against `audit/offline-native-build-inputs`.
Prior source, tests, package, CI, native patch, acquisition records and PR heads
remain unchanged. Acquired139 files are retained, not recopied or reacquired.

## Design decision, not a new execution grant

Retain strict rejection of **every hardware attempt**, including a denied one.
Propose, but do not adopt, a separate capability-closed discovery policy that
could classify only narrowly proven, pre-effect failures as diagnostic evidence.
No silent change to the earlier plan's stop-on-denial rule. Current Gate A stays
blocked regardless of design review, synthetic tests or CI.

Preferred future architecture: independent kernel deny controls plus a trusted
external observer, with exact source/loader/output/FD/namespace/clock provenance.
DEV=CPU/env-only filtering is not containment; source-filter patches are outside
scope. A microVM remains a possible separately reviewed alternative, not a tested
backend. No Docker runtime/profile/kernel support is claimed here.

Errno/pathname/stdout alone are insufficient. Missing guard/path/FD coverage is
unknown, not zero. Inherited FDs, aliases, policy/source mutation, observer loss,
sysfs control, raw-device/USB/CAN/camera/VFIO/network/privilege operations reject.
Conditional source paths are not observations of actual hardware or host mutation.

The required hardware-success/effect counts of0 are security invariants, not
measured values. Actual observations stay null. Receipt/digest is not provenance
authenticity, guard deployment, Gate A approval or application authority.

## Source state

R c2130730239bcdb4cbde9361ab90c8d99aa4ff55 and comparative
C f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 remain frozen. Preserved patch SHA-256
8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac and applied tree
6185197d6f334f745a9c082519013b8fe0376f65 remain unchanged; synthetic995… unpublished.

Current `ajouatom/openpilot:carrot-wip` moved two commits ahead of C to
1fbce2fe7869fda285ee860f7172743e04f6022f (bd1ea4e… then1fbce2f…). Compare metadata
includes log.capnp/modeld.py/workflow changes. This is a branch observation, not a
new semantic audit/source profile, runtime fingerprint or permission. New HEAD is
not promoted and no native schema is changed by this work.

## Verification boundary and retained blockers

Fresh builder/independent review, local preservation checks and hosted exact-head
push/PR CI are recorded in the Draft PR after completion. None executes/qualifies
the proposed kernel boundary. No actual implementation, synthetic checker, runner,
guard/profile, collector, kernel/native probe, image/container or native build was
created or run. Ordinary preserved CyberPilot tests/neutral package builds are
separate from actual native controller/device execution.

Full input/toolchain/image/LLVM/system closure, offline PEP517 installation,
model-pickle safety and the remaining transitive build-action audit remain
unqualified. H7 source policy, q absence, estimator separation and all false
candidate/application/runtime/owner permissions remain unchanged.

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

The design/planning skills kept attempted access, denied capability and CPU
selection separate, and made policy adoption an explicit future gate rather than
silently relaxing the existing rejection rule.

## Recommended next SINGLE task

Implement only the **pure offline synthetic contract checker** in the linked plan,
if separately approved. It can expose contradictory/insufficient evidence without
device/kernel/native execution or adopting the proposed denial policy. It must
reject OBSERVED inputs and keep every real permission/qualification false.
Do not automatically start that implementation, backend qualification or B/C/D.
