# DENY-FD v2 Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax; one fresh whole-branch reviewer at the end.

**Goal:** Implement only approved source/compile-only v2 inventory diagnostics and pinned history permission.
**Architecture:** Keep P/P2 and39old paths intact; freeze one loader hook in P3, then enable a new pinned helper. Pure v2 decoder checks exact untrusted point references; a separate fixed guest C source is compiled, never executed.
**Tech Stack:** Python>=3.12.3,<3.13 stdlib,pytest,Git,Linux static C compiler; existing dev tools only.
**Spec:** docs/superpowers/specs/2026-11-01-deny-fd-v2-producer-design.md.

## Global Constraints

- Base75fd4358a2d42bec55dc85ba85afbb23e8feb6f9;new branchfeat/deny-fd-v2-source-contract.
- Exact1existing+18new paths as spec table;19delta/58cumulative;no directory wildcard.
-39old paths byte-exact;original P/P2,22postimages,P2two postimages,old tests/guards unchanged.
- P3 first commit parent exactly base;one old hook finalized before freeze;helper pins after P3.
- Pure decoder has no IO/operational/legacy/PR54/application dependencies;all9permissionsfalse.
- No guest/kernel/vehicle/host-ELF execution,capture,Params/controller/schema,estimator bridge.
- No remote writes,push,PR,ready,merge/rebase/squash/force;no prior PR/main movement.
- Resource bounds1024events/64FDs/4096linebytes/1MiBserial;unknown generation/drop mustnull.

## Review Focus

- Historical P2 mutant HEAD must retain old validation without granting new paths; missing objects are not negative ancestry.
- Cause references must bind exact same-point FD rows, including FD0, not a case-number or expected-inventory shortcut.
- A valid-looking observed header or synthetic fixture must not acquire provenance authenticity or operational authority.
- Logging/clock failures must terminate the stopped child without resume or fabricated timestamps/success frame.
- Source manifest M,ELF and final capture identities must not form self-hash cycles or accept changed working sources.

### Task 1: Exact successor history permission

**Files:** modify only tests/history_transition/deny_fd_successor.py;create tests/history_transition/deny_fd_v2_successor.py,tests/test_deny_fd_v2_history_policy.py,docs/evidence/deny_fd_v2_history_successor_v1.json;include this plan/combined spec in P3.
**Interfaces:** new `validate_v2_successor(root:Path)->frozenset[str]`;constants BASE,PREREGISTRATION,NEW_PATHS. Existing loader only imports it and unions its final result.

- [x] Write missing-helper test and real-Git P2/P3 cohort fixtures;run missing API test. Expected:RED feature absent.
- [x] Finalize old hook;generate39preserved+1pre/post manifest with18literal additions;commit P3 as first commit(parent=base),without new helper. Expected:immutable P3,intermediate RED not published.
- [x] Implement new helper:original P/P2-derived40scope,tri-state B ancestry,required P3 current cohort,parent/lineage/raw blobs,modes,index/worktree,CRLF,closed19delta;no fetch or fallback. Historical cohort returns empty only after normal exit1.
- [x] Real Git tests:39paths*3layers*4mutations,modified hook3*4,missing/wrong pins/parent,source object errors,unmerged/symlink/extra path,working manifests,downgrade,CRLF;original B node executes in isolated fixed clone.
- [x] Run `.venv/bin/python -m pytest tests/test_deny_fd_v2_history_policy.py tests/test_history_transition_policy.py tests/architecture -q -p no:cacheprovider`. Expected:all history guards GREEN;final19file completeness deferred until Task4 but existing guards not skipped.
- [x] Commit enabling helper/tests. Ledger exact P3 and test result.

### Task 2: Pure v2 contracts,wire and inventory evaluator

**Files:** tests/deny_fd_v2/{__init__,contracts,wire,validation}.py;tests/test_deny_fd_v2_wire.py;tests/test_deny_fd_v2_validation.py;docs/evidence/deny_fd_v2_schema.json.
**Interfaces:** frozen `Event(seq:int,time_ns:int,kind:str,values:tuple)`;`Capture(events:tuple[Event,...])`;`Decision(outcome:str,reasons:tuple[str,...])`;`decode(raw:bytes)->Capture`;`check_inventory(capture:Capture)->Decision`;`canonical_digest(capture:Capture)->str`.

- [x] Write missing decoder API and literal DFD01..06 flat-wire fixtures (no actual capture);run missing API test. Expected:RED API absent.
- [x] Implement exact type/arity/enums/bounds/immutable copy and LF markers;clock/schema/evidence fixed;no v1 fallback. Implement grammar and source-row lookup,set relations,result/reap/END checks with reasoned rejection. Decisions remain BLOCKED/9false.
- [x] Tests pin FD0,multiple extras,no-denial/missing/mixed,exact source/cohort/time/count,wrong refs,all syntax/type/enum/unknown cases,raw/synthetic trust limits and deterministic digests. No source-derived expected values.
- [x] Run new tests and isolated pure coverage(stmt>=98%,branch>=95%,target100/100);expected GREEN. Run installed mypy and new pure-module mypy/ruff;commit pure API and tests.

### Task 3: Fixed source and compile-only binding

**Files:** tests/deny_fd_v2/guest/probe.c,tests/deny_fd_v2/build.py;extend approved new tests/architecture/test_deny_fd_v2_boundary.py and validation test file;docs/deny_fd_v2_contract.md.
**Interfaces:** `describe_sources(revision:str)->dict[str,object]` reads only fixed raw Git source set;`compile_fixed_probe(destination:Path)->dict[str,object]` consumes fixed source manifest,verifies working/Git bytes,spawns only fixed compiler/version commands,writes only new owned destination;never executes ELF.

- [x] Write missing build API/C compile contract tests;expected RED before implementation. Pin malformed/tampered source manifest,working source drift,nonempty destination,compiler failure and fixed argv/no target execution.
- [x] Implement C guest guard,closedDFD01..06 profiles,root bootstrap/two stops,complete stopped FD scan,stored per-FD refs,timestamps and snapshot,actual set differences,strict v2 emission,cleanup/reap. No post-point resume,exec/read,case-selected denial,unknown default0 or artificial clock increments.
- [x] Implement fixed compile helper using subprocess argument vectors,strict fixed source list and separate pre/post-build records;no caller command/payload/compiler flags. Run genuine static compilation explicitly,never execute it. Unit doubles cover external compiler failure paths but do not replace actual compile evidence.
- [x] Commit source+tests as M after quality checks;generate source manifest from raw M files excluding itself/ELF/capture,then compile again with real M/digest. Expected:ELF exists and source binding matches;runtime unqualified.

### Task 4: Final bounded verification and local handoff

**Files:** docs/evidence/deny_fd_v2_sources.json;docs/deny_fd_v2_result.md;approved new architecture/tests/spec/plan bookkeeping only.
**Interfaces:** current M-bound source manifest;exact19delta+58cumulative and39frozen+1P3 checks.

- [x] Add final current-HEAD completeness check for all19 paths and wheel/source separation;do not use this final check for partial P3 test fixtures.
- [x] Run full pytest,coverage and unchanged subsystem gates,audits/history,ruff/format/mypy,sdist/wheel,fresh wheel import72byte-identical package files/replay/knowledge/owner/science/friction/receipt smoke. Expected:GREEN;no runtime qualification claims.
- [x] Verify source M manifest and genuine compile record,39old files/P2postimages/legacyv1,onehookP3 exact;commit pre-review result. Expected:clean final head.
- [x] One fresh whole-branch reviewer checked base..2665a15 and all ledger rulings:C0/I2/M0. BothImportant findings received one RED→GREEN author fix pass,new sourceM2481b84/manifest/genuinecompile and full5049PASS coverage/packaging rerun;no second reviewer or independent-clean-new-head claim.
- [x] Retain local branch/workspace. Record source implemented/compile-only,OBSERVED_V2_CAPTURE_UNAVAILABLE,LEGACY_PR34_M1_OPEN,FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED,APPLICATION_NOT_AUTHORIZED/all9false. No publication or next task auto-start.

Final metadata head receives one additional full-suite/clean-status handoff gate;
its observed exact SHA/result belongs to the owned external ledger and final
handoff after the commit,not a self-referential or premature result here.

### Task 5: Approved Windows nested-pytest isolation repair

**Base:** ccc269e6157cdec6696fbe74020a55781d6dcf22(PR55 exact published head).
**Spec:** appended follow-up in the existing producer design;historical Tasks1..4
remain complete. Current approval permits only PR55 append-only push/CI within
the same19paths. No older PR/main changes,timeout increase,skip/xfail,guard/node
rewrite,sourceM2 change or runtime execution. Use retained native inline workflow.
**Files:** tests/test_deny_fd_v2_history_policy.py;this plan;the existing spec;
docs/deny_fd_v2_result.md. No new repo paths.
**Interface:** session-autouse fixture scopes PYTEST_DEBUG_TEMPROOT to a freshly
owned child root below the parent's already-created tmp_path_factory basetemp;
environment is restored on teardown. No runtime/public API changes.

**Repair review focus:** never clean foreign sessions;do not shift cleanup to
the adjacent frozen runner;do not route parents into their own descendant or
delete the active parent root;preserve original60second/node/source checks;
do not claim historical Windows timing or runtime qualification from a canary.

- [ ] Add real-process parametrized regression test_nested_replays_preserve_foreign_sessions:
  seed4private fake stale sessions with literal canaries;run a fresh child pytest
  with owned parent basetemp and foreign PYTEST_DEBUG_TEMPROOT. Select either
  the exact V2 original replay,or V2 API then unchanged old historical replay.
  Require exit0 and literal1/2passed summaries plus all canary bytes preserved.
  Run focused tests before fixture implementation. Expected:2RED due foreign
  canaries removed,not a source assertion or missing dependency.
- [ ] Add the minimal session-autouse temporary-root fixture using pytest's
  scoped MonkeyPatch. Keep original replay command/assertions/timeout60 unchanged.
  Run focused regression and original node. Expected:GREEN,foreign canaries intact.
- [ ] Run full pytest,coverage and unchanged subsystem gates;history/source audits,
  ruff/format/mypy,build/fresh-wheel/replay/owner/science/receipt smoke. Verify
 19delta/58cumulative,original22/preserved39/P3hook and unchangedM2source bytes.
  Expected:allGREEN,no test or gate exclusions/criteria changes.
- [ ] Record observed result and commit append-only. One fresh whole-branch
  reviewer checks exact head and repair focus. Material findings receive one
  RED→GREEN author pass/full rerun,no repeated reviewer.
- [ ] Push only PR55's explicit new head after remote-match checks;watch both
  push and PR exact-head CI. Keep Draft and all9permissionsfalse. Record actual
  Windows outcomes,not a Linux-only fix claim. No auto-next-task or merge.
