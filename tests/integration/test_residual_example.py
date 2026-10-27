"""The synthetic example runs independently and prints deterministic evidence."""

import json
import subprocess
import sys
from pathlib import Path


def test_synthetic_example_is_deterministic_in_two_fresh_processes():
    path = Path(__file__).resolve().parents[2] / "examples" / "residual_shadow.py"
    results = [
        subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=30)
        for _ in range(2)
    ]
    for result in results:
        assert result.returncode == 0, result.stderr
    assert results[0].stdout == results[1].stdout
    records = [json.loads(line) for line in results[0].stdout.splitlines()]
    assert len(records) == 4
    assert records[2]["sample_count"] == 3
    assert records[2]["proposal"] == 10.5
    assert records[2]["gate"] == "ACCEPTED_FOR_SHADOW"
    assert records[3]["sample_count"] == 0  # Override clears evidence.
    for record in records:
        assert record["scope"] == "SYNTHETIC_NOT_FOR_VEHICLE_USE"
        assert record["mode"] == "SHADOW"
        assert record["baseline"] == record["effective"] == {"synthetic.test_only": 10.0}
        assert record["effective_equals_baseline"] is True
