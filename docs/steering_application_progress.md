# Steering application implementation plan and ledger

Plan identity: steering-only shared bounded application, approved 2026-10-29.
Base: b24ef18e4270af5ab4f731aca31cf95f4f4b0cce.
Branch: feat/steering-bounded-application.
Spec: [accepted design](steering_application_design.md).

## Constraints and rulings

- Preserve PR #8 at e4361678ed176cbd7c0bb6f838d3daa7174caf22. Reuse its
  isolated worktree on a new branch from main; no changes to its branch/ref.
- No longitudinal parameters or behavior. Initial family is steering torque
  response factor/friction only; names are selectors, never vehicle permission.
- No new learner/fit: reuse CyberPilot research/evidence through an explicitly
  unqualified neutral bridge. Do not turn offline AUTO_ALLOWED into authority.
- Existing OFF/SHADOW contracts, engines, adapter and safety algorithms stay
  unchanged. Application is a separate explicit capability, not a shadow mode.
- Ruling: caller-injected synchronous target and independent owner authorizer are
  mandatory. No default target, authorizer, bounds, rate, deadline or authority.
  Their trusted implementations are a separate integration boundary.
- Ruling: do not add a concrete Carrot writer before units/owner arbitration are
  proven. Existing torqued and custom-torque behavior prevent safe blind setter
  reuse. Report this as a real-integration gate, not as completed vehicle tuning.
- No Params, persistence, network, threads/processes, vehicle install/run,
  private datasets, production source edits or upstream PR.

## Tasks

1. [x] Source audit and approved steering-only design; clean baseline regression.
2. [x] TDD immutable steering-only policy/request/authorization/target contracts.
   Reject longitudinal IDs, incomplete policy, unknown states and malformed values.
3. [x] TDD neutral CyberPilot research bridge; preserve qualification blockers.
4. [x] TDD single-owner compare-and-swap, readback and actual step/rate accounting.
   Consume rejected attempts; no automatic clipping or retry repair.
5. [x] TDD override/staleness/disarm/watchdog rollback, uncertain writes, foreign
   ownership, rollback failure and sticky fault behavior. Never invent baseline
   success when readback/ownership is unknown. Document synchronous watchdog limits.
6. [x] Property, dependency, side-effect and integration tests; retain old goldens.
7. [x] Full lint/format/type/coverage/build and fresh installed-wheel checks.
8. [ ] One fresh independent full-diff review, correction/reverification if needed;
   append-only push and separate Draft PR with exact-head CI. No merge.

Each implementation task uses a failing behavioral test before the minimal code.
Record measured checks and design decisions below as work progresses.

## Execution evidence

- Repository is clean at the new branch base. Prior PR #8 is preserved remotely.
- Public CyberPilot interface hashes were verified for four selected modules;
  no source bodies or private results copied. Original audit pin remains unchanged.

- RED: absent application contracts (23 failures), absent coordinator (33), and
  absent CyberPilot bridge (11). Behavioral RED/GREEN also covers timeout masking,
  hold expiry during authorization, no-change owner conflict, rejected timestamp
  high-water, malformed attempt repair, authority exceptions and rollback outcome.
- Current full tests after review corrections: 889 base / 1026 native actual-schema
  combined; 0 failures or skips. Baseline was 738 / 875. New tests are synthetic only.
- Native coverage: overall 99.02%, application 99.63%, coordinator 99.36%;
  pure receipt contract and safety 100%. Ruff/format and mypy pass (45 source files).
  Base environment overall coverage is 97.54%; native compatibility covers the
  optional schema-loading paths absent from a base install.
- Ruling: proposal IDs are session-local 32-hex encoding of attempt sequence.
  Coupled with persistent-in-session high-water, bounded ID eviction cannot
  revive a rejected identity under a new counter. Metadata/evidence has its own hash.
- Ruling: rollback uses a separate caller-supplied deadline. An observed baseline
  does not hide malformed acknowledgements, exceptions, missing timing or overruns;
  recovery_reason exposes these and latches FAULTED. No unknown owner is overwritten.
- Ruling: constructor capability checks inspect required callable methods only;
  no target/authority/clock method is invoked. Injected implementations remain trusted.

- Wheel/sdist build passed in an empty temporary output directory. Fresh base
  wheel imports all 44 discoverable submodules without openpilot, verifies typed
  optional-dependency rejection, synthetic commit/readback/rollback and four old
  goldens. A separate actual-schema wheel verifies unchanged generic/Hyundai
  read-only mappings and the same synthetic application path. No vehicle writer ran.
- Initial independent review at 2f8f138c0cd4ca7cbb4df86a647653f082e29e8c
  reported Critical 0 / Important 4 / Minor 0. Reproduced RED cases cover hold
  expiry masked by override/authorization denial, watchdog callback overruns,
  stale grants after callbacks, legitimate grants issued at callback completion,
  and idle time incorrectly counted as rollback duration. The corrected code
  refreshes clocks at each boundary, gives known deadlines priority, and anchors
  recovery at its own entry. Regression tests also exercise both steering selectors.
- Corrected wheel/sdist and two new fresh environments passed: base imports all
  44 discoverable modules and rejects missing optional dependencies; native wheel
  verifies generic and four Hyundai False/True schema mappings. Both verify the
  synthetic apply/rollback and all four unchanged replay goldens. Final exact-head
  review confirmation and remote CI are required before this task is reported done.
- Application coverage 99.63% includes branches; the coordinator is 99.36%.
  The remaining uncovered paths are the absent-last-clock recovery branch and
  grant expiry after a capability returns. No internal-state fabrication is used
  solely to increase coverage.
