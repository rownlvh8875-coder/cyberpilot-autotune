# Torque geometry context binding

Classification: GEOMETRY_CONTEXT_PARAMETER, not a tunable friction parameter.
Status: TORQUE_GEOMETRY_CONTEXT_BINDING_READY (research contract only) and
CENTER_TO_FRONT_RATIO_CONTEXT_REQUIRED.

## Revision-specific semantics

c2130730239bcdb4cbde9361ab90c8d99aa4ff55 has no dynamic CenterToFrontRatio
Params key, liveParameters field or VM.update_geometry in the audited path.
Bind actual CP.centerToFront, CP.wheelbase and their ratio as STATIC_CP.
No new field is assumed/backported.

f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3:
Params CenterToFrontRatio -> requested_center_to_front_ratio -> paramsd
LateralGeometry.step/apply_geometry -> liveParameters.centerToFrontRatio ->
controlsd VM.update_geometry -> coherent LateralGeometry/VehicleModel.
The source guard accepts requested percentages 31..69, otherwise CP default.
Raw 0 means VEHICLE_DEFAULT intent; **never** physical ratio 0.0.
The effective ratio must be resolved from actual CP or actual applied evidence,
not a hardcoded vehicle value. The pure intent resolver does not claim that
a requested override has already been applied.

paramsd rate limits the live ratio and updates Kalman globals/rewind history.
controlsd applies the consumed LP ratio to its own VM, which also has guards/
isclose tolerance. Thus raw requested Params, paramsd target, published LP
candidate and actual applied VM snapshot are distinct. Snapshot/generation
receipts are still required. Source guards and rates are not safe vehicle
ranges and are not tuning recommendations.

Geometry sets aF=L*r, aR=L*(1-r), and redistributes both stiffness baselines:
Cf_new=Cf0*(1-r)/(1-r0), Cr_new=Cr0*r/r0, preserving effective global stiffness k.
controlsd separately clamps LP stiffness and resolves effective steer ratio
from live ratio, SteerRatioRate and CustomSR (source CustomSR raw scale 0.1).
These are distinct from center-to-front ratio. SAD/liveDelay is a third,
separate timing context, with the actual applied delay/alignment recorded.

The current carrot-wip head was rechecked at H6 start and still equals f5e4.
No branch movement/diff review was required. Only these exact pins are claimed.

## Immutable context / epoch contract

SteeringGeometryContext includes exact source_revision, vehicle_context_digest,
wheelbase, center_to_front, center_to_front_ratio, steer_ratio_effective,
stiffness_factor, controller_mode, geometry_generation, snapshot_time_ns, cohort,
geometry_source, steer_ratio_rate, custom_sr, delay_source, effective_delay_s,
custom_torque_mode and installed factor/friction context.
None remains None; incomplete context blocks scientific comparison. No vehicle
defaults or Santa Fe special cases exist in the research package.
snapshot_time_ns identifies installation/capture of the immutable context,
not every sample's measurement time; samples have separate monotonic time_ns.
A new snapshot/cohort cannot silently replace the previous one.

Any changed geometry/vehicle/stiffness/generation closes the epoch with
GEOMETRY_CONTEXT_CHANGED. Effective steer ratio/rate/CustomSR, SAD/liveDelay
source/value, custom/controller mode, installed F/C, source revision or cohort
changes also close the epoch. The next context has a new digest. No fit pools
same torque observations across changed contexts; no simultaneous CG/friction
optimization or writer action is allowed.

## Generic source-based sensitivity (not vehicle qualification)

The preregistered toy uses L=2.73m,r0=.43,m=1234kg,j=2300kg*m²,
Cf0=70000,Cr0=90000,k=.95,sR=14.7,speed=18m/s,steer=.035rad,roll=.02rad.
Ratios .43,.44,.51 are mathematical perturbations, **not** approved ranges.

A crucial cancellation must not be hidden. With coherent redistribution,

sf = m/(k*L) * [r0/Cr0 - (1-r0)/Cf0],

so the steady curvature factor and roll compensation are invariant in r under
this fixed model. Altering axle lengths without stiffness redistribution would
manufacture a steady effect that does not match this source.

However dynamic A/B matrices and transient lateral velocity/yaw generally
change. Explicit-Euler diagnostics (dt=.001s,200 steps), independently checked
against isolated exact-source matrices, show:

| ratio | steady curvature (1/m) | max transient acceleration change (m/s²) | naive mismatched-geometry F | naive C |
|---|---:|---:|---:|---:|
| .43 | .000367406658 | 0 | 2.400000 | .170000000 |
| .44 | .000367406658 | .002251035 | 2.440039 | .169999696 |
| .51 | .000367406658 | .018008284 | 2.703564 | .169997677 |

The naive estimates intentionally reuse baseline torque with a different
acceleration mapping: an UNADMITTED_GEOMETRY_MISMATCH_NEGATIVE_CONTROL, not
a qualified response model. A correct mixed-window fit rejects the context
change. These values establish generic confounding, not actual vehicle effect
sizes or friction sensitivity guarantees.

Verdict: GEOMETRY_CONTEXT_MATERIAL for the tested generic transient.
Coherent steady invariance is separately reported. Both findings preserve the
conservative geometry binding; neither validates an actual vehicle model,
SteerRatio/SAD co-tuning, bounds, runtime encoding or application.
