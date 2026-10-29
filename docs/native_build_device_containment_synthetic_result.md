# Synthetic device-containment checker implementation

2026-10-30 (Asia/Seoul). Base PR24:
`04205c27226229d6cfc5ba50bb132d44ff885232`, branch
`feat/synthetic-device-containment-checker`. This implements all three tasks of
the [approved pure-checker plan](superpowers/plans/2026-10-30-cpu-device-containment-validation.md).
It does **not** implement the future observed receipt, a guard or a native runner.

## Implemented boundary

Repository-only `compatibility/native_containment`, outside the installed wheel:

- `parse_synthetic_case(str)` accepts only exact
  `synthetic-native-containment-case-v1` / `SYNTHETIC` JSON. Duplicate, missing,
  unknown keys, invalid enums, nonfinite values, bool-as-int, invalid UInt64,
  OBSERVED, empty events and enabled real permissions raise `ValueError`.
- Frozen slotted case/event/proof dataclasses recursively preserve immutable
  values. Direct constructors validate too. Event lists and flag arrays are
  defensively copied; duplicate flags reject; flags sort, event order does not.
- `canonical_digest(case)` uses sorted compact UTF-8 JSON, explicit nulls and
  SHA-256, with revalidation. Digest is content identity only. Policy context is
  external: changing only mode does not change a case's digest.
- Frozen `SyntheticPolicyContext` is a simulation. A true
  `hypothetical_adoption_for_test` is **not actual policy adoption**.
- `evaluate_synthetic(case, policy)` returns only `REJECTED` or
  `DIAGNOSTIC_EXPECTED_DENIAL_ONLY`, with every applicable reason deduplicated in
  the contract's enum order. There is no observed/run-reviewable/accepted state.
  Returned decisions defensively copy their reasons and validate status/mode
  consistency even when constructed directly.

The modeled scope is one discovery child plus a nonempty security-event list,
not a complete runtime trace or ordinary build-file IO stream. Typed event
actor/generation/clock/order mismatches reach reasoned rejection; malformed
schema/scalars fail parsing. The root clock is exactly
`synthetic-monotonic-ns-v1`. Sequence gaps alone do not invent a drop count;
unknown/false modeled trace-completeness rejects.

## Decision matrix

| Synthetic situation | Outcome |
|---|---|
| Current STRICT_NO_DEVICE_ATTEMPT, including denied candidate open | REJECTED / DEVICE_ATTEMPT_STRICT |
| Proposed mode without hypothetical adoption | REJECTED / POLICY_NOT_ADOPTED |
| Complete modeled proposed denial, every required condition true | DIAGNOSTIC_EXPECTED_DENIAL_ONLY; not real evidence or authority |
| Missing/false proof, unknown FD/effect/count, wrong cohort/identity/clock/order | REJECTED with typed reasons |
| Exposed PROHIBITED_HARDWARE, even denied | ENFORCEMENT_UNQUALIFIED plus other applicable reasons |
| Successful modeled prohibited handle/effect | PROHIBITED_CAPABILITY_ACQUIRED |
| Control/ioctl/mmap/privilege/unmediated-async attempt, even denied | CONTROL_OPERATION_ATTEMPTED |
| Network/FD-pass attempt, even denied | NETWORK_OR_FD_PASS_ATTEMPTED |
| Any noncandidate endpoint/operation/flags/errno/resolution | UNEXPECTED_DISCOVERY_OPERATION |

Only exact `/dev/kfd`, `/dev/nvidiactl`, `/dev/nvidia-uvm`, `/dev/kgsl-3d0`
requests, exact O_RDWR or O_RDWR|O_CLOEXEC, proven modeled ENOENT/EACCES/EPERM,
PRIVATE_NAMESPACE_ABSENCE or POLICY_DENIED_NO_OBJECT and all other required
claims can be diagnostic. Paths and CPU/errno labels do not prove resolution.
Sysfs mutation labels can add a rejection reason, never grant an exception.
No plausible first denial erases a fatal event elsewhere in the case.

## Tests and verification

TDD: Task1 RED51 then GREEN; Task2 RED48 then GREEN; Task3 initially exposed
eight mutable/inconsistent direct-decision failures, then a strict-mode direct
decision inconsistency. All were fixed with their failing tests retained.

Final focused suite: **220 passed**, **286/286 statements, 128/128 branches**.
Fixtures are hand-authored dictionaries only; no fake device nodes/syscalls.
Adversarial cases cover null versus zero/false, source drift, process/exec and
clock mismatch, duplicate/reordered timestamps/sequences, incomplete modeled
loader/descendant/observer proofs, proc-fd/relative/alias labels, hardware FD
imports, O_PATH/create/truncate/append, noncandidate devices and fatal operations.
Pyc/preload/clone/capture loss are represented by failed/unknown modeled claims;
these tests **do not detect those conditions on a real host**.

Architecture guards reject non-neutral imports and IO/execution calls; the
installed package has no bridge to the checker. Full regression: **1714 passed**. Lint/format,
strict mypy (including compatibility code), history/source audits and final
exact-head CI/reviewer results are recorded in the PR. The existing native offline
suite passed **192/192**, without skips or native execution. A prior full core
coverage run passed **1713/1713**, overall **98.52%**, before the additional final
strict-constructor regression. The final full-suite count is recorded in the PR.

Neutral sdist/wheel built without new dependencies, using already installed
system setuptools84/wheel because the project venv lacks that backend. A fresh
no-index/no-deps wheel environment imported **70 neutral modules** and verified
replay goldens, observation-v2, optional-adapter, knowledge, owner, science, H6
and H7 smoke tests. `compatibility` is absent from that installed wheel.

Local exact-source audit attempts exposed incomplete cached Git blobs; no source
or evidence was patched to hide this. Local manifest/history audits passed;
the existing CI's independent exact-source job is required before handoff.

## Preserved state and non-goals

PR24's manifest remains an immutable historical design snapshot, including its
then-false implementation-exists field. Its canonical digest remains
`4296dc27fa164d578ff4a4848c53640021d9aeaad4eb99b99d65654140b4f7e9`.
This result supersedes only that historical absence of a **synthetic checker**,
not absence of a real producer/collector/enforcer/verifier.

R remains `c2130730239bcdb4cbde9361ab90c8d99aa4ff55`, C remains
`f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3`, patch SHA-256 remains
`8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac`.
No earlier PR, source, native patch, old evidence, test, CI or policy is changed.

- SYNTHETIC_DEVICE_CONTAINMENT_CHECKER_READY (model only).
- STRICT_NO_DEVICE_ATTEMPT retained; discovery proposal **not adopted**.
- GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED; B/C/D not started.
- FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED / NOT_QUALIFIED.
- INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED.
- FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED; q remains unavailable.
- REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED; NO_EMPIRICAL_ESTIMATOR_BRIDGE.
- FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE and factor identification blocker retained.
- PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED.
- VEHICLE_APPLICATION_BOUNDS_UNRESOLVED; RUNTIME_FINGERPRINT_UNCONFIRMED.
- WATCHDOG_EXECUTION_MODEL_UNRESOLVED; EXTERNAL_EXECUTOR_UNQUALIFIED.
- APPLICATION_NOT_AUTHORIZED.

Every decision has evidence_kind SYNTHETIC and runtime_qualified=false; all
candidate_generation_allowed/application_authorized/runtime_accepted/
owner_proposal_allowed fields remain false. No native build/import/model load,
container/image, kernel policy/probe, device access, controller/schema/Params/
SubMaster, vehicle, estimator qualification, application/owner bridge,
longitudinal, external AI, upstream/native-fork PR or merge.

## Next single task (not started)

Separately scoped **backend feasibility and enforcement-evidence design** using
harmless fixtures: select a concrete MAC/device/syscall/observer architecture and
specify authoritative path/FD binding, immutable-loader closure and trace/guard
coverage. Those are unresolved; this checker cannot supply their truth. No actual
backend, policy adoption or native execution starts automatically.
