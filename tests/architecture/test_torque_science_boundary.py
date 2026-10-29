"""Offline scientific research cannot flow into existing runtime/owner layers."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/cyberpilot_autotune"


def test_existing_namespaces_never_import_scientific_research():
    for path in ROOT.rglob("*.py"):
        if "research" in path.relative_to(ROOT).parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert "research" not in (node.module or "").split(".")
            elif isinstance(node, ast.Import):
                assert all("research" not in a.name.split(".") for a in node.names)


def test_research_has_only_explicit_pure_math_dependencies_and_no_io_authority():
    allowed = {"dataclasses", "hashlib", "json", "math", "re", "random", "numpy"}
    forbidden_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "Params",
        "SubMaster",
        "PubMaster",
        "SteeringRequest",
        "commit",
        "put",
        "put_bool",
        "send",
        "exec",
        "eval",
        "__import__",
        "start",
    }
    for path in (ROOT / "research").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert all(a.name.split(".")[0] in allowed for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert (node.module or "").split(".")[0] in allowed
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                )
                assert name not in forbidden_calls


def test_generator_shares_no_estimator_or_analytic_helper_with_the_oracle():
    path = ROOT / "research/torque_identification/synthetic.py"
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.level:
            assert node.module == "contracts"
        elif isinstance(node, ast.Import):
            assert all(a.name != "numpy" for a in node.names)
