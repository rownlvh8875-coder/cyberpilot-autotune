# Inherited OFD provenance design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design first-observation identity without inventing pre-arm allocation history.
**Architecture:** Pure SYNTHETIC_ONLY premise checker,selected-source audit and future
bootstrap design. No producer/VM/actual-receipt conversion or prior-file edits.
**Tech Stack:** Python3.12,selected read-only Linux6.12.113 PR40 source references.
**Spec:** docs/superpowers/specs/2026-10-31-inherited-ofd-provenance-design.md

## Global Constraints

- Base21a542eba9e889323b2cb1b7d7c75d9c9cab1025;branchdesign/inherited-ofd-provenance.
- All previous src/compatibility/CI/tests/evidence/actualsource/assets/27oldPRs frozen.
- No guest execution/kernel build/hosttrace;new test-only synthetic design,all9false/BLOCKED.
- FIRST_OBSERVED != ALLOCATION;no lifetime/copycut/coverage/runtime qualification.
- Inline,one fresh final review,one authorC/I TDDpass,no re-review,ownDraft/no merge.

## Review Focus

1. First-observed tag silently becomes allocation birth after copy or in descendants.
2. Bootstrap PID1 identity accidentally changes managed-root scope enrollment.
3. Alias equality or unavailable fields inferred from FD/path/inode/content instead of consumed source.
4. Mixed boot/issuer/generation/role or wrong paired record stage yields committed synthetic links.
5. Same-domain ordinal,oneCPU,file_lock,empty graph or local counts mistaken for completeness/global cut.

### Task1: Immutable synthetic origin/lineage premise checker

**Files:** new tests/inherited_ofd_design/{__init__,model}.py;
tests/test_inherited_ofd_design.py;spec above.
**Interfaces:** evaluate(data:object)->Decision with exact fields/values/bounds fromspec.

- [ ] Tests first: seeded parent/table/OFD yields consistent conditional alias links but historyfalse;unknown parent/source/OFD yields no invented link;all-birth example still historyfalse;abort/failed no links.
- [ ] Adversaries: observed-class,origin/stage promotion,duplicate/reuse/role/boot/epoch/generation drift,wrong pairedread/ordering/source-destOFD,zero/Bool/Float/nonfinite/oversized/cyclic/unknownfields;digest mutation/defensivecopy.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_inherited_ofd_design.py`;Expected missingAPIRED,then implement pure checker and same command allPASS.
- [ ] Run ruff/format/mypy/newpurecoverage;Expected clean and>=98/95;commit.

### Task2: Source-bound evidence,architecture and bounded result

**Files:** new tests/inherited_ofd_design/audit.py;tests/test_inherited_ofd_design_audit.py;
tests/architecture/test_inherited_ofd_design_boundary.py;
docs/evidence/inherited_ofd_design_{schema,sources,cases}.json;
docs/inherited_ofd_identity_contract.md;docs/inherited_ofd_identity_result.md;
new narrow .gitattributes entries only.
**Interfaces:** consumes Task1 evaluate;produces validate(kernel_root:Path|None=None)->dict.

- [ ] Audit missingAPIRED tests: catalogexpectedoutcomes,source/schema/case/hash drift and reclassification cannot pass;optional sourcebytes not claimed by default.
- [ ] Implement offlineaudit,fixedsemantic/case/source manifests;explicit source verification validates file/blob/ranges,not runtime/history qualification.
- [ ] Document approaches/prearm capture point,newwire+issuer/scope split,partialknownlineage vs birth,initialization/reuse/publication/quiescence/loss/perturbation prerequisites,PR40mapping/non-goals/retainedblockers.
- [ ] Architectureguard pureimports/noIO/nooldoraclebridge and everypreviouspath frozen;runfocused/fullpytest,oldaudits/native192,ruff/format/mypy/build/freshwheel/CRLF;ExpectedallPASS.
- [ ] Publish bounded result+single next recommendation,commit,one fresh review onexplicithead;C/I oneauthorTDDpass/fullrerun,minorledgerdefer,no2ndreview.
- [ ] OwnstackedDraftvsfeat/guest-per-slot-fork-copy,attach,exactheadpush+PR6jobs each;27oldPRsnapshot/mainunchanged,clean;Koreanhandoffallrulings/costs/minors.
- [ ] Recoverably archiveonlythisplanworkspace;allpriorassets/planspreserved.
