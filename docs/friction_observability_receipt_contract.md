# H7 frozen read-only friction receipt semantics

## Intent and authority

Answer only: which exact inputs/context did one executed LINEAR feedforward
callback use, and what raw output did it return? This is an immutable neutral
evidence envelope, not a command, estimator result, application evidence, or
authorization. ELIGIBLE means structural observation completeness/consistency
only; all empirical, excitation, estimator, runtime and application gates remain.
H6 target u_cb=a_cb/F+C*q+b0 is unchanged. No H6 estimator bridge.

## Provenance / accepted requirements

H6 PR15 e3dd29df5d54a179017badf351138cdd4da977a5 passed 12/12 exact-head CI,
five append-only commits, final fresh C0/I0/M0, zero unresolved threads.
It merged 2026-10-29T08:55:18Z as a5d3514f23797829eb58d08c638b22cf4dd30c8a;
parents 43ca6761749e71ec575906f099b02386bc76d994 and H6 head.
H6 head ancestor and merge/head tree equality verified; this merge is H7 base.
H7 branch feat/friction-observability-receipt. Baseline 1261 tests pass.

Primary source pins R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55,
C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3. carrot-wip was rechecked at
H7 start and still equals C. Moving branches never auto-promote source profiles.
Acceptance basis: all six H6 observation/gap/estimand/identifiability/geometry/
result documents and three policy/source/geometry manifests, preserved unchanged.

## Chosen neutral design

Considered: (1) a flat all-required receipt discarding missing diagnostics;
(2) optional immutable raw receipt + separate pure structural eligibility
evaluator; (3) a runtime collector/adapter. Choose (2) per the user's recommended
separation: preserves truthful partial diagnostics without silent admission.
(1) loses missing-signal evidence; (3) is expressly out of scope.

Package observability/ contains enums/primitives, frozen source/cycle/context/
signal/stage contracts and a pure evaluator. No imports from research, estimator,
application, owner, adapters, native runtime, cereal, Params, network, IO,
processes or threads. No globals holding mutable state, collector or producer.
H6 geometry semantics are mirrored/linked explicitly in a neutral applied
geometry snapshot; importing H6 research would violate existing architecture.
No conversion to H6 samples or application types is exposed.

## Identity, causality and atomicity

Session is a non-identifying opaque SHA-256 nonce; cycle and generation IDs are
UInt64, never wall clock/object address. Receipt/source schema versions are
separate. Source revision is exact Git SHA, vehicle digest is mechanical context
only (no VIN/dongle/route/GPS/driver/CAN/model payload/images).

Cycle identity binds session, cycle ID, control Event monotonic time, callback
enter/exit, receipt completion time, exact source, vehicle digest and controller/
installed/geometry generations.
controller_cycle_start_mono_time_ns is the actual controlsd Controls.state_control
entry timestamp, before local CC/fallback-LP allocation and before the later
LatControlTorque entry/context snapshot. It is not reconstructed from Event time.
Consumed sources have explicit role, monotonic time/domain, sequence/opaque
identity, valid/alive and consumed/not-used state.
Required role declarations cover carState/livePose/liveParameters/carControl/modelV2.
Both pins pass modelV2 and read orientation.x for model_good even on the active
LINEAR path; its identity/time/health and consumed=True are therefore mandatory,
without storing model payload or applying an NN quality/sample threshold.
Other model/control inputs are declared if actually read. Latest-seen is not consumed.
Local cycle carControl builders are labeled LOCAL_CYCLE_OBJECT; a later published
carControl Event is never retroactively called a consumed input.
For both pinned profiles, carState/modelV2 origin must be WIRE_EVENT and carControl
origin must be LOCAL_CYCLE_OBJECT. Every consumed local object additionally
binds controller_cycle_digest to the exact current CycleIdentity.digest; source
identity/sequence cannot be reused across distinct cycles in the same session
and controller instance. Unchanged wire samples may legitimately be consumed
again. liveParameters is not blanket-classified as wire: the pinned source has
a lateral_vehicle_parameters local fallback, which requires the same explicit
local-cycle binding when represented. This is structural provenance only, not
proof that a declared producer or fallback is authentic or active.

Every core scalar has value-or-None, observed stage, precision, origin, cycle
binding and capture time. Source cohort duplicates, future consumed times,
wrong clocks, mixed snapshot/cycle IDs and generation mismatches fail closed.
control_event_mono_time_ns is the controlsState Event timestamp (t_ctl), distinct
from the later requested carControl Event timestamp (t_cmd). Pinned R/C create
and publish controlsState before creating/publishing carControl. Consumed source
time <= context; cycle start <= local-object creation <= context <= callback entry
<= exit <= PID/gain capture <= t_ctl <= t_cmd <= downstream events <= receipt
completion. Optional downstream observations use
their actual Event times; t_ctl and t_cmd need not be equal. Snapshot
evidence is captured within the cycle; downstream values require their own
exact causal references. Unavailable downstream stages stay None.
For increasing cycle IDs in the same session/controller instance, the next
cycle start (and therefore local creation/context/callback) cannot precede the
previous t_ctl, or
previous requested-command t_cmd when that Event identity is supplied. This
matches the pinned serial update -> state_control -> publish loop. Do not use
previous receipt completion or host/applied companion times as the boundary:
later downstream evidence can legitimately complete after the next cycle begins.
A new session/instance starts a separate epoch, not an implicitly pooled sample.
Older wire inputs are permitted before cycle start; consumed fresh local objects
must lie inside their own [cycle start, context] interval even without previous.

No freshness, low-error/jerk/speed/excitation/sample-count/F/C range or condition
number safety cutoff is invented. Structural numerical equation consistency
uses a documented binary64 roundoff allowance, not an empirical threshold.
The source threshold constant 0.3, normalized q's [-1,1] domain and exact helper
zero/clipped states are not relaxed by that arithmetic allowance. An available
offset also requires consistent installed/filtered/raw source-field provenance;
an unavailable optional offset remains None, not an invented zero/regressor.

## Exact LINEAR and q

a_cb=desired_lateral_accel-roll_compensation, roll_compensation=roll*g.
friction_input=desired_lateral_accel-actual_lateral_accel.
Strict interior deadzone zeroes input; endpoints survive. Normalized q is
clip(centered_error/threshold,-1,1) when compensation is enabled, otherwise zero.
Raw u is actual callback return before PID k_f; installed F/C are CONTEXT_ONLY.

Existing source interpolates [-threshold,+threshold] to [-C,+C], returning the
friction term, not a separately exposed normalized q. Thus no existing producer
can supply direct q by observation. q_observed requires a future explicitly
instrumented helper state; q_reconstructed is diagnostic only, never a fallback
and never friction_term/installed_C. A future helper refactor/tap needs numerical
parity review: normalized multiplication need not be bit-identical to interp.

Both raw inputs and observed q are required for the full LINEAR contract.
Source-consistency checks do not infer optimal friction. latAccelOffset is
recorded with exact installed field/origin and optional value; the pinned LINEAR
callback does not consume it. It is not a new regressor.

## Context and stages

Actual executed callback family, standard/custom selector and call-site identity
are distinct. Supported eligibility stage is LINEAR_CALLBACK_PRE_PID, including
explicitly bound CUSTOM+LINEAR; NN_LITE/NN/GM/other remain diagnostic only and
IDENTIFICATION_MODEL_UNSUPPORTED. Wrong scalar stage never falls back to LINEAR.

Required installed parameter and speed-effective PID gain snapshots have exact
generations, cohort/capture binding; p/i/d/f alone do not establish gains.
Stage decomposition separately labels raw callback, scaled f, p/i/d, preclip sum,
post-PID clip, requested actuator torque, host/controller output and applied
normalized torque. Signs are explicit: internal PID output is negated at the
LatControlTorque return. Downstream optional values cannot substitute raw u.
No observation of future applied output is fabricated inside a callback.

Applied geometry includes source/vehicle/generation/actual VM snapshot identity,
wheelbase/axle ratio/stiffness/effective SR and raw/effective SR-rate/CustomSR.
R uses static CP baseline plus actual applied VM SR/stiffness; C requires actual
applied VM geometry, not Params request/paramsd target/LP candidate. Zero intent
means VEHICLE_DEFAULT; missing applied ratio stays None. No vehicle defaults.
Delay has source/effective value, method/version, raw vs already-aligned state,
application count and sample-pair identity; reject double correction.
Limits separately record timer saturation and instantaneous controller/curvature/
steer/actuator limits, steeringPressed, override, activity and source health.

Pure evaluate(receipt, policy, previous=None) returns a reasoned immutable
decision, never a qualified estimator/application object. previous is caller
state, not a cache; detects duplicate/out-of-order cycles and epoch context
changes. Any geometry/mode/installed F/C/gain/SR/delay/generation change rejects
pooling; the caller may explicitly start a new epoch with no previous.
Digest is canonical content identity only, never authenticity or authority.
None/zero/False and legacy Float32/direct binary64 origins remain distinct.

## Wire and capture (design, no implementation)

Float64 for local numeric values preserving Python float/NumPy float64 binary64;
UInt64 for IDs/times; explicit presence/status for unavailable values; enums for
stage/family/mode/origin/precision/source; Bool only with presence distinction.
No actual cereal tags. Semantic/unit/precision/timing/stage changes version the
receipt; source SHA changes alone do not automatically version semantics.
Runtime encoding remains unqualified until actual compatibility/device tests.

Evaluate future capture choices A=cycle snapshot inside LatControlTorque.update,
B=callback wrapper only, C=PID boundary only, D=controlsd wrapper only. Prefer A:
in-cycle local callback/helper and PID taps, supplied exact consumed-source/applied
VM snapshots, one immutable core finalization. Helper instrumentation is a future
prerequisite, not current q availability. Downstream application receipts remain
external linked evidence; never mutate the original core or use nearest joins.
No producer code is implemented. Final scores/explanation in capture document.

## Verification and publication

Twenty required synthetic fixtures: full LINEAR, missing q/u, wrong mode,
deadzone interior/±boundary, compensation off, saturation/override, geometry/F/C
changes, source-time mismatch, duplicate cycle, nonfinite, legacy Float32-only,
NN_LITE/NN diagnostic and applied-as-raw negative control. Add properties for
canonical ordering/determinism, source/mode/generation changes, None vs zero/
False, precision, missing q independence from C, epoch changes, source duplicates,
future source times and clock domains.

Source audit pins R/C callback inputs/LINEAR and NN equations, helper/threshold/
compensation, custom latching/unused offset, PID ordering/scaling/clip/sign,
geometry and old observation-v2. Each claim has repo, revision, path, symbol/range,
blob and range SHA-256. A separate semantic schema manifest lists every nested
field/type/unit/stage/requirement/source/availability/eligibility meaning.

Retain all H2-H6 validators/results/tests, old coverage floors and goldens; new
package >=98% statements/>=95% branches, target 100/100. Full pytest, lint,
format, mypy, source/history audits, build and isolated vanilla/research wheel.
Fresh independent exact-head review; C/I findings require RED->append-only fix->
full rerun->NEW reviewer. Publish only requested Draft PR; no H7 merge.

## Rulings / scope

Ruling: reuse dedicated cloud checkout and requested branch — onboarding explicitly
prohibits extra worktrees without a request; cost is reduced concurrent-branch
isolation, mitigated by clean baseline and protected-file audit.
Ruling: neutral mirror/link of H6 geometry, not a research import — required by
existing architecture; cost is duplicate semantic definitions, mitigated by
source/projection parity tests and preserved H6 implementation.

Forbidden: actual native/cereal/custom schema/controller/torqued/controlsd change,
Params access, publisher/subscriber/runtime producer, persistence/writer/vehicle,
estimator qualification/candidate/SteeringRequest/AuthorizationGrant/application,
PR8/9 mutation, external AI, longitudinal or upstream PR. No new real/holdout/
evaluation data and no repeated artifact search. No automatic next task.

Final statuses distinguish receipt/wire/capture/encoding DESIGN readiness from
FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED,
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED,
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED,
NO_EMPIRICAL_ESTIMATOR_BRIDGE and all existing frozen-artifact/factor/bounds/
fingerprint/watchdog/external-executor/application/identification blockers.

## Source-grounded implementation clarifications

The entry context timestamp covers installed/applied context. Actual speed-effective
PID gains are captured later, after current speed latching, with their own cycle
digest and capture timestamp. One atomic receipt is one cycle, not a claim all
stages existed at a single instant. Final sealing can occur after publication.

Pinned LINEAR feedforward passes compensation=True. A known disabled-compensation
receipt retains q=0 as a valid diagnostic, but is not eligible for that pinned
call site; this is distinct from an unknown flag.

Optional downstream values require actual command/event lineage, monotonic times,
clock, source validity/transport health and exact-reference witnesses in addition
to a cycle label. No future applied output is invented during core capture.

Historical compatibility exception: only three old namespace inventory allowlists
add observability. Original source/golden hash checks remain. H6 history accepts
only those exact byte substitutions; its other AST and all candidate code/results/
policy remain unchanged. This scoped amendment is separately mutation-tested.
