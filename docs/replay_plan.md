# Deterministic synthetic replay implementation plan

Historical core plan; its strict observation-order schema rule was superseded by
the authorized completion plan in replay_completion_plan.md. Evaluation clocks
remain ordered; observation anomalies are now characterized by the engine.

> Execute inline using test-driven-development and verification-before-completion.
> The user approved the next single task: deterministic replay harness. Persistence
> remains NOT_AUTHORIZED, as do vehicle integration/application and real logs.

Base: 26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0. PR #2 is Draft/HOLD;
use feat/deterministic-replay and a separate stacked Draft PR, without merging it.

## Design decisions

- Library API consumes an explicit synthetic JSON string; no implicit file scan,
  network, real-log decoder, state persistence or external callback learner.
- Strict schema v1 binds scope SYNTHETIC_TEST_ONLY, learner residual-ewma-v1,
  synthetic monotonic domain/origin, canonical units, one synthetic ParameterSpec,
  trusted baseline, explicit gate/learner config and ordered observation/clock events.
- Every observation explicitly supplies control_active, including null when unknown.
  Unavailable signals stay null. Scope labels do not authenticate data provenance.
- Reject unknown/missing keys, duplicate keys, incompatible versions, non-finite or
  invalid numeric types, ambiguous units, sequence/time reordering and inconsistent
  clock domains before any learner/engine execution. Bound JSON to 256 KiB and
  events to 1000; these are research resource caps, not vehicle parameters.
- Capture times may be later than their evaluation clock to exercise future-input
  admission vetoes. Injected clock readings themselves must be monotonic and share
  the declared domain. Expected safety vetoes are valid fixture data, not parse errors.
- Each run constructs fresh OFF/NoOp and SHADOW/residual engines using trusted
  baseline. Compare every output to that baseline. No production package mutation.
- Report ordered traces, proposal/eligible counts, actual rejection reason counts,
  override/saturation exclusions, exact maximum proposed delta, internal errors and
  independent invariant violations. Software checks pass only with zero violations
  and internal errors; this never authorizes vehicle application or persistence.
- Independent checks cover baseline/mode/sequence/OFF emptiness and eligible hard
  bounds/step/rate/proposal binding. They do not re-run the gate to verify itself.
- Canonical hash binds the scenario/configuration and deterministic traces/summary.
  Sorted keys, explicit float.hex tags and exact rational tags distinguish types,
  signed zero and large integers. No wall clock, paths or latency enter the hash.
- Per-event OFF/SHADOW latency uses a separate injectable perf_counter_ns timer.
  Counts/timing are in memory; no output files are written by the library.
- One small synthetic golden fixture has hand-derived expected metrics and a pinned
  digest. Fresh-process and four-platform/Python CI runs verify the same digest.
  Real replay acceptance and persistence approval remain owner decisions.

## Review focus

Malformed input must never partially execute; mutable nested aliases must not alter
scenario/report; digest must bind policy/input changes but exclude timer changes;
unsafe eligible decisions/internal faults must fail software acceptance; baseline
identity must be checked against trusted scenario data rather than result self-equality.

## Task 1: Schema and canonical encoding

Files: replay/{schema,canonical,__init__}.py; tests/unit/test_replay_schema.py.
APIs: load_replay(document:str)->ReplayScenario, ReplayEvent, ReplayScenario,
canonical_bytes(value:object)->bytes. Frozen validated, defensively copied structures.

- [x] Write failing strict schema/units/order/type/immutability and canonical byte tests.
- [x] Observe RED, implement minimal typed schema/decoder/encoding, verify GREEN.
- [x] Full tests, lint/format/mypy/whitespace; atomic commit.

## Task 2: Runner and independent evidence

Files: replay/runner.py; tests/{unit,integration,property}/test_replay*.py.
API: run_replay(scenario, *, timer_ns=perf_counter_ns)->ReplayReport. Immutable
results, summary, digest and separately measured latency; fresh engines each run.

- [x] Write failing known-stream counts, baseline identity, independent violation,
  timer-excluded digest and deterministic input/policy-binding tests.
- [x] Observe RED; implement bounded runner and report without IO/application.
- [x] Add generated stream invariants; full checks and atomic commit.

## Task 3: Golden evidence and delivery

Files: tests/fixtures/replay/{golden_v1,golden_v1.expected}.json;
examples/replay_synthetic.py; docs/{replay_spec,replay_acceptance,replay_progress}.md;
README, roadmap, architecture, CI and package metadata.

- [x] Golden expected metrics: 21 events, 5 proposals, 2 eligible; 2 low-confidence,
  1 rate veto; admission vetoes and exact maximum delta 3/2; zero invariant violations.
- [x] Pin digest after matching hand-derived metrics; check two fresh processes,
  malformed fixtures and guarded import/execution with no network/writes/threads.
- [x] Independent read-only review; meaningful findings fixed with RED/GREEN.
- [x] Clean clone install, full tests/coverage/lint/type/build and isolated wheel smoke.
- [x] Commit/push normally, create stacked Draft PR, inspect final CI; keep PR #2 HOLD.
