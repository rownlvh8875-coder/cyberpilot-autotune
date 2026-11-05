# Internal-D / manager-owned cohort design

Base:d70b425bb061c710fd0aabe2fdd396c765d16770.
Scope: unbound same-UID native research, **simulated cgroup boundary**.
No actual system/user unit, delegated cgroup write, credentials, Docker, vehicle or provider binding.

## Components and private interfaces

- research/domain_cohort/policy.c + internal.h: hidden private native D state machine.
  The parent argument is a live original-P reference from fixed E's NPG1 path.
  No CLI/RPC/environment/receipt/path/PID/FD-number import or recovery interface exists.
- peer.c: fixed fd0 E entry, unchanged old image/trampoline/SCM_CREDENTIALS helpers.
  New fixed run_domain_worker creates D and asks clone3 for CLONE_PIDFD|CLONE_INTO_CGROUP.
- worker.c: includes the old static fixed worker entry witness, then waits at most4500ms.
  Natural expiry exits42; it is not accepted as SIGKILL.
- tests/native/domain_cohort_driver.c: only new ordinary fixture files and original live worker pidfd.
  Fstatfs/controller metadata and clone-into-D effects are simulated; actual clone/exec/kill/wait remain native.
- tests/test_domain_cohort.py: attested build composition, native cases and passive test-only counters.

Existing101 source/test/report files remain byte-identical. Old branches and evidence are preserved.
Generated domain_reference.c is an exact pinned old source with only main renamed.
Its original_D/exactly_child/no_descendants/wait_domain_original helpers are reused.
The old launcher is NEVER called: no pathname P rediscovery, old PRCTL sequence or old worker launch.
The old native driver is similarly pinned and composed through build-only entry/wrapper renames.
These generated files are fixture build inputs, not verified protected-origin executables.
No package/provider/public library export is created; internal component symbols use hidden visibility.

## Ownership and sequence

F owns original M and regular P; M owns original E; E owns D and original W.
P is created after manager job acceptance, so M/E inherit no P reference from F.
E receives P through the existing one-shot private channel and holds it across D/W lifetime.

1. Reject non-cgroup2/type/owner P before D creation (fixture supplies virtual metadata).
2. Duplicate live P, establish OFD anchor, generate exclusive random owned-d-* child.
3. Retain original D fd+anchor and verify original name/OFD/zero descendants.
4. Ask for W birth into original D, atomically retain original pidfd, fixed sealed exec.
5. Verify current NWE1 image/parent/FD/credentials/context witness.
6. Require exact W member only, E not W, no descendants, original P/D identity.
7. Issue exactly one cgroup.kill-shaped write; consume attempt before open/write.
8. Consume original W pidfd before exact native SIGKILL wait.
9. Require unique populated0 event and original D, then unlink own D, close own handles.
10. E completes NPG1 only after D path success; M/F original waits and final event checks remain unchanged.

Creation is mkdir/open with a trusted-single-owner gap. Checks before stop/unlink are snapshots,
not an admission fence against coequal writers. Those limits are NOT repaired by hashes or metadata.

## Failure and cleanup

Partial write/unknown close/wait, extra member/descendant, wrong FD/name or late manager failure reject.
No retry, pathname reattachment, numeric PID/FD recovery or source automatic repair.
Before D stop is attempted, failure may stop only original W pidfd once and wait once.
After an ambiguous D-stop attempt, no second signal/write is issued: wait once for bounded W expiry.
Unknown wait consumes the original handle; later cleanup cannot retry that wait.
No anchor means no inode-only close: retain process-bound UNKNOWN and let process termination reclaim its FD table.
If native D removal happened before a later close/return error, the passive audit retains removal=true,
while the coordinator result stays UNKNOWN/REJECTED and does not remove P.
SDK internal close remains UNAVAILABLE; arbitrary descendant/async-writer drain is not certified.

## What the fixture proves

New P/D are real ordinary directories; descriptor/OFD/exec/parent/pidfd operations are native.
The test boundary strips CLONE_INTO_CGROUP before real child creation and records the original request.
A kill-file simulator signals only the original pidfd retained at this E-owned birth.
This is **not actual cgroup placement, kernel cgroup.kill, namespace containment or host authorization**.
Controller files are created/updated/removed only under the new fixture's own private P/D.
No existing cgroup/controller/service is touched.
New credential changes are simulated through the unchanged no-forward shim.
Existing baseline direct-child self-restriction tests remain separate from new credential proof.

Actual F1/protected manager/code/loader/UID transition/readonly mount/namespace/external writer drain
remain UNAVAILABLE. Provider UNBOUND, qualification16UNAVAILABLE/available0, all14 project flagsfalse.
