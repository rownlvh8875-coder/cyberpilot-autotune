"""The scope experiment stays outside installed code and freezes all old evidence."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "06e218ca9e17af9547fc7871df70d2b9415f2cb9"


def test_pure_contract_has_only_memory_operations_and_no_runtime_or_authority_dependency():
    for name, allowed in (
        ("model.py", {"dataclasses", "tests.guest_raw_lifetime.model"}),
        ("image.py", {"gzip", "io", "model"}),
    ):
        tree = ast.parse((ROOT / "tests/guest_root_scope" / name).read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(n.name in allowed for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module in allowed
            elif isinstance(node, ast.Call):
                function = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert function not in {
                    "open",
                    "exec",
                    "eval",
                    "compile",
                    "__import__",
                    "read_bytes",
                    "write_bytes",
                    "write_text",
                    "connect",
                    "Thread",
                    "Popen",
                    "run",
                    "system",
                }


def test_all_preexisting_runtime_tests_evidence_and_experiments_are_byte_unchanged():
    previous = subprocess.check_output(
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
            ["git", "diff", "--name-only", BASE, "--", *previous],
            cwd=ROOT,
            text=True,
        )
        == ""
    )
