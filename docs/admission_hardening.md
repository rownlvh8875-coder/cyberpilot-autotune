# Phase 5 learning admission hardening

User assessment retained: synthetic shadow implementation CONDITIONAL_PASS,
PR #2 merge readiness HOLD, persistence NOT_AUTHORIZED. This change implements
only the requested admission strengthening; no replay harness is implemented.

## Preserved history and PR base

- Original Phase 5 head and CI evidence: 6931b562f4d56eab336bb89b6a8c9d8b340eef02.
- PR #1 merged using GitHub merge_method=merge, expected head 5d67bc6.
- Merge/new main base: 05b016237afec7c53195cb802bef2c3ae8138a8c.
- Merge parents: bf042cc1ee24d65d1e152066c4f0883ab0c85fee and
  5d67bc640939adbc888b19cbb6264dcf6b0cc5ac. No squash/rebase was used.
- PR #2 retargeted from feat/bootstrap-shadow-core to main, still Draft.
  Its pre-hardening diff contains the same 21 Phase 5 files as before retargeting.
- Append-only commits on feat/shadow-residual-statistics; no force push or rewrite.

## Contract and admission decisions

ObservationSnapshot gains keyword-only control_active: bool|None=None. True means
the evaluated controller is actually controlling at that snapshot, False is
explicit inactivity, None is unknown. Unknown is never inferred from cruise/UI
state. Constructors allow None but learning admission rejects it. No real Carrot
field mapping is implemented. Synthetic fixtures explicitly supply True.

ResidualStatisticsConfig and GateConfig both require a caller-supplied finite
nonnegative minimum_speed_mps, with no default. The gate owns the common policy.
A learner may declare its minimum through an optional LearningRequirements
Protocol. Engine construction rejects a gate policy weaker than that learner's
declared minimum, preventing configuration drift from bypassing pre-call checks.

SafetyGate.validate_learning_sample performs structural/time/freshness/order
validation, exact trusted-baseline identity, actual active control, minimum speed,
override and saturation vetoes before observe(). The same boundary is rechecked
after learner work. Candidate evaluation independently retains its existing
ordered checks and adds active/speed checks to the driver/saturation veto stage.
ResidualStatisticsLearner also checks active/speed/override/saturation itself.

Rejected frames with valid nonnegative integer sequences consume engine sequence
high-water even if other fields are rejected. Timestamp high-water advances only
for finite nonnegative timestamps at or before the injected clock. Future times
therefore cannot poison normal stream time. Previous high-water values are used
for the current frame's gate/rate evaluation. Correcting/replaying an already
rejected sequence cannot manufacture samples. No unbounded rejection cache exists.
Standalone observe() also reserves any valid sequence before structural/order
checks. Repairing an early-rejected frame cannot manufacture learner samples.

reset() deletes evidence only, preserving sequence/time high-water. It is valid
within the same monotonic stream. A restarted sequence/time domain requires a
new learner instance (and an engine for that new domain). OFF does not call clock,
admission, observe or reset. Effective parameters always equal trusted baseline.

## Test-first implementation and completion checklist

- [x] Contract/config validation RED then GREEN; migrate synthetic callers.
- [x] Pre-call active/speed/veto/call-count tests RED then GREEN.
- [x] Rejected-frame replay, exact minimum, reset/high-water and OFF tests.
- [x] Standalone learner defense-in-depth, incompatible policy, numeric properties.
- [x] Independent review and full regression, lint/format/mypy/coverage/build/wheel.
- [x] Push normally, inspect full CI at final head, keep PR #2 Draft/HOLD.

Next single work item after this hardening: deterministic replay harness.
Persistent learner state remains unauthorized until replay acceptance criteria
exist and explicit authorization is obtained. Vehicle control, Apply modes,
actual Carrot mapping, real logs/collection and vehicle limits remain non-goals.

## Verification ledger

- Contract RED: control_active construction failed because the field did not exist.
- Contract GREEN: 269 tests passed after adding three-state activity and explicit
  minimum-speed configuration and migrating synthetic-only callers. Original
  head/CI remain intact; this intermediate contract commit does not claim the
  admission boundary is complete.
- Admission RED: control_active=None reached observe() once in the old engine.
  Common admission now excludes unqualified frames before observe(), also in
  empty-proposal streams, and rechecks after work.
- Numeric-policy RED: a finite integer minimum above float exact precision could
  be rounded during policy comparison. The comparison now validates without
  coercing the learner requirement, rejecting an actually weaker gate policy.
- Independent review found one Important standalone replay gap: structural or
  timestamp-order rejection occurred before reserving a valid sequence. Two
  regression cases reproduced sample_count=1 after repairing the rejected frame.
  The learner now reserves that identity before those checks; the same tests
  verify zero evidence on replay and fresh evidence only at the next sequence.
- Reviewer ran 178 focused tests and reported no other findings. The Important
  finding was fixed in f20fbcf using two RED/GREEN regressions; full suite is now
  335 passed, 0 failed, 0 skipped. No deferred review findings remain.
- Local branch-inclusive coverage: overall 98.55%, safety 100.00%, runtime 100.00%,
  residual learner 97.85%. Ruff lint/format and strict mypy passed (26 source files).
- Package research version is 0.1.0a2 for the strengthened constructor/admission
  contracts; no release is published. Existing 0.1.0a1 and original SHA/CI evidence
  remain historical records.

## Clean-environment verification and delivery

- Fresh remote clone at 857bbde0a7aee74b0cbc758b11f042fe74464c7c; newly created
  CPython 3.12.14 venv; pip upgrade and editable dev installation succeeded.
- pytest and coverage runs: 335 passed, 0 failed, 0 skipped. Added 78 admission
  cases/properties relative to preserved Phase 5 head 6931b56, including 64 focused
  integration cases and two generated threshold/repaired-replay properties.
- Coverage: 98.55% overall, 100.00% safety and runtime, 97.85% residual learner.
- Ruff check passed; ruff format --check: 66 files formatted; strict mypy:
  no issues in 26 source files; git diff --check passed.
- Clean-clone build produced 0.1.0a2 wheel and sdist. A separate new venv installed
  the wheel with --no-deps; isolated Python imported every module, verified version,
  exercised unknown/inactive control rejection and eligible shadow baseline identity.
- Working trees were clean after verification; build/venv/coverage files are ignored.
- The final completion-record commit changes only this document. Code, tests,
  examples, metadata and CI are identical to the validated clone. Final head checks
  are inspected before the user-facing report and linked from PR #2.
- PR #2 remains Draft with main base 05b0162. Its retarget initially retained only
  the 21 existing Phase 5 files; final diff includes the required admission contracts
  and tests, with no duplicated bootstrap scaffolding. This hardening changes 26
  files; PR #2 contains 33 changed files in total. Existing history is preserved.
- Implementation and validation do not change the user's HOLD merge-readiness
  assessment. No Ready transition or merge of PR #2 is performed.
