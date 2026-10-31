"""Keep strict admission additive, explicit, repository-only and capability-free."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "0095e64fbe8cf9815e14226f527bf654315a12dc"


def test_every_baseline_tracked_blob_is_preserved():
    before = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
    )
    assert not before & changed


def test_new_facade_has_only_explicit_neutral_imports_and_pure_calls():
    package = ROOT / "tests/strict_containment"
    init = ast.parse((package / "__init__.py").read_bytes())
    assert len(init.body) == 1 and isinstance(init.body[0], ast.Expr)
    assert isinstance(init.body[0].value, ast.Constant)
    tree = ast.parse((package / "validation.py").read_bytes())
    imports = {
        "compatibility.native_containment.contracts": {
            "SyntheticContainmentCase",
            "canonical_digest",
            "parse_synthetic_case",
        },
        "compatibility.native_containment.validation": {
            "SyntheticContainmentDecision",
            "SyntheticPolicyContext",
            "evaluate_synthetic",
        },
    }
    calls = {
        "canonical_digest",
        "parse_synthetic_case",
        "digest_case_strict",
        "evaluate_synthetic",
        "ValueError",
    }
    for node in tree.body:
        assert isinstance(node, (ast.Expr, ast.ImportFrom, ast.Assign, ast.FunctionDef))
        if isinstance(node, ast.Assign):
            assert len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            assert node.targets[0].id == "VALIDATOR_PROFILE" and isinstance(
                node.value, ast.Constant
            )
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.Import, ast.Global, ast.Nonlocal, ast.ClassDef))
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module in imports
            assert all(n.name in imports[node.module] and n.asname is None for n in node.names)
        elif isinstance(node, ast.Call):
            assert isinstance(node.func, ast.Name) and node.func.id in calls
        elif isinstance(node, ast.ExceptHandler):
            assert isinstance(node.type, ast.Name) and node.type.id == "UnicodeEncodeError"
        elif isinstance(node, ast.Assign):
            assert all(
                isinstance(t, ast.Name) and t.id in {"case", "VALIDATOR_PROFILE"}
                for t in node.targets
            )
    # No legacy caller, installed package, CI or import site is redirected by this facade.
    for path in (ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_bytes())):
            if isinstance(node, ast.Import):
                assert all(not n.name.startswith("tests.strict_containment") for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("tests.strict_containment")
