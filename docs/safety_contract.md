# Safety contract: Phase 0-4

This is software invariant evidence for research. It is not a vehicle safety
claim, calibration, certification or permission for production deployment.

## Authority and immutable fallback

Only OFF and SHADOW exist. An engine receives a validated, defensively copied
baseline at construction. Snapshot data cannot replace it. EngineResult refuses
unequal effective and baseline mappings, and exposes immutable mappings and
tuples. Eligibility means a would-be candidate only. There is no controller,
Params, actuator, transport, file sink or application callback in the API.
Mapping copies validate finite numeric scalars without converting them; this
preserves exact input baseline identity even for integers beyond float precision.

## Ordered gate evaluation

`safety/gate.py` implements this order. Numeric prerequisites needed to compare
time/freshness/sequence are checked at their stage before the general sanitizer.

| Order | Check | Rejection |
|---:|---|---|
| 1 | Exact ObservationSnapshot type exists | INVALID_OBSERVATION |
| 2 | Finite nonnegative monotonic times; capture not in future | NON_FINITE / INVALID_OBSERVATION / FUTURE_TIMESTAMP |
| 3 | Nonnegative source age plus elapsed capture age within policy | NON_FINITE / INVALID_OBSERVATION / STALE_OBSERVATION |
| 4 | Nonnegative integer sequence; strict sequence and capture-time increase | INVALID_OBSERVATION / OUT_OF_ORDER |
| 5 | Revalidate all observation/proposal numbers, types, flags, required signals, trusted baseline and proposal capture binding | NON_FINITE / INVALID_OBSERVATION / INVALID_PROPOSAL / FUTURE_TIMESTAMP / BASELINE_MISMATCH |
| 6 | Registered specification exists | UNKNOWN_PARAMETER |
| 7 | Entire snapshot baseline and proposed baseline equal trusted baseline | BASELINE_MISMATCH |
| 8 | Exact nonempty context match | CONTEXT_MISMATCH |
| 9 | Minimum sample count | INSUFFICIENT_SAMPLES |
| 10 | Minimum confidence | LOW_CONFIDENCE |
| 11 | Driver override veto | DRIVER_OVERRIDE |
| 12 | Controller saturation veto | CONTROLLER_SATURATED |
| 13 | Candidate and baseline within hard bounds | OUT_OF_BOUNDS |
| 14 | Absolute baseline-relative step within maximum_step | STEP_LIMIT_EXCEEDED |
| 15 | Absolute baseline-relative delta within elapsed rate budget | RATE_LIMIT_EXCEEDED |
| 16 | Explicit engine health must be True | UNHEALTHY |
| 17 | Construct eligible decision | ACCEPTED_FOR_SHADOW |

No clipping occurs. Inclusive exact bounds are allowed. Step and rate comparisons
use exact rational representations of supplied floats to avoid overflow and
rounding slack in budget multiplication. Rate uses observation capture intervals,
not wall time or call frequency. Unknown previous timestamp admits only delta=0.
Equal timestamps reject even with increasing sequence. One engine owns one source
stream; a context change does not reset sequence history or bypass rate limits.

Optional lateral acceleration may be None. Missing speed, desired/measured
curvature, override or saturation prevents admission. False source validity also
prevents admission. No unavailable signal becomes a valid zero or False.

## Runtime boundary

Malformed input is rejected before calling the learner, including an empty
proposal path. Unexpected gate/learner/clock errors are caught only by the engine
processing boundary. Partial results are discarded and INTERNAL_ERROR diagnostics
retain the trusted baseline. Construction/configuration failures remain visible
as ValidationError. Diagnostics expose error class only, never error text or raw
data. No files or external events are emitted.

Stream state consists only of admitted sequence/capture time and observed clock
high-water information. OFF does not read time, invoke learner or mutate stream
state. SHADOW consumes an admitted frame even when downstream code fails, so an
identical frame cannot be retried to manufacture additional evidence.

The injected clock must share a monotonic domain with the adapter. Clock
regression is unhealthy. Freshness is rechecked after learner work, including
empty proposals. This detects completed slow work; synchronous Python cannot
preempt a hung learner. No hard real-time watchdog claim is made.
