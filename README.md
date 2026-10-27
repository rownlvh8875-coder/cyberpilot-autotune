# CyberPilot AutoTune

Independent controller tuning research. This repository is in the research and
shadow-only stage. It has no production vehicle control or controller write path.

The purpose is a reusable, fail-closed, bounded online adaptation framework for
controller tuning research, developed independently for eventual small upstream
PRs. Current modes are OFF and SHADOW; effective values always equal baseline.

Architecture: observation source -> read-only adapter -> immutable snapshot ->
proposal-only learner -> Safety Gate -> runtime enforcer -> immutable result.
The core does not depend on openpilot. See [architecture](docs/architecture.md).

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
python -m pytest --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=85
python -m coverage report --include="*/safety/*" --fail-under=95
python -m build
```

`src/cyberpilot_autotune` contains contracts, safety, runtime, learners, adapter
interfaces and in-memory diagnostics. `tests` contains unit, property,
integration and architecture tests. `examples` is synthetic only. `docs` records
the audit, safety contract, integration evidence and future roadmap.

No production safety or performance claim is made. There is no Apply mode,
real learner, controller write API, vehicle deployment, persistence, real log
ingestion, network telemetry or vehicle parameter registry. Python plugins are
trusted code; this is not a sandbox or a hard real-time implementation.

The source audit is pinned to CyberPilot commit
`588d6b21c21089065a7d9165d6e7a438e8aa6297`; the current branch HEAD was also
recorded separately in the [inventory](docs/porting_inventory.md). No code was
copied from that source. Future phases are recorded in
[the roadmap](docs/roadmap.md) and are not implemented by this milestone.

License selection is pending. No LICENSE file is provided. Source references do
not establish a license for this independent repository.
