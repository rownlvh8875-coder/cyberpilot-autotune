# Neutral actual-binding integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the offline neutral checker as an independently reviewable main-based Draft PR.

**Architecture:** Byte-identical nine-module runtime under a canonical diagnostics namespace. A pinned historical ZIP is test data only; isolated child roots prevent repository tests from shadowing its exact legacy types. A dedicated additional workflow leaves stacked CI files unchanged.

**Tech Stack:** Python >=3.12.3,<3.13, stdlib runtime, pytest, Ruff E/F/I/UP/B, strict mypy, setuptools.

**Spec:** `docs/superpowers/specs/2026-11-02-diagnostic-actual-binding-design.md`

## Global Constraints

- Base a5d3514f23797829eb58d08c638b22cf4dd30c8a; branch feat/diagnostic-actual-binding.
- Preserve all 476 portable cases and all existing CI thresholds/workflow bytes.
- Preserve frozen legacy bytes; explicitly document their historical I001.
- No legacy v1 promotion, alternate runtime alias, reference factory or authority.
- All nine permissions false; no collector/vehicle/controller/Params/schema/application.
- New branch/append-only commits/Draft PR only; existing PRs/main untouched.

## Review Focus

- An ambient tests package must not supply the actual legacy constructor.
- Missing/corrupt historical ZIP members must fail before source execution.
- A checkout-root shadow module must not satisfy the installed-wheel smoke.
- Namespace migration must not change canonical bytes/digests or exact type identity.
- Consistent synthetic inputs must never grant provenance/admission/permissions.

---

### Task 1: Canonical package and preserved behavior

**Files:** Create src/cyberpilot_autotune/diagnostics/{__init__.py,actual_binding/*.py}; tests/diagnostics/actual_binding/*.py; tests/fixtures/actual_binding/{legacy_contracts.zip,acceptance-coverage-map.json}; docs/evidence/actual_binding_integration_sources.json.

**Interfaces:** Consumes portable release runtime nine files and checks thirteen files; produces the five exact canonical exports and migrated 476-case suite. Test-only helpers run real old constructors with src/test-vector/ZIP roots only.

Integration discovery: three historical inventory tests require narrowly scoped
extension using tests/audit/diagnostic_inventory.py. Preserve all old byte checks,
allow exactly ten verified diagnostic files, and test missing/modified/extra files.

- [ ] Port the tests first with canonical imports and relocated evidence mapping.
- [ ] Run a canonical API test; expected RED: neutral package absent.
- [ ] Copy byte-identical runtime and inert parent; run new tests, expected namespace/fixture RED.
- [ ] Add pinned ZIP and isolated child helper; require actual SevenInputReference rejection and assert origins, absence/corruption failures, and checkout-shadow isolation.
- [ ] Run all 476 ported cases plus integration tests and full pytest; expected all pass, no skips.
- [ ] Commit feat: integrate neutral actual-binding diagnostics.

### Task 2: CI, installed wheel and handoff

**Files:** Create .github/workflows/diagnostic-actual-binding.yml; tests/wheel_actual_binding_smoke.py; docs/diagnostic_actual_binding.md; docs/evidence/actual_binding_integration_result.json.

**Interfaces:** Consumes Task 1 canonical API/fixture; produces CI matrix, reproducible wheel smoke and truthful limitations. No common CI modification.

- [ ] Add real installed-wheel smoke using the synthetic vector path and canonical API, rejecting checkout imports and checking all false facets. Run with an empty wheel environment first; expected RED: package absent.
- [ ] Build/install vanilla wheel outside checkout, run smoke and existing replay/knowledge/owner/science/friction smoke; expected pass with optional research absence handled explicitly, then research smoke after numpy installation.
- [ ] Add dedicated Linux/Windows × 3.12.3/3.12 workflow, strict coverage gate statement >=98%, branch >=95% for the nine new modules. No threshold reductions.
- [ ] Run repository-wide Ruff/format/mypy, full main+new pytest with coverage, existing audit/history/source validators and golden replay; record exact outcomes and unavailable local platform proofs honestly.
- [ ] Write result and limitations; commit test: verify diagnostics wheel and isolated legacy fixtures.
- [ ] Fresh whole-branch independent review at final exact head; fix Important/Critical with RED→GREEN and full rerun if needed.
- [ ] Push only new branch, create Draft PR, inspect both event CIs, recheck existing heads/base/draft, and attach URL. No merge.
