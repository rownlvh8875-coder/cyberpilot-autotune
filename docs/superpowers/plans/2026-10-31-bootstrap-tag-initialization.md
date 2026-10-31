# Bounded bootstrap tag initialization / reuse audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin selected initialization/reuse source facts without runtime admission.
**Architecture:** Immutable closed source-scope catalog plus read-only source/
repository byte audit;new files only,not a C semantics analyzer or producer.
**Tech Stack:** Python3.12,exact Linux6.12.113+unchanged PR42 patch.
**Spec:** docs/superpowers/specs/2026-10-31-bootstrap-tag-initialization-design.md

## Global Constraints

- Base37c0e614f01e13b5e6078178b3712c0ec6ba4495,branch audit/bootstrap-tag-initialization.
- Static source audit only,no source/runtime/old capture edits or new VM executions.
- Five subjects,thirteen open obligations,all nine permissions false/global counts None.
- No qualification,PR41/35/30 bridge,vehicle/Params/application/shared writes/merge.
- Preserve29oldPRs/maina5d3514f;ownstackedDraftvsfeat/guest-first-observed-bootstrap.
- Inline/TDD/one fresh final review/one C-I fix pass;no routine check-in gates.

## Review Focus

1. Byte integrity/citation checks advertised as proof of C control flow or runtime reuse.
2. File noaccount/backing omissions mistaken for definitely reachable tagged user FDs.
3. Early duplicate failures or final task free confused with post-hook TASK_FINALIZE.
4. Static zero initialization or atomic issuer number mistaken for atomic tag publication.
5. Optional external source verification/default embedded verification confused;old actual data reclassified.

### Task1: Immutable conservative source scope

**Files:** new tests/bootstrap_tag_audit/{__init__,model}.py;
tests/test_bootstrap_tag_initialization.py.
**Interfaces:** assess(rows:Any,available_claims:frozenset[str])->BoundaryAudit;
BoundaryAudit.boundaries tuple of SubjectBoundary(subject,citations,open_obligations).
No untrusted flags accepted. model exports fixed citation/obligation sets consumed byTask2.

Citation IDs bysubject:
TASK:TASK_X86_DUP,TASK_DUP_FAILURES,TASK_ALLOC_CALL,TASK_RESET_GATE,TASK_LATE_ABORT,
TASK_FREE,STATIC_INIT_TASK,TASK_LAYOUT.
NAMESPACE:NS_CONSTRUCTOR,NS_SHARED,NS_ATTACH,NS_FREE,NS_UNSHARE,NS_UNSHARE_EFFECT,
NS_STATIC_INIT,NS_LAYOUT,NS_CPC_ALLOCATED.
OFD:OFD_INIT,OFD_NORMAL_ALLOC,OFD_NOACCOUNT,OFD_BACKING,OFD_FREE,OFD_CACHE,OFD_LAYOUT,
OFD_RCU_REVALIDATE,RCU_REUSE_WARNING.
SEED:SEED_WALK,SEED_ABORT,ORIGIN_READ,COPY_RAW_READ.
ISSUER:COOKIE_STORAGE,COOKIE_CAS,COHORT_NONCE.

- [x] Literal five-subject fixture and omission/duplicate/cross-subject/authority/type/immutability tests;runpytest and expect missing API assertion RED.
- [x] Implement closed shape/type/unique/exact cohort checks and frozen defensive copies;focusedGREEN,coverage98/95minimum.
- [x] Fullpytest/ruff/mypy and commit `feat: define conservative bootstrap tag audit scope`.

### Task2: Exact source evidence and offline validator

**Files:** new tests/bootstrap_tag_audit/audit.py;
tests/test_bootstrap_tag_initialization_audit.py;
docs/evidence/bootstrap_tag_initialization_{sources,result}.json;
tests/architecture/test_bootstrap_tag_audit_boundary.py;two narrow .gitattributes rules.
**Interfaces:** consumesTask1assess+fixedsets;validate(pristine_root=None,patched_root=None)->dict;
validate_sources(data,pristine_root=None,patched_root=None)->frozenset[str];
validate_result(data,claims)->BoundaryAudit. Full provenance/cohort frozen before reads.

- [x] Extractninepristinefilesfromverifiedarchiveintofreshdurablereferenceprefix;
  freeze11patchedfiles/33embeddedranges and4repositoryrecords,nevereditexistingassets.
- [x] MissingAPI RED plus source/range/blob/base64/catalog/path/authority/paired-root/CLI adversaries;tests run real audit against controlled bytes,not grep its implementation.
- [x] Implement fixed canonical catalog/embedded/source checks;explicit paired sourceGREEN;architectureguards old paths/no writes/process/network/qualification bridge.
- [x] Fullpytest/ruff/mypy and commit `audit: pin bootstrap tag initialization and reuse boundaries`.

### Task3: Boundary matrix,regression,review and Draft publication

**Files:** new docs/bootstrap_tag_initialization_{audit,result}.md.
**Interfaces:** Task2reportandsource IDs bind document citations;no new runtime API.

- [ ] Writefive-subject/13-obligation matrix with exact source anchors,source-only vs runtime limits andnextsingletask.
- [ ] Fullpytest/alloldsourcehistoryaudits/PR42explicit source-assets/native192/replay4;
  ruff/format/mypy/build/freshvanilla-researchwheel/purecoverage;commitresult.
- [ ] Fresh exact-head whole-branch review with verbatim Review Focus;oneauthor C/I RED→GREEN fixpass/fullrerun,no rereview,minors deferred.
- [ ] Fresh exact-head pytest/CRLF97+newtests;ownstackedDraft,attach,push+PRCI6jobseach;
 29oldPR/mainpreservation,clean;Koreanhandoffallrulings/costs/minors.
- [ ] Recoverablyarchiveonlyownplanworkspace,keepdurablesourceassetsandalloldplans.
