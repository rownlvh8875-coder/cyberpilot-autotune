"""No actual decoder/application bridge; every pre-existing path stays frozen."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "21a542eba9e889323b2cb1b7d7c75d9c9cab1025"


def test_pure_design_uses_only_memory_and_no_runtime_or_observed_receipt_dependency():
    tree = ast.parse((ROOT / "tests/inherited_ofd_design/model.py").read_bytes())
    allowed = {
        "hashlib",
        "json",
        "re",
        "dataclasses",
        "typing",
        "tests.audit.fd_ofd_lifetime_model",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(n.name in allowed for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            assert name not in {
                "open",
                "exec",
                "eval",
                "compile",
                "__import__",
                "read_bytes",
                "write_bytes",
                "write_text",
                "run",
                "Popen",
                "system",
                "connect",
                "Thread",
            }


def test_all_prior_runtime_tests_evidence_and_actual_producers_remain_byte_unchanged():
    paths = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            BASE,
            "--",
            "src",
            "compatibility",
            ".github",
            "tests",
            "docs/evidence",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert (
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *paths],
            cwd=ROOT,
            text=True,
        )
        == ""
    )
