# Synthetic replay progress

Base: 26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0.
Branch: feat/deterministic-replay. Baseline: 335 tests passed, working tree clean.
Plan: replay_plan.md; existing replay_spec.md defines the approved future scope.

- PR #1 is merged; PR #2 remains Draft/HOLD. No merge or retarget of PR #2 is
  authorized by this replay task. Use a separate stacked PR for the new harness.
- Persistence and actual vehicle/log integration remain unauthorized.
- Pre-flight: schema uses existing immutable contracts/configs; runner creates fresh
  OFF/SHADOW engines and uses the existing admission boundary. No core signature
  changes or learner algorithm changes are needed.
