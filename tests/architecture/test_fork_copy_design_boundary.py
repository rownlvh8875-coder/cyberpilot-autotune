"""Design remains pure and all previous source/evidence stays frozen."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "420538d7c20edcfca3eadf136b30b622ca2bede9"


def test_copy_contract_is_pure_and_has_no_producer_application_or_runtime_dependency():
    tree = ast.parse((ROOT / "tests/fork_copy_design/model.py").read_bytes())
    allowed = {"hashlib", "json", "dataclasses", "typing", "tests.audit.fd_ofd_lifetime_model"}
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


def test_previous_runtime_tests_sources_evidence_and_guest_producers_remain_unchanged():
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
