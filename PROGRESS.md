# Progress
A COMPLETE: new WSL2 EUID1000/capability-free workspace; clone clean main at 4b77b31d.
Exact three local systemd package checksum matches; no package authenticity/qualification inference.
Private HF reference unavailable from prior normal auth check; not read, not reconstructed.
B COMPLETE: separate harness chosen because product frozen successor path inventories cannot admit new native code
without altering guards; existing fixed cloud executor audited, not copied as portable native implementation.
Next: venv setup, RED tests, minimal native implementation.

C IN PROGRESS: 41 tests GREEN, including real clone3 fixed child and malformed protocol. RED lifetime tests exposed skipped FD close and primary cancellation masking; repaired and rechecked. Internal D remains absent.
Venv ensurepip absent; venv --without-pip + existing pure Python bundled pip used only in new venv. No system install.

D: one factory user-unit attempt executed after 69 GREEN tests. See logs/user-unit-lab.txt. No existing unit lifecycle changes; original systemd-run job only, external unit is not D.

E IN PROGRESS: product full regression 2786/0/0, coverage98.50%; safety100/residual97.85/replay98.48.
Ruff/format/mypy/replay PASS. Default python -m build blocked by missing ensurepip;
dedicated venv build dependencies + --no-isolation succeeds without global changes.
New suite115 GREEN; C fault linker fixtures are test-only, no production fault controls.
Late RED repairs: failed factory cleanup, sticky close uncertainty, unknown post-release execution,
supervisor vs worker exit semantics. All restored GREEN.
Final independent review + final revision bounded lab revalidation + final handoff remain.

E REVIEW: independent whole-change review200b4f9 returned3 P2. All3 reproduced RED; repairs underway, parent-only post-review verification. Directory same-OFD ownership limit retained, no general guarantee.

E POST-REVIEW:3P2 RED→GREEN. Parent extended original-OFD repair after kcmp self-probe succeeded:
retained factory duplication + KCMP_FILE, UNKNOWN on unavailable; no metadata fallback.
Tests now include same-directory/different-OFD reopen, original anchor equality and denied query.
This extension has author self-review only. Internal D and adversarial FD-table/namespace custody absent.

E CODE COMPLETE:123 unique new tests GREEN, mypy7files, ruff/format PASS. kcmp original OFD repair includes denied-query no-fallback and same-directory independent reopen. Independent review remains bound200b4f9; later code author-reviewed only.
Next: immutable code commit, final-source bounded unit revalidation, final report/local handoff commit.

F COMPLETE: code b962485; final revision-bound user-unit succeeded, loaded/kernel limits exact,
source/test hashes stable, post LoadState=not-found/ActiveState=inactive. Two sequential real unit
experiments total, never more than one active. New123 + unchanged product2786 (final rerun) PASS.
Python92.68%, product98.50%, C targeted lines82.35%; static/build/new-wheel smoke PASS.
Directory fixtures69dirs/14files/112bytes retained intentionally after ownership-loss tests.
Final report and evidence completed. Local report-only handoff commit pending; no push/PR/upload.
Remaining next research item: internal D custody boundary. All flags false, UNBOUND,16UNAVAILABLE.

## Internal-D successor
Started from9545d54 in research/native-e-internal-d worktree, original harness/product preserved.
Design chooses trusted single-owner lab (mkdir/open atomic custody gap remains unqualified).
Next: RED domain contract/API tests and fixed native implementation.

Domain code compiled Werror; full151 tests PASS (baseline123+28 unique). Native helper tests use regular fixtures; no real-D claim yet. Next: committed-source bounded delegated lab.

Independent review3f72de3:2P2+1P3. Native test fixtures reproduced all3 (3RED/1positive).
Repaired terminal uncertainty, readdir cleanEOF, and exact waitid SIGKILL evidence.
Python coverage before added gate cases was89.99 (below90, not claimedPASS despite pytest exit0);
added meaningful scope/gate tests without lowering threshold.
Next: full GREEN/static, source-bound final real-D lab, final report/bundle.

Review fixes + exec-image refinement GREEN:169unique tests, Python91.74% at threshold90;
mypy9modules, ruff/format, native3fixedELFs Werror PASS. Normal exit137 rejected separately from SIGKILL.
Existing product2786PASS/98.50% fresh, unchanged. Next: final bound realD run and package/handoff.

Author safety pass: D's direct members alone do not exclude an unexpected nested cgroup.
Added original-fd cgroup.stat snapshot requiring nr_descendants=0/nr_dying_descendants=0
before admission and stop; unknown/nonzero retains D and stops only original pidfd.
Not an admission fence against changes AFTER the snapshot.2new native fixture cases RED→GREEN.

Latest new-unit experiment b2f2d50 BLOCKED_GATE_OR_JOB; native cleanupUNKNOWN/exit21, no domain success claims.
Source pins stable; outer unit not-found/inactive. No failed-D reattachment or cleanup retry.
New cgroup.stat descendant guard suspected bounded read/schema issue; read-only current-self schema diagnosis only.
Earlier3f72/5d7 PASS are kept bound to those old revisions; do not promote them to b2f2.

Read-only schema diagnosis: current cgroup.stat380bytes, subsystem rows interleaved between required fields.
Repaired bounded4KiB by-key parser; exact required counters zero, missing/duplicate/negative/oversize reject.
Kernel-shape fixture RED→GREEN. Oversize fixture corrected to actually exceed4096 (not threshold relaxation).
Full176PASS/0FAIL/0SKIP, coverage91.74. Failed b2f2 unit result remains UNKNOWN, never promoted.
Next fresh cohort only after repaired source commit; no old-D cleanup retry.

Internal-D cycle COMPLETE_WITH_LIMITATIONS: final runtime385b0e1 fresh-cohort PASS, all8facts true,
exact SIGKILL; source pins stable; unitnotfound. Earlier b2f2 UNKNOWN preserved with no reattach/retry.
178research(123preserved+55new)+2786product PASS, Python91.74/98.50; static/build/wheel PASS.
4serial actual units:3PASS/1BLOCKED, never concurrent. No qualification/flag change.
Runtime code unchanged after final unit;2test-only write-fault cases added afterward.
Final report/evidence prepared; local handoff commit/bundle and final CLEAN verification remain.
Next research task: admission fence/original custody protocol; full provider remains UNBOUND.

## Admission-fence design successor
Fresh694604e/CLEAN confirmed; switched new design-only branch, original branch ref preserved.
Baseline31file manifest saved; src/tests/pyproject/old reports locked for this scope.
Source gaps: mkdir/open245-249; checked membership279-280 vs kill285-288; name check296 vs unlink299.
Current trusted single-owner PASS retained. Coequal writer authority is a threat assumption, not an observed attacker.
Architecture choice proposed: protected exclusive-parent/host-principal boundary before E creates D.
No new prototype/unit/build/test or system setting work authorized by this design step.

ADR-F1 design complete: OS-exclusive authority prerequisite, original live handoff, quarantine/lifecycle,
T01-T15 future acceptance. No enforcement implementation or actual adversarial run claimed.
Independent ADR/base-source review NO_MATERIAL_FINDINGS; ADR SHA5d8fd6c4 unchanged afterward.
Source/test/config/old evidence31/31 preserved. New docs only;14false/UNBOUND/16UNAVAILABLE retained.
Documentation checks and local delivery finalization follow; no tests rerun for design-only changes.

Design handoff: JSON/links/T01-T15/14flags/append-only checks PASS; runtime tests NOT_RUN_DESIGN_ONLY.
Delivery guard failed before commit due to leading-whitespace strip in porcelain parsing; reproduced/fixed,
no source/index mutation before that failure. Corrected guard preserves all six expected documentation paths.
Only six documentation/evidence files changed. Local commit/bundle state is in FINAL_DELIVERY.json;
command results in final-verification.json in the new diagnostic delivery folder. No remote push.
Next: dedicated-host-principal F/E/W provisioning/rollback plan only, no automatic application.
Commit identity missing: first commit rejected before creation (exit128). Use command-local Codex Research identity; no git config file/global mutation.

## Minimal provisioning-plan successor
Fresh aadf62f/CLEAN; isolated new branch research/native-e-provisioning-plan; previous design branch preserved.
Plan only. Existing tracked files except append-only PLAN/PROGRESS are SHA256-frozen.
Primary systemd255 source/manual interface review; no new host-global setting or account changes.
Key issue: E-created direct child requires credential handoff; cross-UID proc checks and pidfd signal permissions
must be explicitly redesigned, not silently solved by creating service accounts or granting broad ptrace/kill caps.

Provisioning proposal drafted with two new static E/W principals, bootstrap-only SETUID/GID and explicit high-privilege risk;
F factory/original private IPC+unit integration and cross-UID entry proof remain blockers, not assumed implemented.
Source audit found fd0/.supervisor, root-owned worker/name, proc/FD, pidfd signal and PDEATHSIG incompatibilities.
Independent review precision fixes added to sections5-6/Q09-Q10. Final plan SHA27cf1e2d reviewed PASS_DOCUMENT_CONSISTENCY_ONLY.
No runtime code/tests/OS account/unit/service/cgroup mutations. 14false/UNBOUND/16UNAVAILABLE retained.

Provisioning-plan handoff: document checks PASS (41 protected files, append-only records, Q01-Q10/P0-P8,
INI parse only, links,14false/UNBOUND/16UNAVAILABLE). No runtime tests or new artifacts/units/workers executed.
Source and earlier branch refs preserved. Six documentation/evidence files only; local commit and bundle;
final command results and delivery hashes recorded in new FINAL_DELIVERY.json, no remote push.
Next: unprivileged pure TDD fixed credential-seal bootstrap; no actual UID/capability/system-unit change.

## Credential-seal native implementation
Fresh f5c62ac/CLEAN; research/native-e-credential-seal branch in existing isolated worktree.
Implementation will be a native component with Linux syscall boundary (test-only linker interposition), plus cBPF generator.
No runtime main/provider registration/OS lab integration. IDs configure policy data, not authority; result cannot grant RUN.
Existing source and tests unchanged. New tests block all calls through component syscall symbol rather than mutating credentials.
Ruling: preserve research logs/ledger rather than skill scratch cleanup; user requires evidence preservation.

Review REQUEST_CHANGES: important x32 guard acceptance + I/O-uncertainty test gaps; reentry gap promoted to required coverage.
RED7/positive1 reproduced actual ABI acceptance and missing test injection. One fix pass rejects ILP32/non64 pointer/long;
adds pre/post close, post open/read, PDEATHSIG query failures and nested same-attempt coverage. No runtime integration.
Wrong research venv product run2675PASS/111FAIL was all missing numpy; preserved log, retry uses existing harness venv with numpy.
Ruling: actual kernel/custody/parent/exec/factory/host-policy scope remains explicitly unapproved; fixture results cannot fill16 evidence.

Task1/2 complete: generated native cBPF + real syscall sequence tested ONLY through no-forward linker fixture.
Task3 complete: post-review full236PASS (178preserved+58new), product2786PASS proper preexisting numpy venv;
unique final3022PASS/0FAIL/0SKIP; Python91.74/product98.50; C fixture line100, outcomes82.42; UBSan37PASS.
Strict compile/ruff/format/mypy/package build exit0. No source/runtime qualification from fixture coverage.
Independent review REQUEST_CHANGES fixed in one TDD pass, no post-fix independent review/C0I0 claim.
Native source changes after review limited to explicit LP64/ILP32 compile guard; test-only fault/reentry coverage added.
Rulings/excluded kernel/custody/integration/trusted-proc/OS scope and evidence-preservation cost recorded in review report.
Task4 report/evidence prepared, local final commit/bundle pending. All45 previous tracked files preserved.

Task4 complete: source/report/evidence/review, old45-file preservation and result logs verified; local append-only commit/bundle.
Keep branch/worktree as explicitly requested; no merge/push/PR/cleanup. FINAL_DELIVERY.json records exact handoff SHA/hash.
Next unprivileged implementation is original F-to-E private channel/P-grant lifetime; actual system unit/cgroup remains forbidden.

## Native private parent handoff
Fresh a961f2c/CLEAN, new research/native-e-parent-handoff in existing isolated linked worktree.
F/E will be fixed native roles; original E pidfd born in native F so Python controller cancellation cannot discard an unrecorded E birth.
P is a fresh private REGULAR directory only. No arbitrary external parent import and no cgroup authority claims.
Old worker protocol remains unchanged/FD-rejecting. New parent protocol is separate NPG1 with same bounded context field layout.
Ruling: preserve all prior tracked files and logs; no refactor of historical handles/protocol to absorb FD-capable semantics.

Initial native24-case run23PASS/1FAIL: close_unknown fixture reused a generic injection flag, so no close fault occurred;
separated flags,25PASS. New forbidden-FS test RED proved check followed creation; moved FS validation before mkdirat,
using retained base directory FD for creation/open/unlink. No actual cgroup used. Channel ownership transfer made explicit.
New F_GETFD-error RED caught negative-return bitmask being treated CLOEXEC; explicit negative rejection added.
Received FD accounting now checks every actually delivered descriptor consumed once before native peer exit;
foreign original descriptors remain open, duplicate/late/truncated rights and old-context replay are exercised.

Independent review REQUEST_CHANGES: cgroup-v1 gate missing (RED1/positive2), late final-base close contract,
and receive-FD counter silently ignored duplicate close (separate RED1). One fix pass rejects both CGROUP magic values
before creation and uses per-delivery retained OFD anchors in test accounting. Existing production closure paths remain one-shot.
Ruling: pre-removal uncertainty suppresses removal; a later base close UNKNOWN reports parent_removed=true as historical fact.
No recreation/rollback/false cleanup success. Added targeted late-close test (passed existing truthful output), documented limitation.
All real handoff work remains private regular-directory/same-UID fixture; protected systemd factory and W exec-entry absent.

Tasks1-3 complete: native IPC30 initial/33 final focused; research269 + product2786 =3055 unique PASS/0FAIL/0SKIP.
Python91.74/product98.50 preserved; handoff.c line96.57/outcomes72.52 (test-only child GCOV dump); UBSan33;
unwrapped fixed native PASS; strict compile/ruff/format/mypy/package build exit0.
GCOV initial diagnostic exit97 from libgcov fcntl lock wrapper is retained with its regular-directory residue;
new diagnostic-only shim/cohort measured coverage. No actual cgroup/systemd/credential/worker/provider qualification.
Final review REQUEST_CHANGES addressed by author TDD/contract clarification; no post-fix independent C0I0 claim.
Report/evidence prepared; local commit/bundle pending. Earlier52 tracked files remain identical.

Task4 complete: final report/evidence/review, source-bound native checks and old52-file hashes verified;
local append-only commit and bundle with FINAL_DELIVERY.json. Keep current branch/worktree; no push/merge/PR/cleanup.
Next code work: fixed W exec-entry/FD/parent proof plus credential/handoff unprivileged integration.
Protected systemd factory/real cgroup binding and qualification remain UNAVAILABLE, not filled by these fixture results.

## Fixed worker entry integration
Fresh42b7711/CLEAN; new isolated branch. Frozen old tracked files except append-only ledgers.
Reuse prior native components, no existing source/test edits. Design choices recorded in PLAN.
Actual exec/FD/parent facts are separated from credential syscall simulation; no protected-host promotion.

Focused55PASS, full research324PASS/product2786PASS before final review.
UBSan first53PASS/2FAIL: fortified __poll_chk bypassed test-only poll injection;
same test boundary now wraps both symbols, then55PASS. No production criterion relaxed.
A logging-wrapper missing-json error occurred AFTER UBSan55PASS; output preserved, final rerun records exit directly.
Self-review clock_unavailable RED showed initial failed time read could pass inherited helper arithmetic;
new-entry preflight/receiver/exec-EOF and raw W clock guards added, GREEN. Old source remains byte-identical.
Independent review birth-report issue reproduced2RED: final NPG1 ACK failure erased prior W birth;
unknown/killed E status incorrectly emitted false. Monotonic true and unavailable null now2GREEN.
No new credential/OS privilege/service/cgroup work; fixture and product qualification remain separate.

Final review completed: no other Important/Critical finding. Minor recv-error buffer read
reproduced RED and fixed early return; fixed E-to-W cancelled creation fixture added (original pidfd retained).
Final60newPASS,329researchPASS,2786productPASS =>3115uniquePASS/0FAIL/0SKIP.
UBSan60PASS; fixed freestanding worker uninstrumented; C line/branch coverageUNAVAILABLE.
Ruff/format/mypy9modules/build all exit0; existing Python91.74/product98.50, threshold90 unchanged.
All58 protected hashes preserved, no product/harness ref or worktree changes.
Korean final report/review/evidence written. Final local commit and delivery follow; no push.

## Administrator review package successor
Fresh8c0058e/CLEAN, new branch. Old protected file count recorded in new preservation manifest.
Architecture review is selecting systemd255 StartTransientUnit with private stdin FD, not installing old lab binary.
Old integration is sameUID regular-P lab: fixed IDs, caller-owned image, F-cloned E, no CLONE_INTO_CGROUP.
No current source is promoted into root service. New config files will be .proposed review artifacts only.

Review package: chose v255 system bus StartTransientUnit(modefail,AddRef,private stdin UNIX FD),
manager-owned E vs E-owned W explicitly separated. Old sameUID lab remains noninstallable.
Exact new paths + persistent deny-only attempt.intent; no unnecessary private /run folder.
Reviewer Important parser mismatch: NBSP/VT/FF and account prefix false PASS reproduced RED;
printable ASCII+TAB/LF/CR guards added. Minor sysusers global DB backups/nscd effects now explicit,
unapproved future impact and automatic global restore excluded. Review73GREEN/full402PASS.
Ruff/format/mypy10modules/content lint exit0; checker94.96, oldPython91.74.
Prior product source unchanged, no rerun or duplicate PASS counting. Packaging/C unchanged.
Existing68hashes and append-only ledgers preserved. Report/evidence complete; local commit/delivery follow.
Next genuine code gap: fixed factory private FD/manager lifecycle backend, not additional metadata flags.
All14false/UNBOUND/16UNAVAILABLE, OS apply remains blocked. No remote push/PR/upload.

## Factory manager backend fixture
Fresh4595279/CLEAN. New isolated branch, preservation manifest freezes old tracked files except ledgers.
Runtime libsystemd.so.0 exists; sd-bus.h/pkg-config/linker dev symlink absent.
Use minimal audited public ABI declarations and -l:libsystemd.so.0; no install or actual manager access.
Native private synthetic M/E lifecycle, real library wire + SCM_RIGHTS, keeps OS proof boundary explicit.

Native private sd-bus normal28PASS after unit-prefix length fix (bad hardcoded22 vs actual24).
Added three late Unref event RED cases: pre/post-reply duplicate/owner-change could escape earlier check.
F now consumes original M wait once, drains private peer to disconnect, revalidates observations.
M E wait also consumes original handle BEFORE uncertain wait. No retry on cleanup path.
Library teardown void API cannot expose internal close syscall results: new RED disclosure test,
protocol-only outcome and explicit library-close UNAVAILABLE; native handle scope separate.
Same-process second attempt RED→GREEN with atomic one-shot, not persistent authority.
Expanded42native fixtures PASS, including real FD type/extra/dup, manager-held endpoint, timeout/cancel/reuse.
No actual bus/unit/credentials/P/D/W, no new dependencies installed.

Final source44→46tests: generation-change + unexpected sender negatives.
Important constructor issue independently confirmed; both pre-library/pre-transfer native-FD leak cases RED,
then explicit ownership transfer/native refs cleanup GREEN. Test-only strict compiler warning fixed before RED.
Final46focusedPASS,448researchPASS,UBSan46PASS,GCOV46PASS; native branch percentages exposed, no SDK/kernel claims.
Ruff/format/mypy10modules exit0; old Python91.74 preserved; no packaging/product/native-old-source changes.
Library close remains UNAVAILABLE; protocol success is NOT global cleanup/qualification.
Report/review/evidence written. Local commit/bundle pending, no push; UNBOUND/16UNAVAILABLE/14false.
Next actual code gap is M-owned E + original P handoff + W-entry integration in unprivileged fixture.

## M-owned E / P / W integrated fixture
Fresh4643a9e/CLEAN,92 protected source/report/test hashes. New research/native-e-cohort-integration.
Plan appended; no actual manager/credential/cgroup change. Default remains unbound.
Next RED integration contract, then new native coordinator.

Initial contract RED37 missing new module; native compilation then fixed macro nesting/test buffer warning.
38focusedGREEN. Added live shared-memory test-only creation/wait audit RED→GREEN6 cases.
Reused old typed parser/framing/worker source unchanged. W actual exec; UID/cap/NNP calls simulated.
M waits E up to10s, F gives M15s; forced/unknown wait remains UNKNOWN, no descendant-drain claim.
Next whole-tree regression, focused UBSan/coverage and independent source review.

Independent source review REQUEST_CHANGES: Important P2 context clock failure + Minor plan creation-order mismatch.
Exact clock-failure RED observed full protocol success/W birth, then use one checked timestamp before encoding.
Final: Ruling: P is created AFTER accepted manager job, so neither M nor E inherits P.
This is intentional and safer than the preliminary before-M plan sentence; sameUID mkdir/open gap stays unqualified.
Final: Ruling: upper-bound forced M/E termination does not prove descendant drain; UNKNOWN retained.
Minor doc mismatch clarified by this append; no old plan/evidence rewritten.
Next repaired suite/UBSan/GCOV, no independent C0/I0 claim for final tree.

Final source repaired: research493PASS,45new; UBSan45/GCOV45. Python91.74 at unchanged90.
C fixture coordinator93.43line/59.70branch, peer100line/50branch; SDK/staticW not instrumented.
Default compile coverage separate24.82line/8.21branch; no merged/overwritten source-key claim.
Ruff/format60files/mypy10modules exit0; packaging/product unchanged NOT_RERUN.
92old hashes and append-only ledgers preserved. Report/review/evidence ready; local commit/bundle next.
All14false/UNBOUND/16UNAVAILABLE, no actual unit/cgroup/credential/global policy/vehicle.
Next code gap: E-owned internal-D backend joined to manager-owned E, still unqualified.

## Internal D in manager-owned cohort
Fresh d70b425/CLEAN,101 protected files. New research/native-e-domain-cohort.
Old native source guards/wait reused by attested build-only entry rename, old launchers NOT called.
No actual cgroup/credential/unit operations; fixed W kernel exec/termination + simulated controller boundary.
Next RED native integration contract.

Initial missing-module RED. Native normal/policy failures:19GREEN after test-only name-replacement
fixture corrected to bypass component mkdir wrapper (otherwise it counted the adversarial replacement as another E creation).
Added later membership/kill/open/unlink/close failures, strict duplicate-populated events and foreign-FD no-close audit.
No old source changed. Private component symbols hidden; fixed-only binary, no provider/import API.
Next expanded native suite + independent source review.

Expanded29GREEN. Independent source review REQUEST_CHANGES: Important2, no Critical/Minor.
Both precisely RED: single W generation-clock error yielded full protocol/D removal;
partial-parent same-inode/different-OFD replacement caused one foreign close.
Fix pass: check a single generation timestamp; without established parent OFD anchor retain
process-bound UNKNOWN and never close/recover numeric FD. No old source or test criteria changed.
Ruling: missing anchor can retain own FD until process exit; this is safer than inode-only close
and cannot be claimed full cleanup. Final post-fix independent C0/I0 is not claimed.
Next targetedGREEN then whole research/UBSan/GCOV/static checks.

Final source:524researchPASS=493old+31new,0FAIL/0SKIP; UBSan31/GCOV31 are repeats, not added.
PolicyC100line/70.29branch, peer97.89/61.18; SDK/staticW/kernel excluded. Python91.74/threshold90 unchanged.
Ruff/format64files/mypy10modules/C strict build PASS; product/package unchanged NOT_RERUN.
New backend credentials no-forward; existing baseline child self NNP/rlimit checks unchanged, no global settings.
Source-only review Important2 both RED→GREEN; no final-tree independent C0/I0 claim.
101 old hashes and append-only ledgers preserved; report/evidence complete. Local commit/bundle next, no push.
Symbol verification initially expected HIDDEN text; linker localized functions to LOCAL instead.
Final source-bound binary: all5 private symbols LOCAL and absent from dynamic symbol table.
Next: fixed real-cgroup2 user-unit lab adapter under original bounded scope; actual qualification remains unavailable.

## Real cgroup adapter / continuous follow-through
Fresh ed8b68a/CLEAN,111 protected files; new research/native-e-real-cgroup.
Current user manager active delegated cpu/memory/pids. root -.slice active/same controller group.
app.slice lacks cpu subtree, so choose existing user root slice to avoid changing existing controllers.
No real unit created yet. Next RED fixed adapter/gate/controller contracts.

Initial import RED, native link collision from old unused direct_supervisor_main renamed in build-only scope copy.
31new controller/gate/build/direct-scope tests GREEN. Author RED4 fixed malformed unit identity,
frame ordering and initial lookup race; duplicate JSON-key RED fixed with rejection.
Valid gate same-PID exec/FD test passed without implementation repair.
No actual unit yet. Root-slice decision avoids preexisting app.slice controller modification.
Next review and source-bound regression/runtime commit before conditional real labs.

2026-11-06 review fix pass: Important3 + bounded FIFO minor reproduced RED and repaired.
Source snapshot compile + pre/post original equality; communicate exclusively owns closure after entry,
unknown streams retained with original job; GO bounded read1 + strict EOF, duplicate/trailing/partial reject.
FIFO opens NONBLOCK and regular-type check before reads. Unsupported stdin-type RED repaired by checked concrete
buffer interface, so strict mypy remains enabled without ignores.
Focused62GREEN/coverage>=90; new Python package mapping via explicit module targets + MYPYPATH root/src (no criteria waived).
Next final full source-bound regression/runtime local commit, actual units still0.

Runtime readiness:586freshresearchPASS=524preserved+62new,0FAIL/0SKIP.
New Python91.04%, old91.74%, threshold90 unchanged; strict native compile, Ruff/format70, mypy14 PASS.
All111old hashes/old refs preserved. Important3+FIFO minor RED→GREEN; no post-fix independent C0/I0 claim.
Source fixes now frozen for local runtime commit; actual units still0.
2026-11-06 next fresh kernel positive unit, then serial private-kit drift-negative only if first completed.

Actual kernel positive PASS_REAL_CGROUP_POSITIVE: real placement/kill/original wait/D reclaim, unit collected.
Continued automatically to NEW kit+unit drift-negative: ASSET_DRIFT before F/W, PASS_REAL_SOURCE_DRIFT_BLOCKED.
2serial units, no overlap, final lab namespace0, sources31/31 + old111 unchanged.
Preservation audit retained whole_serial_operating_preserved=false: only manager/MainPID + manager_starttime differ
between WSL calls; each attempt before/after identity stable, configs across both stable. CauseUNKNOWN/no tracing,
no workflow existing-service restart. This is not promoted into same-generation/continuous preservation PASS.
Kernel facts stay bound to their separate fresh attempts. No further OS experiments initiated.
Reports/evidence prepared; prototype authorized bundle complete with protected-origin/F1/crossUID/qualification gaps explicit.
Next local final metadata commit/bundle; no push, no actual payload/provider promotion.

## Persistent native factory intent
Fresh d24cb17/CLEAN; isolated branch, old123 nonledger pins frozen. Existing private manager46baselinePASS.
Design: deny-only original-FD intent before synthetic manager, no OS unit/admin work. Next RED tests.
Initial missing-module RED observed. Strict compiler rejected test-driver misleading indentation, fixed test-only.
41 focusedGREEN. Added real inherited-FD sweep assertions and socket/OFD/unknown syscall cases.
No new actual unit/cgroup/admin work. Next focused/static/review.
53focusedGREEN. UBSan first run51PASS/2FAIL: fortified compiler emitted __pread_chk, bypassing test-only pread injection.
Observed nm undefined symbol + installed unistd-decl.h signature; wrap fortified call without disabling fortification.
Production unchanged. Next UBSan/GCOV then whole regression.
Independent whole-change source review Important1: final-anchor inode-only close. RED2 reproduced foreign close after successful primary close.
Ruling: consume/close primary only; retain terminal anchor slots in static process-bound context until exit — no comparator/recovery after close; cost bounded FD residue, no full cleanup claim.
Reviewer declined OS power loss/hostile sameUID/F1/crossUID/actual manager qualification: stay UNAVAILABLE, not implemented by latch.
No material minors. Final repair author-verified; no post-fix independent C0/I0 claim.
Author contract audit found receipt ambiguity: unverified durability emitted false. RED6 incl existing/twice/unknownsyscalls.
Use null for unknown/uninspected/second-attempt durability, retain false only known no creation and true only observed fsync sequence.
New unique5 cases (existing twice case augmented). Final suite must be source-bound after this reporting fix; prior run is interim.
Author lab-bound audit: pause fault fixture had unbounded wait if harness vanished. RED independent6s wait timed out; original new child killed/reaped by finally.
Test-only pause now alarm4 fixed; no existing process touched. New unique1, total61. Core production unchanged from null fix.
Final regression ledger must distinguish current collected646 from final focused61 (dedup647) or rerun one fully collected647; no historical double-count.

Final verification: full646PASS, final native61PASS (overlap60), authoritative647unique/0FAIL/0SKIP.
UBSan61/GCOV61 repeats; intent C line100/outcomes74.68, factory line100/outcomes89.47. Old Python91.74 threshold90.
Ruff/format76/mypy14 strict checksPASS. Old123 pins and original refs preserved, ledgers append-only.
No OS unit/cgroup/admin/service/payload/remote action. All14false/UNBOUND/16UNAVAILABLE.
Next native dynamic manager owner/job binding, before any protected administrator apply.
