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

- [ ] Add direct original-API Unicode and exact-integer negative/regression tests.
- [ ] Run them RED against the unchanged functions; record the root causes.
- [ ] Implement only the two approved function changes; run focused tests GREEN.

### Task 2: Preserve historical characterizations

- [ ] Add failing checks for the closed frozen-case runner and snapshot integrity.
- [ ] Implement a bounded, test-only full Git snapshot and isolated pytest runner.
- [ ] Retain the five old node IDs, delegating only their bodies to the snapshot.
- [ ] Run old cases, both strict facades and current original-API tests.

### Task 3: Exact history transition

- [ ] Add policy rejection/integration tests and observe RED.
- [ ] Change only the 18 approved guard assertions, retaining BASE/scope checks.
- [ ] Freeze exact existing-file pre/postimages in local append-only commit P.
- [ ] Implement the helper pinned to P; validate all three current representations.
- [ ] Run adversarial policy tests and the full architecture suite GREEN.

### Task 4: Verification and handoff

- [ ] Full regressions, audits, lint/format/types, coverage, replay and fresh wheel.
- [ ] Check exact 29-path bound and preserved installed package/CI/fixtures/evidence.
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

Pending implementation. Baseline: 4,195 passed in 39.28 seconds.
