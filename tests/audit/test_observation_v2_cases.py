"""Literal synthetic evidence is separate from implementation logic."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from cyberpilot_autotune.adapters.carrot_receipt_contract import evaluate
from tests.fixtures.carrot_v2 import BASELINE, complete

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "docs/evidence/carrot_observation_v2_cases.json").read_text(encoding="utf-8")
)


def changed(value, parts, replacement):
    key, *rest = parts
    if isinstance(value, dict) or hasattr(value, "items"):
        result = dict(value)
        # Parameter IDs contain dots; they remain a single mapping key.
        if ".".join(parts) in result:
            result[".".join(parts)] = replacement
        else:
            result[key] = changed(result[key], rest, replacement) if rest else replacement
        return result
    item = getattr(value, key)
    return replace(value, **{key: changed(item, rest, replacement) if rest else replacement})


def from_case(case):
    attempt, policy = complete(case["kind"])
    for path, value in case["patch"].items():
        if value == "NON_FINITE":
            value = float("nan")
        subject, *parts = path.split(".")
        if subject == "attempt":
            attempt = changed(attempt, parts, value)
        else:
            policy = changed(policy, parts, value)
    return attempt, policy


def projection(result, baseline_unchanged):
    snapshot = result.snapshot
    return {
        "reason": result.reason.value,
        "control_active": result.control_active,
        "controller_saturated": result.controller_saturated,
        "source_valid": snapshot is not None and snapshot.source_valid,
        **{
            name: getattr(snapshot, name) if snapshot else None
            for name in (
                "driver_override",
                "speed_mps",
                "desired_curvature_inv_m",
                "measured_curvature_inv_m",
                "timestamp_s",
                "source_age_s",
                "context_key",
            )
        },
        "cohort_key": list(result.cohort_key) if result.cohort_key else None,
        "baseline_unchanged": baseline_unchanged,
    }


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda case: case["id"])
def test_literal_mapping_cases(case):
    attempt, policy = from_case(case)
    before = dict(attempt.baseline_parameters)
    result = evaluate(attempt, policy, BASELINE)
    assert projection(result, dict(attempt.baseline_parameters) == before) == case["expected"]
    assert evaluate(attempt, policy, BASELINE) == result
    if result.snapshot:
        assert result.snapshot.baseline_parameters == BASELINE
        assert result.snapshot.lateral_acceleration_mps2 is None
