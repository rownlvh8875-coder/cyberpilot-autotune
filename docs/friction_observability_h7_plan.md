# H7 Friction Observability Receipt Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL superpowers:executing-plans. Inline TDD, one final fresh reviewer; user H7 spec governs fresh re-review after C/I fixes.

Goal: pure immutable neutral receipt and structural eligibility, no runtime or estimator bridge.
Architecture: enums/primitives -> source/cycle and snapshot/value contracts -> pure evaluator.
Tech stack: existing Python >=3.12.3,<3.13, stdlib only for new package, pytest/Hypothesis.
Spec: docs/friction_observability_receipt_contract.md and user H7 master prompt (54 sections).
Base: a5d3514f23797829eb58d08c638b22cf4dd30c8a.

## Global constraints

All existing source/evidence/goldens unchanged; additive CI and the exact historical
namespace inventory extensions recorded below are the only compatibility exceptions.
No schema/native/Params/
runtime/application/estimator edits; H6 preserved. PR8/9 unchanged. All new output
authority absent or fixed false. No empirical thresholds. No external AI or real data.
Existing managed checkout, no extra worktree or new dependencies.

## Review focus

1. Correctly shaped but wrong-stage/downstream values masquerading as raw callback.
2. Reconstructed/installed-C-derived q or legacy Float32 mislabeled exact.
3. Valid individual snapshots with mismatched generation/cycle/source/clock lineage.
4. Changed geometry/F/C/mode/SR/delay or replayed cycle incorrectly pooled.
5. Receipt/ELIGIBLE/digest mistaken as estimator, producer, vehicle readiness or authority.

## Tasks / interfaces / ledger

### Task 1 — frozen semantics and durable plan

Files: this plan and docs/friction_observability_receipt_contract.md.
Inputs: H6 authoritative docs/manifests, guarded PR15 merge, full baseline.
Outputs: frozen intended API and acceptance basis before implementation.
- [x] Read H6 basis and inspect architecture/source.
- [x] Verify baseline 1261 tests; PR15 guarded merge, parent/ancestor/tree proof.
- [x] Commit freeze before new Python code (83c2170d699894a8044b1e82d453281ccd495d5d).
Expected: first H7 commit contains only these two documents.

### Task 2 — immutable contracts, wrong-stage test-first boundary

Create src/cyberpilot_autotune/observability/{__init__,types,contracts,context,validation}.py.
Tests tests/unit/test_friction_receipt.py and tests/fixtures/friction_receipt.py.
Interfaces: LateralTorqueIdentificationReceipt / SourceIdentity / CycleIdentity /
ScalarObservation / InstalledParameters / GainSnapshot / AppliedGeometryContext /
DelayContext / ControllerStageDecomposition / LimitState; frozen typed records.
- [x] Write tests for full receipt, missing/zero/False, finite/UInt64 validation,
  defensive copies, provenance/stages/precision/digest.
- [x] Run tests RED for missing contracts, then minimal implementation GREEN.
- [x] Add pure evaluate(receipt, ObservationPolicy(), previous=None) ->
  ObservationEligibilityDecision with enum reasons, status ELIGIBLE/REJECTED.
- [x] Run twenty adversarial cases RED->GREEN; no producer/bridge imports.
Expected: targeted pytest pass, mypy clean; commit contract/tests.

### Task 3 — causal consistency and adversarial properties

Files tests/property/test_friction_receipt_properties.py,
tests/architecture/test_friction_receipt_boundary.py and new package only.
Consumes Task2 API; produces complete structural guard/properties.
- [x] RED->GREEN for every context drift, wrong clock/future source, duplicate
  source/cycle, source value stage substitution, q reconstruction and Float32.
- [x] Full targeted coverage >=98/95; all decision reasons exercised.
Expected: deterministic digests, immutable defensive copy, no authority/import/IO.
Commit append-only.

### Task 4 — source and semantic schema audit

Create tests/audit/{validate_friction_receipt,test_friction_receipt_audit}.py and
docs/evidence/friction_observability_receipt_{sources,schema}.json.
Consume source refs /tmp/carrot-audit and frozen Task1. Produce exact file/blob/
claim-range digests, R/C source-equation behavior checks, complete schema fields.
- [x] Mutation/adversarial audit tests RED first.
- [x] Implement validator without runtime imports/Params; exact-source math only.
- [x] Verify protected pre-H7 files, history and schema reproduction.
Expected: all exact source claims + semantic schema pass; append-only audit commit.

### Task 5 — wire, capture, source compatibility and mapping documents

Create docs/friction_observability_wire_design.md,
docs/friction_observability_capture_architecture.md,
docs/friction_observability_source_compatibility.md,
docs/friction_receipt_observation_v2_mapping.md,
docs/friction_observability_h7_result.md.
Consume neutral schema/audit/behavior, produce no-tag Float64/presence/versioning
proposal, four capture options with exactly one preference, R/C table, exact/wrong/
missing/cohort v2 mapping and negative statuses. Update contract only as documented
clarifications, not post-hoc acceptance relaxation. Commit docs.

### Task 6 — full verification, final exact-head review and Draft PR

Modify only .github/workflows/ci.yml add H7 tests/coverage/source/wheel checks.
Create tests/wheel_friction_receipt_smoke.py.
- [x] Full pytest/coverage; old H2-H6 audits/goldens, lint/format/mypy/build.
- [x] Fresh vanilla wheel with no schema/NumPy required for H7; old smokes,
  H6 optional+research smoke; content hashes and H7 synthetic evaluation.
- [ ] Commit final result, fresh independent review on final exact head.
- [ ] C/I if any: RED fix -> full rerun -> NEW fresh review.
- [ ] Push feat/friction-observability-receipt; Draft PR title exactly
  Define read-only friction observability receipt contract. Attach PR, monitor
  push+PR CI exact head, update PR body without changing reviewed head.
Expected: clean working tree; C0/I0 and all CI pass; no H7 merge.

## Pre-flight interface/rulings

Task2 values/context digest supplies Task3 adversaries and Task4 schema inventory;
Task4 source semantics controls Task5 prose and Task6 source/wheel guards.
No H6 estimator import: neutral mirror/link avoids existing architecture violation.
User supplied detailed implementation workflow; no additional brainstorming approval
round is needed to execute the requested scope. Only user-requested final review
delegation; no implementer agents. Remote skill script locators are not executable
filesystem paths, so this tracked plan is the durable ledger.

## Progress

Task 1: complete, freeze 83c2170; no new Python existed at freeze.
Task 2: complete, tests 065eee6 then implementation 6eb4c68. Missing-package RED,
then 31 basic tests GREEN; added causal adversaries RED->GREEN. Full suite 1302
passed before the latest 41 additional primitive/adversarial cases.
Task 3: complete. Latest targeted suite 111 passed; package 829 statements /
264 branches 100% each. Direct LINEAR a/error/roll arithmetic uses exact binary64
equality, including one-ulp boundary adversary RED->GREEN. Separate gain actual-use
time binding and exact downstream command/event lineage also pinned RED->GREEN.
Task 4: complete. Schema absent-module/enum-inventory/source-auditor RED->GREEN;
41 source files, 30 semantic claims, 44 isolated math cases, 143 schema fields,
18 enums, all 20 requested synthetic fixtures pass. History protects 264 original
files (three exact namespace amendments included); H6 validator other AST unchanged.
Full suite 1372 passed after review fixes, overall coverage 98.51%,
lint/format/mypy/build pass.
Task 5: complete, wire/capture/source compatibility/v2 mapping and final result
written. No native patch or empirical threshold.
Task 6: CI additive checks and fresh-wheel script complete. Fresh vanilla wheel
passes 70 imports without NumPy/native schemas, six H7 hashes and complete/partial
receipts/schema. All replay/knowledge/owner/optional smokes pass; separate research
wheel passes H5's 43 and H6's 26 cases. Final reviewed head/PR/CI publication is
recorded in the PR body and handoff, avoiding post-review local edits.

Ruling: three historical namespace inventory tests require observability as an
additional isolated namespace. Their original source/golden hashes remain intact.
H6 history validator now accepts only those exact byte substitutions (or original
bytes), tested against unrelated edits and removed hash guards. No H6 candidate,
numeric/source result, policy or other validator semantics changes. Cost: a narrow
compatibility amendment to historical inventory preservation, not a generic hash
exemption. Full regression first exposed these three failures; all 1302 then passed.

Source clarification: pinned LINEAR feedforward always passes compensation=True.
A disabled-compensation synthetic receipt remains a valid raw diagnostic with q=0,
but is rejected for pinned call-site eligibility, not treated as unavailable.
Observed q is still never filled from reconstruction or installed C.
Transient downstream sample-pair IDs and unapplied candidate/request values change
content identity but not installed/applied epoch state; RED tests pinned this.

Review round 1: exact head ad8dfe78392a3c966777fe724493e0b4c23e7725, C0/I2/M0.
Both source-cohort findings reproduced RED: incompatible source origin and stale
local carControl reused across cycles. Added source-specific role/origin checks,
explicit current-cycle binding for consumed local objects and same-instance local
identity/sequence nonreuse, retaining valid wire reuse and local LP fallback.
New source-AST mutation test also observed RED->GREEN. Full suite 1372 and
targeted111/100%-100% rerun; new exact-head review required, no finding waived.
