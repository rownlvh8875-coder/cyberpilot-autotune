# Synthetic replay software acceptance

These are executable synthetic regression criteria, not owner-approved vehicle
or real-data replay criteria. Persistence remains NOT_AUTHORIZED even after they
pass. Acceptance is assessed on run_replay outputs with reviewed code/fixtures;
caller-forged reports are not independent evidence.

## Required software checks

- Strict schema admission before execution: explicit units/domain/activity/policy
  and trusted baseline. Invalid JSON, versions, types and order reject.
- Every OFF/SHADOW baseline and effective mapping equals the trusted baseline.
  OFF invokes no clock/admission/observe/reset and returns no candidate.
- Independent eligible candidate binding, admission/freshness, evidence, bounds,
  step and rate checks pass. Zero invariant violations and INTERNAL_ERROR/UNHEALTHY
  diagnostics. Expected admission/gate vetoes are correct fail-closed behavior.
- Fresh engines/learners per run. Identical deterministic bytes/hash across
  injected timers, fresh processes, hash seeds and the CI matrix.
- Guarded import/execution prohibits file writes, sockets, threads, processes and
  optional vehicle dependencies; static boundaries cover replay/ too.
- Full regression/lint/format/type/build/wheel smoke passes; coverage >=90%
  overall and >=95% for safety, residual learner and replay.

ReplayReport.software_checks_passed implements the zero invariant/internal/health
error rule for that run. It does not imply golden-match, full-suite success or
physical experiment permission. Tests/CI check the other requirements. Latency is
observational, excluded from deterministic acceptance. Candidate counts do not
establish performance or driving-quality improvement.

## Hand-derived golden scenario

All fixture bounds, speeds, curvature residuals and coefficients are synthetic,
test-only and unrelated to steering/longitudinal tuning. Baseline is
synthetic.test_only=10.0; alpha=1/2; minimum samples=3; coefficient=2; gate confidence
threshold=0.8; step=2; rate=1 per second. None are vehicle defaults.

| Event indices | Expected behavior |
|---|---|
| 0..2 | Constant residual 1/4; at 2, proposal 10.5, confidence 1, eligible |
| 3..11 | Override, saturation, unknown/inactive control, low speed, invalid source, stale, baseline mismatch and missing desired signal veto; clear evidence |
| 12..14 | Fresh constant window; at 14, proposal 10.5, eligible |
| 15..16 | Residual 3/4; means 1/2 then 5/8; innovation 1/4 gives confidence 1/2; two LOW_CONFIDENCE rejections |
| 17..19 | New context/window, residual 3/4; at 19, proposal 11.5 exceeds 1-second rate budget; RATE_LIMIT_EXCEEDED |
| 20 | Capture 31 with evaluation clock 30; FUTURE_TIMESTAMP |

Required: 21 events, 5 proposals, 2 eligible, override/saturation exclusions 1 each,
maximum absolute proposed delta 3/2, zero violations/internal errors. Reason counts
are pinned in golden_v1.expected.json. Invalid source and missing desired signal
both produce INVALID_OBSERVATION. Trusted baseline comparison covers all 42 outputs.

Pinned SHA-256:
`5434e0cd203a08fb97662d94b91d66665bb950ba8cb276f90597efc8af673af5`.
Hand-derived metrics were verified before pinning this digest. Fresh-process tests
exclude nondeterministic latency from comparisons.

## Before later real-data or persistence work

Separate owner decisions must define authorized provenance, privacy/retention,
specific dataset/vehicle/controller context, validated unit/freshness/activity
mappings, replay acceptance thresholds and representative faults. Persistence also
needs explicit authorization and reviewed schema/version/integrity, atomic
replacement, corruption fallback, expiry/reset, storage/permission and opt-in
policies. Nothing starts automatically here. Application/deployment require their
own RFC and approvals; the package contains no controller write capability.

## Focused and CLI completion

Require all three focused fixtures, per-event sample-count/reason expectations,
split digest domains and canonical fresh-process output to match on the complete
Windows/Ubuntu x Python matrix. Observation ordering anomalies reach runtime;
only evaluation clock/domain violations reject at schema admission. See
replay_ordering.md for the current conservative policy and its availability limit.
CLI verify-all must pass from source and the installed wheel with explicit local
fixture arguments. Exit-code and error-redaction tests are required. Historical
aggregate fixture bytes/result digest stay unchanged. Synthetic software evidence
does not supply real-data acceptance or remove NOT_AUTHORIZED persistence status.
