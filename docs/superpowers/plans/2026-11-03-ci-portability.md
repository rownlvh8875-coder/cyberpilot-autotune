# CI Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. This small repair is executed inline, followed by one fresh independent review.

**Goal:** Repair ambient Git-config and frozen-source newline CI failures without relaxing any safety gate.

**Architecture:** Test-only scoped configuration discovery and isolated synthetic Git setup. Actual capture implementations and CI workflow bytes remain frozen. Extend the historical guard with a separately bounded successor range.

**Tech Stack:** Existing Python 3.12, pytest, Git, Ruff, mypy; no new dependency.

**Spec:** `docs/superpowers/specs/2026-11-03-ci-portability-design.md`

## Global Constraints

- Base: `ce138c503ff320a2a6956ceff3d8735418b72bcc`; same feature branch, append-only.
- Product/reader/core/workflow/collector source bytes unchanged; K1 equality stays raw.
- No new skip, qualification claim, helper acceptance or coverage-floor change.
- No real host config/HOME mutation, manual dispatch, main merge or application work.
- All prior blockers and nine false permissions retained.

## Review Focus

- Isolation must restore discovery even after exceptions and must not leak to non-capture tests.
- Helpers in any of the three declared synthetic sources must still reject before Git child execution.
- Read-only child capture must use the explicit synthetic scope without weakening its audit hook.
- Fresh autocrlf checkout must preserve every frozen K1 core byte without normalizing the assertion.
- New scope must not widen old history ranges or allow unknown/untracked/status-alias mutations.

### Task 1: Bounded CI portability repair

**Files — create:** this plan, its spec, `tests/test_audit_compatibility_capture_portability.py`, `docs/evidence/audit_compatibility/ci-portability-v1/registration.json`.

**Files — modify:** `.gitattributes`, `tests/fixtures/audit_compatibility_capture.py`, the architecture/cohort/git/worktree capture test modules, `tests/test_audit_compatibility_history_architecture.py`, `tests/test_actions_preflight_registration.py`. Shared `tests/conftest.py` stays byte-identical.

**Interfaces:** `synthetic_config_scope(paths)` is a restoring test-only context manager. `request(root)` declares those paths; `git(root, *args, input=None)` uses child-only neutral system/global config. `_ci_portability_changes(rows)` checks only this repair's literal 4-addition/8-modification inventory.

- [x] Write regressions for private declared config sources, synthetic Git isolation and actual autocrlf checkout. Run the new file and observe these failures against the base.
- [x] Implement explicit fixture imports and child adoption; add helper-source rejection and restoration cases. Append the single LF rule. Preserve all existing security tests.
- [x] Freeze old registration checks at the base, add the separate current scope and adversarial consumer tests. Do not alter `_phase_changes` or `_registered_preflight_changes`.
- [x] Run targeted tests, whole pytest, Ruff, format, mypy, existing audits/coverage/replay/build/fresh-wheel checks. Record actual limitations rather than claiming unavailable checks.
- [ ] Commit once all local gates pass; obtain fresh exact-head independent review. Any important fix requires its own RED-to-GREEN and append-only commit, without weakening gates.
- [ ] Publication hold: because of the documented development host-config incident, finish local verification/review only. After environment recovery/verification and renewed publication direction, check the remote base and publish a normal fast-forward feature update; monitor only automatic exact-head push CI. Do not merge or dispatch.

Expected: local gates green, no unrelated paths, unchanged runtime qualification; hosted CI results reported exactly, including cancellations/failures.

### Task 2: Separate source inspection from neutral synthetic Git

**Follow-up base:** `3fc532d5c2634e716401701278cb45b49dbea3ac`. Task 1 is not to be repeated: that exact head was reviewed/published after the user adopted a verified current baseline. Its Windows CI exposed the follow-up defect; the original host-state equality remains unconfirmed.

**Files:** modify only `tests/test_audit_compatibility_capture_portability.py` and append this existing plan/spec. No new source file or expanded old allowlist.

**Interfaces:** module-local `source_git(*args) -> bytes` executes the existing trusted source `diff`, `show`, and `ls-files` calls at `ROOT`, preserving inherited Git configuration/environment plus no-lazy-fetch/no-optional-lock guards. The unchanged fixture `git(root,*args,input=None)` remains the neutral synthetic setup path. It is not a new public execution boundary.

**Review Focus:**

- Source metadata retains checkout normalization while the synthetic helper remains isolated.
- CRLF representation changes do not hide real content edits or untracked files.
- Every real source-metadata consumer uses the source path, not just the new regression helper.
- K1 object bytes and direct raw-byte comparison remain exact; no data promotion or guard weakening.
- Follow-up changes are exactly three registered modifications; host config and all frozen runtime/workflow bytes stay untouched.

- [x] Write a real Git LF-blob/fresh-CRLF-checkout regression using only private paths; it must show the current neutral source route misclassifies `sample.py` as modified. Also test actual content edits, raw blob bytes and untracked inventory.
- [x] Add four real-consumer routing regressions: K1 fresh checkout, checkout policy, repair inventory, frozen namespaces. Make the neutral setup route reject the real source root; run and observe RED before implementation.
- [x] Implement `source_git(*args)` without neutralizing inherited source config. Route every `git(ROOT,...)` metadata call in this module through it, leaving synthetic setup calls untouched. Pin the follow-up's exact three-path inventory.
- [ ] Run the new cases, full pytest, coverage and unchanged floors, Ruff/format, mypy, existing source/history audits/replay/build/fresh wheel. Commit append-only and obtain one fresh exact-head independent review.
- [ ] After clean scoped review, verify the remote still equals this base; publish a normal fast-forward on the same feature branch and monitor its automatic exact-head CI to terminal state. No PR/merge/force/manual dispatch; report actual failures/cancellations instead of waiving them.

Expected: RED source-normalization/routing cases become GREEN without relaxing any existing assertion; no host settings writes; remote Windows/Linux outcomes reported separately from synthetic checks.
