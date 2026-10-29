# H6 identifiability and uncertainty

## Structural statement (LINEAR callback only)

For exact pre-PID callback response u, actual callback input a, and independently
observed normalized state q, u=a/F+Cq+b0 has a unique joint solution precisely
when [a,q,1] has column rank 3 and the recovered acceleration slope is positive.
The inverse model uses [u,q,1]; its q coefficient is -F*C, so C=-beta_q/beta_u.
Both are conditional controller-domain models, not a physical plant calibration.

If q is latent, the same a=1.2,u=.6,F=2.4 can be explained by
C=.2,q=.5 or C=.4,q=.25. Applied torque/achieved acceleration alone cannot
distinguish these explanations. If a and q are collinear, full state observation
still does not identify all coefficients. Numerical SVD rank is an algebraic/
floating-point diagnostic, not an empirical condition-number acceptance policy.

- All q=0: FRICTION_UNOBSERVABLE_IN_DEADZONE.
- Single sign: FRICTION_EXCITATION_INSUFFICIENT (conservative policy, even if
  varying positive q could in principle give algebraic rank).
- Branch model without q=±1: BRANCH_REQUIRES_SATURATED_STATES.
- Rank deficient: NONIDENTIFIABLE_DESIGN_MATRIX.
- Unknown applied geometry/cohort/delay: CONTEXT_UNAVAILABLE.
- A geometry change closes the window; changing mode/installed F/C/steer ratio/
  custom setting/delay also closes it. Duplicated source times are not new evidence.

Branch intercepts are b_plus=b-F*C and b_minus=b+F*C. Their separation is 2FC,
not 2C. Joint within-branch slope needs excitation within each branch.
Unequal sample counts do not require equal weighting to recover an ideal
noiseless model; directional asymmetry instead invalidates a unique scalar-C
interpretation. The synthetic asymmetric response yields a branch average .22,
not an optimal parameter recommendation.

## Factor dependence

Known F is synthetic oracle input only. The unknown-F fits estimate F/C jointly
under rank/exogeneity assumptions. A supplied wrong F=3 rather than 2.4 gives
C≈.217877 in the correlated-state fixture. The joint fit returns .17 instead.

For fixed observed q, regression with intercept gives

C(F)=Cov(q,u)/Var(q) - Cov(q,a)/(F*Var(q)).

It is affine in 1/F. Evaluating a declared positive F interval's two endpoints
therefore gives exact extrema for this deterministic fitting sensitivity.
F∈[2.1,2.7] gives approximately [.135802,.196599] in that fixture. This is NOT
a confidence interval, a posterior, an uncertainty guarantee, or vehicle-safe
bounds; it omits signal/model uncertainty. H5 factor empirical qualification
is still blocked. Installed F telemetry would supply context, not qualification.

## EIV / state uncertainty

Noise in a biases the controller-domain regressor; noise in u biases the inverse
regressor. Noisy desired/actual state produces uncertain q; threshold/deadzone
and clipping make that error nonlinear and potentially correlated with a/u.
The q-noise fixture gives C≈.173143 instead of .17; it need not be simple
attenuation. Exact-q oracle and measured noisy-q cases are separately recorded.
OLS independence/exogeneity does not hold automatically in a closed loop;
these deterministic stress tests do not correct endogeneity or prove consistency
for driving logs. No statistical SE/route CI is fabricated.

## PID and target stage

Raw callback ff is before PID k_f, feedback and clipping. Source PID computes
f=k_f*ff, p=error*k_p, d=error_rate*k_d, integrates/clamps i, then clips the sum.
LatControlTorque returns its negative; actuators/vehicle limits/delay are later.
The published f is not necessarily raw ff (zero k_f is not invertible).

The toy PID contribution .23*q+.05*a makes a naive total-torque fit report
C=.40 and F≈2.142857 instead of .17 and 2.4. Feedforward-only and subtraction
recover the ideal toy, but subtraction is valid only for this unclipped,
synchronized synthetic decomposition. It cannot undo clipping, actuator limits,
or dynamic lag in real data. Low-error selection can eliminate the very q
excitation needed for C; no real jerk/error selection threshold is justified
(SELECTION_THRESHOLD_UNJUSTIFIED). A joint dynamic model needs separately
identified plant, state, noise and timing; H6 does not qualify one.

## Exactly one current-signal verdict

NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS.

Conditional status:
FRICTION_CONTROLLER_MODEL_IDENTIFIABLE_WITH_REQUIRED_SIGNALS, LINEAR-only,
full-rank, exact-state, correct-stage, exogenous/synthetic scope.
Joint status: FACTOR_FRICTION_JOINT_IDENTIFIABILITY_CONDITIONAL_FULL_RANK_ONLY.
Neither status qualifies an empirical F or C.

ControllerFrictionEstimate carries estimand, mode, factor dependence, estimate,
numerical uncertainty diagnostic, status, completeness, geometry digest, and
immutable false candidate/application/runtime/owner-proposal flags. Its scalar
estimate is not consumable by H4 or PR9.
