"""Focused fixtures pin each event, metrics, all digest domains and process bytes."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from cyberpilot_autotune.replay.cli import main

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/replay"
NAMES = ["constant_residual", "admission_reset", "ordering_high_water"]


@pytest.mark.parametrize("name", NAMES)
def test_focused_expected_including_per_event_characterization(name, capfd):
    assert (
        main(
            [
                "verify",
                str(FIXTURES / f"{name}_v1.json"),
                str(FIXTURES / f"{name}_v1.expected.json"),
            ]
        )
        == 0
    )
    output = json.loads(capfd.readouterr().out)
    expected = json.loads((FIXTURES / f"{name}_v1.expected.json").read_text())
    assert output == expected
    assert output["internal_error_count"] == output["invariant_violations"] == 0
    assert all(event["baseline_retained"] for event in output["events"])


@pytest.mark.parametrize("name", ["golden", *NAMES])
def test_each_fixture_has_byte_identical_fresh_process_output(name):
    outputs = []
    for seed in ("3", "927"):
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "cyberpilot_autotune.replay.cli",
                "run",
                str(FIXTURES / f"{name}_v1.json"),
            ],
            env=dict(os.environ, PYTHONHASHSEED=seed),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert result.stderr == b""
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]
    output = json.loads(outputs[0])
    expected = json.loads((FIXTURES / f"{name}_v1.expected.json").read_text())
    assert all(output[key] == value for key, value in expected.items())


def test_focused_sample_count_expectation_cannot_be_changed_silently(tmp_path, capfd):
    expected = json.loads((FIXTURES / "ordering_high_water_v1.expected.json").read_text())
    expected["events"][8]["sample_count"] = 1  # Repaired rejected sequence adds no evidence.
    path = tmp_path / "expected.json"
    path.write_text(json.dumps(expected))
    assert main(["verify", str(FIXTURES / "ordering_high_water_v1.json"), str(path)]) == 3
    assert capfd.readouterr().out == ""


def test_focused_expectation_cannot_downgrade_to_legacy_checks(tmp_path, capfd):
    from cyberpilot_autotune.replay.cli import LEGACY_KEYS

    full = json.loads((FIXTURES / "constant_residual_v1.expected.json").read_text())
    path = tmp_path / "expected.json"
    path.write_text(json.dumps({key: full[key] for key in LEGACY_KEYS}))
    assert main(["verify", str(FIXTURES / "constant_residual_v1.json"), str(path)]) == 3
    assert capfd.readouterr().out == ""
