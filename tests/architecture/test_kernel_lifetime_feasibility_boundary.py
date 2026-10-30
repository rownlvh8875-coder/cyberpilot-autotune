"""Design-only witnesses cannot import or execute observer/application machinery."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "a982d1bec759916013981f9cbc76ced6679c71ea"


def test_copy_and_loss_witnesses_are_pure_test_only_functions():
    tree = ast.parse((ROOT / "tests/audit/kernel_lifetime_witness.py").read_bytes())
    allowed = {"dataclasses", "itertools"}
    forbidden = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "write_text",
        "write_bytes",
        "connect",
        "start",
        "system",
        "popen",
        "socket",
        "Thread",
        "Popen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(n.name.split(".")[0] in allowed for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            assert name not in forbidden


def test_previous_runtime_contracts_actual_evidence_and_fixtures_are_untouched():
    old_evidence = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE, "--", "docs/evidence"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    old_audit = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE, "--", "tests/audit"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    paths = [
        "src",
        "compatibility",
        ".github",
        "tests/fixtures",
        "tests/experiments",
        *old_evidence,
        *old_audit,
    ]
    assert (
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *paths],
            cwd=ROOT,
            text=True,
        )
        == ""
    )
