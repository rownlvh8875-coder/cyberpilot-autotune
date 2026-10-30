# Guest consumption prototype review record

Independent read-only review **C0 / I3 / M1** at exact
`f57e203382ef233108132a6af37453772fdd1242` versus base
`c5b824f4f37e05bcac81769f1d01a55a51c26e1d`. Reviewer ran89 focused tests and
offline kernel/source/capture audit (7files/11ranges/7captures), reproduced all
three Important contradictions, and did not mutate tracked files/index/HEAD or
run guests/native payloads. No permission escalation was found in actual captures.

All three Important findings accepted, with19 regressions observed RED before
the fix and22 GREEN afterward (three positive cases retained). One author fix
pass/full rerun; **no independent fix-head re-review and no C0/I0 claim there**.
Final actual rerun, broad regression and exact-head CI results are in the handoff.

## Important fixes

- I1: split only physical LF/CRLF, not Python splitlines separators. Nine
  VT/FF/CR/control/NEL/Unicode interleaving cases reject; legitimate LF/CRLF
  retain identical typed event content.
- I2: fork BIRTH inherits the exact active parent image object, not a different
  inode with matching bytes or another known executable. Same/different-byte
  substitutions reject; a later explicit child EXEC can change the image.
- I3: ERROR enters a global abort phase. New object/birth/exec/read/map/metadata/
  failed-call/error records reject. Payload draining and actual exit/reap remain
  observable, without inventing more consumption after fatal collection failure.

Tests: `tests/unit/test_guest_consumption_review_fixes.py`.

## Exhaustive rulings before cleanup

1. Inline implementation/one review without repeated approval menus: user
   delegated these decisions. Cost: author-selected architecture and boundaries.
2. Reuse dedicated checkout/new branch. Cost: less filesystem isolation than a
   separate worktree.
3. Manual owned ledger because cloud workspace helper is unavailable.
   Cost: manual bookkeeping risk; no other plan's ledger reused.
4. Ptrace stopped-buffer prototype, not a full kernel/file-object observer.
   Cost: loader reads/page touches, hostile/external writers and generalized
   concurrency remain unqualified; no full FD/OFD alias qualification.
5. Seven new fixed fixtures, old HF payloads/evidence untouched.
   Cost: no general compiler/native workload support.
6. Return observation plus original raw serial data rather than observation only.
   Cost: callers handle a pair; no writer/persistence service is introduced.
7. Reviewer did not execute fresh guests/native/dynamic C fault injection:
   author actual runs plus independent replay/source inspection suffice for this
   scoped prototype. Cost: C runtime/fault paths not independently exercised.
8. General workloads, hostile/shared-memory concurrency, full FD/OFD aliases,
   external writers, async IO, kernel-loader reads and page touches excluded:
   explicitly remain unqualified. Cost: no completeness guarantee for these inputs.
9. Authenticity, input sealing, executor/output qualification and host TOCTOU
   excluded: keep untrusted observations and all authority false. Cost: coherent
   forgery, mutation and real execution guarantees are not ruled out.
10. Carrot/vehicle/controller/Params/application/host-policy effects excluded:
    no such operations or modified old packages. Cost: no deployment/vehicle/
    host-policy qualification.

## Deferred minors

M1: manifest permission/path boundary tests start from incomplete top-level
shapes, so those particular guard mutations are not independently caught.
The actual guards remain present/reviewed, and the binary path is not data-driven;
this is a test-quality gap, not a found permission escalation. It remains Minor,
not artificially promoted to justify another fix. Cost: incomplete mutation
coverage for those guards until a separate test-improvement task.

## Remote verification continuation

The first push/PR CI at5bde1cf failed one Windows path expectation (not a runtime
mutation): `Path('/owned/new.cpio.gz')` renders native backslashes. The test now
checks unchanged native argument propagation, including a space-containing path.
No collector/runtime/source manifest/capture bytes changed and M1 was not fixed
incidentally. Windows CI provided RED; local full2454 passed before the new push.
The verification pass remains open until the final remote matrix is green.
