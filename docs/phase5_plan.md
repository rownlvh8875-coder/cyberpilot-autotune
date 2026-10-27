# Shadow residual statistics implementation plan

> Agent workflow: execute inline using executing-plans, test-driven-development
> and verification-before-completion. User authorized implementation of the next
> learner step; do not introduce another approval checkpoint.

Goal: one deterministic, bounded, proposal-only residual learner in SHADOW.
Spec: phase5_design.md; Phase 0-4 contracts continue to apply.
Tech stack: Python >=3.12.3,<3.13, standard library; existing dev tools and CI.

## Review focus

- Invalid/stale frames skipped by engine must still clear warm learner evidence.
- Reset must not allow replayed/out-of-order frames to manufacture sample counts.
- Context/baseline switches and exact age/gap boundaries must restart correctly.
- Extreme finite numbers must not overflow into proposals or mutate baseline.
- Confidence must describe a heuristic; limits belong to gate, never implicit clipping.

## Task 1: Residual learner

Files: core/residual.py; tests/unit/test_residual.py;
tests/property/test_residual_properties.py.

Interfaces: ResidualStatisticsConfig (explicit fields in spec), immutable
ResidualStatistics snapshot; ResidualStatisticsLearner(parameter: ParameterSpec,
config: ResidualStatisticsConfig), observe(snapshot)->tuple[TuningProposal,...],
reset()->None, statistics property->ResidualStatistics|None.

- [ ] Write tests for formulas, thresholds, configuration, invalid/missing data,
  override/saturation/outlier exclusion, resets, ordering, bounds independence,
  extreme arithmetic, capped state and immutable results.
- [ ] Run tests and observe missing-feature RED.
- [ ] Implement one-window EWMA using rational intermediates and finite outputs.
- [ ] Add generated stream determinism and extreme-value properties.
- [ ] Run full pytest, ruff lint/format, strict mypy and git diff --check; commit.

## Task 2: Reset integration

Files: core/learner.py; runtime/engine.py; tests/integration/test_residual_runtime.py.
Produces optional runtime-checkable ResettableLearner.reset()->None; existing
Learner.observe signature and stateless learners remain compatible.

- [ ] Warm real learner, inject invalid/stale/late frames and prove preexisting
  engine wrongly retains evidence (RED). Include reset throwing and OFF no calls.
- [ ] Add optional reset to shadow rejection paths within outer exception boundary.
- [ ] Prove eligible, out-of-bounds, step/rate, override/saturation and unknown
  candidates keep original baseline. Run all checks and commit.

## Task 3: Example, docs and completion

Files: examples/residual_shadow.py, README.md, core/no_op.py docstring,
docs/{architecture,safety_contract,roadmap,progress}.md and phase5_progress.md.

- [ ] Run synthetic learner example through SHADOW, printing statistical evidence,
  proposal/gate decision and effective==baseline; no scripted production learner.
- [ ] Extend guarded import/execution tests to cover stateful learner in both modes.
- [ ] Document formulas, resets, scope, limitations and actual verification results.
- [ ] Obtain independent read-only whole-branch review; substantive fixes use RED/GREEN.
- [ ] Revalidate editable install, tests, coverage >=85%/safety >=95%, lint/format,
  mypy, sdist/wheel and isolated wheel import; commit and push feature branch.
- [ ] Create separate stacked Draft PR against feat/bootstrap-shadow-core; preserve
  PR #1/main. Inspect final CI and report actual results in Korean.
