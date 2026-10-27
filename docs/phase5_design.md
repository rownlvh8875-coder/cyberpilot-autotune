# Phase 5: Deterministic shadow residual statistics

Scope approved by the user: the next small shadow-only learner change. Preserve
Phase 0-4 invariants; no application, persistence, real replay ingestion, vehicle
adapter, vehicle constants or new runtime dependencies. Base: 5d67bc6. PR #1 is
still open, so this change uses a separate stacked branch and PR against it.

## Approach and alternatives

Use a bounded, single-context EWMA of desired minus measured curvature (1/m),
with an EWMA of absolute innovations as a consistency indicator. Exclude samples
beyond an explicit absolute residual cutoff rather than clipping observations.
Sliding windows retain unnecessary raw observations; unbounded/context-indexed
state makes eviction and stale evidence harder to reason about. EWMA requires
only one fixed-size state. This is a research heuristic, not a controller model.

All configuration is explicit: alpha in (0,1], minimum_samples >=2,
maximum_samples >= minimum_samples, maximum_source_age_s >=0, maximum_sample_gap_s
>0, maximum_state_age_s >= maximum_sample_gap_s, maximum_absolute_residual_inv_m
>0, consistency_scale_inv_m >0, mean_deadband_inv_m >=0 (below residual cutoff),
and nonzero signed parameter_delta_per_inv_m. No vehicle defaults exist.
The target ParameterSpec supplies identity/units only; bounds/step/rate remain
the gate's responsibility. The caller must supply a justified residual-to-target
coefficient. The shipped example is explicitly synthetic and not a calibration.

## State and computation

Retain at most one context, exact target baseline, window-start time, capped
sample count, mean residual and mean absolute innovation. A separate sequence/
timestamp high-water cursor survives evidence resets. No observation history or
context cache is retained. Statistics are exposed as a frozen validated snapshot.

For residual r, mean m and absolute innovation d:

- First admitted sample: m=r, d=0, n=1.
- Later: m'=(1-alpha)*m + alpha*r;
  d'=(1-alpha)*d + alpha*abs(r-m); n'=min(n+1, maximum_samples).
- confidence=min(1,n/minimum_samples)*max(0,1-d/consistency_scale_inv_m).

Confidence measures support and consistency only. It is not a calibrated
probability, correctness estimate or evidence of improved driving.
After minimum_samples, emit at most one proposal when abs(m)>mean_deadband_inv_m:
candidate=baseline + parameter_delta_per_inv_m*m. Do not clip to bounds/step/rate.
Bind proposal to current timestamp/context/baseline and a fixed learner version.
The Safety Gate may reject any candidate, including low confidence or limits.

Use exact rational intermediates and round retained statistics to finite floats
once per sample. Reject arithmetic that cannot be represented finitely; do not
emit NaN/infinity or silently coerce baseline. This avoids overflow in residual
subtraction and EWMA innovations. No random source, clock or IO is used by learner.

## Resets and ordering

Invalid contract construction raises ValidationError after clearing evidence.
Invalid source, missing required signals/target baseline, age violation, override,
saturation, outlier or unrepresentable arithmetic clear evidence and emit nothing.
Non-increasing sequence or timestamp clears evidence, retains high-water cursor
and emits nothing. Admitted excluded frames consume their cursor.
Context or target-baseline changes, gap >maximum_sample_gap_s, or window age
>maximum_state_age_s start a fresh window with the current valid sample. Exact
boundaries are inclusive. Public reset() clears evidence, preserving ordering;
construct a new learner for a new sequence/time domain.

Runtime has an optional ResettableLearner Protocol. Rejected pre-admission and
post-work frames reset capable learners, including malformed proposals and clock
regression, without changing existing stateless learners. A reset error is caught
by the engine's outer boundary and latches INTERNAL_ERROR. Internal faults retain
the existing health latch; use a new/reset learner when replacing an engine.
OFF performs no observe/reset calls. One engine owns one learner instance.

## Evidence and acceptance

Known synthetic streams must prove the formulas, minimum samples, outlier/noise
behavior, every reset, exact time boundaries, capped memory/count, immutable
statistics, explicit conversion sign, no clipping and deterministic fresh runs.
Integration must prove invalid/stale frames actually clear warm state, both modes
retain baseline, eligible proposals remain counterfactual, and reset exceptions
cannot escape. Property tests cover generated streams and extreme finite values.
Existing AST, offline, import, coverage, type/build/wheel and CI checks remain.
No source code is ported or copied; the pinned Phase 0 audit remains unchanged.
