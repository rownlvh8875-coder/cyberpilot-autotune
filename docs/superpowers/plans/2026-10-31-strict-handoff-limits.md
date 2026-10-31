# Strict Handoff Limits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure opt-in schema validator requiring exact integer limit metadata before all unchanged handoff-schema checks.

**Architecture:** A test-only object API rejects wrong limit shape/type/value,
then delegates the complete original validate_schema. It does not implement a
JSON decoder, mutate metadata, repair old callers or promote evidence.

**Tech Stack:** Python3.12 stdlib/typing, pytest/coverage, unchanged design audit.

**Spec:** `docs/superpowers/specs/2026-10-31-history-preserving-strict-input-design.md`, PR33 section and shared constraints.

## Global Constraints

- Frozen source base `1d3c7622603ad402e4f5d1ddb23a77f4d267a6b4`; preserve all its tracked blobs.
- New code only under `tests/strict_handoff`; new tests/architecture/result names below.
- No src/compatibility/fixtures/CI/history-guard/source/evidence edits or schema relabeling.
- Exact constants: members16, bytes_per_member4096, events1024, json_bytes2097152.
- Exact int/dict only; no bool/float/str/subclass coercion, fallback or input mutation.
- SYNTHETIC only; all permissions/runtime qualification remain false.
- No guest/kernel/device/vehicle/Params/application execution or bridge; old PRs untouched.
- No merge/rebase/force/shared push; no caller adoption authorized by this plan.

## Review Focus

- Equal-value floats from decimal or exponent JSON notation must reject, not become integers.
- int/dict subclasses and caller-crafted mapping equality must not bypass exact-type guards.
- Valid integer limits must still undergo every unrelated legacy schema/permission check.
- Missing/extra keys, None and false must not be repaired or substituted by defaults.
- The object API must not claim duplicate-key detection after a permissive JSON decode or fixed old callers.

### Task 1: Exact-limit facade and regression boundary

**Files:**
- Create `tests/strict_handoff/__init__.py` (docstring only).
- Create `tests/strict_handoff/validation.py` (profile and pure object validator).
- Create `tests/test_strict_handoff_limits.py` (strict admission and delegation tests).
- Create `tests/architecture/test_strict_handoff_limits_boundary.py` (old-blob/import guard).
- Create `docs/strict_handoff_limits_result.md` (actual results and adoption limits).

**Interfaces:**
- Consumes unchanged `tests.audit.validate_guest_input_handoff_design.validate_schema`;
  tests obtain the published valid object via unchanged `load("schema")`.
- Produces `VALIDATOR_PROFILE="handoff-limit-exact-int-strict-v1"` and
  `validate_schema_strict(data: Any) -> None` in validation.py.
- Independent of strict containment plan; no cross-import or generic shared parser.

- [ ] Write the absent-API regression first:

```python
@pytest.mark.parametrize("field", ["members", "bytes_per_member", "events", "json_bytes"])
def test_float_equal_limit_metadata_rejected(field):
    data = load("schema")
    data["limits"][field] = float(data["limits"][field])
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)
```

- [ ] Run `python -m pytest -q tests/test_strict_handoff_limits.py`.
  Expected: RED missing strict module/API, not a skipped test.
- [ ] Implement root/limits exact-dict checks, the four exact literal keys and
  values, and `type(value) is int`; bad limit guard raises exact ValueError code.
  Then call unchanged validate_schema(data). No coercion/default/normalization,
  input mutation, caller rebinding or weakened legacy branch.
- [ ] Add `test_equal_json_floats_reject_after_decode` for16.0/16e0 and equivalent
  decimal/exponent spellings of all four constants. This explicitly tests decoded
  floats, not lexical duplicate-key properties the object API cannot recover.
- [ ] Add `test_nonexact_shape_and_integer_types_reject` for None, bool, numeric
  str, float, int subclass, dict subclass/UserDict/equality-spoof mapping,
  missing/extra key and wrong exact integer for each limit. No data repair allowed.
- [ ] Add `test_valid_exact_limits_delegate_all_original_checks`: published valid
  object returns None; wrong scope/clock/schema/encoding, field/unit/stage,
  runtime_producer_implemented/runtime_qualified and each permission mutation
  must still reject through legacy validation. Keep original exception semantics
  for invalid fields outside limits.
- [ ] Add `test_success_and_failure_do_not_mutate_input` using independent deep
  copies for valid and rejected dicts, None versus zero/false retained.
- [ ] Add `test_legacy_load_policy_is_not_replaced`: inspect/use the unchanged
  load("schema") for published assets; retain old duplicate-key/nonfinite/2MiB
  checks. New facade receives objects only and makes no raw-parser claim.
  Characterize the old validate_schema accepting float-equal values without
  presenting that as new strict success or claiming the original API repaired.
- [ ] Add architecture guard preserving all baseline tracked blobs; allow only
  new paths. New facade imports typing and the exact old audit module only;
  prohibit runtime/application/network/thread/process/IO calls in the new facade.
  Do not reject the frozen audit's existing source-inspection CLI merely because
  it is imported: the facade calls validate_schema only, never validate/load/main.
- [ ] Run focused tests, then `python -m pytest -q` and
  `python -m tests.audit.validate_guest_input_handoff_design`.
  Expected: GREEN, same original BLOCKED/false runtime/permission report.
- [ ] Measure only new facade using separate COVERAGE_FILE:
  `python -m pytest --cov=tests.strict_handoff --cov-branch --cov-report=term-missing --cov-fail-under=100 tests/test_strict_handoff_limits.py`.
  Expected: zero missed statements and branches; no original threshold reduction.
- [ ] Run `python -m ruff check .`, `python -m ruff format --check .`,
  `python -m mypy src/cyberpilot_autotune`, `python -m build`; inspect fresh wheel
  namelist to confirm tests/strict_handoff absent. Expected: PASS. Preserve actual
  Linux/Windows exact-head CI and inherited skips without claiming runtime proof.
- [ ] Write the new result doc: opt-in validator implemented only after actual
  GREEN, LEGACY_CALLERS_UNMIGRATED and PR33 original finding still open pending
  separately reviewed adoption. Commit named files with
  `feat: add explicit exact-integer handoff limits gate`.
- [ ] One fresh final whole-branch review, exact-head full rerun and separately
  permitted own Draft/CI handoff. No original PR33/49 edit/retarget/merge.

## Stop / next decision

Do not migrate validate()/old import sites, alter original source or whitelist
history changes. Caller inventory and adoption require a separate reviewed
decision. Execution has **not started** in the design branch.
