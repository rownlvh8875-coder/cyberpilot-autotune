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
