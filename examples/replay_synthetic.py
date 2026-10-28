"""Delegate the historical synthetic fixture to the explicit read-only CLI."""

from pathlib import Path

from cyberpilot_autotune.replay.cli import main

if __name__ == "__main__":
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/replay/golden_v1.json"
    raise SystemExit(main(["run", str(fixture)]))
