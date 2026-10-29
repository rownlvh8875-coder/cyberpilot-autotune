# H5 scientific estimands (before any fit)

Scope: offline research only. Numerical agreement, a stable slope, bucket counts,
and parameter names confer no identification or application authority. No H5
output is a SteeringRequest, PR #9 QualifiedEvidence or a parameter recommendation.

## Factor: LINEAR_MODE_LAT_ACCEL_FACTOR

For the pinned base linear callback, let u be its normalized torque coordinate,
a_c its lateral-acceleration input and F > 0 its latAccelFactor. With friction
compensation active, u = a_c/F + C q(e; d, t). F has the conditional meaning
lateral acceleration per normalized torque. It is not a global coefficient for
NN, NN-lite, GM or custom callbacks, nor a proven physical vehicle plant slope.

The source-derived center deadzone is important: q = 0 for -d < e < d;
otherwise q = clip(e/t, -1, 1), with t > 0. It does NOT subtract d from e.
The actual callback imports the five-argument helper from opendbc.car.__init__,
not the similarly named four-argument helper in lateral.py.

The torqued observation x = -carOutput.actuatorsOutput.torque is in the callback's
sign convention only under an additional binding of applied output to callback
output. The final PID, feedforward, saturation, dynamics and lag can break that
binding. y = v * calibrated_yaw_rate - sin(device_roll) * g is an observation,
not automatically a_c. A conditional observation model is

    y = F (u - C q) + b + epsilon_y,    x = u + epsilon_x.

Here b is a nuisance observation intercept. Native TLS applies SVD to [x, 1, y],
not ordinary centered two-dimensional TLS. The slope equals F on a nondegenerate
noise-free no-friction affine line; this algebra does not establish the required
observation equivalence in real evidence. The raw slope is named
linear_mode_tls_lat_accel_slope until independent qualification exists.

## Offset: TORQUED_LATERAL_ACCEL_OFFSET

b is the intercept of the above observation relation in m/s^2. It is a nuisance
parameter for factor/friction identification, not a separately enabled tuning
target. Constant roll bias or one-sided friction occupancy can confound b.
Nothing here proves that the base callback consumes its stored latAccelOffset.

## Friction: LINEAR_CONTROLLER_FRICTION_MAGNITUDE

C >= 0 is the normalized-torque amplitude in the pinned helper: h(e) = C q(e).
It is zero when friction compensation is disabled. This definition is separate
from actual mechanical friction and from the native residual coefficient.

## Native residual coefficient (separate estimand)

For positive fitted slope s, native_residual_spread_coefficient is

    1.5 * std((y - s*x) / sqrt(1 + s*s)),    population denominator N.

The multiplier's source comment (~85% data coverage) is empirical intent, not a
derivation of C. For a fixed projection s, the spread depends on
(F-s)u - F*C*q + epsilon_y - s*epsilon_x. Even at s=F it mixes factor,
occupancy, measurement noise and their covariance. A constant b cancels from
the standard deviation, but can affect the uncentered TLS fit when noisy.

With q unobserved, x/y alone generally admit multiple (F, C, b, q, noise)
explanations. Scientific verdicts must distinguish the ideal conditional factor
identity from real identification, and report friction failure independently.

## Source and data constraints

Runtime c2130730239bcdb4cbde9361ab90c8d99aa4ff55; integration
7a2f051b1f3847786318900444c88c2ba7a74a67; observed carrot-wip
f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3; CyberPilot scientific interface
02652a441c1c39b4a9c3bfaf1132217f0e57b384. No automatic pin update.
Only existing frozen development_fit point evidence may be analyzed, after a
policy freeze commit. No raw CAN/GPS/video/VIN, unhashed route names, holdout,
development_evaluation or vehicle acceptance data may be consumed/exported.

Candidate generation, runtime acceptance and application authorization remain
false regardless of any scientific result. Encoding, bounds, fingerprint and
external watchdog/containment acceptance remain separate unresolved gates.
