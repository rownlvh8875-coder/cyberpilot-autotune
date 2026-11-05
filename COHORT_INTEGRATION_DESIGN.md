# M-owned E / original P / fixed W integration

This is an unbound **same-UID native research fixture**, not a systemd provider.
Base:4643a9e7be574c6d3f9db114ebff7ce518777b5d. No protected-origin or F1 claim.

## Ownership and sequence

| Actor | Original live handles | Creates/waits |
| --- | --- | --- |
| F coordinator | private bus socket + OFD anchor, M pidfd, new regular P directory + anchor | M only |
| synthetic M | received E endpoint duplicate + anchor, original E pidfd | E only |
| fixed E | fd0 private endpoint, received original-P reference, W image/socket/pipe/pidfd | W only |
| fixed W | devnull0..2, private socket3, own exec image | no child or imported parent directory |

F negotiates the private real libsystemd bus, owner, subscriptions, job and generation.
Only after the job is accepted does F create P; M/E cannot inherit P from F.
M's early close_range also removes inherited F handles before the message transfer.
M's typed request parser takes an owned duplicate of the library-borrowed E endpoint.
The new E entry closes inherited bus/native FDs before reading NPG1 on fd0.

NPG1: HELLO→READY→GRANT(one SCM_RIGHTS P, dev/ino, fixed context)→ACK→COMMIT→F EOF.
E holds P while existing run_worker performs the sealed fixed-image exec and NWE1 proof.
E closes its P references, sends CLOSED, explicitly shutdowns write, then exits.
M retains an E endpoint until original E wait; therefore plain E close is insufficient for F EOF.
F performs UnrefUnit, original M wait and final private-event drain.
Only then, with no native uncertainty, F may remove its own still-matching empty regular P.

## Source/API

- research/cohort_integration/cohort.c: ci_run_fixed(void), no caller-selected resource/command.
  Includes unchanged factory.c for static bus/IPC helpers. New sequencing is explicit here.
- research/cohort_integration/peer.c: ci_peer_fixed(void), fd0 fixed private E entry.
  Includes unchanged worker_entry/integration.c for entry_peer/run_worker.
- tests/native/cohort_manager.c: test-only M constructor and lifecycle; includes old typed parser/events.
- tests/native/cohort_driver.c: test-only fixed fault cases and shared-memory creation/wait counters.
- tests/test_cohort_integration.py: native builds/fixtures, no actual manager connection.

Default links unchanged unbound.c (ENOSYS) and never creates P/M/E/W.
No factory API accepts paths, PID, numeric FD, unit names, callbacks or serialized receipts.
The internal data encoder still accepts a factory-created endpoint; it is not a public adoption API.
Same-process atomic one-shot is not a persistent cross-process admission fence.
Passive summary/exit/audit values are not used to reconstruct live authority.

## Bounds and uncertainty

Each primitive frame is bounded512bytes with explicit EOF; exact old50byte context retained.
Cohort/generation/nonce/stage/sequence are checked through existing NPG1/NWE1.
Generation timestamp is read once and checked before encoding; it is not a host-admission proof.
F gives E's protocol7500ms before final framed reply. M gives E10000ms, F gives M15000ms.
Wait attempts consume original handles before uncertainty; no numeric PID-based retry or adoption.
Forced M/E termination at a bound does NOT prove arbitrary descendants drained.
Unknown waits/close/mapping/name/partial cleanup remain UNKNOWN; owned directory residue is preserved.
Void SDK teardown still exposes no internal close status: library_close_result=UNAVAILABLE.
Even normal protocol completion is NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE, never global cleanup success.

M's User/capability/NNP/limits/ExecStart properties remain **wire data only**.
The credential TU is linked through the existing no-forward syscall shim; no actual security write.
Actual W exec/FD/socket/parent checks use the kernel; cross-UID credentials are simulated, not certified.
W's entry FD mask and kernel SCM_CREDENTIALS are existing fixed-entry checks, not hostile-E attestation.
The fixture build path/image is caller-owned research storage; sealed bytes do not authenticate origin.
P is an ordinary private directory. mkdir/open and check/unlink gaps are trusted-single-owner assumptions.
No actual cgroup D, readonly mount, namespace containment, protected loader, admission fence,
external writer/async drain, native provider registration or product integration is implemented here.

## Verification and outcome

The final report/evidence records fresh tests, C coverage exclusions and independent review.
Old92 source/report/test files are byte-preserved; ledgers append-only.
All14 project flags false; provider UNBOUND; qualification16UNAVAILABLE/available0.
No package/system install, service, actual bus, account, global policy, Docker, vehicle or remote publication.
