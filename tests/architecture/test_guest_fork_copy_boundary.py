"""Observed guest experiment never becomes a synthetic/application/runtime bridge."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "4a04a5a38a68970624380c10113c97a752af4aa8"


def test_pure_codec_and_image_have_no_io_authority_or_synthetic_oracle_dependency():
    for name, allowed in (
        ("model.py", {"dataclasses", "tests.guest_raw_lifetime.model"}),
        ("image.py", {"gzip", "io", "model", "tests.guest_raw_lifetime.model"}),
    ):
        tree = ast.parse((ROOT / "tests/guest_fork_copy" / name).read_bytes())
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


def test_every_previous_runtime_test_evidence_and_compatibility_path_is_unchanged():
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
