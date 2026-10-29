# Carrot Read-Only Friction Producer Patch Design

## Authority, intent and acceptance

The user's approval of the next single task authorizes the previously recommended
actual Carrot read-only schema/producer **patch design**, not native implementation,
merging H7, a device experiment or application. This document is the design unit;
the accompanying execution plan builds only documentation and offline audit tools.

Design base: CyberPilot H7 exact head
5357d5d555d49b258affa237d83b8491b8a8c6ce, PR16 OPEN/Draft with exact-head C0/I0/M0
and push/PR CI success. PR16 is not merged. The design branch is stacked on that
head, with a proposed Draft PR against feat/friction-observability-receipt.
PR8/9 remain untouched at e4361678ed176cbd7c0bb6f838d3daa7174caf22 and
6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5.

Primary native blueprint: R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55 in the user's
openpilot fork. Comparative port profile: C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3
in ajouatom/openpilot. carrot-wip was re-read and remains C. This is not evidence
of the user's device fingerprint, and C is not promoted to the runtime profile.

Acceptance: a builder can identify exact future edit sites, immutable wire fields,
capture order, unavailable semantics, compatibility tests and qualification gates.
The design must not conceal a controller-math change behind an observability label.

## Approaches and selected boundary

H7 architecture A remains selected: cycle-local LatControlTorque capture, narrowly
scoped PID taps, exact caller-supplied context, final sealing after publication.
Callback-only, PID-only and controlsd-only capture cannot supply all internal stages.

For q specifically, three alternatives were considered:

1. **Passive legacy-preserving capture, selected.** Leave helper/callback arithmetic
   unchanged. Capture actual a/error/raw u, installed/applied context and PID stages.
   q_observed is UNAVAILABLE; optional reconstruction is a separately named offline
   diagnostic and never fills the wire truth field. This produces partial diagnostic
   receipts, not eligible H7 identification observations.
2. Replace interpolation with first-class normalized q then C*q. This creates an
   actual C-independent control state, but synthetic counterexamples show changed
   binary64 outputs. It is a separate controller-math change, not this read-only
   patch, even if differences seem small. No vehicle-safe tolerance is inferred.
3. Add a parallel normalization solely for telemetry and call it observed q.
   Rejected: moving reconstruction into the helper does not prove it was the
   operational state used by the legacy term. Dividing by installed C is also
   forbidden, including when C is zero.

The binding H6 estimand remains u_cb=a_cb/F+C*q+b0. A finite synthetic corpus does
not prove universal equivalence or impossibility of every future implementation;
it disproves a universal bit-equivalence claim for the straightforward rewrite.
No empirical estimator bridge or scientific qualification is introduced.

## Exact proposed native patch surface (NOT applied)

| Native file | Proposed future edit | Preservation condition |
|---|---|---|
| openpilot/cereal/custom.capnp | rename empty CustomReserved3 to LateralTorqueIdentificationReceipt, add owned fields/nested types | retain 0xda96579883444c35 and file ID; no other reserved payload reused |
| openpilot/cereal/log.capnp | rename customReserved3 Event member to lateralTorqueIdentification | retain ordinal 110 and its reserved struct identity; existing union members/types untouched |
| openpilot/cereal/services.py | add matching service, nominal 100 Hz, should_log=False | no old service/frequency/queue changes; frequency is source control rate, not sample admission |
| openpilot/selfdrive/controls/controlsd.py | supply cycle/source/installed/applied snapshots and finalize after existing command send | do not change command values, message timestamps/order or existing Params reads |
| openpilot/selfdrive/controls/lib/latcontrol_torque.py | capture actual FF invocation and returned raw value around the original single call | no callback replacement, extra callback evaluation, equation or argument changes |
| openpilot/common/pid.py | optional torque-only tap of values at their existing computation sites | default None for all old callers; no longitudinal call-site/gain/state changes |
| openpilot/selfdrive/controls/lib/friction_observation.py (new) | bounded passive capture/validation/sealing support | no Params, network client, subscriber, writer, estimator or application bridge |

No edit to opendbc friction helpers, interfaces, torqued, liveTorqueParameters,
CarController, safety, longitudinal logic or actuator ownership is in the selected
patch. Shared PID tap compatibility for every old caller is a mandatory test gate,
not a claim that timing overhead is zero. Native edits above are a future plan only.

## Wire and schema evolution proposal

Both pins reserve empty CustomReserved3 at type ID 0xda96579883444c35 and Event
ordinal 110. Reuse of that designated fork slot, preserving its identity/type link,
is preferable to allocating a new global Event ordinal or opaque raw Data channel.
These are proposed names/ordinals in a design manifest, not an allocation or patch.
Revalidate the exact reservation and other fork users before implementation.

The neutral H7 semantic inventory has 144 fields in 15 records. ObservationPolicy
and ObservationEligibilityDecision are evaluator-local and excluded from wire;
all other fields receive an explicit proposed ordinal/type mapping. Authority and
eligibility decisions are not serialized as permissions. Enum wire values reserve
0 for unknown; numeric ordinals do not inherit Python declaration indices.
The initial proposal derives ordinals from the frozen H7 inventory. After any
native schema ships, its explicit ordinal map is authoritative and append-only;
never regenerate shipped ordinals from a changed Python declaration order.

Use explicit OptionalFloat64/OptionalUInt64/OptionalBool/OptionalDigest unions:
unavailable @0 :Void, value @1 :payload. Do not use a numeric default to represent
absence, nor assume a generic parameter can wrap primitive Cap'n Proto values.
Optional structs require pointer-presence validation. Empty/default structs and
unknown required enums are not valid observations. Required Float64 values retain
the exact consumed binary64 value; old Float32 telemetry is never promoted to raw.

Native source revision is 20 binary bytes, SHA-256 content IDs 32 bytes; decoding
to H7 lower-case hex is deterministic. Session is a non-identifying random nonce
created once per controller process, not a route/dongle/VIN. Optional digests retain
presence separately. Times/counters/generations are UInt64. Float64 values reject
NaN/Inf. Text is restricted to schema/version/source-field/alignment tokens, not
arbitrary vehicle, location or model payloads. Source roles are bounded by H7's
seven roles, downstream identities by its three distinct downstream stages.

Receipt version friction-observation-v1 is separate from source and schema digests.
A future decoder requires explicit presence and supported semantics; unknown/new
versions fail closed. Old empty reserved messages fail required-version/presence
checks, never decode to zeros or LINEAR. Old readers may ignore new fields; field
renaming is not a promise that old string-based APIs know the new service name.
Compile/evolution/round-trip tests remain required before runtime qualification.

## Atomic capture sequence and exact identities

1. At Controls.state_control entry, sample cycle start before local CC/fallback LP
   allocation. Use the pinned messaging monotonic clock conversion consistently;
   do not mix wall time, floating-source seconds or unexplained clock domains.
2. Snapshot each actually consumed reader with its own logMonoTime, recv_frame,
   seen/valid/alive, source role and process/session identity at consumption. No
   sm.update or later "latest" lookup is allowed between reference and metadata
   capture. recv_frame is local receive identity, not an invented publisher sequence.
3. Assign fresh local CC identity at allocation: session/controller generation/cycle
   plus deterministic local allocation counter. Source time lies in [start,context].
   It is not the later published carControl Event and never Python id()/address.
   Local fallback LP needs the same binding, not a fabricated liveParameters Event.
4. Required roles are carState, livePose, liveParameters, carControl and modelV2.
   CS/model are wire-origin, CC local. modelV2 is consumed even on LINEAR because
   model_good reads orientation.x. Capture only IDs/health, not model arrays. A
   genuinely unused livePose is declared unused. Exact calibrated-pose dependencies
   must follow their actual retained source IDs, not a newer livePose message.
5. Capture actually latched F/C/optional offset/custom selector and the actual VM
   tuple after existing latching. Increment observational generations on exact
   installed/applied tuple change; no epsilon, writer ownership or authority is
   implied. Requested/paramsd/LP candidate geometry cannot replace applied state.
6. At the actual FF call, capture original scalar inputs/flags and exact executed
   branch/function/site; invoke the callback exactly once; record its raw return.
   NN_LITE/NN/GM/unknown remain unsupported diagnostics. CUSTOM alone is not a family.
7. PID taps capture actual operands without re-evaluating gain getters: current
   speed is latched first; capture each gain when the old code reads it, p/i/d/f,
   actual preclip local sum, limits and clipped output. A skipped integrator gain
   read is unavailable, not a recomputed claim of actual use. Preserve float32
   pid_log.error consumption and native operation order/types/grouping.
8. Capture same-cycle timer saturation separately from instantaneous controller,
   curvature/controls/vehicle limits, override and source health. If the exact
   current flag is unavailable, do not replace it with the previous cached flag.
9. Existing publish later mutates CC orientation/angular velocity. Never use that
   final CC to backfill the earlier consumed local object. Create controlsState and
   carControl Events at their existing sites; preserve their distinct t_ctl/t_cmd
   and sends. Finalize only after the actual command send when it is included.
   Read-only observation gets its own later publication time, not a fabricated
   callback/control Event timestamp. Host/applied outputs normally remain None.

Enforce previous known command/control <= next cycle start <= local creation <=
context <= callback <= PID/gain capture <= t_ctl <= t_cmd <= receipt completion.
Wire samples can be older; late host/applied companion completion cannot delay the
next cycle. The one core receipt is immutable; later exact-linked companion data
is separate, never a mutation or nearest-time join.
Taps use a provisional session/generation/cycle token, not a premature final
CycleIdentity digest. Construct the final identity only after actual t_ctl/t_cmd
and CycleIdentity.receipt_complete_mono_time_ns are known. Completion here is the
immutable semantic snapshot boundary, before hashing/serialization/transport,
not a claim that transport has completed. Late companions link to that final ID.

## Capturability and honest partial results

q_observed is always None in the selected legacy-preserving patch. Configured
effective gains not read in a branch are also None. If an effective delay was not
actually selected/applied on a branch, report it unavailable rather than reread
Params, assume CP delay, or borrow an NN initialization value. Alignment is raw;
do not shift callback values to match a downstream topic. Any missing applied VM,
installed/source/limit witness remains unavailable with structural rejection.

The native module does not import CyberPilot or run an estimator. A future boundary
decoder can construct neutral receipts only when structural identities are present.
It must report MISSING_Q for an otherwise complete passive receipt. A new native
patch SHA/schema digest must be registered explicitly; never label instrumented
source as the old R/C pin to bypass H7's source allowlist. No candidate new SHA is
known in this design, so registration and runtime fingerprint remain unqualified.

## Noninterference, failure and resource gates

Disabled by default through an explicit startup construction option, not a new
Params key. Old callers pass no observer. Taps perform bounded scalar assignment
only: no formatting, hashing, serialization, persistence, new subscriber, callback
re-evaluation or extra Params read. Observer-only failures drop/disable observation;
do not catch original controller exceptions or modify the existing sanitizer.
No error recovery is allowed to modify commands, PID state, control mode or limits.

Serialization/publication is after the existing command send, outside callback/PID
computation. Existing PubMaster.send serializes synchronously and supplies no
nonblocking argument in its Python API: do not call it nonblocking or timing-free.
Activation requires measured bounded transport/allocation/deadline behavior and
failure injection on the target build. No thread/background collector is added as
an unexplained workaround. If transport cannot satisfy the execution gate, retain
disabled capture/publication. Numeric parity is not scheduling or vehicle safety.
No latency/memory safety threshold or sample-selection threshold is invented here.

## Required future implementation/qualification tests

- old schema/reader vs proposed reserved-slot messages; required presence, unknown
  enums/version, None/zero/False, finite Float64, UInt64, duplicates and bounds;
- source SHA/blob/range checks, exact required MODEL consumption, old wire reuse,
  local-object creation/cycle bindings, calibrated-pose retained IDs, context drift;
- disabled observer and observer-failure injection preserve callback args/call
  count/return bits, PID state/return bits and requested commands over synthetic
  LINEAR/NN_LITE/NN/GM/custom/reset/override/freeze/clip/nonfinite cases;
- actual gain-read and preclip taps, not reconstructed stages or extra getter calls;
- passive q always unavailable; C*q rewrite counterexamples preserved; no installed
  C-derived or telemetry-only normalization labeled HELPER_OBSERVED;
- full R baseline regression before any C port; C port separately verifies dynamic
  applied geometry; source/profile registration, fresh wheel and native builds;
- bounded native transport/failure/performance tests before any parked runtime
  qualification. Device/Phase8B.2B/application gates remain separate and unstarted.

The companion implementation plan assigns exact file/symbol edits and RED/GREEN
gates, but its native tasks are future work, not approval to execute them now.

## Status and non-goals

Read-only diagnostic patch design can be ready while full H7 producer eligibility
is blocked. Retain FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED,
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED,
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED, NO_EMPIRICAL_ESTIMATOR_BRIDGE,
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE, factor/parameter qualification unresolved,
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED, RUNTIME_FINGERPRINT_UNCONFIRMED,
WATCHDOG_EXECUTION_MODEL_UNRESOLVED, EXTERNAL_EXECUTOR_UNQUALIFIED and
APPLICATION_NOT_AUTHORIZED. All four authority flags remain false/absent.
No actual native/schema/producer/Params/controller changes, upstream PR, real data,
vehicle, application, longitudinal or external AI integration are performed here.
