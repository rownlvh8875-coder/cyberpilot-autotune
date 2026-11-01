# DENY-FD v2 Isolated Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fixed, closed-default v2 collection harness without executing QEMU, the guest or target ELF.

**Architecture:** New test-only assets/image/capture/runner modules; no v1 runner reuse. A P4 exact-content successor allows only the design's 22-path delta while retaining original acceptance checks in their original cohort.

**Tech Stack:** Existing Python3.12 standard-library/pytest/coverage/ruff/mypy/build stack; cached QEMU10.0.13 assets read only.

**Spec:** docs/superpowers/specs/2026-11-01-deny-fd-v2-harness-design.md. User approved Native execution on 2026-11-01; implementation progress is recorded externally.

## Global Constraints

- Base a97321f6bbf5c3e5d6e3205615e0a600b059b89a; preserve main/PR8/PR9/PR54/PR55 refs.
- New branch feat/deny-fd-v2-isolated-harness; proposed ignored worktree .worktrees/deny-fd-v2-isolated-harness. Creation is part of requested plan approval.
- Exactly the spec's 2 modified +20 new paths; no other edits or directory permissions.
- Preserve six raw M2 files, all old captures/manifests, P/P2/P3, original22 and original18 guards; no relaxed assertions/skips/60-second historical replay.
- All nine spec permissions false; every decision BLOCKED; all inherited blockers retained.
- No QEMU/guest/target-ELF/vehicle execution, network/download, Params/controller/schema, estimator/owner/application bridge, external publication or merge.
- No implementation before review of this plan and its explicit routing scope.
- Default imports/CLI must work on Windows too; import POSIX-only facilities lazily after explicit Linux opt-in. Real new process-group tests may be Linux-specific, without altering any old skip.

**Exact file ownership:** Task1 owns spec list entries1,2,3,5,6,7,19,20 and both modified paths; Task2 owns4,8,9,10,11,15,16; Task3 owns12,17 and extends9; Task4 owns13,14,18 and extends20; Task5 updates only already-listed documentation/tests. All paths are literal in design.md, not inferred directory permissions.

## Review Focus

- A VM file changes after a superficial hash check: launch must revalidate the complete fixed profile, consume retained image bytes and decline hostile-host/atomic-input closure claims (Task2/4).
- Output floods, deadlines, or descendants survive parent exit: bound raw collection, stop/reap the owned process group and retain explicit failure evidence (Task4).
- A later case or persistence fails: keep prior completed cases and the current raw prefix; do not publish a complete successful batch (Task3/4).
- Plausible synthetic/v1/wrong-source bytes appear: cross-check fixed source/case/framing; no authenticity or v2-observed upgrade (Task3).
- Missing Git objects or mutated history images masquerade as old cohorts: fail closed; preserve the exact old node replay and current scope separately (Task1).

## Task 1: Exact history extension and preserved-source replay

**Files:** The two modified paths and new history helper/manifest, spec/plan, contracts/result docs, history and architecture tests listed in the spec. No other old source.

**Interfaces:** validate_harness_successor(root: Path)->frozenset[str] returns only verified new literal paths; replay_original_scope(root: Path, tmp_path: Path)->None runs the exact B source/node with an owned basetemp and timeout60. P4's manifest binds 56 preserved and2 explicit modified images.

- [ ] Create the approved isolated worktree, use existing dependencies, run baseline full pytest with a new owned basetemp; stop on any baseline failure.
- [ ] Write test_historical_cohort_grants_no_harness_paths, test_current_delta_is_exact_22, test_original_19_path_node_replays_original_source and parametrized HEAD/index/worktree/mode/missing-object/ancestry-error mutations. Assert original source/node/timeout, exact path sets and rejection of unlisted sibling files.
- [ ] Run those nodes RED before the helper exists; record the actual failure, not a mocked pass.
- [ ] Prepare P4's sole-parent-B manifest and the two minimal routing postimages. Old architecture assertion is replayed unchanged on B; the new current guard must independently require the22-path delta.
- [ ] Commit P4 as preregistration, clearly labeled incomplete/non-runtime metadata; then pin its actual SHA in the new helper and implement the closed checks/union. No self-hash or historical negative-ancestry grant.
- [ ] Run history/architecture tests GREEN including the original B node, original22/P/P2/P3 checks and preservation of every other old path. Commit the helper/tests with no readiness claim until full gates.

Test step anchor (historical_checkout is a real shared clone of exact B created
by a fixture in the new history test file; it is not a fake Git response):

```python
def test_historical_cohort_grants_no_harness_paths(historical_checkout):
    from tests.history_transition.deny_fd_v2_harness_successor import validate_harness_successor
    assert validate_harness_successor(historical_checkout) == frozenset()
```

Run RED/GREEN: `python -m pytest -q tests/test_deny_fd_v2_harness_history.py tests/architecture/test_deny_fd_v2_harness_boundary.py --basetemp="$harness_test_root/p" -p no:cacheprovider`.
Before implementation expect missing helper/API; afterward require0failures.

## Task 2: Fixed asset verification and deterministic minimal image

**Files:** assets.py, image.py, contracts.py, __init__.py, assets manifest, test_deny_fd_v2_harness_assets.py, test_deny_fd_v2_harness_image.py.

**Interfaces:** frozen AssetBundle stores pinned identities plus defensive retained probe/busybox bytes; preflight()->AssetBundle; build_image(assets: AssetBundle, case: str)->bytes. The manifest binds VM d98a259c..., M2 source/manifest and the915376-byte probe exactly as specified.

- [ ] Write tests test_missing_or_changed_asset_fails_closed, test_complete_vm_tree_rejects_extra_or_symlink_escape, test_relocated_compile_record_keeps_original_command, test_image_is_deterministic_and_minimal, test_unknown_case_or_payload_rejected, test_consumed_probe_is_retained_verified_bytes. Assert no process/network/compiler call and no legacy guest executables in the archive.
- [ ] Run tests RED; implement strict immutable types and fixed-profile bounded reads. Verify raw source Git objects and complete cached VM cohort; record unavailable separately from false/zero. Never auto-download/recompile or invoke a version command on QEMU/probe.
- [ ] Implement deterministic in-memory newc/gzip with the spec's exact v2 scope/init and only static busybox/probe plus required bootstrap entries. Preserve actual probe exit status; no success marker on setup failure.
- [ ] Run tests GREEN and a fresh read-only real preflight. Record content identity only, not build closure/runtime readiness. Commit.

Image test anchor (synthetic_assets is an explicitly synthetic fixture defined
in the new assets test file, binding only unit-test profile expectations; it
never stands in for real preflight/acquisition evidence):

Import that fixture explicitly from tests.test_deny_fd_v2_harness_assets in
the image/capture test modules; do not add a global conftest or hidden autoload.

```python
def test_image_is_deterministic_and_minimal(synthetic_assets):
    from tests.deny_fd_v2_harness.image import build_image
    from compatibility.guest_input_closure.archive import parse_image
    raw = build_image(synthetic_assets, "DFD01")
    assert raw == build_image(synthetic_assets, "DFD01")
    entries = {item.path: item for item in parse_image(raw)}
    assert entries["deny-fd-v2-probe"].data == synthetic_assets.probe
    assert entries["etc/deny-fd-v2-scope"].data == b"deny-fd-v2: fixed pre-exec inventory probe only\n"
    assert not {"harmless-fixtures", "exec-helper", "guard.bpf.o", "syscall-collector"} & entries.keys()
```

AssetBundle's public byte fields are probe:bytes and busybox:bytes; other identity
fields are source_revision:str, source_manifest_digest:str, vm_cohort_digest:str.
Constructing a bundle is not attestation; the launch path accepts no caller bundle
and obtains/revalidates only the fixed preflight profile. The pure image builder
must also enforce its fixed profile; controlled test-profile substitution is
test-only, never a runtime option or accepted actual-v2 artifact.
Run RED/GREEN: `python -m pytest -q tests/test_deny_fd_v2_harness_assets.py tests/test_deny_fd_v2_harness_image.py --basetemp="$harness_test_root/p" -p no:cacheprovider`; require0failures after implementation.

## Task 3: Untrusted acquisition record and batch failure semantics

**Files:** capture.py, contracts.py, test_deny_fd_v2_harness_capture.py; contract/result docs as appropriate.

**Interfaces:** frozen AcquisitionRecord stores case/attempt/source/build/VM/init/image/argv/raw/exit/termination/clock identities and fixed permissions. validate_capture(raw: bytes, case: str, assets: AssetBundle)->Capture uses the existing v2 decoder/checker read-only. CaptureFailure retains current bytes, completeness and prior completed records; no application adapter.

- [ ] Write test_wrong_source_case_or_window_rejected, test_v1_or_synthetic_claim_cannot_authenticate_acquisition, test_none_is_not_zero_exit, test_raw_prefix_is_explicitly_incomplete, test_later_failure_retains_completed_cases and test_record_digest_grants_no_authority. Assert exact observed bytes/digests, not fabricated guest fields.
- [ ] Run RED; implement exact typed identity/cross-binding and reasoned failures. Keep content consistency separate from actual acquisition provenance. A diagnostic-consistent result stays BLOCKED with all9false.
- [ ] Run GREEN, immutable/defensive-copy/digest property tests and old decoder regressions. Commit.

Include test_wrong_requested_policy_or_expected_fd_rejected: compare POLICY/
EXPECT with the fixed requested profile from unchanged C; do not choose CAUSE,
observed inventory or denial from labels.

Wrong-source test anchor (reuse the unchanged, explicitly synthetic wire generator):

```python
def test_wrong_source_case_or_window_rejected(synthetic_assets):
    import pytest
    from tests.test_deny_fd_v2_wire import encoded, vector
    from tests.deny_fd_v2_harness.capture import validate_capture
    rows = vector(case="DFD01")
    rows[0][5] = "f" * 40
    rows[0][6] = synthetic_assets.source_manifest_digest
    with pytest.raises(ValueError):
        validate_capture(encoded(rows), "DFD01", synthetic_assets)
```

Define AcquisitionRecord fields exactly as case:str, attempt_id:str,
source_revision:str, source_manifest_digest:str, probe_sha256:str,
vm_cohort_digest:str, kernel_sha256:str, init_sha256:str, image_sha256:str,
argv:tuple[str,...], raw:bytes, exit_code:int|None, termination:str,
raw_complete:bool, host_start_ns:int, host_end_ns:int; raw size/digest and
permissions/status are derived read-only properties. Termination is one of
EXITED,NONZERO_EXIT,TIMEOUT,OUTPUT_LIMIT,IO_ERROR,CLEANUP_ERROR. Clock domain is
HOST_MONOTONIC_NS and cannot be compared directly with guest event times.
CaptureFailure(ValueError) has reason:str, raw:bytes, raw_complete:bool,
completed:tuple[AcquisitionRecord,...]. None exit status must never mean0.
Run RED/GREEN: `python -m pytest -q tests/test_deny_fd_v2_harness_capture.py tests/test_deny_fd_v2_wire.py tests/test_deny_fd_v2_validation.py --basetemp="$harness_test_root/p" -p no:cacheprovider`; require0failures after implementation.

## Task 4: Closed-default runner, bounded collection and future opt-in CLI

**Files:** runner.py, host_main.py, test_deny_fd_v2_harness_runner.py, new architecture guard.

**Interfaces:** qemu_arguments(image_path: Path)->tuple[str,...]; capture_cases(cases: tuple[str,...], destination: Path, *, run_prepared_guest: bool=False)->tuple[AcquisitionRecord,...]; main(argv: list[str]|None=None)->int. Public caller controls only fixed cases, a new output destination and explicit diagnostic intent; no command/payload/VM overrides.

- [ ] Write test_default_cli_and_import_never_spawn_or_write, test_only_fixed_tcg_argv_allowed, test_prelaunch_asset_drift_denies_spawn, test_nonzero_timeout_flood_or_cleanup_error_retains_raw, test_write_failure_is_not_success and test_partial_batch_preserves_prior_raw. Use fake QEMU process boundaries, never QEMU itself.
- [ ] Run RED; implement Linux-only fixed launch with explicit environment, new owned output/image paths outside checkout, Popen(shell=False,start_new_session=True), bounded nonblocking output, deadline180s and terminate/grace2s/kill/reap. Preserve raw bytes and failure metadata before reclaiming only proven-owned ephemeral files.
- [ ] Test the private process supervision primitive with harmless fixed Python workers on Linux (including a descendant holding a pipe), explicitly distinguish those host tests from guest evidence. Keep new platform-specific limitations visible; never skip an old test or loosen a deadline.
- [ ] Implement default exit2/BLOCKED/NOT_STARTED; an explicit future diagnostic opt-in still exits2/BLOCKED after consistent capture. No environment variable/autoload/import path may enable launch.
- [ ] Run GREEN with a launch spy prohibiting every QEMU/probe invocation throughout the test suite. Commit.

Default-denied test anchor:

```python
def test_default_cli_and_import_never_spawn_or_write(tmp_path, monkeypatch):
    import subprocess
    import pytest
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("unexpected launch"))
    from tests.deny_fd_v2_harness.host_main import main
    assert main([]) == 2
    assert list(tmp_path.iterdir()) == []
```

Run RED/GREEN: `python -m pytest -q tests/test_deny_fd_v2_harness_runner.py tests/architecture/test_deny_fd_v2_harness_boundary.py --basetemp="$harness_test_root/p" -p no:cacheprovider`; require0failures after implementation. Timeout/flood/descendant tests additionally assert bounded raw length<=1048576, explicit incompleteness, recorded termination, and no surviving owned child after reap.

## Task 5: Full regression, packaging and final source review

**Files:** contract/result/spec/plan within approved scope only; external evidence under this task's owned workspace.

- [ ] Run full pytest; unchanged main/subsystem coverage, H2–H7/source/history audits, Ruff/format, mypy, build, replay11/4goldens, fresh outside-checkout wheel and all smoke gates. New package target100/100, minimum98statement/95branch; no weakened old gate. Fresh wheel product files must equal B and exclude harness/tests/compatibility.
- [ ] Use owned explicit temp roots and passed-clone cleanup only; do not delete old508/511, archives or another plan's workspace. Preserve failures/aborts honestly. Do not rerun whole suites without a changed gate or need for final exact-head verification.
- [ ] Commit final metadata, rerun affected/full exact-head gates as needed, then request one fresh independent whole-branch review using the requesting-code-review workflow. No claimed human or runtime approval.
- [ ] Resolve any finding with RED test, append-only fix and fresh evidence/review. Do not alter source M2, old acceptance rules, candidate permissions or retained blockers.
- [ ] Hand off local clean exact head and observed checks. State HARNESS_IMPLEMENTED_NOT_EXECUTED/OBSERVED_V2_CAPTURE_UNAVAILABLE. No automatic guest execution, push/PR, ready or merge.

For every pytest command above create a NEW owned root first with
`harness_test_root=$(mktemp -d /tmp/cp-v2-harness-test.XXXXXX)`; never point
--basetemp at an existing unrelated directory. Use the existing project venv's
Python executable in the approved worktree rather than installing dependencies.
Final commands include `python -m pytest -q`,
`python -m pytest --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=90`,
`python -m ruff check .`, `python -m ruff format --check .`,
`python -m mypy src/cyberpilot_autotune tests/deny_fd_v2_harness`, `python -m build`.
Supply the owned basetemp/cache options to both full pytest invocations.
Run every unchanged subsystem/audit/replay/wheel command from
.github/workflows/ci.yml as well; exit0 and original thresholds are required.
New-package statement/branch reports must name the included harness files and
explicitly exclude any claim of C/kernel/QEMU execution coverage.

## Self-review and handoff

Execution ruling: the final22-file completeness assertion depends on Tasks2–4;
its GREEN gate belongs to Task5. Task1's intermediate gate runs all implemented
history semantics and the unchanged predecessor regressions without claiming
whole-branch readiness. The final test is not skipped or weakened.

All design sections map to Tasks1–5; each Review Focus line has an owning test.
All named interfaces/types are defined above. P4 SHA and new commit hashes are
post-commit identities, not unspecified behavior or a self-reference. The branch
scope cannot silently grow: any extra existing/new path returns to review.

Recommended execution method: Native — one tightly coupled history/assets/
capture/runner contract, implemented inline with a final fresh independent review.
Please review the22-path scope and the exact original-source replay routing
before implementation. No implementation or worktree creation has started.
