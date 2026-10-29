# Synthetic CPU Device Containment Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement only a pure synthetic contract checker for the proposed
device-containment evidence; never establish actual guard/policy/runtime authority.

**Architecture:** Strict immutable JSON parsing and canonical identity feed a pure
synthetic evidence evaluator. Its only inputs are synthetic records and simulated
policy context; OBSERVED records reject because no trusted binding/backend exists.
No kernel collector, sandbox runner or native adapter is part of this plan.

**Tech Stack:** Python>=3.12.3 standard library, existing pytest, ruff and mypy;
repository-only compatibility code, no new installed-wheel dependencies.

**Spec:** [design](../specs/2026-10-30-cpu-device-containment-design.md),
[contract](../../native_build_device_containment_contract.md),
[semantic manifest](../../evidence/native_build_device_containment_contract.json).

## Global Constraints

- This plan is FUTURE WORK, not executed or automatically authorized by design approval.
- Current rule remains STRICT_NO_DEVICE_ATTEMPT; CAPABILITY_CLOSED_DISCOVERY_PROPOSAL is not adopted.
- R c2130730239bcdb4cbde9361ab90c8d99aa4ff55, C f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 and patch8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac stay fixed.
- Gate A BLOCKED; no B/C/D, native/source/controller/schema/Params/SubMaster/application/owner change or execution.
- No installs, images/containers, kernel probes/policy loading, physical/synthetic device-node creation, hardware callbacks, native imports, model unpickling or network needed.
- New code stays in compatibility/native_containment, outside the installed neutral package; old policy/receipt/evidence/tests/CI remain unchanged.
- All candidate/application/runtime/owner and real-qualification flags are absent or fixed false.

## Review Focus

1. Caller marks a record OBSERVED/guard-active: reject; synthetic logic cannot manufacture trust.
2. Empty trace/None is mistaken for zero capability: reject incomplete fields, preserve null versus0/false.
3. Denied control/alias/FD escape is mislabeled expected discovery: fatal reasons take precedence.
4. Mutable path/argv/CPU label substitutes for bound source/resource/cohort: reject unknown binding.
5. Simulated proposal adoption leaks into current policy or execution: fixed false real permissions and no IO/import bridge.

---

### Task 1: Strict synthetic evidence representation

**Files:** Create `compatibility/native_containment/__init__.py`, `contracts.py`,
`tests/unit/test_native_containment_contracts.py`.

**Interfaces:** `parse_synthetic_case(raw: str) -> SyntheticContainmentCase`
and `canonical_digest(case: SyntheticContainmentCase) -> str`.
The exact fields/types are in the manifest's `synthetic_case_v1` block, schema
`synthetic-native-containment-case-v1`. It models one discovery child and a nonempty
security-event list, not the full future observed receipt. Cases are frozen,
recursively immutable and defensive-copied. No active guard/executable policy.

- [ ] Obtain explicit approval for this pure implementation only; implement the
  exact `synthetic_case_v1` fields, enums, nulls and parser ValueError rules.
- [ ] Write RED tests for duplicate/unknown keys, OBSERVED kind, bool-as-int,
  NaN/Inf, invalid sequence/time/generation, unsupported schema and nested mutation.
- [ ] Implement the minimal parser/immutable types without native/application,
  openpilot/cereal/Params or execution imports. Reject missing/ambiguous fields.
- [ ] Write/run canonical identity tests: stable key order; source/mode/generation
  differences change digest; null differs from0/false; digest grants no authority.
- [ ] Run the new tests and full `python -m pytest -q`; commit only on green.

### Task 2: Pure synthetic decision matrix

**Files:** Create `compatibility/native_containment/validation.py` and
`tests/unit/test_native_containment_decisions.py`.

**Interfaces:** Consumes Task1's case. Define frozen
`SyntheticPolicyContext(mode, hypothetical_adoption_for_test, expected_source_cohort_digest)`
with the manifest's context field types, and
`evaluate_synthetic(case, policy) -> SyntheticContainmentDecision`.
Context is explicitly a simulation, never a trusted adoption reference.
Decision contains deterministic ordered reasons and synthetic-only classification,
with all real qualification/permission flags false. The eight modeled_proofs map
to manifest reasons; null/false rejects. Case source, actor/generations/domain,
sequence/result/resolution/counts and exact candidate conditions must all match.
No OBSERVED record is accepted and no run-reviewable/authorization verdict exists
in this first implementation.

- [ ] RED: strict-mode candidate denied open returns REJECTED/DEVICE_ATTEMPT_STRICT;
  proposed mode without hypothetical adoption returns REJECTED/POLICY_NOT_ADOPTED.
- [ ] RED: a complete modeled proposal candidate may classify as
  DIAGNOSTIC_EXPECTED_DENIAL_ONLY, never a run grant or runtime-qualified result.
- [ ] RED: missing guard, resolution, FD/effect result, lineage, clock or complete
  coverage rejects. ENOENT/CPU string alone and empty logs cannot pass.
- [ ] Implement the contract's all-required-conjunction checks and deterministic
  reason order. Fatal operations/successful prohibited capabilities always reject,
  even if another event is a plausible expected denial.
- [ ] Run both new modules and full pytest, then commit. Do not add a collector,
  network, thread, process, file writer or evaluator-to-native/application bridge.

### Task 3: Adversarial fixtures, boundary guards and handoff

**Files:** Create `tests/fixtures/native_containment.py`,
`tests/unit/test_native_containment_adversarial.py`,
`tests/architecture/test_native_containment_boundary.py`, and
`docs/native_build_device_containment_synthetic_result.md`.

**Interfaces:** Consumes Task1/2 APIs; fixture builders produce only synthetic data.
Result documents modeled decisions separately from unobserved enforcement.

- [ ] Add RED cases for missing/unknown guard and source/input drift; stale pyc/
  preload/loader identity; PID reuse/exec generation; wrong clock; duplicate,
  reordered, dropped or unmatched events; child/clone/observer loss.
- [ ] Add RED cases for proc-fd/dirfd/symlink/hardlink ambiguity, inherited/passed
  hardware FDs, successful O_PATH/device open, ioctl/mmap, network, privilege,
  sysfs mutation attempts and noncandidate endpoint/flag combinations.
- [ ] Pin architectural absence of openpilot/cereal/Params/application/owner/native
  imports, subprocess/socket/thread/filesystem writers, policy loading and IO.
  Fixtures are dictionaries/dataclasses, never mknod or actual syscall probes.
- [ ] Run full pytest, lint/format/mypy as appropriate for the new compatibility
  code, existing source/native regression suite and neutral build/fresh wheel.
- [ ] Fresh exact-head independent review; publish a stacked CyberPilot Draft PR,
  preserving earlier heads and Gate A BLOCKED. No native-fork/upstream PR/merge.
- [ ] Recommend exactly one next task: separately scoped backend feasibility/
  enforcement-evidence design, not automatic guard/native execution. Stop.

Future backend qualification is deliberately NOT an executable task in this plan.
It must first choose/prove a concrete kernel/MAC/device/audit backend and trusted
path/FD binding using harmless fixtures under separate security-sensitive approval.
