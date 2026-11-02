"""Separate prepared Python process for each first-call observation."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "case,status",
    (
        ("consistent", "REPORTED_BINDING_CONSISTENT"),
        ("incomplete", "INCOMPLETE"),
        ("reject", "REJECTED"),
        ("incomparable", "REPORTED_TIME_ORDER_UNCOMPARABLE"),
    ),
)
def test_prepared_first_call_has_no_forbidden_effects(case, status):
    root = Path(__file__).resolve().parents[3]
    script = Path(__file__).with_name("cold_probe.py")
    assert script.is_file(), "prepared first-call observer not implemented"
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(script), str(root), case],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["structural_status"] == status and value["forbidden_events"] == []
    assert value["sha256_c_calls"] > 0 and value["first_assessor_call_observed"] is True
    assert value["native_kernel_qualified"] is False
