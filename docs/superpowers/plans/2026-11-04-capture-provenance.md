# Pure Capture Provenance Bundle Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Validate supplied capture-provenance metadata without reading sources or producing H receipts.

**Architecture:** A separate test-only pure package owns six immutable DTOs and one
assessor. Closed132target/273witness-role catalogs and exact10A2M scope are embedded
from this reviewed pack. No old preparation/H1/product import or writer/producer exists.

**Tech Stack:** Existing Python>=3.12.3,<3.13,stdlib dataclasses/typing,pytest/Ruff/mypy/
coverage;no dependency/workflow/config change. Use existing prepared environment.

**Spec:** capture-design.md,capture-contract.json,capture-catalog.json,acceptance.json
and scope-proposal.json in this immutable design pack. Adopt spec/plan at the exact
proposed repository paths;registration embeds the reviewed objects and manifest digest.

## Global Constraints

- Base7422a868a5802ab49b496429448795e88c4de074/tree14154790b5379280c2b24cdd50cde6e9a7a35229.
- PR61/60/8/9/main and all other oldrefs remain unchanged. New branch only:
  feat/capture-provenance-bundle;NEW DraftPR basefeat/preflight-profile-diagnostic-mapping.
- Exactly10new/2oldmodified paths;old exceptions are two named consumer function bodies.
  No added old imports/globals/helpers/functions;new scope helpers in new scope-test only.
- All6DTOs fixedBLOCKED/all9false/H_executedfalse/integratedfalse/profile_recordNone/
  contentonly/atomicityNOT_ESTABLISHED. Complete result COHORT_METADATA_CONSISTENT only.
- ExactDTO fields/types and algorithms are in capture-contract.json;no new wire/digest API.
- No raw H values,source reader,provider,collector,H-target constructor,clock,IO,process,
  network,thread,application/owner bridge or runtime admission. Full producer remains blocked.
- Newpackage>=98statement/>=95branch,zero exclusions;all old tests/floors stay unchanged.
- Public fixture is fictional metadata only. No actual host/R0/identity data collection.

## Review Focus

- Missing root epoch beside a known negative/error OR mutually conflicting peers:
  Task2 CP30/31/37,never early-return or compare only against an absent root.
- One source event reused by legitimate roles versus conflicting partial metadata:
  Task2 CP20/21/23/39/40;partial inverse identities cannot erase known alias contradictions.
- Three consumption witnesses per original O/D field:Task2 CP07+catalog assertion;
  one command cannot certify the other two or be silently mapped to their contexts.
- Source counters and stage timing are distinct:Task2 CP24/25/28/38;compare time only
  across known equal domains,never infer global sequence order or actual target deadline math.
- Current raw/untracked/frozen scope checks remain live:Task1 tamper table and Task3
  exact-source preservation;oldA+M staysA and catalog cannot widen phase permissions.

---

### Task1: close the successor while preserving every older consumer

**Files:**Create tests/test_capture_provenance_scope.py,
docs/evidence/audit_compatibility/capture-provenance-v1/registration.json,
docs/superpowers/specs/2026-11-04-capture-provenance.md,
docs/superpowers/plans/2026-11-04-capture-provenance.md.
Modify only tests/test_audit_compatibility_history_architecture.py::
test_all_earlier_files_and_guard_bytes_are_preserved and
tests/test_preflight_profile_mapping_architecture.py::
test_final_scope_is_exact_and_manifest_cannot_grant_authority.

**Interfaces:**new scope helpers:
`assert_capture_scope(rows:list[str],*,exact:bool=False)->None` and
`assert_capture_composition(repair:list[str],profile:list[str],mapping:list[str],
new:list[str],profile_current:list[str],repair_current:list[str],
mapping_current:list[str])->None`.
The latter independently freezes literal repair4A5M,profile14A2M,mapping10A2M and
compares exact composed status rows including new. Oldhelpers are invoked unchanged
on frozen ranges before new helpers. Module import has no old-consumer call cycle.

- [ ] RED `test_capture_scope_is_closed` accepts literal10A2M/subset,then rejects
  old product/provider/prep/mapper helper/workflow edits,unknown path,duplicate,alias,D/R.
  `test_composition_preserves_all_prior_rows` rejects each missing/extra/duplicate old
  or current row. Run new scope module:expected assertionFAIL absent helper,not typo.
- [ ] Implement helpers from literal path/status sets,never from mutable registration.
  Freeze209edaa..db915(9rows),4b77..0ac6(16),0ac6..7422(12).
  Old helper composition verifies frozen4b77..7422(26) and209..7422(33).
- [ ] Global consumer retains exact raw `git diff --no-renames --name-status 4b77`,
  `...209edaa`,`...0ac6` calls WITHOUT an end argument,plus untracked and every earlier
  tree/range check. Add separate7422..current+untracked and compare new composed
  statuses. All new logic stays within the named body or new scope-test helpers.
- [ ] Mapper final-inventory consumer reads frozen0ac6..7422 without current/untracked
  augmentation;retain all original registration/blocker/noauthority assertions,then
  locally invoke the real global consumer. Old profile consumer already does that;
  do not edit it. New final scope guard owns current7422..current+untracked.
- [ ] Run old/new rawrange/untracked/tree/manifest tamper cases. Verify top-level AST
  and all old nonconsumer source bytes at7422 before commit. Full pytest expectedgreen.
  Complete new final counts will be4b77/current36,209/current43,0ac6/current22,new12.
- [ ] Commit only registration/docs/scope and the two bounded consumer changes.

### Task2: immutable metadata and cohort/event assessment

**Files:**Create tests/audit_capture_provenance/{__init__,contracts,validation}.py,
tests/fixtures/capture_provenance.py,tests/test_capture_provenance.py.

**Interfaces:**Six exact frozen/slotted DTOs with fields in capture-contract.json:
CaptureEpoch,WitnessContext,CaptureWitness,CaptureWitnessBundle,CaptureIssue,
CaptureAlignmentDecision. Public function:
`assess_capture_bundle(bundle:CaptureWitnessBundle)->CaptureAlignmentDecision`.
Expose these names from __init__.py only;no reader/decoder/serializer/adapter API.

- [ ] Write `test_complete_fictional_metadata_is_not_capture_or_admission`:construct
  baseline_recipe from acceptance.json;assert273witnesses/132paths,
  alignment_statusCOHORT_METADATA_CONSISTENT,allfixedfacets/9false/profile_recordNone.
  Write parametrized `test_planned_metadata_case` forCP01–CP40,including exact
  targeted reasons and locator fields. Assert current public API absent ->RED,
  not a module-collection error. No runtime CR case is claimed executed.
- [ ] Implement literal catalogs/closed locators,exact primitive/tuple/forged graph
  validation in contracts.py and one pure assessment algorithm in validation.py.
  Batch None command_id/attempt is expected;command None is unavailable. Copy and
  normalize tuples in catalog order;no unknown/duplicate keys or default witnesses.
- [ ] Pin independent known-error and missing-fact collection on every path. CP20
  permits exact shared source events across different roles;CP23 compares recursively
  available context fields so one missing field cannot hide known metadata conflict.
  Require all involved keys in source-alias/context-change/boundary-reuse reasons.
- [ ] Check all source-event groups,per-source sequence/time order,inclusive capture
  window and command stage partial order. Do NOT inspect referenced payloads or call
  the old profile comparator;actual target deadline/value/enforcement truth is absent.
  Check known peer epoch contradictions independently of root availability(CP37).
  Time comparisons require known matching domains(CP38);known event-ID components
  conflict even with partial remaining identity(CP39/40). Preserve both errors/missing.
- [ ] Test every273key deletion,each nullable primitive and all context dimensions;
  malformed int/bool/float/overflow/nonfinite/subclass and nested forged graph fail
  constantValueError without secret/canary echo. Known0 never becomes missing.
  Missing root policy/epoch does not erase negative outcomes or event conflicts.
- [ ] Run new behavior/scope tests,Ruff/format/strictmypy newpackage. Expectedgreen.
  Run whole project before commit;no old floors/xfails/skips/exclusions changed.
- [ ] Commit only this neutral metadata implementation and its fixture/tests.

### Task3: architecture,full verification and bounded publication

**Files:**Create tests/test_capture_provenance_architecture.py;extend only new owned
files as needed. No extra existing-file edit beyondTask1 exceptions.

- [ ] Fresh-process import/assessment audit forbids file writes/network/clock/process/
  thread and H/prep/mapper/product/collector imports. Assert all6DTO facets immutable,
  exact code/subject registry,no target result/value or hidden capability is emitted.
- [ ] Test final exact10A2M at7422,current/untracked/frozen tamper hooks and all old
  nonconsumer bytes/top-level AST/helper functions preserved. Registration cannot
  expand catalog/scope/permissions. No automatic reuse of prior S/R0/H runtime facts.
- [ ] Run full pytest,packagecoverage>=98statement/>=95branch(no exclusions),all old
  floors,source/history audits,Ruff/format/mypy,replay,build and freshwheel smokes.
  The package is test-only;product-wheel import proves absence of new dependency,
  not installed availability of this test package or runtime collection capability.
- [ ] Commit. Fresh exact-head whole-branch review;C/I fixes requireRED->GREEN/full
  rerun and recorded exact-head evidence. Never claim C0/I0/M0 when minors remain.
- [ ] Recheck exactPR61head/base/refs and credentials. If intact,push ONLY a NEW
  nonforce feature branch and create a NEW DraftPR on the declared stack. Attach it.
  Verify exact-headpush+PR CI. Preserve all oldPRs/main;no merge/rebase/admin bypass.
- [ ] Retain evidence append-only with byte/digest verification. Report implemented
  provenance validator separately from NOT_IMPLEMENTED runtime producer and all
  inherited blockers. Stop before any reader/provider/historical collection or H.

## Full producer is a later separately scoped project

CR01–CR07 are explicit NOT_EXECUTED obligations,not this plan's tests. Effectful
provider/bootstrap/supervisor/readers require actual reviewed content,policy,budgets,
complete expected inventories and authority before their implementation/qualification
can be planned as runnable work. No numeric defaults,privileged fallback or fake source
hook pins are supplied here. This plan never grants an H execution scope.

## Self-review

132catalog/273keys + exact six DTO/interface ->Task2;phase/current/frozen guards ->Task1+3;
privacy/noeffects/knownnegative+missing/context/event/window rules ->Task2+3. Each Review
Focus has an explicit owning test. Full physical capture and H value truth are outside
this plan,clearly blocked rather than silently waived. Execution method is inline under
the user's existing delegation;this design-only task does not start implementation.
