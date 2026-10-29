# Future Carrot passive friction observation producer — NOT EXECUTED

This is a builder-ready proposal, not an instruction to implement in the current
task. Separate approval is needed for any native edit, source registration,
activation or runtime experiment. The approved task produced only this design,
offline audit artifacts/tests and additive CyberPilot CI hooks.

## Fixed inputs and acceptance boundary

- CyberPilot H7 basis: 5357d5d555d49b258affa237d83b8491b8a8c6ce, PR16 unmerged.
- Primary native base R: c2130730239bcdb4cbde9361ab90c8d99aa4ff55,
  rownlvh8875-coder/openpilot. C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3
  is a separate comparative port, not an automatic upgrade or device fingerprint.
- Normative design: superpowers/specs/2026-10-29-carrot-friction-producer-design.md.
- Machine-readable proposed mapping: evidence/carrot_friction_patch_wire.json;
  source/blob/symbol/range pins: evidence/carrot_friction_patch_sources.json;
  synthetic numerical counterexamples: evidence/carrot_friction_patch_math.json.
- Selected producer is passive/diagnostic. q_observed is always unavailable.
  An otherwise complete receipt is REJECTED/MISSING_Q, not an eligible observation.
- No native-to-H6 estimator bridge or application adapter. The native producer
  must not import CyberPilot, and this task does not implement a decoder either.

## 1. Reconfirm the source and freeze native tests (future RED)

Before editing, verify the exact base and reserved slot against all other users
of this fork. Branch movement invalidates automatic use of this proposal. Keep
opendbc helpers/interfaces, torqued, liveTorqueParameters publication, longitudinal
call sites and writer/safety/CarController behavior unchanged.

Extract a native synthetic harness around actual R callback/PID/controlsd sites.
It must record invocation order/args/types/raw return bits, PID gain getter count,
PID state transitions and original controlsState/carControl sends. Include LINEAR,
NN_LITE, NN, custom selector/equation, reset/inactive, override/freeze and clip paths.
Existing nonfinite sanitization/exception behavior is baseline, not redesigned.
Write failing tests for missing taps, incorrect feedforward call-site identity,
presence/unknown wire defaults, local CC consumption and observer-failure parity.
Do not count the current offline design audit as a native harness or passing
native regression. Run the full pinned native baseline first.

## 2. Proposed schema and service (future implementation)

| File / symbol | Edit boundary | Required tests |
|---|---|---|
| openpilot/cereal/custom.capnp / CustomReserved3 | rename to LateralTorqueIdentificationReceipt, keep type ID 0xda96579883444c35 and file ID; add proposed records/fields | compile, old/new reader interoperability, no reserved-slot collision |
| openpilot/cereal/log.capnp / Event.customReserved3 | rename to lateralTorqueIdentification, retain ordinal110 and type identity | other union members byte/type compatible; old empty payload rejected |
| openpilot/cereal/services.py / SERVICE_LIST | add lateralTorqueIdentification, 100Hz nominal, should_log=False | old service keys/frequencies unchanged; no default logging or startup activation |

Use the explicit 134-field wire mapping in 13 records and 16 enums. The other
10 H7 fields (ObservationPolicy and ObservationEligibilityDecision) stay local.
Never serialize an eligibility verdict or permission. Initial mapping ordinals
are proposed, not allocated; after shipping, preserve every explicit ordinal/type
and append new fields. A changed Python declaration order cannot renumber wire.

OptionalFloat64/UInt64/Bool/Digest have unavailable @0 :Void / value @1 :payload.
Required numeric wrappers must select value; optional/required struct pointers
need explicit presence validation, not default empty objects. Unknown enum0 and
missing schema version must never become LINEAR, zero or false. UInt64 overflow,
NaN/Inf, malformed fixed-length Data and duplicate IDs fail closed. Git revision
is Data20, SHA-256 digest Data32; session/cycle tokens are non-identifying. Restrict
Text to fixed semantic tokens, source-field IDs and versions. No VIN/dongle/route,
GPS/driver/rawCAN/images/full model output. Preserve all decoded consumed precision
as Float64; widening old Float32 telemetry does not recover raw local precision.

Required future tests include None vs0/False, default wrapper selection, absent
pointer, unknown enum, negative/overflow counters, schema-version mismatch,
Float32-rounding negative cases, old empty reserved messages and stable ordinals.
All allocations/bounds must be explicit in native implementation tests. No claim
of compiled cereal compatibility is made by this design-only mapping.

## 3. Cycle-local capture interface (future implementation)

Proposed native-only helper module:
openpilot/selfdrive/controls/lib/friction_observation.py. The interface is a
bounded, optional per-cycle capture sink, not a background collector or estimator.
Proposed operations: begin_cycle, capture_context, capture_callback, capture_pid,
capture_limits and seal. These are semantic interface names, not shipped APIs.

At Controls.state_control entry, begin the cycle BEFORE CC/local fallback LP
allocation and snapshot generation latching. Use a process nonce plus controller
generation and monotone cycle counter. At allocation, assign local CC/fallback LP
provenance from a deterministic per-cycle local allocation counter. Never id(),
address, wall time or branch name. Keep the provisional token separate from the
final CycleIdentity digest until actual control/command and completion times exist.

Capture each consumed reader together with its own SubMaster logMonoTime,
recv_frame, seen, valid/alive and role at the consumption boundary. No sm.update
or later latest-reader lookup may intervene. recv_frame is a local reception
sequence, not publisher sequence. Retained calibrated pose must retain the source
identity that produced it; the latest livePose identity is not a substitute.

Required roles are CAR_STATE, LIVE_POSE, LIVE_PARAMETERS, CAR_CONTROL and MODEL;
actually unused roles must be explicit. LINEAR still consumes modelV2 orientation.x
for model_good. This does not permit storing model payload. Bind actual local CC
values before Controls.publish later mutates orientationNED/angularVelocity.
Do not label the final published carControl Event as the earlier consumed source.

Snapshot actual consumed installed F/C, optional raw/filtered/effective offset,
selector AND executed callback family; applied VM wheelbase/centerToFront/ratio,
stiffness/effective steer ratio and effective custom settings with their witnesses.
Advance observational generations on exact tuple changes, without epsilon or
authority. A request, paramsd candidate or published liveParameters geometry is
not proof that VM applied it. Missing applied witnesses remain unavailable.

No effective-delay guess: capture only a delay actually selected/applied on this
branch, its source and raw/aligned status. Do not reread Params, copy a stale NN
initializer or use CP delay as an undocumented fallback. Raw alignment is explicit;
never shift values twice. Sample-pair IDs are required if future alignment occurs.

Future RED cases: duplicate cycle/source identities, future or wrong-clock source
time, stale/latest pose misjoin, later CC backfill, mode/F/C/VM generation drift,
unavailable local provenance, missing required MODEL and reused old source revision.

## 4. Exact callback and PID taps (future implementation)

Target LatControlTorque.update's actual feedforward callback call, not the two
setpoint/measurement calls used to compute pid_log.error. In the non-NN LINEAR
branch the feedforward site passes:

    a_cb = desired_lateral_accel - roll_compensation
    friction_input = desired_lateral_accel - actual_lateral_accel
    friction_compensation = True
    gravity_adjusted = True

The recorded raw return is ff before PID k_f. Record the executed callback family,
exact call site and raw operands/flags. Original callback arguments, order, call
count and return value must stay identical. Capture references/scalars around the
existing invocation; never invoke it again to observe. NN_LITE/NN/GM/custom-NN
remain diagnostic/unsupported and must never fall back to LINEAR. A controller
selector of CUSTOM does not identify the executed equation.

get_friction retains strict-interior center deadzone followed by existing
np.interp(error, [-threshold,threshold], [-C,C]); exact ±deadzone survive, no width
subtraction. Threshold0.3 is source semantics, not an H7 admission threshold.
No helper edit or first-class q exists in this passive proposal. q_observed=None,
never helper-term/C, parallel normalization or reconstruction mislabeled truth.

Add optional torque-only sink to PIDController.update, defaultNone for all old
callers. Preserve current speed assignment and original arithmetic types/order:
p=float(error)*k_p; f=feedforward*k_f; d=error_rate*k_d; optional i update/clip;
control=p+i+d+f; clipped self.control. Capture a gain at its actual old getter/read,
not an extra interpolation. k_i is unavailable if override/freeze skips that read.
Do not promote configured scheduled gains to a cohort actually consumed this cycle.
Preserve native Float32 pid_log.error readback; do not feed higher precision instead.
Capture the actual preclip local sum and actual clipped output, never reconstruct
their sum from published rounded components. Existing sign inversion to requested
torque must remain explicit and cannot replace raw ff.

Future tests: bitwise callback/PID/command/state parity with disabled/enabled/failing
sink, getter/callback counts, skipped k_i, wrong callback-site and raw/applied
substitution. Shared PID default compatibility must cover all existing native
callers; no longitudinal caller is edited. Reject the C*q rewrite using the
nonzero binary64 witnesses, not a claim that the discrepancy is vehicle-safe.

## 5. Limits, final sealing and publication (future implementation)

Capture same-cycle steeringPressed/override, source health, timer saturation,
instantaneous output limit and curvature/controls/vehicle limits independently.
Unknown is unavailable; do not backfill previous-cycle flags or infer a new
empirical limit threshold. H7/observation-v2 timer vs instantaneous distinction
is retained. Host/controller/applied outputs normally remain unavailable.

Keep existing Controls.publish Event creation and sends untouched. controlsState
t_ctl and later carControl t_cmd are distinct events. Complete the semantic snapshot
after the original command send; stamp CycleIdentity.receipt_complete_mono_time_ns, then
freeze final identity and compute content digest/serialize/publish with a separate
later Event time. Completion is NOT hashing/IO completion. Enforce preceding known
control/command <= next start <= local creation <= context <= callback <= PID <=
t_ctl <= t_cmd <= snapshot completion. External wire inputs may be older.
Late exact-linked downstream companions cannot mutate the sealed core or delay the
next cycle; no nearest-time joins. Do not invent downstream data just to fill fields.

Default activation is off via explicit startup construction option, not a Params
key. Callback/PID taps do bounded scalar assignment only; no formatting, hashing,
serialization, file/network IO, new subscriber, thread or extra Params access.
Observer-only failures drop/disable observation and preserve original exceptions,
commands, gains, sanitizer and control state. Do not swallow native control errors.

PubMaster.send(self,s,dat) synchronously runs to_bytes and send(dat); there is no
Python nonblocking parameter. Publication after command send is not timing-free
and may still harm the next cycle. Before activation, separately qualify bounded
allocation/serialization/transport, backpressure, drop/disconnect and deadline
behavior on the exact target build. Do not invent a safety cutoff or hide an
unqualified thread/queue. Failure to establish an execution budget means remain
disabled, not weaken the gate. should_log=False does not authorize persistence.

## 6. Registration, port and separate qualification gates

Instrumented native code has a NEW exact SHA/schema digest. Do not label it c213
or f5e4 to pass H7's existing source allowlist. Registration/decoder compatibility
is a separate explicit reviewed change; the proposed candidate SHA is unknown now.
No runtime fingerprint, parked test or Phase8B.2B acceptance is inferred.

Run pinned R full native tests/build/schema compatibility and synthetic parity
before any C port. For C, redo source/object checks and explicitly verify dynamic
SteerRatioRate/CustomSR/CenterToFrontRatio applied VM paths, mode and delay drift;
no automatic promotion. Current carrot-wip movement is only a source observation.

Current offline reproduction (these commands do not implement a producer):

    python -m pytest -q tests/audit/test_carrot_friction_patch_design.py
    GIT_NO_LAZY_FETCH=1 python -m tests.audit.validate_carrot_friction_patch_design \
      --reference-checkout /path/to/pinned-git-objects --verify-history

Native RED/GREEN tests, performance/transport gates, compiled schema compatibility,
device fingerprint, Phase8B.2B and empirical qualification are future/unexecuted.
Even an accepted native diagnostic producer remains MISSING_Q. Producing an
eligible independent q would need a separately justified and qualified design,
possibly a controller-math work item, not silent expansion of this passive patch.

## Stop conditions and retained blockers

Stop if consumed identities/capture stage cannot be proved, the reserved slot is
occupied, default/disabled behavior changes, source is unregistered, command/state
parity fails, or execution/transport bounds are unqualified. Do not relax H7.
No F/C recommendation, estimator fitting or selection threshold is permitted.
Candidate generation/application/runtime acceptance/owner proposals stay false.
All H7 scientific/application/device/artifact/watchdog/executor blockers remain.

Recommended next single task, only after separate approval: implement the selected
passive diagnostic schema/producer patch with native synthetic parity tests and
default-disabled activation. Not runtime use, estimator qualification or merging
the current H7/design PRs; those require their own explicit decisions.
