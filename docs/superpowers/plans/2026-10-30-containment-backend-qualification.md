# Harmless Containment Backend Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separately authorized regular-file-only harness that reports
named primitive/lineage observations without qualifying device containment.

**Architecture:** Explicit external host/scope approval precedes any host work.
Pure report validation is separate from an opt-in C17/libbpf/seccomp harness;
neither accepts native/Carrot payloads or grants runtime/application authority.

**Tech Stack:** Existing Python3.12 standard library/pytest for pure tests;
C17, Linux native x86_64, libbpf/clang for the future host harness, with exact
maintained kernel/config/BTF/toolchain inputs supplied by the approved host cohort.
No dependency, compiler, VM or host is installed/chosen by executing this document.

**Spec:** [binding design](../specs/2026-10-30-containment-backend-feasibility-design.md)
and [HF01–HF24 protocol](../../containment_backend_qualification_protocol.md).

## Global Constraints

- **NOT_EXECUTABLE_BACKEND_HOST_UNSELECTED.** This plan is not implementation or execution approval.
- Before any task, the operator must have separately approved the exact dedicated device-free test host, maintained kernel/build/config/BTF/toolchain cohort, privilege/cgroup/BPF/seccomp/namespace operations, disposable filesystem scope and independent recovery supervisor. Record external authority, not a self-authored approval flag. The current managed cloud instance is not an implicit target.
- If any external precondition is absent or ambiguous, stop without installing, compiling, probing, configuring or running. These are missing authority/input bindings, not builder discretion or placeholders to guess.
- Only owned temporary regular files/directories/symlinks and ordinary pipe/FD fixtures. No device nodes, actual device-class tests, native/Carrot/model/Params/controller/SubMaster/services/vehicle payloads, networking or host mounts/data.
- STRICT_NO_DEVICE_ATTEMPT retained; CAPABILITY_CLOSED_DISCOVERY_PROPOSAL not adopted. Gate A BLOCKED; B/C/D not started.
- Initial broker profile is read-only; reject all O_PATH and create/write/truncate, unsupported ABI/flags, unbound dirfd/cwd, EAGAIN and unknown evidence. No CONTINUE, unscoped fallback or policy widening.
- Use RESOLVE_IN_ROOT|RESOLVE_NO_MAGICLINKS for the approved root; never combine IN_ROOT and BENEATH. ADDFD_FLAG_SEND does not transact prior filesystem effects.
- Host-specific source/hook review must precede loading any program. v6.12 commit adc218676eef25575469234709c2d87185ca223a is a source reference only, not the host kernel.
- Installed package, old checker/evidence/tests/CI, source/native patch and prior PRs stay unchanged. New harness is repository-only and never part of default pytest/CI execution.
- All runtime_qualified/candidate_generation_allowed/application_authorized/runtime_accepted/owner_proposal_allowed false. Harmless results cannot qualify actual device enforcement, closure, watchdog or native compatibility.

## Review Focus

1. A caller fabricates host approval/guard-active strings: pure validation must not establish external authority; missing trusted scope is a hard stop.
2. A regular-file stand-in is mistaken for a real char/block/driver test: outcomes support only named harmless claims; device coverage stays UNQUALIFIED.
3. A tracee changes args/dirfd/generation or cancels a request: no CONTINUE or replacement-task FD injection; unknown lineage rejects.
4. A listener/observer/guard dies, or cgroup.kill is unsupported: no ENOSYS-as-killed inference, run receipt invalid and observed stop recorded separately.
5. Generated/preload/pyc inputs or effectful open drift: reject closure/effects; recomputed hashes or atomic ADDFD cannot conceal prior writes.

---

### Task 1: Pure scope/report boundaries (after external preconditions only)

**Files:** Create `compatibility/containment_backend_harmless/__init__.py`,
`records.py`, `validation.py`, `tests/unit/test_backend_harmless_records.py`.

**Interfaces:** Frozen `HarmlessFixtureResult(fixture_id, evidence_cohort_digest,
outcome, actual_observations, reasons)`; observations use immutable typed optional
fields, never arbitrary mutable mappings. Define frozen `HarmlessObservations`
with digest-or-null fields `kernel_build_digest`, `kernel_config_digest`,
`btf_digest`, `source_loader_digest`, `object_receipt_digest`, `fd_lineage_digest`;
bool-or-null fields `guard_active`, `collector_bound`, `process_lineage_complete`,
`trace_complete`, `tree_exit_observed`, `broker_effects_observed`; `clock_domain`
is nonempty UTF-8 str-or-null; `successful_prohibited_handles` and
`successful_prohibited_effects` are UInt64-or-null (fixture scope only, not actual
device measurements). Every field is required, with null representing unknown.
`validate_harmless_result(raw: str) ->
HarmlessFixtureResult` enforces exact keys/enums, canonical UTF-8, finite values,
HF01–HF24 scope and fixed-false permissions. Outcomes are exactly
PASS_NAMED_HARMLESS_FIXTURE/REJECTED/NOT_SUPPORTED/UNAVAILABLE. No OBSERVED
containment, real-policy-adoption or application-authority type exists. Result
envelope has exact schema_version `harmless-backend-fixture-v1`; evidence_kind
`UNTRUSTED_FIXTURE_REPORT` until an external verifier binds it. No parser can
promote that kind. Reasons are immutable nonempty UTF-8 strings. PASS requires
empty reasons, all six digests and clock present, guard/collector/lineage/trace/
tree-exit true, effects false and both fixture counts0; every other outcome has
at least one reason. Per-HF expected assertions still need independent verification.

- [ ] Write RED tests `test_fabricated_scope_is_not_authority`, `test_standin_is_not_device_qualification`, `test_null_is_not_zero`, `test_unknown_keys_and_non_utf8_reject`; assert no real qualification can become true and rejected canonical input raises ValueError.
- [ ] Run `.venv/bin/python -m pytest tests/unit/test_backend_harmless_records.py -q`; Expected: FAIL for absent contract, not a collection typo.
- [ ] Implement the immutable parser and pure invariants; external operational authorization remains outside these types. No IO/probes/host imports in records or validation.
- [ ] Run the focused command and full `.venv/bin/python -m pytest -q`; Expected: all pass, no host action. Commit `feat: define harmless backend result boundaries`.

### Task 2: Opt-in approved-host regular-file harness

**Files:** Create `compatibility/containment_backend_harmless/host_main.py`,
`host/guard.bpf.c`, `host/broker.c`, `host/fixtures.c`, `host/build_manifest.json`,
`host_cases.py`, `tests/architecture/test_backend_harmless_boundary.py`.

**Interfaces:** `host_main.main(argv: Sequence[str]) -> int` has no import-time
effects. Invocation without an externally approved matching host/scope fails
before host IO. It accepts only explicit fixture IDs, never arbitrary commands,
native artifacts or policy expansion. `host_cases.py` is opt-in outside default
pytest testpaths; no CI entry. C harness uses the approved cohort's UAPI/libbpf
headers and must not download anything. Exact build arguments/input hashes and
host-specific hook review are captured before any load; no generic kernel fallback.
The only C entry interfaces are `int run_fixture(const char *fixture_id, int report_fd)`
and `int broker_readonly_main(int listener_fd, int approved_root_fd, int report_fd)`;
fixture_id must be one of HF01–HF24 and report_fd a trusted setup pipe. No shell,
exec-command string or user-supplied payload parameter is accepted.

- [ ] RED pure boundary test: importing/invoking without actual granted scope produces no process/syscall/policy action; arbitrary executable arguments reject. Run unit/architecture tests; Expected: FAIL for missing boundary.
- [ ] On the separately approved isolated host only, add failing fixture assertions HF01–HF12 for request/result/object/FD lineage, flags, buffer and dirfd mutation, cancellation/PID reuse. Expected mismatches invalidate the fixture rather than widen policy. No synthetic dictionary may stand in for these host observations.
- [ ] Implement only read-only broker emulation and independent guard wiring from the reviewed host cohort; all O_PATH/create/truncate/write unsupported. Denied discovery is POLICY_DENIED_NO_OBJECT, never an invented kernel absence. Preserve prior LSM denial; all control FDs stay outside payload scope.
- [ ] Add HF13–HF24 fault/closure cases, including listener loss versus actual termination, threaded-cgroup preflight rejection, collector loss, generated-loader drift and stand-in limits. Expected: unsupported/unknown evidence invalidates whole run; zero real-device qualification.
- [ ] Run explicit approved-host fixture entry per ID, then pure full pytest/architecture/lint/mypy/build checks without host tests in default CI. Expected: named observations recorded or reasoned NOT_SUPPORTED; no device/native execution. Commit `test: add opt-in harmless backend qualification harness` only if scope and fixture evidence are intact.

### Task 3: Honest partial evidence and handoff

**Files:** Create `docs/evidence/containment_backend_harmless_results.json` and
`docs/containment_backend_harmless_result.md`.

**Interfaces:** Consume validated Task1 results and actual Task2 host evidence.
Keep each fixture result separate; require actual source/guard/observer/FD/effect
availability, including canceled requests and any broker-side effects. A fixture
pass never sets overall containment/runtime/native/application qualification.

- [ ] RED tests `test_empty_capture_does_not_prove_zero` and `test_listener_loss_is_not_tree_exit`; assert unknown count/stop remains null or rejected, never0/true.
- [ ] Implement report validation and publish either named partial fixture observations or explicit NOT_SUPPORTED/UNAVAILABLE failures. Verify the report digest and scope independently; no full containment verdict.
- [ ] Run all pure regressions and separate authorized host cases; Expected: accurately reported per-fixture results, no unauthorized activity or hidden failure. Fresh independent final review checks the five Review Focus cases and exact host/scope cohort.
- [ ] Publish an append-only stacked Draft only; no merge/prior PR edit. Retain actual device class, native compatibility, complete closure and watchdog/application blockers. Stop; any actual device-class test or exact-R execution is a new decision.

Self-review: Task1 owns trust/type boundaries; Task2 owns HF01–HF24 and the five
failure classes; Task3 owns zero/termination/partial-result honesty. Concrete
external host/operation pins are required inputs, not supplied by this plan.
No task is authorized to invent them. Native inline execution preference is
preserved **only after** those security-sensitive prerequisites are satisfied.
