# Native E local research plan
Source reference: cyberpilot-autotune 4b77b31dd23010f2d2b394466d88b04a4a2720e2, clean main clone.
Independent harness: no product/guard edits, no runtime/admission integration.
- [x] A: isolated Linux workspace, source/guard audit, exact three dpkg checks (MATCH).
- [x] B: design below; author review of scope and authority.
- [x] C: RED protocol/lifetime/receipt tests; implement protocol.py, handles.py, supervisor.c, runner.py; GREEN.
- [x] D: fixed direct-child native lab; one conditional gated user-unit lab with all six verified limits.
- [x] E: full harness + existing regression; lint/type/build/coverage; one fresh independent review; repairs.
- [x] F: final report and local append-only commits, no push.

## Design/API
Public API: run_fixed() -> passive frozen Observation; no arbitrary command, path, PID, FD, unit or receipt argument.
Private binary E owns sealed synthetic memfd, socketpair, original clone3(CLONE_PIDFD) child handle from creation.
Worker is compiled fixed code, cannot accept arbitrary payload/command. Control uses bounded length framing,
version/cohort/generation/nonce/sequence/stage and exact EOF. Reject ancillary descriptors, close received FDs.
E waits for controller RUN only after creation acknowledgement; EOF/cancellation ends its own child through pidfd.
Python controller never signals numeric PID. Uncertain close/wait yields UNKNOWN, no retry or receipt recovery.
Owned handles are factory-only, nonserializable; identity loss refuses to close reused foreign directory/socket FD.
Creation-time OFD anchors + same-process kcmp verified; hostile FD-table races remain outside scope.
No runtime grant from booleans, hashes or serialized observations.
External systemd lab unit is systemd-created and NOT internal D; E direct child is NOT a cgroup D.
Internal D, aggregate descendant custody/admission fence, readonly mount, namespaces, async/external-writer drain
are NOT IMPLEMENTED. Only bounded fixed synthetic worker may run.
All 14 project flags remain false; registration UNBOUND; old 16 qualification evidences UNAVAILABLE.

## Tests/completion
tests/test_protocol.py: malformed contexts/order, bounds/EOF/duplicates/SCM_RIGHTS.
tests/test_handles.py: FD reuse/loss, nonserialization, close uncertainty no retry.
tests/test_runner.py: real native fixed child + test-only injected spawn/cancel/wait/failures, receipt impotence.
tests/test_lab.py: limits/gating/one factory unit; native lab truth separate from mocks.
Commands: venv python -m pytest --cov=native_e_lab --cov-branch; ruff; mypy; build.
Native build: cc -std=c11 -O2 -Wall -Wextra -Werror.
Existing product checks run unchanged in separate clone using dedicated venv; report blockers honestly.

## Successor: internal D (2026-11-05)
Spec: INTERNAL_D_DESIGN.md. Implementation owner executes inline, TDD.
- [x] Isolated branch/worktree at9545d54; preserve old report/evidence and product.
- [x] tests/test_domain.py: strict context/report, unsupported parent, unchanged false flags/API.
- [x] domain_supervisor.c: new D lifetime, born-in-D pidfd, E outside, one-shot kill/drain/remove.
- [x] domain.py/domain_gate.py: closed wire runner + kernel/delegation gate, no arbitrary resource API.
- [x] lab.py/build_native.py/package data: fixed new entry, preserved old path, compile/syntax.
- [x] Native policy/fault fixtures: cancellation, wrong scope/membership, uncertain write/wait, no wrong unlink.
- [x] Full regression/static/build/coverage, conditional bounded real unit, one independent review and fixes.
- [x] New LOCAL_INTERNAL_D_FINAL_REPORT.md/evidence, local commits/bundle; no push.
Completion: actual PASS only if D created, worker born inside, E outside, active worker stopped by Dfd,
original wait, populated0, original D removed and external unit collected. Otherwise BLOCKED/UNKNOWN accurately.

## Admission fence / original custody design successor (design only)
Base694604e, new branch research/native-e-admission-design in existing isolated worktree.
No src/tests/build/dependencies/OS-lab modifications. Previous reports/evidence immutable.
- [x] Read prior design, review, progress, final report and source mutation sites.
- [x] Freeze31 source/test/config/evidence files; verify original research/product branches.
- [x] Consult primary cgroup-v2/unlinkat/chmod/open/user-namespace documentation.
- [x] Draft ADR: threat model, exact gaps, rejected options, proposed exclusive host authority.
- [x] Specify original live parent/D/child chain and terminal one-shot lifecycle obligations.
- [x] Define adversarial acceptance cases and future implementation plan, no execution claims.
- [x] One fresh independent design review, address findings, verify document consistency/preservation.
- [x] New report/evidence and local commit/bundle; no push or new runtime qualification.
Completion means design handoff only. Current strong-fence OS execution remains blocked absent enforcement proof.

## Dedicated-host-principal provisioning / rollback plan (2026-11-05)
Base aadf62ff3d826ed432b412f18143d5fa1144d4ba; new research/native-e-provisioning-plan branch.
Plan-only: no accounts, services, policy, code, test, dependency or cgroup changes.
- [x] Read frozen ADR-F1/report and confirm CLEAN/base/original refs.
- [x] Specify minimal identities, capability phases, exact owned paths and systemd255 proposal.
- [x] Identify cross-UID source incompatibilities and missing artifacts; no apply-ready claim.
- [x] Specify gated administrator-only transaction, impact, ownership evidence, rollback/quarantine.
- [x] Fresh independent review and fixes; document consistency and protected-source checks.
- [x] Korean report/evidence, local append-only commit and verified delivery bundle; no push.
Completion is a reviewable change proposal only; no permission change or runtime qualification.

## Fixed credential-seal native component implementation (2026-11-05)
Goal: unbound C bootstrap component + offline BPF policy and syscall-boundary fixtures, no real credential changes.
Architecture: new research/credential_seal/seal.c + seal.h; no package/provider/lab integration.
Spec: NATIVE_E_PROVISIONING_PLAN.md sections3/6/Q02/Q03/Q09. Inline execution, TDD, final independent review.
Global constraints: x86_64 Linux research only; no UID0 targets; IDs are data not authority; no command/path/PID/FD API.
No actual setresuid/setgroups/capset/seccomp/prctl security changes in test processes: linker syscall wrapper has no forwarding.
Old source/tests/config/evidence protected; PLAN/PROGRESS append-only. UNBOUND/16UNAVAILABLE/14false.
Review focus: high32 syscall args/x32 ABI; partial failed syscall no retry; missing/duplicate status; retained saved/fs IDs;
repeat/reentrant attempt, parent-death readback and no parent custody claim, no payload execution implied by a seal result.
- [x] Task1 tests/test_credential_seal.py + tests/native/credential_seal_driver.c: RED against missing C component,
  real generated BPF evaluated by independent interpreter; native transaction fixture must not forward security syscalls.
- [x] Task2 research/credential_seal/seal.h and seal.c: ce_build_id_filter(ids,out,capacity),
  ce_seal_worker(attempt,ids), ce_seal_owner(attempt,ids); no main/CLI, raw syscalls never exercised live this stage.
  Validate profile/preflight before mutation, consume one-shot before attempt, exact seal/readback, unknown terminal.
- [x] Task3 full research pytest/coverage>=90, focused C coverage if practical, strict compiler, ruff/format/mypy,
  unchanged product regression, fresh independent whole-change review and RED→GREEN fixes.
- [x] Task4 Korean report/evidence/roadmap; local commit/bundle; no push, no OS provision or runtime qualification.
No plan approval menu: user explicitly delegated implementation choices and authorized continuous execution.
Existing isolated linked worktree reused; previous branches preserved. Prior reports are not rewritten.

## Original private parent handoff: unprivileged native fixture (2026-11-05)
Goal: fixed native F creates NEW private regular-directory P and socketpair, owns E clone3 pidfd from birth,
transfers one P FD after HELLO/READY, confirms ACK/COMMIT/EOF, requires original E closure/exit, then closes own refs.
Architecture: research/parent_handoff/handoff.c fixed no-arg native fixture; no arbitrary path/PID/FD/command/unit API.
Tests tests/test_parent_handoff.py + tests/native/parent_handoff_driver.c compile/run test-only fault wrappers.
Reuse protocol Context 50-byte field layout concept; new NPG1 namespace because old worker reader must reject all FDs.
No change to existing runtime/protocol/handles/credential component. General fixture is NOT a cgroup grant/provider/F1.
Global constraints: LP64 x86_64; one new fixed child, original pidfd wait/stop only; no OS service/credential/cgroup work.
Absolute bounded protocol deadline; exact one FD with CLOEXEC only in GRANT; no RUN or payload stage.
Review focus: ancillary delivered with any prefix/body chunk; control truncation; partial send ambiguity; extra bytes/EOF;
FD-number reuse must not close foreign resources; cancellation/uncertain wait/close must not cause lookup/retry/deletion.
- [x] Task1: write real native boundary tests first; RED; fixed native factory/peer and protocol implementation GREEN.
- [x] Task2: fault cases for bad contexts/order/framing/FD count/type/truncation/replay/EOF and terminal lifecycle.
- [x] Task3: full research tests/coverage>=90, product regression existing numpy venv, compiler/UBSan/gcov/lint/type/build;
  fresh independent review and one RED→GREEN fix pass. Mock/native/OS qualification remain distinct.
- [x] Task4: Korean report/evidence/local commit/bundle, old tracked hashes unchanged, no push; remaining entry-proof work explicit.
Inline work and plan choices already delegated; no approval menu. Evidence and original branches/worktree retained.

## Fixed W entry + component integration (2026-11-05)
Base42b7711; isolated research/native-e-worker-entry. Historical components/reports unchanged.
Implementer choice: real same-UID sealed-memfd static ELF exec with original clone3 pidfd,
SCM_CREDENTIALS sender + fixed worker self exec/FD/parent witness. This is trusted-code fixture evidence,
NOT protected code origin, cross-UID credential proof, systemd binding or F1 admission fence.
Credential component runs through no-forward test-only syscall shim. Unwrapped current user must reject
before W birth; actual credential/security changes are forbidden. No arbitrary payload/path/FD/PID API.
Original F/P handoff helpers reused by include; NPG1 remains unchanged. New NWE1 bounded stream protocol.
Worker entry gets only devnull0..2 + private socket3; self-probe FDs close, no inherited P/control handle.
Executable copied from fixed adjacent static ELF into new write/grow/shrink/seal-sealed memfd.
E establishes filter phase before birth, W-seal and E-owner-seal after birth; real phase unavailable.
- [x] RED tests/test_worker_entry.py and test-only native shim/driver.
- [x] research/worker_entry/entry_credential.c/h, integration.c, fixed_worker.c.
- [x] malformed/context/FD/exec/lifetime/uncertainty regression; no retry/recover.
- [x] full research/product regression, strict compiler/UBSan, lint/type/build/coverage.
- [x] fresh independent whole-change review, TDD fixes and verification.
- [x] Korean report/evidence/local append-only commit/bundle; no push or provider qualification.
All14false, providerUNBOUND, qualification16UNAVAILABLE. Existing single PLAN/PROGRESS append-only.

Completion: worker-entry tasks1-6 above are COMPLETE_WITH_LIMITATIONS.
Final new60PASS, research329PASS, product2786PASS, unique3115PASS/0FAIL/0SKIP.
UBSan60PASS excludes freestanding raw worker instrumentation; native C coverageUNAVAILABLE.
Static/type/old Python package build PASS. Independent Important1/Minor1 addressed by author TDD;
production repair reread, final test-only repair not independently rereviewed. No final C0/I0 certification.
Protected factory/cross-UID/cgroup integration and qualification remain unavailable.

## Current F/E/W administrator review bundle (2026-11-05)
Base8c0058e; isolated research/native-e-admin-review. Actual OS apply is NOT authorized.
Use architecture ADR to update old provisioning proposal against new source; decisions owned by implementer.
- [x] Audit current source gaps and systemd255 primary FD-passing API.
- [x] Proposed fixed account/config/artifact/transient-unit footprint, source pins and rollback/quarantine.
- [x] Offline bundle content checker, RED mutation tests then minimal implementation; no install/start API.
- [x] Focused/full research checks and static checks appropriate to new checker; old product code preserved.
- [x] Fresh independent source/design review, address findings and final consistency verification.
- [x] Korean final report/evidence, local append-only commit/bundle; no push.
Completion means REVIEW_READY/APPLY_BLOCKED. Missing host backend/build/UID/loader/F1 evidence remains explicit.
No new account/unit/service/setting/cgroup/credential work, no fixed worker execution outside existing tests.
Retain UNBOUND,16UNAVAILABLE,14false. Keep old sources/reports/evidence and same append-only ledgers.

Completion: administrator-review tasks1-6 COMPLETE_REVIEW_ONLY/APPLY_BLOCKED.
New73purePASS/full402researchPASS, checker94.96%, existingPython91.74%; thresholds90 unchanged.
Prior product2786PASS retained as NOT_RERUN and not added to fresh total.
Fresh independent review Important1(parser whitespace) and Minor1(global sysusers backup/cache effects)
reproduced/documented and fixed by author TDD. No post-fix independent C0/I0 certification.
18source/context pins,68prior files preserved. No accounts/units/privileged source/OS apply/backend execution.

## Native private sd-bus factory/manager fixture (2026-11-05)
Base4595279; isolated research/native-e-factory-manager. Implement A01-A05 as closed native fixture.
Native F creates private bus socketpair and cloned synthetic M (original M pidfd);
M owns E birth/pidfd/wait; F owns fresh E-control socketpair but NEVER adopts E PID/FD as process authority.
Existing libsystemd.so.0, minimal public ABI declarations; no dev headers/package install.
Real sd-bus authentication/message/UNIX-FD marshalling via private inherited sockets ONLY.
Fake M accepts fixed StartTransientUnit-shaped request but creates only compiled tiny E probe,
no system manager, service/unit/cgroup/credential/W payload. Root rejected, no open_system/address/listen API.
Original P/F1 grant absent => E never starts W. Request properties are data, not applied privileges/limits.
Real protected system-bus/UID/loader/born-D backend remains unimplemented; UNBOUND/16UNAVAILABLE/14false.
- [x] RED tests/native factory-manager fixtures and Python regression.
- [x] research/factory_manager public ABI shim, fixed sd-bus request/lifecycle implementation.
- [x] real manager-retained endpoint vs explicit shutdown/EOF, cancellation/identity/duplicate/extraFD/error tests.
- [x] full research/static/native compiler/UBSan/coverage as appropriate; no product code changes.
- [x] fresh independent whole-change review; TDD repairs, no qualification claims.
- [x] Korean report/evidence/local commit/bundle, old files/ledgers preserved; no push.
No generic callback/command/unit/path/PID/FD/receipt execution API. Test fault selector is test-only.
Single bounded M/E pair, original M/E waits in respective parents, UNKNOWN never retried/recovered.

Completion: factory-manager tasks1-6 COMPLETE_NATIVE_PRIVATE_PROTOCOL_WITH_LIMITATIONS.
46newPASS +402preserved =448freshresearchPASS/0FAIL/0SKIP. UBSan46/GCOV46 are repeats, not added.
FactoryC lines97.12/outcomes66.29; requestC100/51; SDK not instrumented. Python91.74 threshold90 unchanged.
Independent Important1 partial constructor FD ownership leak RED2→GREEN; explicit bus_owns_fd and pre-transfer
closure, original waits consumed once. Minor generation test gap covered. No post-fix independent C0/I0.
No actual system bus/PID1/unit/credentials/P/D/W. Library close syscall result remains UNAVAILABLE even normal.
Old80protected hashes/old branches preserved, ledgers append-only. Report/evidence/local delivery follow.

## M-owned E / P handoff / fixed worker integration (2026-11-05)
Base4643a9e; branch research/native-e-cohort-integration.
Uses writing-plans/executing-plans/TDD/verification; user selected autonomous inline execution.
Spec: prior FACTORY_MANAGER_DESIGN.md + original user local-native-E constraints.

Goal: connect real private sd-bus FD delivery to NPG1 original-P grant and NWE1 sealed worker entry.
Architecture: new coordinator reuses old static bus/framing/lifetime helpers; new E TU reuses entry_peer/run_worker.
Synthetic M owns E pidfd; F owns M pidfd/P; E owns W pidfd/sealed image. No F adoption of E/W.
Tech: existing GCC/libsystemd runtime, Python pytest; no new dependency/install.
Existing92 non-ledger tracked files frozen; PLAN/PROGRESS append-only; no old evidence changes.
No actual systemd/system bus, unit, cgroup, credentials, Docker, provider or vehicle.
No API imports caller paths/PIDs/FD numbers/commands/receipts. Default constructor stays ENOSYS.

Interfaces:
- research/cohort_integration/cohort.c: ci_run_fixed(void), fixed orchestration using old factory static helpers.
- research/cohort_integration/peer.c: ci_peer_fixed(void), fixed fd0 only, original existing entry_peer.
- tests/native/cohort_manager.c: fresh private M; reuse old typed parser/events. Creates fixed E only.
- tests/native/cohort_driver.c: test-only boundary failures/counts. No runtime fault/environment API.
- tests/test_cohort_integration.py: real sameUID IPC/exec fixtures; credential TU never forwards writes.
No product API/provider export. M's wire limits remain DATA ONLY.

Review focus: inherited F/P/bus handles; cancellation after E/W birth; stale/late signal after W;
P lifetime until original M confirms E exit; unavailable wait/close/library-close must not become success.

Task1 — RED contract and fixed coordinator:
- [ ] Test normal/default-unbound, M→E→W topology and original P/FD/exec facts; run RED.
- [ ] Implement only new files, strict GCC. Default ENOSYS must create no P/M/E/W.
- [ ] New P before M creation; M closes inherited F handles before reading message; E closes inherited bus.
Task2 — failure/lifetime tests:
- [ ] wrong context/grant/EOF/FD, missing worker/seal failure, late job, cancel E/W,
      wait/close uncertainty, P name replacement, second attempt and foreign descriptor preservation.
- [ ] Tests must observe actual negative outcome/no retry, not just check string constants.
- [ ] Cleanup bounded: M waits E gracefully before optional original-pidfd kill; F gives M larger bound.
      Any forced/unknown termination cannot assert descendants drained. SDK close remains UNAVAILABLE.
Task3 — final verification:
- [ ] Entire research regression + fresh UBSan focused suite, C branch/line instrumentation if feasible.
- [ ] Existing Python lint/format/mypy; preserve thresholds; product unchanged NOT_RERUN.
- [ ] Fresh independent whole-change review once; important findings reproduced RED→GREEN + full suite.
Task4 — delivery:
- [ ] LOCAL_COHORT_INTEGRATION_REPORT.md, review/evidence with separate actual/simulated/unknown.
- [ ] local append-only commit, source bundle/limited logs/new Windows diagnostic folder; CLEAN/no push.
- [ ] all14false/providerUNBOUND/16UNAVAILABLE preserved. One exact remaining implementation gap.

Pre-flight: coordinator→peer contract is NPG1 original endpoint; peer→W is unchanged NWE1.
Manager only observes E exit; F only observes manager summary/exit. Passive reports never grant authority.
Ruling: retain old sources and implement new sequencing coordinator using included static helpers,
rather than alter historical fixtures — enables exact baseline regression, at cost of some coordinator duplication.
Ruling: no workspace cleanup; prior user explicitly requires evidence and residues preserved.

### Cohort final completion
- [x] Tasks1–2 native integration and failure/audit tests (45 unique).
- [x] Task3 repaired full493PASS/0FAIL/0SKIP; UBSan45/GCOV45, static exit0; Important clock RED→GREEN.
- [x] Task4 report/review/evidence prepared; local commit/delivery verification below/external FINAL_DELIVERY.
Ruling: preserve failed fixture residue and records, no workspace cleanup or remote publication.

## Internal-D / manager-owned cohort successor (2026-11-05)
Base d70b425; research/native-e-domain-cohort. Autonomous inline; writing-plans/TDD/verification skills.
Spec: COHORT_INTEGRATION_DESIGN.md and original local-native-E user scope.
Goal: connect E-held original P, E-created D, born-in-D request, fixed W entry, one-shot stop/reclaim.
All101 old non-ledger files immutable; ledgers append-only; no actual cgroup/unit/credential/manager work.

Architecture:
- research/domain_cohort/policy.c + internal.h: private native owned-D state/handles, exact lifetime.
  Reuse old domain_supervisor guards/wait via build-only attested entry rename; never call old launcher.
- research/domain_cohort/peer.c: reuse old worker trampoline/image/framing; fixed run_domain_worker,
  original-P NPG1 successor; no public caller path/PID/FD/command interface.
- research/domain_cohort/worker.c: include old static W proof then bounded stay-alive for domain stop.
- tests/native/domain_cohort_driver.c: include attested old coordinator/manager fixture driver via
  build-only main/wrapper rename, add simulated cgroup FS/CLONE_INTO_CGROUP/kill boundary.
- tests/test_domain_cohort.py: strict builds, real native M/E/W + regular-files controller simulation.
Default F remains ENOSYS; unwrapped regular-P path rejects before D creation.
Request CLONE_INTO_CGROUP in component; fixture strips only that bit before actual fixed child birth.
No namespace/cgroup containment/credential qualification is inferred from this simulation.
Regular-file kill simulator signals only the original E-owned W pidfd, never reopens from numeric PID.

Review focus:
1. wrong D/P FD or name must not touch foreign resource.
2. cancellation after birth retains original pidfd; no retry after unknown write/wait/close.
3. E is not D member in policy; no descendant scope; fail closed on missing/extra metadata.
4. late manager failures preserve W birth and cannot remove P prematurely.
5. forged passive results cannot become public cleanup/adoption authority.

Task1 (native component):
- [ ] Write failing normal/default/reject tests; compile failure RED against absent module.
- [ ] Implement private D phase machine, borrowed-live-P duplication, random exclusive D,
      original-D guard, exact member/zero descendants, one kill write + exact SIGKILL wait,
      strict empty events and removal. New D only; no existing cgroup writes.
- [ ] New E uses CLONE_PIDFD|CLONE_INTO_CGROUP in birth request and fixed sealed W.
Task2 (native fixture boundaries):
- [ ] Real ordinary P/D files; simulated cgroup metadata; no real controller/namespace calls.
- [ ] Distinct malformed membership/descendants/events, source/name/OFD replacement,
      partial/unknown kill/close/wait, cancellation, natural exit42 vs SIGKILL, legacy late events.
- [ ] Live test-only shared audit: create/birth/kill/wait/remove each once; unknown no retry.
Task3:
- [ ] Fresh whole research suite, focused UBSan/GCOV with exclusions, compiler/lint/type.
- [ ] One independent whole-change source review; important issues RED→GREEN, reverify.
Task4:
- [ ] Korean report/review/evidence; local commit/bundle/new Windows diagnostic delivery; no push.
- [ ] UNBOUND,16UNAVAILABLE,14false. Actual HOST/runtime readiness NO.

Ruling: old launcher finds P by pathname and uses old entry protocol, so it will not be called.
Only its guards/owned-child wait are composed from exact hash-pinned source, avoiding duplicate
policy implementation; generated reference files are build-only, not original-source rewrites.
Ruling: preserve failed fixtures/residue/logs; no scratch cleanup or old-D reattachment.

### Domain cohort completion
- [x] Tasks1–2 fixed backend/native31cases, two review defects RED→GREEN.
- [x] Task3 full524PASS/0FAIL/0SKIP, UBSan31/GCOV31, unchanged thresholds/static checks PASS.
- [x] Task4 report/review/evidence prepared; local commit/delivery verification recorded externally.
All101 old files and branch refs preserved. UNBOUND/16UNAVAILABLE/14false. No actual cgroup/manager/credential changes.

## Real cgroup2 lab adapter and continued validation (2026-11-05)
Base ed8b68a; research/native-e-real-cgroup. User requests continuous authorized follow-through.
Preserve111 non-ledger tracked files; PLAN/PROGRESS append-only, no push/PR/system install/global changes.
Spec: DOMAIN_COHORT_DESIGN.md + original local-native-E lab bounds/scope.

Architecture:
- research/real_cgroup/factory.c: fixed native F successor; reuse old bus/NPG1 helpers.
  Current fresh-unit P is opened once before M birth; F releases refs but NEVER unlinks manager-created P.
- scope.c: exact old membership/factory-service/open-parent guards via attested build reference.
- normal.c: fixed normal synthetic M + no-forward credential boundary; NO transport/FS/clone/kill simulation.
- build.py: fixed source-only build kit, no caller paths/commands, private directory, source+asset hashes.
- gate.py: GO token/factory unit/kernel limits/NNP/source checks; exec original native F FD in same unit MainPID.
- lab.py: no-arg fixed positive lab; bounded manager properties + original job; one-shot unit identity.
- tests/test_real_cgroup.py: pure controller/gate/builder contract tests + direct native scope rejection.

Preflight already read:
UID1000, systemd255, existing user manager active/Delegate=yes/cpu memory pids.
Existing user root -.slice active; its ControlGroup equals existing user-manager delegated root.
Root subtree already cpu memory pids; app.slice lacks enabled cpu.
Ruling: fixed Slice=-.slice avoids enabling cpu on existing app.slice.
This is user-manager namespace root, NOT host root. Capture manager/app controller strings and manager starttime before/after.

Review focus:
- P is external-manager-created, not claimed E-owned D or original F custody.
- limits/source must pass BEFORE native worker creation; no control-by-unit-name cleanup.
- exec same PID from original opened FD, no extra Python-created child ownership gap.
- original native M/E/W + exactDkill/wait/reclaim, false/unknown output never promoted.
- callback/receipt/path/unit import not exposed; no OS lab under test collection.

Task1:
- [ ] RED tests import/API/gates/build/default-scope.
- [ ] fixed native adapter + kit/gate/controller; tests GREEN; no real unit yet.
Task2:
- [ ] fresh source review once; defects RED→GREEN, relevant full regressions/compiler/lint/type.
- [ ] source-bound local append-only runtime commit before actual OS lab.
Task3 conditional bounded OS:
- [ ] fresh active local user bus/root slice/delegation, existing controllers unchanged.
- [ ] exactly one positive fresh unit with RuntimeMaxSec30, TimeoutStopSec5,MemoryMax128M,
      MemorySwapMax0,TasksMax8,CPUQuota25%,Delegateyes,NoNewPrivilegesyes,Slice=-.slice.
- [ ] loaded values and actual cgroup files checked before GO; current kit source pinned.
- [ ] native real CLONE_INTO_CGROUP/kernel cgroup.kill; no UID/cap/security syscall forwarding.
- [ ] original job completion, reportDexit/reclaim; unit auto collect only, no existing service actions.
Task4 continued work without approval roundtrip:
- [ ] if positive PASS, new serial source-drift-negative unit (fresh own tampered kit copy),
      gate must reject before F/W/D; otherwise STOP real units and continue pure failure characterization.
- [ ] preserve before/after controller/manager identity, code/source refs, flags; final regressions if fixes.
- [ ] Korean report/review/evidence/local commit/bundle/new diagnostic delivery; no remote publication.
All14false, UNBOUND,16UNAVAILABLE remain. Actual unit lab != provider/kernel custody qualification.
No namespace/mount/admin factory/account installation or old residue cleanup.

### Real cgroup / continuous follow-through completed 2026-11-06
- [x] Tasks1–2 runtime19101cd,586researchPASS/new62,review3Important+1minor RED→GREEN.
- [x] Task3 new bounded real kernel positive PASS, original D stop/SIGKILL/reclaim, unit collected.
- [x] Task4 NEW serial kit-drift-negative PASS (expected gate ASSET_DRIFT before native worker); unit collected.
- [x] Existing configs stable and per-attempt manager stable; inter-WSL manager identity epoch changed, causeUNKNOWN preserved.
- [x] Source111old files/31runtimepins stable; source/report/evidence/local handoff only.
All14false/UNBOUND/16UNAVAILABLE. No existing service restart/global setting/namespace/vehicle/application.

## Native persistent factory intent (2026-11-06)
Base d24cb17; branch research/native-e-factory-intent. Spec FACTORY_INTENT_DESIGN.md.
Goal: native one-shot O_EXCL/fsync admission precondition before existing fixed private manager.
Architecture: research/factory_intent/intent.c internal live-scope ownership; factory.c noarg coordinator;
internal.h hidden types; unbound.c default ENOSYS. Test-only scope/fault driver and existing synthetic M.
Tech: existing GCC/libsystemd/pytest, no new dependency. old123 nonledger files frozen.
User delegated design/inline execution; no approval menu. No privileged apply/new OS unit/cgroup.
Ruling: implement persistent duplicate suppression before manager work, not another OS lab —
full protected F1/crossUID remains blocked; cost: this component alone cannot qualify HOST.
Review Focus: parallel claimant; inode-equivalent FD reuse; partial constructor; create/fsync ambiguity;
intent content or receipt cannot grant/recover authority.
- [ ] Task1 RED tests/test_factory_intent.py + tests/native/factory_intent_driver.c, native default/noarg contracts.
- [ ] Task2 research/factory_intent/internal.h,intent.c,factory.c,unbound.c; narrow native implementation GREEN.
- [ ] Task3 real private-FS/native IPC cases incl concurrent/restart/crash/partial/unknown/tamper/foreign-FD.
- [ ] Task4 full research regression, strict compiler/UBSan/new C coverage, Ruff/format/mypy thresholds unchanged.
- [ ] Task5 one fresh whole-change source review; reproduce important findings RED→GREEN + full verification.
- [ ] Task6 Korean report/evidence, local append-only commit/bundle/new Windows delivery, CLEAN/no push.
Ruling: preserve prior evidence and fixture residue, do not delete workspace; apply old user instruction.

### Factory intent completion
- [x] Tasks1–3 native noarg/default-unbound, O_EXCL/fsync before private M,61 unique failure/lifetime cases.
- [x] Task4 current full646 + final focused61, overlap60 =>647uniquePASS/0FAIL/0SKIP; UBSan61/GCOV61 repeats.
- [x] Task5 independent Important1 RED2→GREEN; author null RED6 and bounded-pause RED1, final native/static checks pass.
- [x] Task6 report/evidence/local append-only commit + private source bundle/delivery; no push.
Cleanup remains partial/UNAVAILABLE; no protected F1/crossUID/system bus/provider qualification.
