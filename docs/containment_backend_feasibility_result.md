# Containment backend feasibility result

2026-10-30 (Asia/Seoul). Base PR25 `3b1342f3e131642c6edbe3b18270a1fe1e7d216b`;
branch `design/containment-backend-feasibility`. **Design/source study only.**

## Delivered

- [Concrete conditional architecture](superpowers/specs/2026-10-30-containment-backend-feasibility-design.md): BPF LSM object guard + cgroup-v2 device BPF + non-CONTINUE seccomp broker + trusted external supervisor/observer.
- [Exact source evidence](evidence/containment_backend_sources.json): nine Linux files, eighteen byte-bound ranges, blob SHA-1/full-file/range SHA-256, reference commit adc218676eef25575469234709c2d87185ca223a.
- [24-fixture harmless protocol](containment_backend_qualification_protocol.md), with every actual result unavailable and explicit device-class limitations.
- [Conditional future implementation plan](superpowers/plans/2026-10-30-containment-backend-qualification.md), blocked on selected approved host/cohort/operation scope; no implementation starts here.

Manifest canonical digest (exclude only content_digest):
`3987fb388b254191ee963816d7c993221fe85f560a7541ba553d0f9f12f471e4`.
Digests identify bytes, not authenticity, a running kernel, policy adoption or authority.

## Findings that change the future design

1. Reference O_PATH returns before file_open LSM. A file_open-only guard is
   insufficient; the initial broker rejects all payload O_PATH, and other FD
   acquisition/inheritance paths need independent closure.
2. Kernel headers warn against notifier-only security policy / pointer-argument
   CONTINUE races. The broker copies its own arguments, never CONTINUEs and relies
   on independent object-level denial. Request labels do not prove object absence.
3. IN_ROOT and BENEATH are mutually exclusive. Kernel-scoped lookup failures have
   no unscoped fallback. Supplied numeric dirfd/PID alone is not a stable identity.
4. ADDFD_FLAG_SEND atomically injects/replies, not prior filesystem side effects.
   Initial qualification is read-only; write/create/truncate/build compatibility
   are not solved by the FD API.
5. Listener loss yields ENOSYS, not a tree kill. cgroup.kill rejects threaded
   cgroups. Independent stop/quiescence and persistent deny-link ownership are
   required; watchdog execution/latency remain unqualified.
6. Regular-file stand-ins cannot qualify char/block-driver hooks, actual inherited
   hardware FDs or real device cgroup denial. Even all24 passes would not clear Gate A.

## Source and preserved state

Linux v6.12 is an API-study snapshot only, not a maintained deployment choice or
current-host feature claim. Actual kernel/build/config/BTF/toolchain/program/link/
host bindings are all null. No probe or privilege test was performed.

R remains c2130730239bcdb4cbde9361ab90c8d99aa4ff55; C remains
f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3. Native patch8aa8b63b… and applied
tree6185197d… remain unchanged. Current ajouatom/openpilot:carrot-wip moved from
1fbce2fe7869fda285ee860f7172743e04f6022f to
cb724a0cb83772ad4fb069f8b83422f5e9cc60d0 via3be19f6332b89a632b6545cd360312152b6e41e6
and cb724a0cb83772ad4fb069f8b83422f5e9cc60d0. Compare metadata concerns lane-change
indicators/selfdrived, documentation, tests and upstream AGENTS.md; it does not
promote C, establish callback compatibility or qualify a runtime fingerprint.

All existing source/tests/CI, PR8/9/16–25, old evidence and acquired inputs are
preserved. PR25's Unicode minor remains deferred. No synthetic receipt is upgraded
to OBSERVED, no estimator/producer/writer/application bridge is added.

## Validation and review boundaries

Baseline and fresh final full pytest:1718 passed each. All nine source files,
eighteen ranges and canonical manifest digest independently recomputed locally;
all24 fixture results/actual observations remain null. Strict mypy74 source files,
ruff and format pass. Independent builder/reviewer findings, exact head and
hosted push/PR checks are recorded in the Draft PR before handoff. They validate
this design/artifact and regressions, not installed kernel enforcement.
No test of prose is presented as proof of backend behavior.

## Status

- BACKEND_FEASIBILITY_DESIGN_COMPLETE (conditional design, not demonstrated feasibility).
- BACKEND_RUNTIME_FEASIBILITY_UNPROVEN; BACKEND_TEST_HOST_UNSELECTED.
- HARMLESS_FIXTURE_QUALIFICATION_NOT_EXECUTED.
- ACTUAL_DEVICE_CLASS_COVERAGE_UNQUALIFIED.
- SECURITY_SENSITIVE_EXECUTION_NOT_AUTHORIZED.
- STRICT_NO_DEVICE_ATTEMPT retained; discovery proposal not adopted.
- GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED; B/C/D not started.

Retain FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED/NOT_QUALIFIED,
INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED,
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED,
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q,
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED, NO_EMPIRICAL_ESTIMATOR_BRIDGE,
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE,
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE,
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED,
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED, RUNTIME_FINGERPRINT_UNCONFIRMED,
WATCHDOG_EXECUTION_MODEL_UNRESOLVED, EXTERNAL_EXECUTOR_UNQUALIFIED,
APPLICATION_NOT_AUTHORIZED. All four permissions and runtime_qualified false.

No native build/import/model loading, container/image, host feature probe or
policy load, device node/access, Params/controller/schema/SubMaster, vehicle,
longitudinal, external AI, upstream/native-fork PR or merge.

## Next single task (not started)

**Select and explicitly authorize a dedicated device-free test host and exact
harmless-operation scope/cohort.** This resolves the plan's external prerequisite,
not the device/native/policy-adoption gates. Until that meaningful security scope
is approved, do not install a backend, load BPF/seccomp, create namespaces/cgroups
or substitute this managed cloud host. Ordinary implementation choices remain
delegated; this host/security boundary is not an ordinary local-code decision.
