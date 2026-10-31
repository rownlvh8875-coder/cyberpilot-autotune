# Strict Containment Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit test-only containment entrypoints that reject non-UTF8 scalar content before returning a parsed case or evaluating it.

**Architecture:** Delegate existing immutable parsing/digest/evaluation semantics;
normalize only UnicodeEncodeError, with no legacy fallback. The new facade is
opt-in and outside the wheel; it does not repair or migrate original APIs.

**Tech Stack:** Python3.12 stdlib, pytest/coverage, existing immutable contracts.

**Spec:** `docs/superpowers/specs/2026-10-31-history-preserving-strict-input-design.md`, PR25 section and shared constraints.

## Global Constraints

- Frozen source base `1d3c7622603ad402e4f5d1ddb23a77f4d267a6b4`; preserve all its tracked blobs.
- New code only under `tests/strict_containment`; new tests/architecture/result names below.
- No src/compatibility/fixtures/CI/history-guard/source/evidence edits, even new compatibility files.
- No schema-version promotion, normalization, coercion, alternate digest encoding or silent fallback.
- SYNTHETIC only; all permissions/runtime qualification remain false.
- No producer, guest/kernel/vehicle/device/Params/application/owner execution or bridge.
- Old PRs untouched; new own Draft only when separately authorized. No merge/rebase/force/shared push.
- Legacy callers and PR25 finding remain open until a separately reviewed adoption decision.

## Review Focus

- Nested optional text/flags or direct construction must reject lone surrogates just like parsed actor_id.
- JSON escaped valid surrogate pairs must remain valid, but Python strings retaining literal surrogate codepoints must reject.
- Valid Unicode must retain legacy digests/decisions with no NFC/NFD, replacement or ASCII rewrite.
- Original duplicate-key/nonfinite/unknown-key/type/permission errors must not become fallback successes.
- A strict facade must not be described as a repaired legacy entrypoint or runtime qualification.

### Task 1: Pure explicit facade and regression boundary

**Files:**
- Create `tests/strict_containment/__init__.py` (docstring only).
- Create `tests/strict_containment/validation.py` (profile and three pure functions).
- Create `tests/test_strict_containment_input.py` (synthetic behavior/property tests).
- Create `tests/architecture/test_strict_containment_input_boundary.py` (old-blob/import guard).
- Create `docs/strict_containment_input_result.md` (actual results and unmigrated callers).

**Interfaces:**
- Consumes unchanged `SyntheticContainmentCase`, `parse_synthetic_case`, `canonical_digest`
  from `compatibility.native_containment.contracts`, and policy/decision/evaluate_synthetic
  from `compatibility.native_containment.validation`; fixture `synthetic_case()` only in tests.
- Produces `VALIDATOR_PROFILE="containment-scalar-utf8-strict-v1"` and
  `parse_case_strict(raw: str) -> SyntheticContainmentCase`,
  `digest_case_strict(case: SyntheticContainmentCase) -> str`,
  `evaluate_case_strict(case: SyntheticContainmentCase, policy: SyntheticPolicyContext) -> SyntheticContainmentDecision`.
- Independent of the strict-handoff plan; no cross-import or shared mutable helper.

- [ ] Write the absent-API regression first, using the actual old fixture:

```python
def test_lone_surrogate_rejected_before_parse_result():
    data = synthetic_case()
    data["actor_id"] = data["events"][0]["actor_id"] = chr(0xD800)
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$") as exc:
        parse_case_strict(json.dumps(data))
    assert type(exc.value) is ValueError
```

- [ ] Run `python -m pytest -q tests/test_strict_containment_input.py`.
  Expected: RED missing strict module/API, not a skipped test.
- [ ] Implement the specified profile/functions in validation.py. Strict digest
  delegates unchanged canonical_digest, catches only UnicodeEncodeError and
  raises exact ValueError code; strict parse calls old parse then strict digest
  before return; strict evaluate calls strict digest then old evaluate. No IO,
  state, registration, broad exception handler or old-function reassignment.
- [ ] Add `test_nested_and_direct_case_surrogates_rejected` for D800/DFFF,
  top/nested actor, requested_endpoint, errno_name, each flag, dataclasses.replace
  and object.__setattr__-forged nested values. Digest and evaluate must raise the
  same exact ValueError before any result can be returned.
- [ ] Add `test_valid_pair_and_scalar_boundaries_keep_legacy_semantics`:
  escaped D83D/DE00 decodes to U+1F600 and succeeds; literal two-surrogate Python
  content rejects. Valid U+D7FF/U+E000/U+10FFFF and control/noncharacter labels
  retain old digest/decision behavior. No filesystem execution implied.
- [ ] Add `test_unicode_goldens_and_no_normalization` with actor_id changed in
  both root/event: fixture default→`07e8c3939efdcd6c5fc4ba2b445b73ba241d7802fae2f195b20b7137348013d1`,
  아이→`d2fc2cd4898c2118a6e24e9434a9680d958b173c15c3171e1e630f84ff1ce0e7`,
  U+1F600→`a538c7fb2078e531d33df0c48524722c337f622ef2731839d369435acea0ccfe`.
  U+00E9 and `e`+U+0301 retain distinct old digests. Different JSON escape spelling
  and object-key order for equal parsed content retain equal digests.
- [ ] Add `test_every_valid_fixture_matches_original_decision` for both policy
  modes, false/unknown modeled proofs, real zero/None and each false permission.
  Compare whole existing immutable decisions, not just status or digest.
- [ ] Add `test_legacy_rejections_propagate_without_repair` for duplicate keys,
  NaN/Inf, wrong/unknown keys, bool/float UInt64, wrong case/policy type,
  permission escalation. Add unchanged legacy characterization showing old
  parse still accepts a surrogate and old digest still raises UnicodeEncodeError;
  never label the original API fixed.
- [ ] Add architecture tests pinning all baseline tracked blobs byte-for-byte,
  permitting new paths only; no .gitattributes edit required. New facade imports
  only the two exact neutral legacy modules; forbid installed/runtime/application,
  IO/network/thread/process dependencies and monkeypatch/global registration.
  Guard tests may use subprocess to inspect Git, but facade may not.
- [ ] Run focused tests, then `python -m pytest -q` and original containment and
  handoff audits. Expected: GREEN with all original acceptance/history guards.
- [ ] Measure only the new facade via pytest-cov using a separate COVERAGE_FILE:
  `python -m pytest --cov=tests.strict_containment --cov-branch --cov-report=term-missing --cov-fail-under=100 tests/test_strict_containment_input.py`.
  Expected: zero missed statements and branches; do not lower original gates.
- [ ] Run `python -m ruff check .`, `python -m ruff format --check .`,
  `python -m mypy src/cyberpilot_autotune`, `python -m build`; inspect fresh wheel
  namelist to assert tests/strict_containment absent. Expected: PASS; vanilla
  package unchanged. Preserve Linux/Windows CI results and inherited skips.
- [ ] Write actual result in the new result doc, explicitly NOT_IMPLEMENTED
  until code exists and LEGACY_CALLERS_UNMIGRATED even after facade tests pass.
  Commit named files with `feat: add explicit strict containment input gate`.
- [ ] One fresh final whole-branch review, actual exact-head full rerun and
  permitted own Draft/CI handoff. Do not edit/retarget/merge original PR25/49.

## Stop / next decision

No actual producer, default caller migration or narrow history-guard amendment
belongs to this plan. A separately reviewed caller-adoption task is required
before claiming the PR25 original finding closed. Execution has **not started**
in the design branch.
