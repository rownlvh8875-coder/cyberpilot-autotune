# Synthetic replay progress

Base: 26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0.
Branch: feat/deterministic-replay. Baseline: 335 tests passed, working tree clean.
Plan: replay_plan.md; replay_spec.md defines the implemented schema and evidence.

- PR #1 is merged; PR #2 remains Draft/HOLD. No merge or retarget of PR #2 is
  authorized by this replay task. Use a separate stacked PR for the new harness.
- Persistence and actual vehicle/log integration remain unauthorized.
- Pre-flight: schema uses existing immutable contracts/configs; runner creates fresh
  OFF/SHADOW engines and uses the existing admission boundary. No core signature
  changes or learner algorithm changes are needed.

## Task 1

- RED: replay schema test failed because the replay package did not exist.
- GREEN: 46 schema/canonical tests passed, covering exact fields/units, duplicate
  keys, numeric failures, ordering, explicit activity, resource caps and immutability.
- Canonical tests use hand-written expected bytes for float.hex, exact integer and
  rational tags. No engine or learner executes during decode.

## Task 2

- RED: integration tests failed because run_replay was absent.
- GREEN: fresh OFF/SHADOW runs, immutable traces/summary, independent trusted
  baseline and bounds/step/rate checks, fault rejection and timer-excluded digest.
- Generated streams cover activity, speed, override, saturation and residual
  transitions; arbitrary text/reordering is rejected with typed errors.
- A large-origin freshness regression first reproduced a false invariant report;
  subtracting capture time before adding source age fixed precision loss.
- Full regression: 401 passed; ruff, format, strict mypy and diff checks passed.

## Independent review

- One read-only fresh-context review found one P2 correctness issue: finite integer
  clocks above 2**53 could round in the engine, manufacturing FUTURE_TIMESTAMP
  despite capture equaling the fixture clock. No other scoped findings were raised.
- Four RED tests reproduced admission of lossy origin/capture/before/after values.
  Schema now requires binary64-lossless time coordinates before engine creation;
  GREEN tests also preserve admission of exactly representable large integers.
- Golden metrics/digest remain unchanged. No engine/gate/learner implementation,
  existing PR #2 history or reference repository changed.

## Task 3

- RED: golden tests first failed because the fixture did not exist. Hand-derived
  expectations then passed, with only the intentionally unpinned digest failing.
  After verifying counts, pinned digest and both fresh-process/hash-seed checks pass.
- Golden: 21 events, 5 proposals, 2 eligible, exact maximum delta 3/2; all 42 engine
  outputs retain trusted baseline; zero violations/internal errors. Latency stays
  separate from deterministic evidence. No real-data/performance claim is made.
- Extended static/guarded architecture checks to replay imports and execution;
  added public report validation, timer regression and generated input coverage.
- CI checks replay coverage >=95%, golden evidence on all four matrix jobs and
  functional golden replay from the separately installed wheel outside checkout.
- Version 0.1.0a3; source distribution includes docs/examples and synthetic test
  fixtures. Runtime dependencies remain empty. Acceptance/roadmap docs explicitly
  preserve NOT_AUTHORIZED persistence and PR #2 Draft/HOLD.
- Local regression: 422 passed; full lint/format/mypy passed. Fresh-clone/build/wheel
  and final remote CI evidence will be recorded after execution.
