# Fixed guest per-slot copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture actual source-local per-slot copy records in six bounded disposable guests.

**Architecture:** New standalone source patch/driver,frozen opt-in runner,observed
wire decoder/diagnostic and byte/source audit;no old runtime/evidence changes.

**Tech Stack:** Python3.12,Linux6.12.113 C,GCC14.2,QEMU10.0.13 TCG.

**Spec:** docs/superpowers/specs/2026-10-31-guest-per-slot-copy-design.md

## Global Constraints

- Base4a04a5a38a68970624380c10113c97a752af4aa8;branchfeat/guest-per-slot-fork-copy.
- New tests/guest_fork_copy only,new source/build prefix,old tracked paths/PRs frozen.
- Six fixed modes,1vCPU512MiBTCG,no network/KVM/sharedFS/passthrough/arbitrary payload.
- Observed records never converted to SYNTHETIC_ONLY;no old oracle/PR35/PR30 bridge.
- All9permissions false,global countsNone,statusBLOCKED,no atomic/runtime qualification.
- Inline,one fresh final review,append-only own Draft,no merge.

## Review Focus

1. Post-return cookie relabeled as pre-walk birth or failed constructor as complete namespace.
2. Actual read/reference/store confused with later reread/expected fixture or synthetic class.
3. Unknown PRESENT/OFD/NULL/stale CLOEXEC collapsed or bool/zero replaces missing value.
4. Fault-injected errors/late task abort treated as natural/passive successful child inventory.
5. Buffer/local counts/stop or one CPU mistaken for global completeness/atomicity/readiness.

### Task1: Observed codec and fixed bootstrap

**Files:** new tests/guest_fork_copy/{__init__,model,image,runner}.py,guest/init.c;
tests/test_guest_fork_copy.py;tests/test_guest_fork_copy_runner.py.
**Interfaces:** parse_serial(raw:bytes)->Capture;assess(capture:Capture)->Decision;
build_image(binary:bytes,case:str)->bytes;capture(case:str)->tuple[Capture,bytes,bytes].

- [x] Write literal CPC frames/196stage fixtures,closed field/uint/context/unknown/NULL/flags/pairing/sequence/failure/loss/no-authority tests;observe missing API RED.
- [x] Implement frozen codec/observed diagnostic with no SYNTHETIC oracle dependency;run focused GREEN.
- [x] Add fixed driver/image/runner tests RED;compile driver,boot old kernel actualmissinginterfaceRED;pin assets after actual build.
- [x] Commit codec/bootstrap after tests/format/type verification;record actual baseline.

### Task2: Source hooks and actual six-case capture

**Files:** new tests/guest_fork_copy/kernel.patch,kernel.config;new owned source/build only.
**Interfaces:** kernel CPCv1 matches Task1 codec;driver expects injected ENOMEM/EAGAIN.

- [x] Fresh source exact archive,freeze selected pristine files,apply old PR38 patch only in new source prefix.
- [x] Implement task-aware copy wrapper,early allocation cookie and stable postcopy linkage,actual bitmap/read/ref/clear/store and saved scalar free,task terminal hooks.
- [x] Preallocated512copyrecords plus separate128lifecycle;inject copy2loss/oldcapacity/constructor/task/prealloc failure without added refs/effect locks.
- [x] Build pinned source/static driver,freeze inputs,run6fresh fixed guests and inspect all frames;no fabricated records or source fallback.
- [x] Run focused/fullcodec/runnerchecks and commit complete patch/runner pins.

### Task3: Evidence,regression and handoff

**Files:** new tests/guest_fork_copy/audit.py;tests/test_guest_fork_copy_audit.py;
architecture guard;docs/evidence/guest_fork_copy_{build,actual,sources}.json;
docs/guest_fork_copy_contract.md;docs/guest_fork_copy_result.md;new attributes only.
**Interfaces:** validate(pristine_root:Path|None=None,patched_root:Path|None=None,*,verify_assets:bool=False)->dict.

- [x] Byte/source/audit/adversarial tests missingAPIRED,bind actual serial/all selected assets and source/ranges;offline-only audit GREEN.
- [ ] Full pytest,pure coverage,ruff/format,mypy,old source/history/native/guest audits,build,freshvanilla/researchwheel,CRLF/exacthead verification.
- [ ] Publish bounded result/blockers,commit,one fresh independent review;one author C/I RED→GREEN pass if needed,defer minor,no re-review.
- [ ] Own stacked Draft vsPR39,attach,verify exacthead push/PR6jobs each,preserve26oldPRs/main,reportKorean/allrulings/costs/minors,nextsingle task.
- [ ] Recoverably archive only ownplan workspace;keep actual producer assets and old work intact.
