# Identifiable Friction Model Redesign 결과

## PR #14 / branch provenance

PR14 merged 2026-10-29T08:01:48Z with exact-head guard
d705622e256b47506752e3e2beb131765c8a0136 and merge commit
43ca6761749e71ec575906f099b02386bc76d994.
Parents: 3ded3dec7011f24b7f1195f0c73bbed290891ff3 and that H5 head.
Merge/head trees equal; H6 started from this new origin/main on
research/friction-identifiable-model. Append-only commits, no force/rebase/
squash/admin bypass. PR8/PR9 are not changed.

First H6 commit de42ce3ad6d7b8aa90133898a04685432972ec1a freezes estimands,
four models, selection rules, geometry, observation requirements and scenarios,
before candidate implementation 274ca24 or any committed comparison results.
Policy canonical SHA-256:
503c1f9d07c4dda45edf55693ad4b25fde89f8f751998cef9cff8b84565cdc8c.
The history audit checks the first commit's exact three-file set, policy identity
and all 242 pre-H6 files except the deliberately extended CI workflow.
No scientific selection weights or scenarios were changed after results.

## Sources / estimand / selection

Exact pins R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55 and
C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 are separately bound; current
carrot-wip was unchanged at H6 start. 30 source files / 52 file/symbol ranges
are file/blob/range-hash pinned. Isolated helper and VM equations match source;
no native service, controller, Params, driving log or data artifact is loaded.

Estimand: conditional controller-domain response coefficient C on independently
observed q in u_cb=a_cb/F+Cq+b0, LINEAR callback scope only.
K=1.5*std(perpendicular residual) remains a different diagnostic, never a C
conversion. Installed C is context; explicit h=C_installed*q reconstruction
is IMPLEMENTED_COEFFICIENT_CONSISTENCY_ONLY, not optimal physical friction.

**Exactly one selection: NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS.**
The frozen source-feasibility/correct-stage/independent-response/cohort gate
takes precedence over synthetic fit accuracy. Future exact signals permit
conditional algebraic identification, not empirical/application readiness.

## Four-family comparison

| Axis | Controller domain | Inverse | Branch separation | Explicit term |
|---|---|---|---|---|
| Structural | rank[a,q,1]=3 | rank[u,q,1]=3; C=-beta_q/beta_u | within-branch slope + ±1 occupancy | rank[q,1]=2 |
| Required signals | raw ff, actual callback a,q | same | same, saturated states | independent h,q |
| F dependence | joint reciprocal slope or supplied F | C divided by fitted F | 2FC separation; joint/supplied F | none for term consistency |
| Noise sensitivity | a/q EIV | u/q EIV and ratio | branch/noise imbalance | q EIV; h provenance dominates |
| Closed-loop bias | not solved by OLS | not solved by OLS | selection/feedback bias | circular if h built from installed C |
| Excitation | both signs, noncollinear a/q | both signs, noncollinear u/q | ±1 and within-branch u spread | nonzero varying q; both signs policy |
| Mode compatibility | conditional LINEAR | conditional LINEAR | conditional LINEAR | call-site-specific; NN override has different stage |
| Complexity | low | low + coefficient ratio | moderate; transition exclusions/asymmetry | low math, high telemetry burden |
| Source grounding | exact linear ff equation | rearrangement, sign explicit | saturated q consequence | helper's separate contribution |
| Current route feasibility | missing raw ff/q/cohort | same gaps | same + excitation | not published; installed-C term not independent truth |
| Upstream friendliness | read-only atomic receipt proposal | same receipt requirements | more selection metadata | extra read-only contribution/state fields; no H6 schema patch |

## All preregistered synthetic comparisons

Synthetic mathematical truth F=2.4,C=.17,b0=.04 except named perturbations.
Values are diagnostics, NOT proposed vehicle settings. K below is native-style
perpendicular spread over synthetic total-torque/acceleration, not a new C
estimator. Explicit columns reconstruct a constructed helper term and are
consistency-only even when numerically exact. Complete input hashes, rank,
condition, occupancy, rich estimand/context/authority metadata and all results
are in evidence/friction_model_synthetic_results.json.

| Scenario | Controller | Inverse | Branch | Explicit consistency | K diagnostic |
|---|---|---|---|---|---:|
| zero_friction | C=-0.000000, F=2.400000 | C=-0.000000, F=2.400000 | C=-0.000000, F=2.400000 | C=0.000000, F=— | 0.000000 |
| symmetric | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.166439 |
| asymmetric_occupancy | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.165374 |
| directional_asymmetry | C=0.219988, F=2.400951 | C=0.220017, F=2.398673 | C=0.220000, F=2.400000 | C=0.220000, F=— | 0.216947 |
| deadzone_only | FRICTION_UNOBSERVABLE_IN_DEADZONE | FRICTION_UNOBSERVABLE_IN_DEADZONE | FRICTION_UNOBSERVABLE_IN_DEADZONE | FRICTION_UNOBSERVABLE_IN_DEADZONE | 0.000000 |
| transition_only | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | BRANCH_REQUIRES_SATURATED_STATES | C=0.170000, F=— | 0.117686 |
| single_sign | FRICTION_EXCITATION_INSUFFICIENT | FRICTION_EXCITATION_INSUFFICIENT | FRICTION_EXCITATION_INSUFFICIENT | FRICTION_EXCITATION_INSUFFICIENT | 0.000000 |
| collinear_design | NONIDENTIFIABLE_DESIGN_MATRIX | NONIDENTIFIABLE_DESIGN_MATRIX | NONIDENTIFIABLE_DESIGN_MATRIX | C=0.170000, F=— | 0.000000 |
| compensation_disabled | FRICTION_UNOBSERVABLE_IN_DEADZONE | FRICTION_UNOBSERVABLE_IN_DEADZONE | FRICTION_UNOBSERVABLE_IN_DEADZONE | FRICTION_UNOBSERVABLE_IN_DEADZONE | 0.000000 |
| known_factor | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.159089 |
| wrong_factor | C=0.217877, F=3.000000 | C=0.217877, F=3.000000 | C=0.225631, F=3.000000 | C=0.170000, F=— | 0.159089 |
| joint_factor | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.159089 |
| factor_interval | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.159089 |
| pid_contamination | C=0.400000, F=2.142857 | C=0.400000, F=2.142857 | C=0.400000, F=2.142857 | C=0.170000, F=— | 0.384166 |
| feedforward_only | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.384166 |
| pid_subtracted | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=2.400000 | C=0.170000, F=— | 0.384166 |
| x_noise | C=0.168932, F=2.407728 | C=0.169101, F=2.394473 | C=0.166606, F=2.384087 | C=0.170000, F=— | 0.166439 |
| a_noise | C=0.169379, F=2.397541 | C=0.169407, F=2.395301 | C=0.168612, F=2.387269 | C=0.170000, F=— | 0.167785 |
| q_noise | C=0.173143, F=2.402249 | C=0.173147, F=2.401969 | C=0.170000, F=2.400000 | C=0.173169, F=— | 0.166439 |
| total_noise | C=0.171531, F=2.407774 | C=0.171708, F=2.391678 | C=0.167571, F=2.348261 | C=0.173169, F=— | 0.167785 |
| delay_mismatch | C=-0.034674, F=5.036774 | C=0.018168, F=1.089617 | C=0.022345, F=1.215903 | C=0.170000, F=— | 0.166439 |
| roll_mismatch | C=0.120000, F=2.400000 | C=0.120000, F=2.400000 | C=0.120000, F=2.400000 | C=0.170000, F=— | 0.117379 |
| geometry_change | GEOMETRY_CONTEXT_CHANGED | GEOMETRY_CONTEXT_CHANGED | GEOMETRY_CONTEXT_CHANGED | GEOMETRY_CONTEXT_CHANGED | 0.166439 |
| mode_change | CONTEXT_CHANGED | CONTEXT_CHANGED | CONTEXT_CHANGED | CONTEXT_CHANGED | 0.166439 |
| saturation | SATURATION_OR_OVERRIDE | SATURATION_OR_OVERRIDE | SATURATION_OR_OVERRIDE | SATURATION_OR_OVERRIDE | 0.154115 |
| driver_override | SATURATION_OR_OVERRIDE | SATURATION_OR_OVERRIDE | SATURATION_OR_OVERRIDE | SATURATION_OR_OVERRIDE | 0.166439 |

Known-F is synthetic oracle input, never a qualified real F. Wrong supplied F
biases C; joint full-rank fitting recovers the ideal model. The correlated-state
F interval [2.1,2.7] maps to C sensitivity [.135802,.196599], not a statistical
CI or safe bounds. Noisy q, regressor noise, delay/roll mismatch and PID feedback
are separately tested. All-zero/single-sign/collinear, saturation/override and
context-change rejection paths are explicit. Branch transitions cannot be
silently labeled deadzone or treated as ±1.

Directional asymmetry produces model-dependent averages rather than a unique
physical scalar C. Exact ideal recovery does not solve feedback endogeneity,
plant hysteresis, measurement precision, model misspecification or route
generalization. No empirical standard errors, route LOO, or data reuse after
model selection are claimed.

## Geometry and observation outcome

CenterToFrontRatio is GEOMETRY_CONTEXT_PARAMETER. c213 binds actual static CP
geometry; f5e4 has a dynamic Params -> paramsd -> liveParameters -> controlsd
VM path. Raw Params zero is VEHICLE_DEFAULT, never physical zero. Unknown CP/
applied evidence remains unavailable, not a fabricated ratio. The immutable
context binds source, vehicle, geometry, stiffness, effective SR, SR-rate/
CustomSR, mode/custom mode, delay, installed F/C, generation and cohort.

Coherent stiffness redistribution makes the tested steady slip/curvature/roll
mapping invariant in ratio; dynamic A/B transient responses still differ.
GEOMETRY_CONTEXT_MATERIAL is scoped to this generic toy transient, not any
actual car or vehicle-safe range. Torque windows with changed geometry reject/
close the epoch; simultaneous geometry/SR/SAD/F/C writer changes cannot be
pooled. See torque_geometry_context.md for cancellation algebra and sensitivity.

The read-only contract and three-profile gap matrix are complete designs:
raw ff/q/per-call helper inputs and full applied context/gain/timing receipts
are still missing. Float32 desired/actual telemetry can at most approximate the
original LINEAR friction input; published PID f is scaled by k_f. observation-v2
is R-pinned and preserved; it is not silently upgraded to f5e4 geometry support.
No real low-error/jerk/condition cutoff is invented.

## Verification / execution ledger

- Task 1: preregistration de42ce3 before code/results.
- Task 2: absent-package and targeted missing-q/report/branch-admission tests
  observed RED; implementation made each GREEN. Tests first committed 37575ae.
- Task 3: independent generator/candidates 274ca24, then explicit immutable
  ControllerFrictionEstimate metadata/authority and Hypothesis properties.
- Task 4: source/current-geometry-claim mutation test observed RED, then exact
  source manifest + isolated math audit + full 26-case reproduction GREEN.
- Targeted new suite: 102 tests, including PR virtual-merge history regression;
  388/388 statements and 98/98 branches covered
  (100% each), including all identifiability decision paths.
- Full coverage regression: 1261 passed, including the additional history test;
  overall coverage 98.15%. Source audits H2/H3/H4/H5 and H6 passed. Build and
  fresh isolated wheel passed: 64 vanilla imports, all old wheel smokes,
  H6 optional-dependency check, six H6 file hashes and all 26 research cases.
- Final-head regression/review and CI must be checked from fresh command output
  and the associated Draft PR. Do not infer CI/review
  success from this prerelease document; exact final head is the review unit.

The final publication record belongs in the Draft PR body and Korean handoff,
so no post-review local edit can silently invalidate an exact-head review.
H2/H3/H4/H5 validators, source hashes, replay golden files and owner/runtime/
application namespaces are preserved. CI only adds H6 verification and fresh
wheel execution to existing jobs; it does not remove old gates.

Ruling: reuse this dedicated cloud checkout/requested branch; no extra worktree
without authorization. Cost if wrong: less concurrent-branch isolation, mitigated
by clean baseline and complete protected-file comparison. No scientific model
preference was chosen from result appearance. No deferred implementation scope.

## Final status and blockers

- FRICTION_MODEL_REDESIGN_COMPLETE (source/math/synthetic/observability design).
- FRICTION_CONTROLLER_MODEL_IDENTIFIABLE_WITH_REQUIRED_SIGNALS
  (conditional full-rank exact-stage LINEAR synthetic scope only).
- FRICTION_OBSERVATION_CONTRACT_READY (design, not live availability).
- TORQUE_GEOMETRY_CONTEXT_BINDING_READY.
- CENTER_TO_FRONT_RATIO_CONTEXT_REQUIRED.
- FACTOR_FRICTION_JOINT_IDENTIFIABILITY_CONDITIONAL_FULL_RANK_ONLY.
- FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
- FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
- VEHICLE_APPLICATION_BOUNDS_UNRESOLVED.
- RUNTIME_FINGERPRINT_UNCONFIRMED.
- REPRESENTATION_ENCODING_UNRESOLVED.
- WATCHDOG_EXECUTION_MODEL_UNRESOLVED.
- EXTERNAL_EXECUTOR_UNQUALIFIED.
- APPLICATION_NOT_AUTHORIZED.

All candidate_generation_allowed/application_authorized/runtime_accepted/
owner_proposal_allowed flags are false. No H4 proposal or PR9 SteeringRequest.

## Recommended next single task

Read-only friction observability schema/receipt design. Required signals and
atomic installed/geometry/timing context must become independently observable
before empirical friction qualification. This next task is recommended only,
not started. No repeated GitHub/Hugging Face artifact search without a new lead.

## Preserved / non-goals

PR8 and PR9 unchanged; H4 owner code/results and all H5 code/results/validators
unchanged. No vehicle application or recommended friction/factor, Params writes,
Carrot writer, torqued/controlsd/controller/schema changes, new driving data,
holdout/evaluation access, application bridge, longitudinal or upstream PR.
