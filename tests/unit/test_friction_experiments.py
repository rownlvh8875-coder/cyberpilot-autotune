"""Frozen-policy experiments cannot select from results or authorize application."""

import ast
import json
from pathlib import Path

import pytest

from cyberpilot_autotune.research.friction_model import experiments
from cyberpilot_autotune.research.friction_model.contracts import digest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/evidence/friction_model_policy.json"


def test_all_preregistered_cases_run_with_pinned_inputs_and_explicit_negative_gates():
    raw = POLICY.read_text()
    result = experiments.run_experiments(raw)
    assert result["selected_model"] == "NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS"
    assert len(result["scenarios"]) == 26
    assert {r["scenario"] for r in result["scenarios"]} == set(
        json.loads(raw)["synthetic"]["scenarios"]
    )
    assert result["policy_sha256"] == digest(json.loads(raw))
    assert all(not v for v in result["authority"].values())
    assert result["geometry"]["verdict"] == "GEOMETRY_CONTEXT_MATERIAL"
    assert result["geometry"]["coherent_steady_invariant"]
    assert len(result["geometry"]["comparisons"]) == 3
    assert result == experiments.run_experiments(raw)


def test_experiment_rejects_mutated_policy_before_any_comparison():
    policy = json.loads(POLICY.read_text())
    policy["synthetic"]["truth"]["friction"] = 0.9
    with pytest.raises(ValueError, match="POLICY_MUTATION"):
        experiments.run_experiments(json.dumps(policy))


def test_independent_oracle_imports_only_contracts_not_estimators_or_q_helpers():
    source = ROOT / "src/cyberpilot_autotune/research/friction_model/synthetic.py"
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.ImportFrom) and node.level:
            assert node.module == "contracts"
        elif isinstance(node, ast.Import):
            assert all(a.name != "numpy" for a in node.names)
