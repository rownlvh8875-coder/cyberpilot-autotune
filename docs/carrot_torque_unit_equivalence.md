# Factor, friction and preserved offset units

Read-only H3 audit at runtime c2130730239bcdb4cbde9361ab90c8d99aa4ff55 and
current f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3. Field names and numeric
forwarding do not establish qualified CyberPilot parameter equivalence.
Evidence suffixes below resolve for both source roles in
[the manifest](evidence/carrot_writer_ownership_sources.json).

## Mathematical domains

Define x as negative returned normalized actuator torque, and y as the estimator's
roll-corrected acceleration: speed × calibrated yaw-rate − sin(device roll) × g.
The source histories interpolate these inputs and use source-specific activity,
override, speed and fit gates; this is not the receipt exact-cohort join contract.
TLS uses rows [x, 1, y]. In its numerical fit, y ≈ a·x + b, where a is slope and
b is intercept. This is a software model statement, not physical measurement or
independent identification qualification.

The base torque callback computes acceleration / factor plus a signed friction
helper. Desired acceleration is curvature × speed²; ordinary feedforward subtracts
roll × g, while actual acceleration can come from VM steering geometry or a
VM/yaw blend. Low-speed factors, PID error, steeringPressed integrator freezing
and actual callback selection also affect output. Internal PID torque is negated
for the returned request. Hyundai scales normalized request by STEER_MAX and
returns its limited result divided by STEER_MAX; no Nm conversion is established.

Evidence: sample-inputs, fit, controller-compute, default-linear, hyundai-output.

## lat_accel_factor

| Field/source | Mathematical role | Representation / scale | Unit and sign | Confidence |
|---|---|---|---|---|
| LateralTorqueAccelFactor | Manual candidate assignment | Native integer text, custom get_float ×0.001 | Same stored controller coefficient after conversion; not itself a physical torque | PROVEN conversion |
| CP.lateralTuning.torque.latAccelFactor | Startup factor/default source | Float32 table value | Default base denominator, callback conditional | CONDITIONAL effect |
| liveTorqueParameters.latAccelFactorRaw | Fitted TLS slope a | Float32, no additional storage scale | Scoped y/x: m/s² per normalized torque in estimator orientation | PROVEN fit role |
| latAccelFactorFiltered | Filtered/clipped slope candidate | Float32 forwarded unchanged | Same scoped role; source health and estimate age distinct | PROVEN forwarding |
| controller torque_params.latAccelFactor | Base inverse denominator | Mutable Float32 builder value | Scoped acceleration / normalized torque; bypassed by some NN/brand paths | CONDITIONAL |
| CyberPilot lat_accel_factor | PR #9 target identifier | Caller ParameterSpec.units string and independently qualified proposal required | No built-in approved source/unit/vehicle registry or inference from identifier | UNRESOLVED equivalence |

**UNIT_EQUIVALENCE_CONDITIONAL / FACTOR_UNIT_EQUIVALENCE_UNRESOLVED.**
The fit slope and base inverse denominator have compatible scoped dimensional
roles, but a universal NN/brand interpretation and qualified CyberPilot mapping
are absent. A source-supported scaling does not supply identification evidence,
runtime mode, baseline, ownership or approved application bounds.

## friction

| Field/source | Mathematical role | Representation / scale | Unit and sign | Confidence |
|---|---|---|---|---|
| LateralTorqueFriction | Manual coefficient assignment | Native integer text, get_float ×0.001 | Production helper's compensation magnitude under selected callback | PROVEN conversion |
| CP friction | Startup/table coefficient | Float32 | Callback-specific magnitude, not a trusted baseline | CONDITIONAL effect |
| frictionCoefficientRaw | std of rotated/perpendicular spread × FRICTION_FACTOR | Float32; source factor is an estimator heuristic | Nonnegative numeric spread in a rotation mixing x/y coordinate magnitudes; general normalized torque conversion unproven | CONDITIONAL units |
| frictionCoefficientFiltered | Clipped/filtered numeric spread | Float32 passed unchanged into controller | Numeric identity is proven; dimensional/identification equivalence is not | CONDITIONAL |
| controller torque_params.friction | Signed interpolation endpoint magnitude | Float32 | In base callback, additive normalized-torque contribution; sign follows deadzoned error | PROVEN scoped role |
| CyberPilot friction | PR #9 independently qualified target coefficient | No automatic diagnostic conversion | Residual/diagnostic spread or same name cannot prove this magnitude | UNRESOLVED |

The production helper is **opendbc.car.get_friction**, imported by interfaces.py
from opendbc/car/__init__.py. It applies center deadzone, interpolates between
negative/positive coefficient at the supplied threshold, and returns zero when
compensation is disabled. It has no direct speed or steeringPressed input; those
change upstream error/jerk/curvature/PID behavior. NN-lite changes friction input
shaping; full NN may use an optional override; GM callback paths differ again.

Rotation normalizes the fit's perpendicular coordinate using its numerical slope.
The source does not supply a proven general physical conversion from that rotated
spread to normalized torque, or from CyberPilot diagnostic friction to this
controller coefficient. We do not invent a slope-dependent multiplier, correct
upstream behavior or label it a vehicle defect based on dimensional inspection.

The old offset test imports a similarly named helper from lateral.py, generates
synthetic data, and leaves factor/friction estimate checks as TODO. It is evidence
about that test's scope, not qualification of the production coefficient.

**UNIT_EQUIVALENCE_CONDITIONAL / FRICTION_UNIT_EQUIVALENCE_UNRESOLVED.**
Evidence: fit, friction, default-linear, controller-compute, gm-neural, gm-siglin,
offset-test, old-test-helper, pr9:research.

## lat_accel_offset: preserved state, not a target

The schema has latAccelOffsetRaw @2 and latAccelOffsetFiltered @5, both Float32;
there is no literal liveTorqueParameters.latAccelOffset member. That is a logical
catalog identifier. The TLS b term is the signed intercept in estimator y units,
scoped m/s², with the estimator orientation/sign convention described above.
It is not a directly established sensor bias, desired steering offset or actuator
command. Raw offset is filtered and the filtered member forwarded unchanged to
the live setter. Positive custom mode instead copies captured CP offset.

Initialization seeds zero or restores a compatible cached value; neither proves
current availability or a trusted baseline. Ordinary reset clears histories/
buckets, retaining the existing filtered state. A not-calculable/invalid fit can
therefore coexist with filtered values and Event validity. The source's finite
and timestamp limitations must not be hidden by treating scalar default zero
as present evidence.

The inspected default linear and GM callbacks do not directly use offset in
their torque equations; full NN coefficient paths do not supply it as a learned
scalar input either. That does not permit dropping it: the owner tuple must
preserve stored coupled state, mode transitions and future consumer semantics.
PR #9's offset is never tunable. H2's global canonical unit remains unresolved;
H3's narrower source-intercept/preserved-state finding does not mutate or promote
the H2 descriptor.

**OFFSET_SEMANTICS_PROVEN** means the traced fit/filter/field/preservation role
only. It does not prove scientific bias identification, externally coherent
effective readback or an approved application conversion. A future tuple must
take offset from its exact controller-effective owner snapshot, not a latest
estimator message, synthetic seed, default, absent field or separate partial write.

Evidence: fit, sample-inputs, estimator-init, reset, filter-update, publish,
schema, cp-schema, live-setter, controller-compute and PR #9 contracts/coordinator.

## No authority promotion

H2 descriptors are an index, not policy or QualifiedEvidence. PR #9 keeps unit
strings and bounds caller-supplied and rejects research exports as authority.
No canonical target values, UI-derived bounds, synthetic safety policy or new
unit conversion code are created here. Factor zero can be an invalid divisor;
friction zero can be a real coefficient. Neither should be used for missing data.
Vehicle bounds/rates and independent identification remain separately unresolved.
