# DENY-FD v2 dedicated transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax. One fresh whole-branch review at end.

**Goal:** Implement a default-closed test-only second-serial collector without changing strict v2 acceptance.
**Architecture:** Fixed two-serial VM profile, separate bounded console/telemetry, immutable new-version records. Historical guards replay original source while a new guard enforces the actual successor.
**Tech Stack:** Existing Python3.12 stdlib/pytest,guest busybox shell;no dependencies.
**Spec:** docs/superpowers/specs/2026-11-01-deny-fd-v2-transport-design.md; exact paths are pinned in docs/evidence/deny_fd_v2_transport_history_v1.json.

## Global Constraints

- New branch feat/deny-fd-v2-isolated-transport from27cfdee;no move of existingPRbranches/main.
- Exactly2routing+20newfiles;P5soleparentbase,76old images preserved;oldP4postimages/M2bytes unchanged.
- No QEMU/probe/guest execution in implementation/tests/CI;only synthetic doubles/harmless host workers.
- 1048576combined bytes,180sdeadline,2sgrace;no assertion/skip/gate/timeout relaxation.
- All9permissionsfalse;all existing runtime/scientific/application blockers remain.
- No push/PR/merge or subsequent runtime task automatically.

## Review Focus

- FIFO opened before producer:early EOF must not be mistaken for process completion.
- Anchors retained after exit:do not wait indefinitely for EOF or lose available bytes.
- One stream floods while other contains terminal markers:fair draining and aggregate cap,never filter.
- Error after valid telemetry:console/selector/persistence/cleanup uncertainty must still reject.
- Guest stdout relocation:fixed child FD profile and old source receipt meaning must not be silently changed.

## Task1: Exact successor and historical replay

**Files:** two routing paths, new history helper/manifest, new architecture/history tests, new committed spec/plan listed in proposed-scope.json.
**Interfaces:** validate_transport_successor(root:Path)->frozenset[str];replay_original_harness_scope(root:Path,tmp_path:Path)->None.
- [ ] Add tests for soleparent,P5 missing/malformed,76preserved drift,two routing pre/postimages,unmerged/index/worktree tamper,outside22 and older cohort scope leakage. Run newhistory+architecture tests:ExpectedRED missing successor.
- [ ] Compute actual base images and actual routingpostimages;create P5 registration withsoleparent27cfdee, no selfhash. Subsequent helper pins actualP5SHA;appendonly,never rewriteP4.
- [ ] Route old22node ONLY for verified P5 descendants to ORIGINAL27cfdee node/assertions;retain original19 replay and unchanged timeout. New guard requires exactcurrent22delta.
- [ ] Run newhistory+all predecessor architecture/history tests:ExpectedPASS;verify no directorygrant. Commit explicit literalpaths.

## Task2: Assets, immutable records and fixed image

**Files:** new package __init__/assets/contracts/image;new assets manifest,contract document,and assets/image test files.
**Interfaces:** preflight()->TransportAssets wrapping oldAssetBundle plus fixedconfig/transportprofile;init_bytes(case:str)->bytes;build_image(assets:TransportAssets,case:str)->bytes;StreamEvidence and TransportProcessResult exactly as design.
- [ ] Write RED tests forconfig/source/VM drift,unknown metadata,None!=0/false,mutation,distinct stream digests/roles,newreceiptversion,no authority;stty/missingdevicefailuresnoEXEC/no fallback;deterministicnewinit/archive,unchangedprobe bytes,onlystdout redirection/no heldfd9.
- [ ] Implement immutable validation,exactprofile and guestinit;use old preflight read-only,not old image/runner mutation. Preserve no import-time IO.
- [ ] Run newassets/imagetests:ExpectedPASS;read-only asset verification allowed,no guestlaunch. Commit explicit paths.

## Task3: Dual-stream supervisor and evidence preservation

**Files:** new runner/capture/host_main,new runner/capture tests;resultdocument.
**Interfaces:** supervise(process:Popen[bytes],telemetry_fd:int,console_fd:int,*,timeout:float=180.0,grace:float=2.0)->TransportProcessResult;
capture_cases(cases:tuple[str,...],destination:Path,*,run_prepared_guest:bool=False)->tuple[TransportAcquisitionRecord,...].
TransportAcquisitionRecord frozen contains StreamEvidence pairs and fields in design;TransportCaptureFailure retains partial pair,currentrecord,completedrecords and distinct acquisition/persistence errors.
- [ ] Write RED tests for default noIO/nospawn,missingLinux/fixedassets,FIFOlink/substitution/refusal,preconnectEOF,writeranchorheld,independentEOF,process-exitdrain,bothstreamsready/flood/aggregatecap,timeouts/close/selector/clock/cleanup/interrupt/persistence errors and all9false.
- [ ] Write RED strict-framing test:console noise with clean telemetry is content-consistent;noise IN telemetry always rejected. No source or acceptance mutation. Test fixedchildprofile from unchangedM2 source and no artificial observed FD rows.
- [ ] Implement fixed argv/endpoints and exclusiveFIFO lifecycle,fair selector loop and existing owned-group semantics;no runtime fallback or caller options. Save telemetry.bin,console.bin,record.json independently;default CLI emits BLOCKED/NOT_STARTED without setup;all outcomes exit2.
- [ ] Run new package+all oldwire/harness/history tests:ExpectedPASS;harness coverage>=98%statement/95%branch,target100/100;no actualguest. Commit explicitpaths.

## Task4: Final source gates and review

**Files:** new contract/resultdocs only;no further code unless confirmed regression requires RED/fix.
**Interfaces:** exact committedsourcehead and externally retained logs/review;no runtime bridge.
- [ ] Run fullpytest,unchangedcoverage90/allsubgates,source/history/science/H6/H7audits,Ruff/format/mypy,offlinebuild/freshoutsidewheel/replaygoldens:ExpectedPASS. Verify productbytes base-identical and newtestpackage excludedfromwheel.
- [ ] Fresh independent wholebranchreview at exacthead with allfive ReviewFocus lines,scopeimages and ledger decisions. Critical/Important:REDtest,appendfix,fullfreshgates;minors explicitlydefer. Review is AI/source-only,notkernel/runtime/humanapproval.
- [ ] Publish source-only result with actual outcomes,remainingttyS1/runtime unqualification and9false. Keep branch/worktree/evidence. Publication and actualDFD01 run are separate scoped tasks.

## Self-review and handoff

All20new names and2modified names map to tasks;7packagefiles match fixedinventory.
Task1scope must be established before Task2/3 files become permitted. Task2types
are consumed unchanged byTask3;all5ReviewFocus failures have Task3tests.
Existing assetkernel support is source evidence only;do not blocksource implementation
on obtaining runtime success,or claim source tests prove runtime success.
Native inline method is preserved from prior delegation. This document is an
implementation plan,not a claim any task has run or P5exists. Current task ends
at planning;implementation follows explicit user direction without changing
the protected prior branch. Plan location external until legal successor exists.
