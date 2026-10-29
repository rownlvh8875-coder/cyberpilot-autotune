# Read-only friction observation contract — DESIGN ONLY

FRICTION_OBSERVATION_CONTRACT_READY means the design is ready, not that its
required telemetry exists. No cereal/schema/native/controller/Params changes
are made here. Compare availability in friction_observability_gap_matrix.md.

## Source and stage rules

Exact profile pins and file/blob/range SHA-256s are in evidence/friction_model_sources.json.
R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55;
C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
Audit IDs runtime/current_controller cover LatControlTorque.update;
runtime/current_friction and callback cover the actual helper/linear callback;
runtime/current_pid cover PIDController.update; current_geometry,
current_paramsd, current_controlsd, current_vehicle_model cover the live path.
observation_v2/snapshot are pinned to the H6 base, not modified by H6.

In both pins, ordinary LINEAR feedforward friction_input is
desired_lateral_accel-actual_lateral_accel (controller lines 279–286).
The callback's a is desired_lateral_accel-roll*g, NOT achieved acceleration.
The q helper zeroes only strictly interior (-deadzone,deadzone), then
clips error/threshold to [-1,1] when compensation is enabled.
At exactly ±deadzone, the input survives; width is not subtracted.

NN_LITE uses accel_friction_factor*error+jerk_friction_factor*lookahead_jerk;
its setpoint/measurement callbacks may also enable friction on jerk inputs.
The factors/state can change in the model_good/steering-angle branches.
Full NN uses transformed setpoint/measurement NN responses, past/future
accel/roll/pitch inputs, and friction_input in a network; optional friction
override contributes to PID error, NOT the same additive feedforward model.
nnLog publication is commented out. Do not infer missing data from declared fields.

GM siglin and neural callbacks add get_friction to a nonlinear base response;
they cannot be fit as a/F without the correct base-model identity. Custom
LateralTorqueCustom rereads factor/friction and PID gains periodically and can
bypass live updates. CUSTOM is not a universal callback family; bind its actual
LINEAR/NN/GM path and installed values/gain cohort. H6 conditional qualification
is LINEAR-only, not an assertion that all five modes share q inputs/equations.

## Proposed atomic observation

Conceptual object: LateralTorqueIdentificationObservation. An immutable
read-only snapshot must be captured from the actual executed branch, after
input/context latching and before PID/limits. It must link downstream stages
by source cohort, never by nearest-message guess. This is a future schema/
receipt design, not a new implemented message.

Timestamp notation:
t_ctl=control cycle Event.logMonoTime; t_pose=livePose.timestamp;
t_lp=liveParameters Event.logMonoTime; t_cmd=carControl Event.logMonoTime;
t_apply=carOutput Event.logMonoTime. Existing event times alone do NOT expose
the exact input cohort consumed in t_ctl. Future fields must carry these exact
integers plus domains, ordered input IDs, installed-context generation/digest
and controller-cycle ID. No freshness/skew tolerances are invented here.

Every row below requires same-cycle health, finite values, source revision/
vehicle binding and exact-stage/cohort receipt. N means unavailable in the
required form today, A a published candidate, D a conditional derivation;
profile-specific differences are in the gap matrix.

| Signal | Source object/topic and stage | Exact time needed | Units | Availability | Additional health | Required? / reason |
|---|---|---|---|---|---|---|
| callback_acceleration | LatControlInputs.lateral_acceleration at ff call, desired-roll*g | t_ctl + consumed t_lp | m/s² | D/N exact | exact roll/desired branch | yes, regression a |
| callback_output_raw | local ff before PID k_f | t_ctl + callback ID | normalized torque | N | finite; actual callback executed | yes, correct response u |
| applied_normalized_torque | carOutput.actuatorsOutput.torque, after vehicle limits | t_apply + t_cmd | normalized torque | A, WRONG_STAGE for u_cb | carOutput valid, transport/safety/limit state | diagnostic required, not regression substitute |
| desired_lateral_accel | controlsState.lateralControlState.torqueState.desiredLateralAccel | t_ctl | m/s² | A Float32 | active torque branch | yes; recorded precision is not original precision |
| actual_lateral_accel | same .actualLateralAccel, VM or blended yaw branch | t_ctl + consumed carState/pose | m/s² | A Float32 | active, VM/pose valid, exact branch | yes, controller state not physical truth |
| roll_compensation | local params.roll*g from consumed liveParameters | t_ctl + t_lp | m/s² | D/N exact | valid roll and receipt | yes, callback a/sign |
| friction_input | actual local variable at friction call | t_ctl | m/s² / mode-defined input | D LINEAR approximate; N others | exact branch/gains/jerk state | yes unless exact q observed |
| deadzone | local lateral_accel_deadzone from VM/steering-angle flag | t_ctl + VM digest | m/s² | N exact | CP angle deadzone + exact VM applied state | yes unless exact q + helper version |
| threshold | FRICTION_THRESHOLD at imported callback helper | t_ctl + source/callback digest | m/s² | D=0.3 in these pins | never infer for unknown callback | yes, q semantics |
| compensation_enabled | actual per-call argument | t_ctl + callback call-site ID | bool | N per-call | true/false explicitly present | yes, q semantics |
| q | exact normalized helper state, before multiplication by C | t_ctl | dimensionless | N | bounded [-1,1], independent of installed C | yes or exact inputs; cannot divide constructed term by C as independent truth |
| friction_term | explicit helper contribution at correct call site | t_ctl | normalized torque | N | distinguish feedforward vs NN PID override | optional; installed-C term is consistency only |
| mode/callback ID | use_nnff/use_nnff_lite/GM model/custom branch | t_ctl + installed generation | enum + digest | N exact cohort | active actual path, no mixed modes | yes, model scope |
| factor_installed | self.torque_params.latAccelFactor after latching | t_ctl + installed generation | m/s² / normalized torque | N exact cohort | F>0; source identity | yes context, not qualified oracle |
| friction_installed | same .friction after latching | t_ctl + installed generation | normalized torque | N exact cohort | finite; writer identity | yes context, never independent C truth |
| PID p/i/d/f and k_f | controlsState torqueState p/i/d/f plus actual gains | t_ctl | normalized torque; gain units explicit | A components, N exact k_f cohort | raw vs scaled ff, integrator/clipping state | yes stage separation |
| PID/pre-limit sum | actual internal p+i+d+f before clip, and clip result | t_ctl | normalized torque | D/N exact | explicit clipping flags | yes if subtraction used |
| saturation | torqueState.saturated plus instantaneous limits | t_ctl/t_apply | bool / enum | A but not complete instantaneous proof | source saturation timer differs from limit receipt | yes exclusion |
| steeringPressed | consumed carState.steeringPressed | consumed t_carState + t_ctl | bool | A | valid CAN/support flag | yes exclusion |
| curvature/command limiting | controlsd curvature_limited, steer_limited_by_controls, output limits | t_ctl/t_apply | bool / enum | N full combined cohort | all limit stages | yes exclusion |
| geometry_applied_context | actual VM snapshot, CP static baseline and LP input receipt | t_ctl + geometry snapshot t_lp | m, ratio, stiffness | R static derivable, C partial; N coherent receipt | complete immutable context | yes; close epoch on changes |
| steer ratio context | VM.sR; consumed SteerRatioRate/CustomSR/live ratio | t_ctl + installed generation | ratio / raw source units | N complete cohort | effective vs raw values distinguished | yes, separate from CG ratio |
| delay context | effective SAD/liveDelay plus alignment application receipt | t_ctl + t_delay + sample pair IDs | seconds | A candidates, N complete cohort | apply delay once, record source/branch | yes, avoid double correction |
| source timestamps/cohort | exact input Event/log times, t_pose, output receipt, generation | all above | ns with clock domain | partial, N full atomic cohort | valid, ordered, no duplicates, no silent gaps | yes, prevent mixing stale inputs |
| vehicle/source context | CP canonical digest and exact revisions | startup/context generation | SHA-256 / Git SHA | static derivable | no branch-name inference | yes provenance |

## No silent fallback

Missing fields remain None/UNAVAILABLE. Inferred current C, baseline CP values,
liveTorqueParameters filtered estimates, zero-valued legacy schema defaults,
or an unsynchronized raw Params read cannot replace installed effective state.
Float32 desired/actual differences only approximately reconstruct original
full-precision LINEAR friction input. f/k_f can approximate ff only with exact
nonzero k_f/cohort and precision acknowledgement. It is not a currently exact
raw-callback observation.

Without source-based real thresholds, low-error/low-jerk selection is blocked
as SELECTION_THRESHOLD_UNJUSTIFIED. Source limit guards are not policy/safe
ranges. Every context change splits/rejects the identification epoch, including
changes made by another writer. No writer or owner proposal is constructed.

The next single task is read-only friction observability schema/receipt design.
It must establish the missing atomic stage/cohort receipts before any empirical
friction-estimator qualification. It is not started by this document.
