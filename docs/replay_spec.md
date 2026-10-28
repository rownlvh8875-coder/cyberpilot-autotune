# Deterministic synthetic replay schema v1

Implemented in replay/. Persistence remains NOT_AUTHORIZED. No library file or
network API, real log decoder, data collection, vehicle adapter or controller
application is provided.

## API and lifecycle

`load_replay(document: str) -> ReplayScenario` validates the entire JSON document
before either engine exists. `run_replay(scenario, *, timer_ns=...)` revalidates
the immutable scenario, creates fresh OFF/NoOp and SHADOW/residual engines and
returns ReplayReport. No state survives a run. The timer defaults to
perf_counter_ns and measures processing only, excluding parsing/report hashing.

Only one synthetic parameter is supported. Documents are capped at 256 KiB UTF-8
and 1..1000 events. These are research resource caps, unrelated to vehicle limits.
Missing/unknown/duplicate fields, nonfinite numbers, numeric booleans, incorrect
types, unsupported versions, ambiguous units and inconsistent clock/order raise
ValidationError before execution. Constructor/configuration and timer errors stay
visible. Existing engine exceptions produce baseline results with INTERNAL_ERROR
and fail software acceptance. No partial engine trace is returned for invalid JSON.

## Exact schema

| Root field | Required value or contract |
|---|---|
| schema_version | Integer 1 |
| scope | SYNTHETIC_TEST_ONLY |
| learner_version | residual-ewma-v1 |
| time_domain | synthetic.monotonic.v1 |
| monotonic_origin_s | Finite nonnegative synthetic origin |
| units | Exact canonical map below |
| baseline_parameters | Single declared parameter, finite and within spec bounds |
| parameter_spec | Every ParameterSpec field; synthetic.* ID; persistence_eligible=false; REJECT |
| gate_config | Every GateConfig field, including caller-supplied minimum_speed_mps |
| learner_config | Every ResidualStatisticsConfig field, without defaults |
| events | Ordered array of event objects |

Exact units: timestamp_s=s, source_age_s=s, speed_mps=m/s,
desired_curvature_inv_m=1/m, measured_curvature_inv_m=1/m,
lateral_acceleration_mps2=m/s^2. Parameter units are explicitly supplied synthetic
units, unrelated to actual gains. Gate minimum speed must cover learner minimum.
Scope/ID labels do not authenticate data provenance.

Each event has exactly clock_before_s, clock_after_s and observation. Observation
supplies every ObservationSnapshot field: timestamp_s, sequence, source_age_s,
context_key, source_valid, speed_mps, desired_curvature_inv_m,
measured_curvature_inv_m, lateral_acceleration_mps2, controller_saturated,
driver_override, baseline_parameters and control_active. Context starts with
synthetic/. Missing signals remain null. Explicit control_active=null is a valid
fixture input vetoed by admission; cruise/UI enabled is never substituted.

Clocks/capture times are finite nonnegative, in the declared domain at/after the
origin and losslessly representable as binary64 (the engine Clock domain).
Integer coordinates that would round during clock conversion reject.
clock_after_s >= clock_before_s; next before clock >= preceding after.
Sequence and capture time strictly increase. Capture may exceed the before clock
to test FUTURE_TIMESTAMP; future captures do not advance engine time high-water.
Structurally valid veto inputs (stale, override, saturation, baseline mismatch,
inactive, missing signals) remain in the fixture for actual admission evaluation.
Nonfinite/unordered documents fail at the schema boundary instead.

## Evidence and timing

ReplayReport holds the scenario, ordered OFF/SHADOW EngineResults, ReplaySummary
and separate ReplayLatency. Nested mappings/tuples are defensively frozen. Summary
contains event/proposal/eligible counts, rejection counts by stable ReasonCode,
override/saturation exclusions, exact maximum absolute proposed delta (Fraction),
independent invariant violations and internal errors. Rejection counts combine
SHADOW diagnostic rejections and rejected candidate decisions. They do not count
all unproductive samples: underfilled/deadband/excluded learner windows without
a diagnostic/proposal contribute no reason count. Override/saturation exclusions
use the actual returned reasons, respecting veto priority.

The independent checker compares both output mappings with the trusted scenario
baseline, mode and sequence. OFF must have no proposals/decisions. Eligible SHADOW
candidates must bind to proposal, parameter, baseline, context, learner version
and event timestamp and satisfy admission, freshness, sample/confidence, bounds,
step and rate limits. Step/rate checks use exact Fraction arithmetic against the
preceding clock-safe capture, including rejected frames. No gate predicate is
reused to verify itself. Per-event latency and totals measure engine.step calls;
tests inject timers. No timing budget or hard real-time claim is made.

## Canonical hash

SHA-256 hashes canonical UTF-8 JSON with report_schema_version=1, scenario,
off_results, shadow_results and summary. Latency is excluded. Keys sort
lexicographically; arrays retain order; compact separators and ensure_ascii=True
remove OS newline/path/hash-seed dependencies. Integers keep exact decimal values.
Finite floats encode as `{"float64":"<float.hex()>"}`, retaining signed zero and
distinguishing integers from floats. Fraction encodes as
`{"rational":["numerator","denominator"]}` in reduced form. Enum uses its stable
string value; dataclasses become field maps. Only string/string-enum mapping keys
are allowed and normalized collisions reject.

Input formatting/key order is immaterial; input/policy/result changes affect the
digest. This encoding is for fixed report contracts, not arbitrary JSON signing.
It supplies neither authenticity, authorized provenance nor a safety certificate.
The golden fixture and hand-derived expectations live at
tests/fixtures/replay/golden_v1{,.expected}.json. See replay_acceptance.md for
criteria and replay_progress.md for executed evidence. Intentional schema/hash
changes require review and versioned fixtures; never silently regenerate a digest
to make an unexplained regression pass.
