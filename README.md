# CyberPilot AutoTune

Independent controller tuning research. This repository is in the research and
shadow-only stage. It has no production vehicle control or controller write path.

The purpose is a reusable, fail-closed, bounded online adaptation framework for
controller tuning research, developed independently for eventual small upstream
PRs. Current modes are OFF and SHADOW; effective values always equal baseline.

Architecture: observation source -> read-only adapter -> immutable snapshot ->
learning admission -> proposal-only learner -> candidate Safety Gate -> runtime
enforcer -> immutable result.
The core does not depend on openpilot. See [architecture](docs/architecture.md).

Phase 8A audited carrot-wip at `604bc0a22733e648ec05b268da1ffaae7db52a69`.
The [read-only signal contract](docs/carrot_signal_contract.md) is blocked on
actual lateral authority and saturation semantics. Unknown signals remain None;
no Carrot mapper or actual adapter is implemented. The
[synthetic evidence](docs/carrot_signal_evidence.md) is a static specification,
not executed vehicle or adapter behavior. Phase 8B is NOT_STARTED.

## Shadow residual learner

Phase 5 adds `ResidualStatisticsLearner` alongside `NoOpLearner`. It maintains
bounded EWMA curvature residual statistics for one context and returns proposals
only after explicit minimum sample requirements. Invalid, old, missing, override,
saturation and outlier evidence is excluded; context/baseline/gap/age transitions
restart the window. Optional learner reset is integrated with SHADOW rejection
paths. Before observe(), common admission requires explicit control_active=True,
speed at least the caller-supplied minimum_speed_mps, valid/fresh/ordered input,
trusted baseline identity and no override/saturation. None means activity is unknown;
cruise/UI enabled is never substituted. Actual Carrot activity mapping is absent.
OFF calls neither clock, admission, observe nor reset.

Both GateConfig and ResidualStatisticsConfig require an explicit finite nonnegative
minimum_speed_mps; no vehicle default exists. Common policy must be at least as
strict as the learner's declared minimum. reset() deletes the evidence window
only and preserves sequence/time high-water within the same monotonic stream.
A restarted sequence/time domain needs a new learner instance and engine.

Every scale, age, threshold and signed residual-to-parameter coefficient must be
supplied explicitly. There are no vehicle defaults. Confidence is a support and
consistency heuristic, not a calibrated probability or driving-quality measure.
SafetyGate still independently checks every candidate; effective values remain
exactly baseline. See [the Phase 5 design](docs/phase5_design.md) for formulas,
reset and numeric policies, and [progress](docs/phase5_progress.md) for evidence.

Run the local synthetic-only demonstration with:

```sh
python examples/residual_shadow.py
```

## Local development

Python >=3.12.3,<3.13 is required, based on inspected integration sources.
Use a local virtual environment (Windows activation path differs):

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m mypy src/cyberpilot_autotune
python -m pytest -q
python -m pytest --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=90
python -m coverage report --include="*/safety/*" --fail-under=95
python -m coverage report --include="*/core/residual.py" --fail-under=95
python -m coverage report --include="*/replay/*" --fail-under=95
python -m pytest tests/integration/test_replay_golden.py -q
python -m cyberpilot_autotune.replay.cli verify-all tests/fixtures/replay
python -m build
```

`src/cyberpilot_autotune` contains contracts, safety, runtime, learners, adapter
interfaces, synthetic replay and in-memory diagnostics. `tests` contains unit, property,
integration and architecture tests. `examples` is synthetic only. `docs` records
the audit, safety contract, integration evidence and future roadmap.

No production safety or performance claim is made. There is no Apply mode,
controller write API, vehicle deployment, persistence, real log ingestion,
network telemetry or vehicle parameter registry. Python plugins are
trusted code; this is not a sandbox or a hard real-time implementation.

The source audit is pinned to CyberPilot commit
`588d6b21c21089065a7d9165d6e7a438e8aa6297`; the current branch HEAD was also
recorded separately in the [inventory](docs/porting_inventory.md). No code was
copied from that source. Remaining phases are recorded in
[the roadmap](docs/roadmap.md). Persistence is NOT_AUTHORIZED; synthetic software
acceptance does not authorize learner state storage or real replay data.

License selection is pending. No LICENSE file is provided. Source references do
not establish a license for this independent repository.

## Deterministic synthetic replay

`cyberpilot_autotune.replay.load_replay(json_string)` validates a bounded synthetic
schema before execution. `run_replay(scenario)` constructs fresh OFF and SHADOW
engines and returns immutable traces, counts, independent invariant checks and a
SHA-256 digest binding the inputs, policy and deterministic results. Runtime
latency is measured separately and excluded from the digest. The library reads
and writes no files. The caller explicitly supplies any document string.

Run the small checked-in synthetic golden fixture locally:

```sh
python -m cyberpilot_autotune.replay.cli run tests/fixtures/replay/constant_residual_v1.json
python -m cyberpilot_autotune.replay.cli verify-all tests/fixtures/replay
```

Only cli.py reads explicit local fixture files; core APIs remain free of file IO.
The example delegates its aggregate fixture to this CLI. run emits canonical JSON
without latency; verify checks digests, counts/reasons and focused event evidence.
scenario_sha256, configuration_sha256 and result_sha256 identify separate domains;
digest remains the result alias. Repeated/regressed observations reach the unchanged
engine; evaluation clocks remain monotonic. Both modes retain baseline. See the
[schema and encoding](docs/replay_spec.md) and
[software acceptance criteria](docs/replay_acceptance.md). A matching digest is
regression evidence, not data authentication or vehicle performance evidence.
Ordering policy and its availability tradeoff are characterized in
[the ordering evidence](docs/replay_ordering.md).
