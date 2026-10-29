# H7 read-only friction wire proposal

Status: FRICTION_OBSERVABILITY_WIRE_DESIGN_READY /
REPRESENTATION_ENCODING_DESIGN_READY. Actual cereal compatibility and execution:
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED. No tags/ordinals/file IDs allocated;
log.capnp/custom.capnp and all native sources unchanged. No encoder, subscriber,
publisher or runtime producer implemented.

## Semantic inventory

evidence/friction_observability_receipt_schema.json enumerates 142 fields in 15
neutral records and 18 enums. It is a semantic proposal, NOT a cereal schema.
The pure schema builder and mutation validator reproduce it without any native
or optional dependency. Policy/eligibility-decision entries are local evaluator
metadata, not proposed control commands or authorization wire types.

| Kind | Proposed encoding | Required distinction |
|---|---|---|
| a/u/error/roll/deadzone/threshold/q | Float64 with explicit presence/status | direct local value vs legacy Float32 vs reconstructed |
| installed F/C/offset, effective gains, geometry, delay | Float64 with presence | context only; decoded input precision provenance retained |
| cycle/invocation/generation/sequence/time | UInt64 with presence where optional | actual zero is valid; absent never decodes as zero |
| active/compensation/health/limits | Bool with presence/status | None != false |
| stage/family/mode/origin/clock/source | explicit enums; unknown retained unsupported | unknown never maps to LINEAR |
| session/vehicle/context/event/pair identity | opaque non-identifying digest | content identity, not authenticity |
| consumed sources/downstream identities | bounded per-role/stage records with explicit IDs/times | no nearest-message/latest-seen substitution |

For optional scalars, propose an availability union or explicit presence/status
plus payload. A zero/default Cap'n Proto numeric field without presence is NOT
evidence of an observed zero. Python None always means unavailable.
No arbitrary vehicle-safe bounds are encoded; UInt64/finite domains and source
equation consistency are structural, not empirical selection thresholds.

## Precision

Pinned helpers/callback/PID operate with Python float and/or NumPy float64
binary64 values. Existing LateralTorqueState p/i/d/f/output/error/actual/desired
fields are Float32. The CP F/C/offset/gain tuning fields are also Float32.
Recording Float64 preserves the exact *consumed* binary64 representation,
including an input previously decoded from Float32; it cannot restore an
original pre-quantization intention. Legacy rounded output is never promoted to
direct local raw output simply by widening it to Float64.

PID error is written to the existing Float32 pid_log.error field before it is
read by PID.update. That is distinct from the full local friction-driving error.
The receipt must not relabel one as the other.

Q is normalized helper state, independent of installed C. The current helper
returns interpolation in [-C,+C], not q. Reconstructed q is a separate diagnostic;
it cannot fill q_observed. A future explicit helper-state implementation needs
reviewed semantics and numerical parity against legacy interpolation.

The three direct input operations (a=desired-roll_compensation,
error=desired-actual, roll_compensation=roll*g) require exact binary64 equality;
even one ulp crossing a deadzone boundary must not be hidden. For normalized-q,
callback/PID algebraic consistency only, the evaluator allows eight binary64 ulps
of roundoff at scale max(1,|a|,|b|). This is not a noise tolerance, safety
bound, low-error/jerk threshold or legacy-Float32 acceptance path. Precision/
origin/stage tags are checked independently.

## Causality and stage bindings

Entry context, callback observations and PID gains have different observation
times inside one cycle. Actual speed-effective gains are captured after PID
latches current speed, with their own cycle digest/time; querying them before
that would observe the previous speed. Installed configuration generation is
still bound to the entry snapshot.

control_event_mono_time_ns is actual cycle publication metadata, which can
follow callback execution. The cycle's deterministic IDs are assigned within
the trusted future call chain; final content digests can be sealed after the
publication time is known. Sealing is not an assertion that a future timestamp
was already known at callback entry.

A carControl builder consumed by the callback is LOCAL_CYCLE_OBJECT, not a later
published carControl Event. Requested/host/applied stages require distinct
DownstreamStageIdentity entries with actual event ID, exact source-command
event ID, monotonic time/domain, controller-cycle digest, exact-reference flag
and valid/transport health. A cycle label alone is insufficient.
A downstream event cannot precede its source command, exceed receipt completion,
or be substituted for raw callback u.

At in-cycle core finalization, future host/applied output normally is unavailable.
Leave it None. A future companion envelope may carry exact linked downstream
evidence; do not mutate the original immutable core or silently time-join it.

## Alignment and epochs

Core fields are unshifted actual callback observations. Delay source/effective
value is context, not an invitation to align core a/u/q. Already shifted core
values are rejected. A single separately identified downstream sample-pair
association can be described; its method/version/count/pair ID are explicit.
More than one correction is rejected. Pair identity and unapplied Params/LP
candidates are per-observation diagnostics, not new installed/applied epochs.
Actual geometry/SR/stiffness/delay/mode/F/C/gain/generation changes do split epochs.

## Versioning and decoding

Receipt version friction-observation-v1 is separate from exact source revision
and source-schema digest. Change semantic meaning, stage, unit, precision or
timing/cohort contract -> new receipt version. A new source SHA alone requires
explicit source compatibility registration/review, not automatic semantic-version
promotion. Current evaluator recognizes only pinned R/C source profiles.
Any real producer patch creates a new source/schema digest and needs registration;
existing pins are synthetic reference semantics, not evidence a producer exists.

Future decoding must reject nonfinite/invalid IDs/unknown required semantics,
preserve all unavailable fields, distinguish enum unknown from LINEAR, and
defensively copy lists. No permissive fallback/default coefficient is allowed.
Cap'n Proto round-trip/evolution/native-build/device tests remain future work.

## Privacy and authority

No VIN, dongle/route/GPS/driver identity, CAN frames, full model output or images.
Vehicle digest must cover only approved mechanical context, not an identifying
payload. Content hash is not a signature or trusted baseline. ELIGIBLE is local
structural observation status, not scientific qualification or application
permission. All four authority flags remain fixed false.
