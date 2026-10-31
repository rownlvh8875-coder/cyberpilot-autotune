"""Origin observations remain test-only; all prior runtime/source/evidence frozen."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "2d11becc2f5b3b71558db6c944de74ddf18354b3"


def test_pure_contract_wire_model_image_have_no_io_or_admission_bridge():
    for filename, allowed in (
        ("contracts.py", {"dataclasses", "tests.guest_raw_lifetime.model"}),
        ("wire.py", {"re", "contracts", "tests.guest_raw_lifetime.model"}),
        ("model.py", {"contracts", "tests.guest_raw_lifetime.model"}),
        ("image.py", {"gzip", "io", "contracts", "tests.guest_raw_lifetime.model"}),
    ):
        tree = ast.parse((ROOT / "tests/guest_bootstrap" / filename).read_bytes())
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
                    "getattr",
                    "globals",
                }


def test_every_preexisting_runtime_experiment_source_test_and_evidence_path_is_unchanged():
    scope = ["src", "compatibility", ".github", "tests", "docs/evidence"]
    previous = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE, "--", *scope],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *scope],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    assert not previous & changed
