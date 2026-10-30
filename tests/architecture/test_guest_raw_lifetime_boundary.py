"""The guest prototype never becomes an installed runtime/application dependency."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "57b2c942d38f26343bb73fa8cf0f813c58f920a5"


def test_raw_model_and_image_builder_have_no_host_io_or_runtime_authority():
    for name, allowed in (
        ("model.py", {"dataclasses", "re"}),
        ("image.py", {"gzip", "io", "model"}),
    ):
        tree = ast.parse((ROOT / "tests/guest_raw_lifetime" / name).read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(n.name.split(".")[0] in allowed for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] in allowed
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


def test_prior_installed_runtime_actual_evidence_and_experiments_are_unchanged():
    previous = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE, "--", "docs/evidence", "tests/audit"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    paths = ["src", "compatibility", ".github", "tests/fixtures", "tests/experiments", *previous]
    assert (
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *paths],
            cwd=ROOT,
            text=True,
        )
        == ""
    )
