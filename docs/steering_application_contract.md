# Steering-only bounded host application contract

This is implementation of the owner-approved application core, not a deployed
vehicle autotuner. It can call an explicitly supplied target's commit capability.
No production target or allow-all authorizer is supplied. Longitudinal is excluded.
No existing OFF/SHADOW engine behavior, read-only integration or replay is changed.

## Single implementation and source reuse

CyberPilot remains the owner of its identification/evidence work. The
[four pinned interface hashes](evidence/steering_application_sources.json) were
verified at 02652a441c1c39b4a9c3bfaf1132217f0e57b384. The original audit pin
588d6b21c21089065a7d9165d6e7a438e8aa6297 is unchanged. Source bodies, estimators,
private data and vehicle constants are not copied. `inspect_research_report`
accepts an explicit dict export, without importing CyberPilot. A recognized
profile or numerical diagnostic remains RESEARCH_ONLY and unauthorized. Asserted
true permission flags, wrong revisions and malformed exports cannot promote it.
Numerical estimates and raw diagnostics are neither retained nor converted.

The current residual-statistics learner is also research-only. Its heuristic
confidence is not independently qualified torque/friction identification.

## Explicit inputs and trusted capabilities

`BoundedSteeringApplicator(policy, baseline, target, authority, clock)` does not invoke
target/authorization/clock methods at construction. Every argument is required.
All contracts are frozen and defensively copy nested parameter mappings.

- SteeringPolicy binds scope, owner, source revision, static context, observation
  context, baseline epoch, non-identifying session token, parameter specs, sample/
  confidence/speed gates, source/target/evidence/authorization ages, transaction
  and rollback deadlines, maximum hold and consumed-ID capacity.
- TargetSnapshot is a coherent selected tuple with revision, monotonic sample
  timestamp, owner/context/epoch/scope and finite values. Only lat_accel_factor,
  friction and a preserved lat_accel_offset can be represented. The offset is
  never a tunable selector. No longitudinal or safety-limit key is accepted.
- SteeringRequest binds one proposal, exact observation, qualified evidence,
  policy digest, session and expected current target revision. Evidence binds its
  content/source/context/target revision and monotonic generation time.
- ApplicationAuthority is an independent trusted caller component. It validates
  real evidence qualification, policy approval, authentication and one-shot grant
  issuance. There is no production implementation in this change. Typed quality,
  scope, a digest or a confidence value is not an authentication boundary.
- AuthorizationGrant binds exact request/policy/evidence digests, issuance and
  expiry. It must be returned by the injected authority for this exact request.
- SteeringTarget is a synchronous single-owner capability. Its snapshot must be
  current and immutable. Its CAS commit compares the expected revision and
  atomically replaces the whole selected tuple, returning exactly revision +1.
  The owner must exclude all competing writers and preserve unrelated state.

This Python API is not a sandbox for malicious injected code. Native owners must
prove the port contract; a setter, bool lease or metadata label is insufficient.

## Admission and transaction

1. Reject closed/faulted domains without calling clock, authority or target.
2. Reserve the structured request sequence and bounded proposal identity before
   later validation. Sequence high-water never decreases. IDs are the sequence
   encoded as 32 lowercase hex digits within the explicit session. This prevents
   replay after ID eviction using a different sequence; no unbounded history.
   Invalid structured sequence requires a fresh owner session.
3. Validate monotonic time and any existing hold expiry, then reserve a structurally
   valid, clock-safe observation timestamp even if admission later rejects.
4. Require exact session/policy/source/context/revision/evidence bindings, live
   source, explicit active control, available speed at the caller minimum, no
   override/saturation, trusted baseline identity, ordered/fresh input and exact
   proposal context/time. Check independent qualification, samples and confidence.
5. Read the target; require coherent identity/tuple, expected revision and current
   values. Check hard bounds, maximum step from current verified values, and rate
   from the last verified change (initially the trusted baseline time anchor).
   Use exact rational comparisons of finite input numbers; never clip.
6. Ask the independent authority, verify its grant, and reread the owner tuple.
   A changed revision is a conflict even for a no-change request. Check deadlines
   before downstream freshness checks so known timeout faults cannot be masked.
   Pass the current monotonic time to the authority and refresh it after the
   callback. Grant age/expiry is checked after authorization, before commit and
   after readback, including time spent inside caller capabilities.
7. Commit via CAS, validate the acknowledgement and independently read back the
   entire tuple/revision. Check time, hold/grant expiry and source again. Only
   this path returns VERIFIED. A no-change result commits nothing and does not
   renew the existing hold. Offset and untuned values are preserved exactly.

Evidence hashes use deterministic canonical JSON bytes with sorted keys and no
nonfinite values; they are exact representation identities, not signatures or a
claim that 10 and 10.0 have identical bytes. Clock and source domains are explicit
caller obligations. No wall clock, worker or mutable singleton exists.

## Rejection, recovery and lifecycle

Any rejected update while a value is owned restores the trusted original
baseline in the same call, subject to actual owner access. Recovery first reads
the target and compares it against the last verified owned revision or the exact
pending CAS cohort. It never overwrites an unknown/foreign revision, including
after an uncertain write. An atomic write that succeeded and then raised can be
identified from matching revision/tuple and recovered; partial/foreign writes
cannot be guessed back into ownership.

Recovery itself is CAS plus independent baseline readback. Exceptions, malformed
acknowledgements and rollback deadline failures are exposed even if the baseline
is finally observed. Baseline recovery is a distinct priority operation, not an
adaptation step/rate update. A real owner must approve its recovery dynamics and
latency; controller actuator limits are never widened by this core.
The recovery deadline starts at recovery entry, excluding idle time since the
previous evaluation. A failed recovery-entry clock still permits best-effort
coherent baseline restoration, while timing qualification remains faulted.

ApplicationReceipt contains the reason/state/attempt sequence, immutable baseline,
effective values only when observed, verified revision, last valid evaluation
clock and optional recovery reason. **Unknown readback is None**, never an invented
baseline. ROLLBACK_FAILED means restoration was not proven. A clock fault may
still permit coherent value readback, but timing qualification remains failed.
Host readback does not prove physical steering or a vehicle response.

States are READY, ACTIVE, DISARMED and FAULTED. Veto recovery can return READY;
clock/context/owner/authority/deadline/uncertain-write faults latch FAULTED. No
automatic retry, rearm or restart exists. `disarm()` restores owned values and
closes the domain; a domain with no owned application makes no baseline-readback
claim. A new reviewed owner session requires a new instance and fresh owner
evidence/authorization, not reuse of a rejected attempt.

`watchdog(snapshot)` must be invoked synchronously by the owner. It checks source,
coherent target state and the active hold expiry; stale/unavailable/override/
saturation causes recovery. Expired holds latch a fault even if a fresh proposal
arrives. Hold deadlines are not extended by replay or no-change calls.
Hold expiry is checked before an ordinary veto can clear the active state, after
authority callbacks even when they deny/raise, and after watchdog target reads.
Watchdog source freshness is also rechecked after the read returns.

There is no autonomous timer or hard real-time preemption. Callback overruns are
detected after return; if the caller stops invoking the domain, this library
cannot restore a controller. An external owner/watchdog guarantee is mandatory
before any concrete vehicle writer is qualified.

## Real integration gates still unresolved

Pinned Carrot c2130730239bcdb4cbde9361ab90c8d99aa4ff55 already writes torque
parameters through controlsd.py:138-142 and latcontrol_torque.py:135-141; custom
torque can make the setter a no-op. No CAS owner revision or exclusive arbitration
is provided by that API. These source facts prevent wrapping it as if it already
satisfied SteeringTarget.

Before a concrete writer: prove source/units (especially diagnostic friction
versus controller coefficient), parameter identification/independent confidence,
single owner versus torqued/custom/NN paths, trusted baseline/epoch/revision,
owner-approved numeric bounds/rates and recovery/watchdog acceptance. Actual
runtime source/fingerprint and parked qualification are also still absent.
These gates are not filled using synthetic values. No actual Carrot writer,
runtime engine/learner connection, Params access, persistence, install, vehicle
test, real log or upstream PR is included. PR #8 remains separately read-only.
