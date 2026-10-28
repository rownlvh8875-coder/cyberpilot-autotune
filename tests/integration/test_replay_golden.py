"""Hand-derived synthetic metrics and versioned cross-process evidence digest."""

import json
import os
import subprocess
import sys
from pathlib import Path

from cyberpilot_autotune.replay import load_replay, run_replay

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "replay"


def test_golden_metrics_match_hand_derived_expectation():
    expected = json.loads((FIXTURES / "golden_v1.expected.json").read_text(encoding="utf-8"))
    report = run_replay(load_replay((FIXTURES / "golden_v1.json").read_text(encoding="utf-8")))
    summary = report.summary
    assert summary.event_count == expected["event_count"]
    assert summary.proposal_count == expected["proposal_count"]
    assert summary.eligible_count == expected["eligible_count"]
    assert {key.value: count for key, count in summary.rejection_counts.items()} == (
        expected["rejection_counts"]
    )
    assert summary.override_exclusion_count == expected["override_exclusion_count"]
    assert summary.saturation_exclusion_count == expected["saturation_exclusion_count"]
    assert [
        summary.maximum_proposed_delta.numerator,
        summary.maximum_proposed_delta.denominator,
    ] == expected["maximum_proposed_delta"]
    assert summary.invariant_violations == expected["invariant_violations"] == 0
    assert summary.internal_error_count == expected["internal_error_count"] == 0
    assert report.software_checks_passed
    # Pin only after the hand-derived metrics above have been verified.
    assert report.digest == expected["sha256"]


def test_two_fresh_processes_and_hash_seeds_reproduce_golden_evidence():
    expected = json.loads((FIXTURES / "golden_v1.expected.json").read_text(encoding="utf-8"))
    outputs = []
    for seed in ("1", "917"):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "examples" / "replay_synthetic.py")],
            cwd=ROOT,
            env=dict(os.environ, PYTHONHASHSEED=seed),
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        data = json.loads(result.stdout)
        assert "latency_ns" not in data
        assert data["sha256"] == expected["sha256"]
        assert data["software_checks_passed"] is True
        outputs.append(data)
    assert outputs[0] == outputs[1]
