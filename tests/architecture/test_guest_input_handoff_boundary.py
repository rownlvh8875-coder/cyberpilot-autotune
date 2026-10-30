"""The handoff deliverable is a test-only design, not runtime implementation."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "0652c87c5e1da83d2cf4a3336713b9839e929ae3"


def test_pure_synthetic_model_has_no_runtime_or_io_capability():
    allowed = {"hashlib", "json", "re", "typing"}
    tree = ast.parse((ROOT / "tests/audit/guest_input_handoff_model.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(n.name.split(".")[0] in allowed for n in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed
        if isinstance(node, ast.Call):
            call = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            assert call not in {
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
            }


def test_no_old_code_runtime_evidence_ci_or_fixture_mutation():
    protected = ["src", "compatibility", ".github", "tests/fixtures"]
    old_evidence = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE, "--", "docs/evidence"], cwd=ROOT, text=True
    ).splitlines()
    assert (
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *protected, *old_evidence],
            cwd=ROOT,
            text=True,
        )
        == ""
    )


def test_no_runtime_producer_added_under_test_design_prefix():
    for path in (ROOT / "tests/audit").glob("*guest_input_handoff*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [n.name for n in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            assert not any(
                n.split(".")[0]
                in {
                    "compatibility",
                    "cyberpilot_autotune",
                    "openpilot",
                    "cereal",
                    "socket",
                    "threading",
                    "multiprocessing",
                    "ctypes",
                    "requests",
                    "urllib",
                }
                for n in names
            )
