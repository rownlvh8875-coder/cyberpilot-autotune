# Owner-scoped tag read protocol design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design independent lifetime/publication premises without runtime qualification.
**Architecture:** Pure synthetic premise/DAG checker,read-only frozen source/schema/
case audit,and future capture design;no actual source/producer adapter.
**Tech Stack:** Python3.12,existing exact PR43 source catalog;no new dependencies.
**Spec:** docs/superpowers/specs/2026-10-31-tag-read-protocol-design.md

## Global Constraints

- Basee01cdc127bbb17073aa47967b926b68088f57ded;sourcecatalog4b0712a7d12069a74032f8f9f91861bf22397436927a278818968d9f647930af.
- Branchdesign/owner-scoped-tag-read-protocol;ownDraftbaseaudit/bootstrap-tag-initialization.
- SYNTHETIC_ONLY/BLOCKED/all9false/allruntimeproofsfalse/globalcountsNone.
- No source/kernel/producer/capture/oldartifact mutation,newrefs/locks,VM/device/vehicle/Params/application/estimator bridge.
- FIRST_OBSERVED unsupported;reference modeOFD-only;no silent stage/mode fallback.
- Preserve30oldPRs/maina5d3514f;appendonly,onefreshreview/oneCIfixpass/no merge.

## Review Focus

1. Synthetic consistency mistaken for C/LKMM proof,source HB or actual lifetime/publication witness.
2. Reference-after-read,RCU-only,relaxed-ref or buffer ordering silently accepted as target publication/lifetime.
3. FIRST_OBSERVED seed promoted to ALLOCATION/private unpublished state or generic referenced TASK/NAMESPACE accepted.
4. Immutable identity pooled across changing membership/cohort or missing/zero/False values defaulted.
5. Emission after release dereferences a target instead of copying saved scalars;real CPB emission n used as HB evidence.

### Task1: Pure conditional read protocol and adversarial DAGs

**Files:** new tests/tag_read_protocol/{__init__,model}.py;
tests/fixtures/tag_read_protocol.py;tests/test_tag_read_protocol.py.
**Interfaces:** evaluate(payload:Any)->ReadProtocolDecision;SyntheticTagSnapshot frozen;
ReadProtocolDecision.premises_consistent/proposed_snapshot/reasons andfixedfalse
qualification/permission fields. Export VERSION,BASE,SOURCE_DIGEST,TOP_FIELDS and
section fields forTask2semantic-schema matching. No model I/O.

- [x] Writeindependentliteral private/reference payloads+negativecasesbeforecode;
  assert consistent positives(alwaysBLOCKED),missing path/cycle/unsupported seed/
  stage/lifetime/publication/member drift/unknowns/observer effects reject;runRED.
- [x] Implement closed typed contexts and explicit transitive DAG relations,
  notlistorder;frozen defensive output,reasonedrejections;focusedGREEN/coverage98-95minimum.
- [x] Fullpytest/ruff/format/mypy and commit `feat: model owner-scoped tag read premises`.

### Task2: Frozen source/schema/synthetic catalog audit

**Files:** new tests/tag_read_protocol/audit.py;tests/test_tag_read_protocol_audit.py;
tests/architecture/test_tag_read_protocol_boundary.py;
docs/evidence/tag_read_protocol_{schema,sources,cases}.json;two .gitattributes rules.
**Interfaces:** validate()->dict;validate_sources(data)->frozenset[str];
validate_schema(data)->None;validate_cases(data)->tuple[int,int]. ConsumesTask1
evaluate/constants and independently literal expected case outcomes,never actualrecords.

- [ ] Freeze semantic sections/types/stages/availability andsource references:
  prior bootstrap_tag_initialization_sources/result JSON,prior model/audit,
  unchanged PR42kernel.patch/guest_bootstrap_sources JSON(exact bytes all-text-disabled).
- [ ] Casescome frompreimplementationliteralfixtures,notmodel-computedexpectations;
  writeauditmissingAPI/corruption/schema/source/cohort/permission/CLItestsRED.
- [ ] Implement frozen canonical manifest/byte checks plus prior static source
  catalog validation(no external-root option ornew runtime witness),case replay,
  architecture oldpath/no IOorbridgeguards;focusedGREEN.
- [ ] Fullpytest/ruff/mypy and commit `audit: freeze tag read protocol design evidence`.

### Task3: Future capture architecture,verification and Draft handoff

**Files:** new docs/tag_read_protocol_{contract,capture_design,result}.md.
**Interfaces:** Task1schema/Task2cases/sourceIDs anchor design and limitations.

- [ ] Document architecture alternatives,exact capture/lifetime/publication/writer/
  membership conditions,oldstage mapping,seed unsupported prerequisites,wire/version/
  availability,performanceunknowns andnextsingleboundedtask;no implementation claim.
- [ ] Fullpytest/oldsource-history/PR42-43sourceassets/native192/replay4/ruff/format/
  mypy/build/freshwheel/purecoverage;commitdocs beforefresh wholebranchreview.
- [ ] Onefresh exact-headreviewwithverbatimReviewFocus;authorC/IONEpassRED→GREEN/
  fullrerunonlyifneeded;allminorsdeferred/allrulingsrecorded,no rereview.
- [ ] Exactheadpytest/CRLF/ownstackedDraft+attach/push+PR6jobseach;30oldPRs/main
  preserved,clean;Koreanhandoffallrulings/costs/minors.
- [ ] Recoverablyarchiveonlyownplanworkspace;alloldplans/assetsremain.
