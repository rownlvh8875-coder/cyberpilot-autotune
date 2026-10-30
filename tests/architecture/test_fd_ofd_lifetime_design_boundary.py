"""The lifecycle deliverable is test-only design, not an operational observer."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "3a831fdd423aa98638082eba126519db19f432d6"


def test_lifecycle_oracle_is_pure_and_cannot_reach_runtime_or_application():
    tree = ast.parse((ROOT / "tests/audit/fd_ofd_lifetime_model.py").read_text())
    allowed = {"hashlib", "json", "re", "dataclasses", "typing"}
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
                else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            )
            assert name not in forbidden


def test_prior_runtime_actual_evidence_and_fixtures_remain_unchanged():
    old = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE, "--", "docs/evidence"], cwd=ROOT, text=True
    ).splitlines()
    paths = ["src", "compatibility", ".github", "tests/fixtures", "tests/experiments", *old]
    assert (
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *paths], cwd=ROOT, text=True
        )
        == ""
    )
