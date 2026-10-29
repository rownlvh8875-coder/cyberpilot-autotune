# H5 factor estimand and identifiability

This is a conditional mathematical result, not a vehicle parameter recommendation.
The exact external source/range index is
[scientific sources](evidence/torque_identification_scientific_sources.json).
H3 unit/source gates and H4 owner correctness are unchanged.

## Actual source path

At runtime c2130730239bcdb4cbde9361ab90c8d99aa4ff55, interfaces.py imports
get_friction from opendbc.car.__init__.py. Its five-argument helper applies a
center deadzone and saturating interpolation; disabled compensation returns0.
It is not the four-argument lateral.py helper used in the native offset test.
The base callback returns a_c/F + C*q. It does not subtract its stored offset.
The controller then uses feedforward plus PID and returns a sign-inverted final
output. Consequently a callback coefficient is not automatically an identified
plant coefficient from applied torque and subsequently observed acceleration.

Native torqued observes x = negative applied actuatorsOutput.torque, not requested
torque. y uses calibrated yaw and device roll: v*yaw - sin(roll)*g. It checks pose
validity, continuous latActive and no override over its buffer, v>15, |x|>.02,
|y|<=1 and the half-open buckets. carOutput/carState/carControl timestamps are
shifted by liveDelay once; the offline fit must not shift frozen rows a second time.
Clipping against CP, FirstOrderFilter and cache restore are not scientific truth.

## Conditional inverse equation

If applied x represents the callback torque coordinate u, and observed y represents
its acceleration input up to nuisance b and errors, then

    u = a_c/F + C*q
    y = F*u + b - F*C*q + epsilon_y
    x = u + epsilon_x.

With C=0, zero errors and nonconstant u, [x,1,y] has null vector proportional to
[F,b,-1]. Native SVD therefore recovers s=F and intercept b. This proves only the
ideal affine submodel. Real closed-loop equivalence, applied/requested stages,
noise covariance, state occupancy and mode must be established independently.

With friction and zero measurement noise, even the OLS diagnostic has

    Cov(u,y)/Var(u) = F * (1 - C*Cov(u,q)/Var(u)).

It is not a replacement for native TLS. Correlation/occupancy can confound F, and
uncorrelated vertical friction spread still biases unweighted TLS.

## Native TLS is not centered 2D TLS

The native raw SVD uses M=[x,1,y]. Its objective is the smallest eigenvector of

    M' M/N = [[E(x*x), E(x), E(x*y)],
              [E(x),   1,    E(y)],
              [E(x*y), E(y), E(y*y)]].

The constant column participates in the TLS geometry. A free-intercept centered
two-dimensional fit is not substituted. An intercept/roll shift can interact with
noise in this uncentered objective. Euclidean TLS also requires an appropriate
x/y noise metric: their different units and unknown error covariance are not
fixed merely by selecting float64.

For the explicitly symmetric zero-mean b=0 submodel, independent u and q and no
measurement error, write Vx=Var(u), Vxy=F*Vx and
Vy=F^2*(Vx+C^2 Var(q)). When the line eigenvalue is below the constant-column
eigenvalue1, the positive slope is

    s = (Vy - Vx + sqrt((Vy-Vx)^2 + 4*Vxy^2)) / (2*Vxy).

That restricted analytic prediction matches independently generated synthetic
observations within the preregistered2e-12 numerical allowance. It is not asserted
for general unbalanced/noisy/nonzero-intercept data.

## Executed synthetic evidence

The15 primary families and28 fixed sensitivity cases use seed17; no vehicle
range is implied. Ideal factor truths0.5,1,2,4 and offsets -0.125,0,0.125 recover
within numerical precision. With truth F=2,C=.1, balanced friction gives s=2.162440;
unbalanced excitation gives s=2.422181; half-amplitude excitation gives s=2.673975.
Neither stable fits nor additional points repair this model-dependent bias.
No-friction x/y-noise, lag mismatch, constant/varying roll, low excitation and mild
nonlinearity are separately characterized in the canonical results JSON.

## Verdict and scope

FACTOR_ESTIMAND_DEFINED.
The ideal no-friction affine identity is mathematically established, but existing
frozen development point/route/epoch/selection artifacts were not accessible after
local, GitHub and Hugging Face metadata searches. Historical counts are not a
substitute for those inputs. No real fit, route influence or uncertainty was run.

FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.

Even with that artifact, the preregistered route-stability acceptance threshold
remains unjustified, independent route sampling unproved, and source/selection/
noise/mode bindings require validation. No GLOBAL_FACTOR_EQUIVALENCE_PROVEN claim
is made. NN_TORQUE, NN_LITE, GM_CALLBACK and CUSTOM_TORQUE are excluded.
