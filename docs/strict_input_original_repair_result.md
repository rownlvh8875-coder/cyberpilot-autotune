# Original strict-input repairs: approved plan and result

> Execute inline with test-driven development and one fresh whole-branch review.

## Approved design and bounds

The user explicitly approved the limited history-policy revision after the
read-only boundary review. Base: `cfc31c36c1fa99c7d00d9609c5360b9e07894d7e`.
Branch: `feat/original-strict-input-repairs`. This is not merge/deployment authority.

Exactly 22 existing paths may change: two original functions, two historical
characterization test files, and the 18 history guards listed in the transition
manifest. Exactly seven new paths: this document,
`docs/evidence/strict_input_history_transition_v1.json`,
`tests/history_transition/{__init__,policy,frozen_cases}.py`,
`tests/test_history_transition_policy.py`, and
`tests/test_original_strict_input_repairs.py`. No other tracked-path change.

Containment parse constructs the same immutable case, checks its unchanged
canonical digest before return, and translates only UnicodeEncodeError to
ValueError("INVALID_UNICODE_SCALAR"). Direct constructors and canonical_digest
remain unchanged. Handoff validates exact dict/string keys/int limit values
16/4096/1024/2097152 before comparisons, retaining its existing ValueError and
all other validation. No reverse facade imports, rebinding or caller migration.

Five historical cases retain their node IDs and execute their original bodies
from a full, byte-verified snapshot of the exact base in a separate interpreter.
Current original-API regressions are additional. No skip, xfail or selection
reduction. No old evidence, fixture, golden, source pin or document is rewritten.

Each history guard keeps its BASE, scope and additive attributes check. Its
absolute current-tree freeze gains one explicit, exact-content exception, not
a directory whitelist. A local append-only preregistration commit P freezes the
22 pre/postimages, modes and guard identities before the new policy helper pins
P. The helper reads the manifest from P, never the working manifest, verifies
HEAD/index/clean-filtered worktree postimages and rejects missing objects without
fetch. P may be RED; only a final verified tip is suitable for any later handoff.
The digest is content identity, not authenticity or safety/application authority.

## Review focus

- Non-string/equality-spoof keys must fail before limit-key equality.
- Nested surrogate text must not escape parse and must preserve valid digests.
- Index-only, worktree-only, mode, deletion and unlisted edits must fail closed.
- Historical execution must not import repaired modules or mix class cohorts.
- Policy provenance must not depend on a mutable manifest or self-referential SHA.

## Implementation plan

### Task 1: Original entrypoint repairs

- [x] Add direct original-API Unicode and exact-integer negative/regression tests.
- [x] Run them RED against the unchanged functions; record the root causes.
- [x] Implement only the two approved function changes; run focused tests GREEN.

### Task 2: Preserve historical characterizations

- [x] Add failing checks for the closed frozen-case runner and snapshot integrity.
- [x] Implement a bounded, test-only full Git snapshot and isolated pytest runner.
- [x] Retain the five old node IDs, delegating only their bodies to the snapshot.
- [x] Run old cases, both strict facades and current original-API tests.

### Task 3: Exact history transition

- [x] Add policy rejection/integration tests and observe RED.
- [x] Change only the 18 approved guard assertions, retaining BASE/scope checks.
- [x] Freeze exact existing-file pre/postimages in local append-only commit P.
- [x] Implement the helper pinned to P; validate all three current representations.
- [x] Run adversarial policy tests and the full architecture suite GREEN.

### Task 4: Verification and handoff

- [x] Full regressions, audits, lint/format/types, coverage, replay and fresh wheel.
- [x] Check exact 29-path bound and preserved installed package/CI/fixtures/evidence.
- [ ] Fresh-context whole-branch review; any material fix gets RED→GREEN/full rerun.
- [ ] Commit final result and report exact local head; no old PR/main/ref changes.

## Non-goals and retained blockers

No kernel/guest/device/vehicle execution; no Params/controller/cereal/schema
deployment; no external AI service, longitudinal, estimator/candidate/application
or owner bridge. No old PR edit/Ready/retarget/merge/rebase/force/shared push.
No v1 evidence promotion or synthetic-to-runtime qualification.
PR34 provenance and PR9 expiry policy remain unresolved.
APPLICATION_NOT_AUTHORIZED; runtime_accepted, candidate_generation_allowed,
application_authorized and owner_proposal_allowed remain false. Source/build
closure, lifetime/publication/concurrency/all-writer/copy-cut, loss/perturbation,
empirical, fingerprint, watchdog and external-executor blockers remain.

## Observed results

Baseline: 4,195 passed in 39.28 seconds. This document is the pre-review
checkpoint; the exact final review head/outcome is reported in the user handoff,
not added afterwards by changing the reviewed head. No independent human or
registered GitHub approval is claimed.

- Original-function RED: 26 failures / 24 passes, including nested Unicode
  surrogates, all four float-equal limits, exact subclasses and hostile keys.
  Minimal original repairs: 278 focused tests passed. Historical transition:
  exactly five expected old assertions failed before the snapshot runner;
  all five are now run unchanged at the frozen base, and 304 focused tests pass.
- History RED: exactly 18 guards failed / 82 passed before the approved exception.
  Local preregistration P: `127f485437437b3472659784b7b05857d8fbd896`, parent exact
  base. P intentionally lacks the enforcing helper and is RED, never published.
  Helper enabled in `3a338e52c37b24886809f75a8a6d04a682d7967f`. All 22 postimages
  remain byte-identical to P. The mutable working manifest is not policy authority.
- 147 policy/architecture tests passed, including all 18 actual guard functions
  rejecting unlisted installed-source edits, HEAD/index/worktree content/delete/
  rename/mode mutations, a hidden staged change, missing-P rejection and actual
  Git-clean CRLF equivalence. On Windows, the test is designed to mutate the
  index because POSIX working-file execute bits are not representable there;
  Windows execution itself has not been performed in this local Linux session.
- Every original guard Git query (AST), BASE and non-history function is unchanged.
  Existing additive `.gitattributes` checks remain. The absolute current-tree
  freeze criterion is explicitly revised, not falsely described as unchanged:
  the helper also checks the exact 29-path bound in all Git representations and
  nonignored additions. Future additions outside the seven new paths require a
  separately approved successor policy, not silent reuse of this exception.
- Full suite: 4,292 passed / 47.29 seconds. Coverage-instrumented full rerun:
  4,292 passed / 119.48 seconds; installed package coverage 98.52%, above the
  unchanged 90% gate. Focused original/facade suite: 525 passed; native containment
  contracts/evaluator 100% statement/branch, strict handoff 100% statement/branch,
  strict containment 100% statements with zero measured branch arcs (branch N/A).
  Full old handoff audit module is 95.45% combined coverage; five old source-error/
  CLI lines and one partial branch are not covered by that focused run.
- Ruff/format pass (655 Python files), mypy passes for 71 installed-source files.
  Observability, observation-v2, steering-knowledge, H5/H6/H7 and patch-design
  manifest/history validators pass. These do not newly verify external source
  checkout bytes where the validator reports `source_bytes_verified=false`.
  Handoff audit remains 66 synthetic cases / six consistent / seven pinned files /
  11 ranges, overall BLOCKED, runtime and permission fields false.
- Replay integration: 11 passed; all four pinned replay goldens verified both
  locally and from the fresh wheel. Fresh default-isolated build produces sdist
  and wheel; all 72 wheel package files match base Git bytes and exclude tests/
  compatibility. Vanilla imports all 70 submodules without NumPy/tests. Knowledge,
  owner, science, friction and receipt smoke pass; optional dependency failures
  are checked before installing research extras, and research smoke passes after.
- The initial `build --no-isolation` attempt failed because the existing dev venv
  lacked setuptools; the normal isolated build passed without changing project
  dependencies. An initial coverage run's stdout filename collided with coverage
  parallel-data cleanup; the separately named captured rerun above is authoritative.

Local status: ORIGINAL_PR25_INPUT_REPAIR_VERIFIED_LOCALLY;
ORIGINAL_PR33_LIMIT_REPAIR_VERIFIED_LOCALLY;
BOUNDED_HISTORY_TRANSITION_VERIFIED_LOCALLY.
These do not repair old PR heads or main before integration, do not migrate
callers by rebinding, and do not close runtime/vehicle/application blockers.
No push, PR creation, Linux/Windows remote CI, merge or deployment is performed.
Main was rechecked as `a5d3514f23797829eb58d08c638b22cf4dd30c8a`.

## Subsequent authorized Draft handoff: Windows correction

The preceding results are the original local checkpoint, not a claim that
publication never subsequently occurred. Authorized Draft PR53 targets PR52's
branch, without editing any previous PR or main. Initial head `192a1ee` push
run41243374748 and PR run41243382078 each had three successful jobs, one Windows
3.12 failure and two fail-fast matrix cancellations. Linux3.12, source audit and
schema compatibility passed; cancelled jobs were not counted as passing.

Windows reported six snapshot failures / 4,266 passes / 20 inherited skips.
`git archive` honors checkout line-ending conversion even on binary stdout:
read-only Linux reproduction with core.autocrlf=false had zero mismatches,
whereas true produced 622 CRLF-only mismatches against frozen Git blobs.
The existing byte-identity check correctly failed closed; it was not weakened.

The correction is confined to the new snapshot helper: per-command
`-c core.autocrlf=false -c core.eol=lf` on git archive, without persistent config
changes or source-byte normalization after extraction. The existing complete
snapshot test now covers default, true/crlf, false/crlf and input/lf host settings
using real Git and every blob's content identity. RED: one failed / three passed.
GREEN focused regressions including all history guards: 447 passed / 15.13s.
Corrected full-suite rerun: 4,295 passed / 52.03s. Ruff/format (655 files),
mypy (71 installed-source files) and diff/scope checks pass.
All 22 original preregistered postimages, P and the overall 29-path bound remain
unchanged. No old source, guard, fixture, digest criterion or test node is relaxed.

The subsequent exact-head review, corrected full-suite results and new push/PR CI
outcomes are recorded in PR53/user handoff after observation; the failed initial
runs remain historical evidence, not silently reclassified as passing. Runtime,
vehicle, candidate/application authority and all retained blockers remain unchanged.
