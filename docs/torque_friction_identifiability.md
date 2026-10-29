# H5 controller friction versus native residual spread

Controller C is a normalized-torque magnitude. Native
native_residual_spread_coefficient is a different mathematical statistic; its name
is retained in every report. No estimate here is recommended for Params or a UI.

## Source equation and inverse branches

For compensation enabled, the actual imported helper implements

    q(e;d,t) = 0                    when -d < e < d
             = clip(e/t,-1,1)      otherwise, t>0
    h(e) = C*q(e;d,t),             u = a_c/F + h(e).

At the exact deadzone boundary the original error is interpolated; d is not
subtracted. Disabled compensation returns0. The inverse observation submodel is
y = F*u + b - F*C*q + epsilon_y. Saturated states q=+1/-1 give two branches with
intercepts b-F*C and b+F*C. Occupancy changes their mixture; a single constant
state can be absorbed entirely into the nuisance intercept.

## What native spread measures

For positive fitted slope s, rotation gives (y-s*x)/sqrt(1+s*s). Thus

    K_native(s) = 1.5/sqrt(1+s*s) * sqrt(Var(
        (F-s)*u - F*C*q + epsilon_y - s*epsilon_x)).

b cancels from this standard deviation but can affect the fitted s through the
uncentered [x,1,y] objective. K uses population standard deviation, denominator N.
The source's1.5 '~85% coverage' comment is empirical intent, not a physical proof.

Only for projection at true s=F and friction-state/noise independence does this
reduce to

    K(F) = 1.5/sqrt(1+F*F) * sqrt(
        F*F*C*C*Var(q) + sigma_y^2 + F*F*sigma_x^2 - 2*F*sigma_xy).

Without independence an additional -2*F*C*Cov(q,epsilon_y-F*epsilon_x) term remains.
The raw fitted slope need not equal F; the restricted symmetric-cloud analytic
prediction is tested separately. No universal transform follows when occupancy,
noise covariance, applied/observed equivalence and true F are unknown.

## Executed counterexamples

All entries below are synthetic, not driving data or vehicle ranges.

| True F | True C | Condition | Raw fitted s | K_native |
|---:|---:|---|---:|---:|
|0.5|0.1|balanced saturated states|0.510162|0.066946|
|1|0.1|same states/excitation|1.051249|0.104733|
|2|0.1|same states/excitation|2.162440|0.130007|
|4|0.1|same states/excitation|4.378394|0.139446|
|2|0.1|constant positive state|2.000000|approximately0|
|2|0.1|half-amplitude excitation|2.673975|0.119071|
|2|0.1|x+y noise std .02|2.152995|0.140770|
|2|0|x+y noise std .02|1.985806|0.035008|

For F=2,C=.1 balanced, absolute coefficient bias is .03000687 and relative bias
+30.0069%. C=.05 gives K=.06654967 (+33.0993%). Relative bias is undefined/null
at C=0, not infinity or an invented zero. Within a fixed declared toy distribution
K increases with the tested C levels; that local monotonicity does not establish
identity or monotonic recovery across changing excitation/noise/F.

Deadzone occupancy can give K approximately0 despite C=.1; partial threshold
occupancy gives K=.02234082. Constant roll bias moves intercept in the ideal
affine case; varying roll contaminates spread without any controller friction.
Lag mismatch likewise produces positive K with C=0. A finite sample cloud is not
a calibrated distribution of physical friction.

## Existing native test gap

The pinned offset test generates y=F*u+b+get_friction(error), rather than the
inverse callback's y=F*(u-C*q)+b. It also imports the separate lateral.py helper.
It tests offset and explicitly leaves factor/friction checks TODO. Those source
facts explain a coverage gap; neither the test's noisy stability nor its TODO
is qualification evidence. The H5 oracle is independently implemented from the
actual callback relation, not copied from this test or from the estimator.

## Separate verdict

FRICTION_ESTIMAND_DEFINED.
FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION.

The counterexamples disprove a universal direct identity between native spread
and C in the declared model class. They do not prove that friction is impossible
to identify with additional observations, calibrated errors and a new estimator.
No friction application bridge, bounds, candidate or native estimator change is
included. Recommended next single task: friction estimator redesign / identifiable
friction model, under a separately specified observation/experimental contract.
