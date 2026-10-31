# Fixed guest FIRST_OBSERVED bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Observe pre-arm identities as FIRST_OBSERVED without inventing allocation history.
**Architecture:** Fresh guest source patch/origin-aware CPBv1,static fixed driver,
pure observed decoder/diagnostic and original-byte/source audit.No oldproducer edits.
**Tech Stack:** Python3.12,Linux6.12.113 C,GCC14.2,QEMU10.0.13TCG.
**Spec:** docs/superpowers/specs/2026-10-31-guest-first-observed-bootstrap-design.md

## Global Constraints

- Base2d11becc2f5b3b71558db6c944de74ddf18354b3;branchfeat/guest-first-observed-bootstrap.
- New tests/guest_bootstrap only,new source/assets;oldsrc/compatibility/CI/tests/evidence/28PRs/main frozen.
- Fixed10modes/1vCPU512MiBTCG,no network/KVM/sharedFS/device/arbitrarypayload.
- OBSERVED_UNTRUSTED/BLOCKED/history/atomic/runtimefalse,all9false/globalcountsNone.
- No actual→SYNTHETIC/PR41oracle/PR35/PR30 bridge;seed!=allocation/rootmembership.
- Inline continuous,no routine approval pauses,one fresh final review/oneCIfixpass,no merge.

## Review Focus

1. Seed identity overwrites allocation provenance or enrolls PID1 as managed root.
2. Missing NODE/unknown PRESENT identity reconstructed from raw tag,FD/path/content.
3. New child/namespace inherits seed origin or failed constructor/task becomes committed.
4. Mixed cohort/role/duplicate issuer/read-store origin pairing accepted as scientific identity proof.
5. Local buffer/oneCPU/file_lock/RCU/bootnonce/copy order mistaken for global cut,history or authority.

### Task1: Observed CPBv1 contract and fixed bootstrap driver

**Files:** new tests/guest_bootstrap/{__init__,contracts,wire,model,image,runner}.py,
guest/init.c,kernel.config;tests/test_guest_bootstrap.py,tests/test_guest_bootstrap_runner.py.
**Interfaces:** exact parse_serial/assess/build_image/capture fromspec.

- [ ] Literal ten-mode frames,raw origin/seed vs allocation/alias/distinct-open/unknown/loss/failure/rejected-command tests missingAPIRED.
- [ ] Implement frozen codec/diagnostic,no synthetic oracle or authority;focusedGREEN andpure98/95minimum.
- [ ] Fixed driver/image/runner testsRED;static compile,newdriveractualoldPR40kernelmissinginterfaceRED;freeze eventualpreparedpins.
- [ ] Fullfocusedformat/typechecks,commitTask1;baselinealltestsrecorded.

### Task2: Fresh source hooks,build and actual ten-case observations

**Files:** new tests/guest_bootstrap/kernel.patch,kernel.config;fresh source/assets only.
**Interfaces:** CPBv1 matchesTask1;sourceactualorigins/one-shot seed/issuer-root separation.

- [ ] Extract exactarchive,newpristine7files/localgit,applyoldPR40patch onlyinnewprefix.
- [ ] Origin/epoch fields and reset/issuance callbacks;seedwalkborrowedactualpointers/bitmaps,one-shot reject/abort/unknown,active arm/stop,newwire.
- [ ] Derive512capacity from472normalrecord count;fixedloss/node6/drop/128small/faultmodes,noextra refs/effectlocks.
- [ ] Buildnewkernel/staticdriver,freezeinputs,run10freshguests,inspectcompleteoriginalbytes/counts/roles/provenance;nevereditlogs.
- [ ] Focused/fulltests/sourcepatchapplycheck,commitstandalonepatch+frozenrunnerpins.

### Task3: Evidence,regression,review and publication

**Files:** new tests/guest_bootstrap/audit.py,tests/test_guest_bootstrap_audit.py,
tests/architecture/test_guest_bootstrap_boundary.py;
docs/evidence/guest_bootstrap_{build,actual,sources}.json;
docs/guest_bootstrap_contract.md,docs/guest_bootstrap_result.md,newnarrowattributes.
**Interfaces:** validate(pristine_root=None,patched_root=None,*,verify_assets=False)->dict;
Task1Capture/Decision+Task2rawfilesfeedoriginalbyte/sourceaudit,notPR41syntheticoracle.

- [ ] MissingAPIRED audit/adversaries,newfinitebuild/source/serialmanifests,prehookliteralrawgoldens;offlineGREEN,explicitselectedsource/assetsverify.
- [ ] Architectureguardsalloldpaths/pureimports,noactual→syntheticbridge;fullpytest/oldsourcehistoryaudits/native192/replay/ruff/format/mypy/build/freshwheel/CRLF/purecoverage.ExpectedallPASS.
- [ ] Commitboundedresult;freshindependentreviewexplicithead,oneauthorC/I RED→GREEN/fullrerun,deferminor,no secondreview.
- [ ] OwnstackedDraftvsdesign/inherited-ofd-provenance,attach,finalexactheadpush+PR6jobseach;28oldPRs/mainpreserved,clean;Koreanhandoffallrulings/costs/minors.
- [ ] Recoverablyarchiveonlyownplanworkspace,keepproducerassetsoutsideit;nootherplanscleanup.
