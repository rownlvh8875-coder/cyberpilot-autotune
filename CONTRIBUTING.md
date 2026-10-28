# Contributing

Use Python >=3.12.3,<3.13 in a virtual environment. Install with
`python -m pip install -e ".[dev]"`. Write a failing behavior test first,
then minimal implementation and regression checks. Use English code and docs.

Before each implementation commit:

```sh
git diff --check
python -m ruff check .
python -m ruff format --check .
python -m mypy src/cyberpilot_autotune
python -m pytest -q
```

Before a PR also run coverage (90% overall, 95% safety/residual/replay), `python -m build`,
and an isolated wheel import. Keep changes small. Document provenance before
copying anything; unresolved source attribution must not be copied. License
selection is pending. Do not add a license without owner approval.

No live vehicle control, real tuning constants, apply capabilities, driving
logs, secrets, network telemetry, generated artifacts or reference checkouts.
Use explicitly synthetic fixtures. New dependencies require a concrete need.
Do not present shadow eligibility as physical validity or permission to apply.

Run `python -m pytest tests/integration/test_replay_golden.py -q` for pinned synthetic
evidence. Investigate changed metrics/bytes before changing a digest; review and
version intentional schema/hash changes. Synthetic software checks do not
authorize real logs, persistence or vehicle experiments.
Also run `python -m cyberpilot_autotune.replay.cli verify-all tests/fixtures/replay`.
Only the explicit CLI boundary may read fixture files; the library remains pure
with respect to file IO. No update-golden command or CI golden rewrites are allowed.
