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

reset() deletes evidence only, preserving sequence/time high-water. It is valid
within the same monotonic stream. A restarted sequence/time domain requires a
new learner instance (and an engine for that new domain). OFF does not call clock,
admission, observe or reset. Effective parameters always equal trusted baseline.

## Test-first implementation and completion checklist

- [x] Contract/config validation RED then GREEN; migrate synthetic callers.
- [ ] Pre-call active/speed/veto/call-count tests RED then GREEN.
- [ ] Rejected-frame replay, exact minimum, reset/high-water and OFF tests.
- [ ] Standalone learner defense-in-depth, incompatible policy, numeric properties.
- [ ] Independent review and full regression, lint/format/mypy/coverage/build/wheel.
- [ ] Push normally, inspect full CI at final head, keep PR #2 Draft/HOLD.

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
