# Carrot read-only signal contract (Phase 8A)

Status: **CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED**.

Inspected repository: https://github.com/ajouatom/openpilot, branch carrot-wip,
exact commit **604bc0a22733e648ec05b268da1ffaae7db52a69**. Fetch and ls-remote agree with the user's
last observed SHA; no intervening commits. Target contract basis is
cyberpilot-autotune main at 09f3f58d9f9f7a59d6f983c4e0536c092aab1a4f.
See carrot_provenance.md and carrot_source_manifest.json for 37 raw-blob hashes.
No reference source body is copied, executed, changed or installed.

This is source evidence and a proposed future read-only boundary, not a runnable
adapter. No carrot_contract.py or mapping code is created: the actual actuator
activity and universal saturation semantics cannot be proven from these messages.
No unknown value becomes False, zero, an empty string or a similarly named field.
Confidence describes the complete proposed mapping; CONDITIONAL is a documented
restriction, not permission to bypass the hard gates.

## Snapshot matrix

Every linked source URL below contains the exact repository, commit and actual
path. Function/symbol names identify the producer and consumer. Policy-only rows
have no invented cereal field or implemented adapter symbol. Missing mandatory
input causes explicit rejection before Snapshot construction; optional unknowns
remain None. No Snapshot is produced by this Phase 8A work.

| Snapshot field | Source topic | Exact schema field | Producer | Consumer | Type | Unit | Sign | Clock domain | Validity requirement | Missing behavior | Confidence | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| timestamp_s | carState + controlsState envelopes | Event.logMonoTime @0 | messaging.new_message; card.Car.state_publish; Controls.publish | SubMaster.update_msgs; future injected-clock engine | UInt64 ns -> float seconds | s | nonnegative | Same-host/boot Python monotonic, conditional attestation | Both timestamps known, finite domain/order/future/skew checks; no remote/replay/simulation substitution | Reject; never wall time or receive-time replacement | CONDITIONAL | [Event](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/cereal/log.capnp#L2617-L2619), [stamp](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/cereal/messaging/__init__.py#L42-L54), policy below |
| sequence | Adapter-owned attempt/cohort identity | None; SubMaster.frame/recv_frame are local poll counters, not source sequences | Future caller-owned stream lifecycle, not implemented | AutoTuneEngine high-water | nonnegative int | count | increasing per stream | One explicitly declared monotonic stream | New required-topic cohort; consume rejected identities; no repaired-frame relabeling | Reject/skip cohort; domain restart requires new instance | CONDITIONAL | [SubMaster.frame and recv_frame](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/cereal/messaging/__init__.py#L255-L271); user contract policy |
| source_age_s | carState + controlsState envelopes | Event.logMonoTime; SubMaster.recv_time is separate metadata | Publication timestamps from both Python publishers | SafetyGate adds elapsed time since timestamp_s | finite float | s, age at snapshot anchor | nonnegative | Same monotonic domain | Integer-ns publication-age calculation; separate receipt-age checks; not sensor age | Reject if clocks unavailable; never assume zero upstream sensor latency | CONDITIONAL | [receive metadata](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/cereal/messaging/__init__.py#L245-L280); age algebra below |
| context_key | Caller controller/baseline epoch metadata | None; no VIN/GPS/driver field | Future opaque versioned context policy, not implemented | ResidualStatisticsLearner context reset/binding | nonempty str | none | N/A | Stable within stream/controller/baseline epoch | Recognized controller/union identity and caller baseline generation | Reject, not empty string; no identifying data | CONDITIONAL | [controller selection](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/controlsd.py#L100-L105), [MEB selector](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/drive_helpers.py#L9-L12); policy below |
| source_valid | Required topic health + payload health | Event.valid @67; CarState.canValid @26; SubMaster.seen/updated/alive/freq_ok | card.Car.state_publish; Controls.publish; SubMaster checks | LateralStartupGate; future strict health policy | Bool after complete proof | none | N/A | Evaluated at one caller clock instant | Individual flags, no ignore/simulator bypass, required estimates/union/activity semantics and alignment proven | Reject unavailable health; do not fabricate a False source signal | CONDITIONAL | [CAN-only controls valid](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/controlsd.py#L424-L435), [carState valid](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/car/card.py#L370-L375), [checks](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/cereal/messaging/__init__.py#L282-L301) |
| speed_mps | carState | CarState.vEgo @1 | Platform CarState.update -> CarStateBase.update_speed_kf -> CarInterfaceBase.update -> card.Car.state_publish | Controls.state_control; VehicleModel.calc_curvature | Float32 -> finite number | m/s | Preserve; negative rejects Snapshot admission, never abs/clamp | carState publication time, not wheel sensing time | Known healthy publisher, finite nonnegative estimate; canValid alone insufficient | None in a diagnostic projection or reject mandatory learning input | PROVEN | [schema](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/car.capnp#L158-L175), [speed filter/wheel conversion](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/interfaces.py#L537-L559), [Tesla producer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/tesla/carstate.py#L168-L181), [VM m/s contract](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/vehicle_model.py#L66-L77) |
| desired_curvature_inv_m | controlsState | ControlsState.desiredCurvature @61 | Controls.state_control smooths/clips target; Controls.publish | LongitudinalPlanner.update; LateralLagEstimator.handle_log; LaC.update receives same internal target before publish | Float32 | 1/m | Preserve branch target convention; no invented left-positive conversion | controlsState publication; model/plan origin is separate | Finite, correct controller family and required plan health; not applied actuator curvature on MEB | None or reject required learner signal | PROVEN | [publish](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/controlsd.py#L432-L435), [1/m consumer argument](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/vehicle_model.py#L92-L104), [serialized consumer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/longitudinal_planner.py#L166-L175) |
| measured_curvature_inv_m | controlsState | ControlsState.curvature @37 | Controls.state_control uses negated VM curvature from steering angle minus learned offset, roll and effective geometry | LateralPlanner.update; LongitudinalPlanner.update | Float32 | 1/m | Exact producer convention is negative VM curvature; physical left/right normalization not approved | controlsState publication; no carState input timestamp in this struct | Explicitly a model estimate, not a direct measurement; current learned/calibration/model validity required | None or reject; no copied steering angle or yaw proxy | CONDITIONAL | [schema estimate comment](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/cereal/log.capnp#L854-L863), [producer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/controlsd.py#L120-L131), [consumer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/lateral_planner.py#L98-L99) |
| lateral_acceleration_mps2 | controlsState, torque union only | LateralTorqueState.actualLateralAccel @9 | LatControlTorque.update computes actual_curvature times vEgo squared, only in active branch | carrot realtime compact_state controlsState schema entry | Float32 optional | m/s^2 | Same native estimated curvature sign; not torque-output sign | controlsState publication; estimator source may be older | Matched torque union, active branch, verified estimator mode; inactive/default/missing angular-velocity fallback is unavailable | None; never promote an unassigned/default/fallback zero | CONDITIONAL | [calculation/missing-vector fallback](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/latcontrol_torque.py#L164-L194), [publish](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/latcontrol_torque.py#L294-L302), [consumer entry](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/carrot/realtime/compact_state.py#L219-L228) |
| controller_saturated | controlsState.lateralControlState union | torqueState.saturated @7, pidState.saturated @8, angleState.saturated @3 | Controller update -> LatControl._check_saturation; MEB publishes dummy angle log | SelfdriveD.update_events; LateralLagEstimator.handle_log | Bool source alert; Snapshot Bool/None unresolved | none | N/A | Controller log publication, no final actuator-limit acknowledgement | Exact controller/union and alert-vs-current-limit meaning required; false timer alert is not absence of limiting | None + blocked; unknown/mismatch/dummy never False | UNRESOLVED | [timer/exclusions](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/latcontrol.py#L26-L33), [alert consumer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/selfdrived/selfdrived.py#L524-L533), [MEB dummy](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/controlsd.py#L239-L265) |
| driver_override | carState | CarState.steeringPressed @9 | Platform steering torque/contact detection; CarInterfaceBase.update -> card.Car.state_publish | LatControlPID.update override; LatControlTorque.update freeze; CarrotControls.lat_suspend_control | Bool / None | none | N/A | carState publication time | Known fresh steering-contact predicate; applies to lateral learning only, not a universal pedal/driver-intent classifier | None or reject; never infer False from missing/default builder | PROVEN | [schema](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/car.capnp#L190-L198), [Tesla producer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/tesla/carstate.py#L224-L232), [PID consumer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/latcontrol_pid.py#L35-L46), [suspend consumer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/carrot/carrot_controls.py#L12-L39) |
| baseline_parameters | Caller only in this design | No approved cereal/Params baseline schema | Caller injects trusted immutable research baseline with explicit identity/units | Target AutoTuneEngine and contract defensive copy | immutable Mapping[str, finite number] | Caller-owned per parameter | Per supplied specification | Fixed baseline epoch, separate from message timestamps | Registry/units/identity supplied and matched; no implicit read of learned or manual values | Reject missing/mismatch; no Params fallback | CONDITIONAL | [target copy contract](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/09f3f58d9f9f7a59d6f983c4e0536c092aab1a4f/src/cyberpilot_autotune/contracts/validation.py#L52-L61), baseline table below |
| control_active | No sufficient published source | Candidates: CarControl.latActive @11; lateral union active @0; SelfdriveState.active @2; PandaState.controlsAllowed @3 | Controls -> published request; card may suppress before apply; hardware safety independently gates commands | card.Car.controls_update / CarInterfaceBase.apply / safety_tx_hook | Snapshot Bool/None | none | N/A | No applied-authority/cycle acknowledgement in CarOutput | Must prove evaluated lateral controller actually has authority at this cohort, not merely requested/engaged | **None; BLOCKED_CONTROL_ACTIVE_SEMANTICS** | UNRESOLVED | [request computation](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/controlsd.py#L143-L166), [downstream override](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/car/card.py#L405-L429), [output schema](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/car.capnp#L611-L615), [independent TX gate](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/safety/safety.h#L259-L292) |

PROVEN rows establish the named source quantity, not universal physical accuracy,
final actuator authority or permission to create a Snapshot while any hard gate is
blocked. Scalar zeros are legitimate only when actually available in that source
mode; they are not a representation of unavailable data.

## Control-active hard gate

The required meaning is actual authority of the evaluated lateral controller at
Snapshot time. The following candidates do not prove it:

| Candidate | Proven source meaning | Why it cannot be the required mapping |
|---|---|---|
| SelfdriveState.enabled | StateMachine enabled set includes preEnabled | Engagement/UI state, not lateral execution; [state.py](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/selfdrived/state.py#L8-L9) |
| SelfdriveState.active | Enabled/softDisabling/overriding state membership | Includes overriding; does not encode controller-specific faults, readiness, suspension or downstream permission; [state output](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/selfdrived/state.py#L107-L112) |
| CarControl.enabled / longActive / cruise.enabled / latEnabled | Engagement, longitudinal request, cruise or steering setting | None independently identifies actual evaluated lateral authority; AlwaysLateral also decouples lateral request from selfdrive active/enabled |
| CarControl.latActive | controlsd requested lateral activity after gear/AlwaysLateral, fault/speed/standstill, suspension, startup and reboot checks | card checks its own process latch/reboot state later and can clear the received request; the original published request is not revised |
| lateralControlState.*.active | Algorithm update active input | Same pre-card request; MEB angle log describes a dummy path |
| PandaState.controlsAllowed | Health packet controls_allowed reported by pandad | Asynchronous hardware status, not command-cycle acknowledgement; source safety helpers have additional permission/limit logic and TX rejection; [health producer](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/panda/board/main_comms.h#L7-L31), [publisher](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/pandad/pandad.cc#L211-L235), [torque checks](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/safety/safety.h#L660-L695) |
| CarOutput.actuatorsOutput nonzero/zero | Previous reported post-CarController actuator quantities | Zero can be a valid active command; no applied latActive or request identifier. card.Car.step publishes state before this iteration's controls_update; [order](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/car/card.py#L499-L508) |

SelfdriveD itself documents asynchronous safety-status mismatch handling at
[selfdrived.py:620-630](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/selfdrived/selfdrived.py#L620-L630).
CarOutput has no authority or originating CarControl timestamp field. Merely adding
healthy topics or a skew threshold cannot manufacture the missing causal fact.
No controller-independent or controller-aware True/False mapping is approved.
control_active remains None and every proposed Carrot mapping is rejected.

## Controller saturation evidence

| Controller type | Saturation field | Semantics | Reliable | Missing behavior |
|---|---|---|---|---|
| Torque | lateralControlState.torqueState.saturated | Output-limit proximity/curvature-limited input passes a timer with speed, safety/rate-limit and driver-press exclusions; assigned only when active | Proven timer-qualified alert; not instantaneous final actuator saturation | Inactive, unmatched mode or missing log -> None; false does not prove unconstrained control |
| PID | lateralControlState.pidState.saturated | Same base timer; output-limit proximity and curvature limit; assigned only when active | Same restricted alert meaning | None if unavailable/inactive/mismatch |
| Standard angle | lateralControlState.angleState.saturated | Desired/measured steering-angle tracking error goes through base timer; angle-specific minimum speed | Tracking-error alert, not an actuator saturation measurement | None if controller identity/meaning not resolved |
| VW MEB custom curvature PID | angleState exists but is explicitly dummy | Actual curvature PID and CarController curvature limits run outside the logged angle controller | **REJECTED** as MEB saturation source | None + reject; do not use dummy False |
| Joystick/debug | lateralControlState.debugState.saturated schema only | joystickd_thread initializes debugState but does not assign active/saturated; [publisher](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/tools/joystick/joystickd.py#L62-L71) | **REJECTED**; default/unpublished Bool is not a sample | None + reject |
| INDI / LQR / deprecated curvature | indiStateDEPRECATED / lqrStateDEPRECATED / curvatureStateDEPRECATED | Deprecated schema members; no corresponding class selected by this pin's Controls constructor | **REJECTED** / unsupported in this contract | None + reject |
| Unknown/custom union mismatch | None approved | Never choose the closest-looking field | **UNRESOLVED** | None + reject |

A safe future narrow contract could retain the source alert as a separately named
veto diagnostic. It cannot silently redefine controller_saturated=False as proof
of absence of current limiting. Until the owner resolves that requirement or a
reliable source exists, BLOCKED_SATURATION_SEMANTICS remains. No synthetic or actual
vehicle thresholds from the source are adopted as target policy defaults.

## Estimated response and sign limits

ControlsState.curvature is explicitly a vehicle-model estimate. controlsd applies
steering offset, effective ratio, stiffness and roll; it does not publish all
per-calculation input health. Native target and estimate signs are preserved from
the negated VM convention. The [reference-frame document](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/common/transformations/README.md#L8-L24)
describes forward/right/down axes; the torque controller's left-positive output
comment is about its returned torque command, not proof of a left-positive
curvature convention for all platforms. No physical sign flip is invented.

Torque actualLateralAccel is computed only in the active branch. In useSteeringAngle
false mode a missing CC.angularVelocity vector falls back to zero curvature before
blending. CC is created in state_control and its angularVelocity is assigned in
publish after LaC.update. This source ordering and missing-vector path cannot be
promoted into a valid measured zero; that mode stays unavailable without further
proof. Non-torque, inactive, missing or mismatched union also means None. No source
bug fix or performance claim is made here.

## Clock, freshness and update policy (design only)

Both required Python publishers use messaging.new_message, which stamps Event
logMonoTime from Python monotonic seconds converted to nanoseconds. SubMaster
stores that envelope value unchanged, and separately records recv_time from its
local update clock. recv_time is a batch observation time, not physical sample
acquisition and not an exact socket-arrival timestamp. frame and recv_frame count
receiver updates. No serialized per-topic global sequence is provided.

Future construction must receive caller-attested same-host/same-boot monotonic
domain, lifecycle identity, and finite nonnegative caller-approved publication-age,
receipt-age and inter-topic-skew limits. There are no vehicle defaults. Reject
remote/replay/simulator domains, unknown provenance, future/negative/reordered
required timestamps or a restarted domain in an existing stream. Do not use wall
time, the new receipt time of an old message, or artificial timestamp increments.
Use integer nanoseconds for validation; divide by 1e9 only at the canonical unit
boundary. If conversion collapses distinct required seconds timestamps, reject
rather than perturb the time to manufacture order.

For publication times t_car and t_controls and evaluation time now, define a
publication-only anchor T=max(t_car,t_controls). The proposed age at that anchor is
T-min(t_car,t_controls), and skew is abs(t_car-t_controls). Therefore the engine's
existing effective age is source_age_s + (now-T) = now-min(t_car,t_controls).
This avoids the double counting that would result from storing
now-minus-publication as age-at-anchor.
Receipt ages now-r_i are checked independently against their supplied limit.
These quantities prove publication freshness only, not physical sensor age or
causal alignment of the carState input consumed by controlsd. ControlsState has
plan timestamps, but no carState input timestamp; temporal proximity is not an
atomic input linkage. Physical sample age remains unresolved, never assumed zero.

The proposed conservative cohort requires both topics seen and updated, with
strictly advancing publication timestamps in one adapter lifecycle. An update on
only one topic causes rejection/no sample; it does not relabel cached data as a
new observation. Future sequence numbers are adapter-owned, deterministic and
consumed on attempted cohorts, including rejected ones. They are not copied from
SubMaster.frame. A new domain requires a new adapter/engine instance. These rules
are documented proposals, not an implemented adapter state machine.

## Source validity policy (design only)

Transport prerequisites are individual seen, updated, Event.valid, alive and
frequency PASS for carState and controlsState, plus actual carState.canValid.
Do not rely on all_checks alone: ignore lists can bypass checks; simulation relaxes
liveness/frequency. Required services must have no bypass and simulation must be
explicitly excluded, not inferred from healthy flags. Default SubMaster messages
are not evidence. Service rates at this pin are carState/controlsState/carControl/
carOutput/selfdriveState 100 Hz, pandaStates 10 Hz, liveParameters 20 Hz and
liveTorqueParameters 4 Hz; frequency is not a permitted freshness bound.

Complete validity would additionally require correctly identified non-dummy
controller/union, finite required quantities, accepted clock/receipt/skew policy,
trusted baseline binding, proven actual activity and resolved saturation semantics,
and current validity of all required estimate inputs. For VM-derived values this
includes liveParameters Event health and payload valid/sensorValid/posenetValid;
pose-derived modes require the relevant pose/calibration validity. The startup
latch is one-way, not ongoing estimate validity. No aggregate validity bit for
this full claim is published in controlsState: its Event.valid is just canValid.

Missing health or signal means explicit rejection, not a fabricated False/zero.
Known valid=false, canValid=false, dead/frequency-failed topic, stale/reordered time,
skew violation or baseline mismatch also reject. Until the two unresolved semantic
hard gates are closed, this composition cannot issue a valid Snapshot at all.

## Baseline and learned parameter classification

No actual parameter registry, bounds or rate limits are approved. The future
boundary must accept a caller-owned immutable baseline with explicit generation,
parameter IDs/units and trusted engine binding. Defensive copy and exact identity
are required; no Params key is read here. A missing/mismatched baseline rejects.

| Parameter / source | Actual producer and consumer | Unit / cadence / persistence evidence | Classification | Baseline meaning |
|---|---|---|---|---|
| liveTorqueParameters.latAccelFactorFiltered | TorqueEstimator.get_msg -> Controls.state_control -> LatControlTorque.update_live_torque_params | Linear consumer divides acceleration by factor; m/s^2 per normalized command, not Nm. Published nominally 4 Hz; source cache trigger every 240 SubMaster frames | READ_ONLY_CANDIDATE | Observation candidate only; not proof of actual privately overridden controller value |
| liveTorqueParameters.frictionCoefficientFiltered | Same estimator/update path; CarInterfaceBase.torque_from_lateral_accel_linear -> get_friction | Added normalized torque-command compensation, not tire friction coefficient or Nm; same publication/cache lifecycle | READ_ONLY_CANDIDATE | Same restrictions; NN/custom controller path may not share linear interpretation |
| Raw factor/offset/friction, liveValid, useParams, version, decay | TorqueEstimator.estimate_params/get_msg | Raw/filtered distinction and fit validity matter; useParams is static eligibility. controlsd checks Event health/useParams, not liveValid in that call | OBSERVATION_ONLY | Do not equate filtered publication or useParams with an applied baseline |
| latAccelOffsetFiltered | TorqueEstimator and live update | Offset in estimator acceleration model; default linear callback shown does not use it; platform callback behavior varies | OBSERVATION_ONLY | No universal effective parameter mapping |
| CP.lateralTuning.torque initial values; CP.steerRatio/geometry | CarParams -> controller/VehicleModel construction | Static configuration; schema has no approved AutoTune registry | OWNER_CONTROLLED | No vehicle constants copied or registry approved |
| liveParameters.steerRatio | VehicleParamsLearner.get_msg -> controlsd ratio resolver -> VehicleModel | Dimensionless angular ratio; nominal 20 Hz; LiveParametersV2 cache on 1200 receiver frames | OBSERVATION_ONLY | Effective ratio may be manual override or scaled; published learned ratio is not necessarily consumed ratio |
| liveParameters.stiffnessFactor | VehicleParamsLearner -> controlsd -> VehicleModel.update_params | Dimensionless scaling of front/rear N/rad stiffness; effective lower clamp and startup fallback exist; restored stiffness reset outside replay | OBSERVATION_ONLY | Not an independent learner-owned tuning parameter |
| liveParameters angle offsets / roll | VehicleParamsLearner -> curvature/torque estimates | Offset degrees, roll radians; payload validity plus health required; cached learner state exists in reference | OBSERVATION_ONLY | Calibration/estimation inputs; not tuning proposals |
| CustomSR, SteerRatioRate | Source Params -> resolve_vehicle_model_steer_ratio | Manual override and scaling change effective ratio; no parameter reads implemented here | USER_PREFERENCE | Never silently treat as owned AutoTune baseline |
| LateralTorqueCustom and manual torque/Kp/Ki/Kf/Kd keys | LatControlTorque.update rereads every 10 controller frames | Custom mode blocks live torque update; effective private values are not published atomically | USER_PREFERENCE | No write, read or automatic key lookup in this target |
| Safety config / CarController and panda limits | CarParams, controller and safety TX checks | Vehicle-specific safety restrictions, independent of learner | SAFETY_LOCKED | Excluded from any registry in this work |
| CarState.steeringTorque as a physical torque baseline | Platform producer | Schema explicitly says units need standardization | NOT_SUITABLE | Do not assume Nm or substitute it for tuning parameters |
| Full effective runtime tuning snapshot | No complete atomic publisher found | Custom/NN callbacks, private overrides and geometry scaling are not bound to a published generation | UNRESOLVED | No automatic extraction; caller-only trusted research baseline policy |

Evidence: [torque estimator](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/locationd/torqued.py#L53-L124),
[fit/publish/cache](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/locationd/torqued.py#L207-L271),
[custom overrides](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/latcontrol_torque.py#L134-L162),
[linear consumption](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/interfaces.py#L411-L418),
[friction compensation](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/__init__.py#L291-L299),
[ratio resolver](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/controls/lib/steer_ratio.py#L4-L20),
[learned geometry publish](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/locationd/paramsd.py#L166-L190),
[restore/reset](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/locationd/paramsd.py#L227-L266),
[parameter cache](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/openpilot/selfdrive/locationd/paramsd.py#L315-L322),
[stiffness scaling](https://github.com/ajouatom/openpilot/blob/604bc0a22733e648ec05b268da1ffaae7db52a69/opendbc_repo/opendbc/car/vehicle_model.py#L41-L45).

The torque cache source comment says 60 seconds but the condition is every 240
SubMaster frames; with its nominal 20 Hz livePose-driven loop that arithmetic is
about 12 seconds. This audit records the code trigger and discrepancy, not an
unverified real-time persistence interval. No reference persistence is implemented
or imported into cyberpilot-autotune.

## Mandatory gates and readiness

| Gate | Result | Action |
|---|---|---|
| control_active | UNRESOLVED | None; BLOCKED_CONTROL_ACTIVE_SEMANTICS |
| saturation | UNRESOLVED for required universal admission meaning | None; BLOCKED_SATURATION_SEMANTICS; restricted source alerts documented only |
| clock alignment | CONDITIONAL publication-clock policy; physical/causal sample linkage unresolved | Require explicit same-domain and caller limits; reject unavailable provenance |
| source validity | CONDITIONAL policy; transport flags proven, complete semantic validity unavailable | Reject until every prerequisite, including unresolved gates, is proven |
| baseline policy | CONDITIONAL caller-owned immutable baseline | No source extraction/Params/vehicle registry; reject missing or mismatch |

Final status: **CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED**. No actual adapter or
message-neutral mapper is started. The synthetic cases in carrot_signal_cases.json
are evidence specifications with static validation, not executed mapping results.
Future work needs a separately authorized resolution of applied lateral authority,
controller-specific saturation meaning and required timestamp/health provenance.
No Phase 8B, persistence or Apply work starts in this PR.
