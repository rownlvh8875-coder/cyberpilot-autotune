# Future capture architecture — design only

Status: FRICTION_OBSERVABILITY_CAPTURE_ARCHITECTURE_READY.
Verdict: ATOMIC_CONTROLLER_RECEIPT_RECOMMENDED.
Selected architecture: **A — cycle-scoped local capture in LatControlTorque.update,
with narrowly scoped helper/PID taps and exact source/applied-context input from
controlsd; one immutable final sealing at cycle publication.**

This is exactly one preferred architecture, frozen in intent before implementation.
It is not a producer patch. No native code/schema/helper is changed in H7.

## Options and qualitative scores

0=missing, 1=partial/supplied, 2=proposed complete with the stated future taps.
Scores are engineering comparisons, not empirical performance measurements or
post-hoc statistical model selection.

| Access / criterion | A: cycle-local capture | B: callback wrapper only | C: PID boundary only | D: controlsd wrapper only |
|---|---:|---:|---:|---:|
| raw callback input/output | 2 | 2 | 0 | 0 |
| independently observed q | 2* | 1* | 0 | 0 |
| actual speed-effective gains | 2* | 0 | 2 | 0 |
| exact executed family/mode | 2 | 1 | 0 | 1 |
| applied VM geometry context | 2, supplied exact | 1 | 0 | 2 |
| local + instantaneous limits | 2 | 0 | 2 PID-only | 1 |
| consumed source identity closure | 2, supplied exact | 1 | 0 | 2 |
| isolated testability | 2 | 2 | 2 | 1 |

*No current direct q output exists.* A requires a reviewed helper-state exposure.
A also requires actual effective-gain capture after current speed is latched.
B cannot recover these by dividing friction term by C or by joining later logs.
C sees scaled feedforward/feedback, not enough callback state. D sees returned/
requested outputs and source messages, not exact internal branch values.
A has the highest implementation coupling; B medium, C/D narrower. These costs
do not outweigh missing causal observability in B/C/D alone.

## Preferred sequence

1. controlsd supplies exact actually consumed source identities and the actual
   applied VM/installed-context snapshot, not later Params or LP lookups.
   A non-identifying session nonce and deterministic cycle/invocation IDs identify
   the cycle; no wall clock, Python id() or object address.
2. After controller parameter latching, capture installed F/C/optional offset,
   actual mode/function/site, source/vehicle/controller/gain/geometry generation.
   Offset is stored-but-unused for pinned LINEAR; no regressor is added.
3. Capture actual callback locals and return at the feedforward call, before k_f.
   Capture q from the actual future helper state before C multiplication.
4. Inside/at PID, capture speed-effective gains *after* self.speed=speed, plus
   p/i/d/f, preclip sum and clipped internal output. Installed gain generation
   and actual-use capture time are separate facts.
5. Preserve timer-qualified saturation separately from instantaneous clip/limit
   flags, steeringPressed/override and source health.
6. Finalize one immutable envelope once the actual control Event publication time
   is known. A cycle-scoped stack capture is not a background collector or
   persistent joiner. controlsd's finalization is plumbing for A, not a second
   preferred alternative. H7 implements neither taps nor finalizer.
7. Normally leave host/applied torque unavailable. Future downstream companion
   evidence must refer to the exact published command/cycle with its own event
   IDs/times/health; no nearest timestamp join and no mutation of the core.

The H7 neutral package only accepts supplied immutable data. It has no stack
builder, collector, subscriber, thread, singleton, timer or persistence.

## Independent q is a real remaining prerequisite

The existing helper computes np.interp(error,[-T,T],[-C,C]); there is no independent
normalized-q local/output. An outside wrapper can reconstruct a diagnostic, not
claim it observed the current helper's independent q. A future design must make
the C-independent state explicit and actually expose that state, with a reviewed
helper contract. Rewriting interpolation as C*q can differ at floating-point
roundoff; it is not automatically a bit-identical read-only patch. Preserve the
callback API and qualify numerical/behavior compatibility before implementation.
This prerequisite is why the next recommendation is an actual patch **design**,
not immediate producer implementation.

## Atomicity, performance and testability

One cycle-local receipt keeps raw a/u/q, mode, installed F/C, gains, applied
geometry and limit state under exact generations. It avoids reconstructing a
fictional cycle from asynchronous latest-seen topics. External dependencies still
require exact consumed IDs; an atomic envelope cannot authenticate a dishonest
producer or prove an omitted dependency was truly unused.

Capture bounded scalar metadata only. Avoid full arrays/model payloads, source
IO, Params rereads, encoding/network/persistence in the control hot path.
A future producer should separate value capture from serialization/hash work
where safe, measure allocation/latency, test callback coverage, and reject partial
cohorts. H7 has no measured controller performance budget and grants no runtime
acceptance. Native schema compatibility, restart/generation behavior, instrumented
q parity, source profile registration and Phase8B.2B remain unresolved prerequisites.
