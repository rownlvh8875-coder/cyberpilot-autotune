"""Keep new exact-limit validation pure, explicit and outside frozen runtime paths."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "c477cfc1b30578165405b6cbb3af26b7334064e5"


def test_every_prior_tracked_blob_is_preserved():
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


def test_new_facade_cannot_access_operational_or_legacy_loader_entrypoints():
    package = ROOT / "tests/strict_handoff"
    init = ast.parse((package / "__init__.py").read_bytes())
    assert len(init.body) == 1 and isinstance(init.body[0], ast.Expr)
    assert isinstance(init.body[0].value, ast.Constant)
    tree = ast.parse((package / "validation.py").read_bytes())
    imports = {
        "typing": {"Any"},
        "tests.audit.validate_guest_input_handoff_design": {"validate_schema"},
    }
    calls = {"type", "len", "any", "ValueError", "validate_schema"}
    for node in tree.body:
        assert isinstance(node, (ast.Expr, ast.ImportFrom, ast.Assign, ast.FunctionDef))
        if isinstance(node, ast.Assign):
            assert len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            assert node.targets[0].id in {"VALIDATOR_PROFILE", "_EXPECTED_LIMITS"}
            assert isinstance(node.value, (ast.Constant, ast.Tuple))
    for node in ast.walk(tree):
        assert not isinstance(
            node,
            (
                ast.Import,
                ast.Global,
                ast.Nonlocal,
                ast.ClassDef,
                ast.Try,
                ast.Delete,
                ast.AugAssign,
                ast.NamedExpr,
            ),
        )
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module in imports
            assert all(n.name in imports[node.module] and n.asname is None for n in node.names)
        elif isinstance(node, ast.Call):
            assert isinstance(node.func, ast.Name) and node.func.id in calls
        elif isinstance(node, ast.Assign):
            assert all(
                isinstance(t, ast.Name)
                and t.id in {"VALIDATOR_PROFILE", "_EXPECTED_LIMITS", "limits", "value"}
                for t in node.targets
            )
    for path in (ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_bytes())):
            if isinstance(node, ast.Import):
                assert all(not n.name.startswith("tests.strict_handoff") for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("tests.strict_handoff")
