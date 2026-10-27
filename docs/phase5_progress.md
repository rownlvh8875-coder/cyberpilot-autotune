# Phase 5 progress

Base: 5d67bc640939adbc888b19cbb6264dcf6b0cc5ac.
Branch: feat/shadow-residual-statistics.
Spec/plan: phase5_design.md and phase5_plan.md.

- Baseline clean: 183 tests passed. PR #1 remains open/draft and unmerged.
- Inline implementation; no work is performed on main or reference repositories.
- Existing dedicated checkout plus separate feature branch provides isolation.
- Pre-flight: learner consumes existing immutable contracts; runtime reset is
  optional to preserve stateless Learner compatibility. No signature conflict.
- Design decisions: one context/window, bounded EWMA plus absolute innovations,
  explicit conversion coefficient and heuristic confidence; no vehicle defaults.
- Source evidence remains pinned to 588d6b21c21089065a7d9165d6e7a438e8aa6297.

## Task 1

- RED: tests/unit/test_residual.py failed because core.residual did not exist.
- GREEN: 54 learner unit cases plus two Hypothesis properties; full suite 239 passed.
- Formula values checked against hand calculations. Generated streams proved
  bounded count/statistics, deterministic output, finite candidates and no input
  baseline mutation. Extreme subtraction/innovation/candidate overflow excluded.
- Ruff lint/format and strict mypy passed. No third-party runtime dependency added.

## Task 2

- RED: pre-admission invalid source retained warmed sample_count=3 in the old
  engine, demonstrating the missing lifecycle boundary.
- GREEN: optional ResettableLearner.reset() is invoked for SHADOW rejection paths;
  stateless learners remain compatible. Reset exceptions become INTERNAL_ERROR
  with the existing health latch. OFF never observes or resets.
- 16 real learner/engine integration cases passed; full suite 255 passed.
- Candidate bounds/step/rate remain independently enforced by SafetyGate.

## Task 3

- Synthetic example RED: script did not exist. GREEN: two fresh processes produce
  identical JSON records; minimum samples, accepted candidate and override reset
  are visible while every effective mapping equals baseline.
- Seven guarded import/execution subprocesses now cover both packaged learners,
  real SHADOW eligibility, OFF and optional reset with file/network/thread denial.
- Current full regression: 257 passed; 98.02% overall branch-inclusive coverage,
  safety 100.00%; learner 97.67%. Ruff lint/format and strict mypy passed.
- Version advances to 0.1.0a1 to distinguish the new research API; no release is
  published. Architecture, safety, README and roadmap describe actual Phase 5 scope.
- Independent read-only review: no Critical, Important or actionable Minor findings.
  Reviewer ran 70 learner unit/runtime cases and additional boundary/replay/overflow
  probes. No source changes were requested and no deferred minors remain.
- Lifecycle decision retained: unexpected internal faults may leave learner
  statistics in memory while permanently latching engine health; no reset callback
  is called from the exception handler. Use a fresh/reset learner when replacing
  that engine. Recoverable rejections do clear evidence. This avoids a second
  callback failure escaping baseline fallback; violating ownership can reuse stale
  evidence, so learner instances must not be shared across engine lifecycles.
- Review exclusions match scope: physical coefficient validity, confidence
  calibration, vehicle suitability/performance and hard deadlines require evidence
  beyond this synthetic milestone; persistence/integration/application remain future.
- Wheel/sdist 0.1.0a1 build succeeded. A new separate venv installed the wheel
  with --no-deps and `python -I` imported all modules including core.residual;
  installed version was verified as 0.1.0a1.
- CI retains the four platform/Python combinations, adds residual learner coverage
  >=95% and imports the new learner from the installed wheel.
