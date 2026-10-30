"""Diagnostic receipt/planner has no operational bridge or privileged imports."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "compatibility/guest_build_receipt"


def test_build_receipt_import_and_call_surface_is_pure_and_closed():
    allowed = {
        "__future__",
        "re",
        "dataclasses",
        "enum",
        "typing",
        "hashlib",
        "json",
        "collections",
        "sys",
    }
    relatives = {"models", "codec", "evaluation", "planning"}
    denied_calls = {
        "open",
        "eval",
        "exec",
        "compile",
        "__import__",
        "write",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "chmod",
        "rename",
        "replace",
        "system",
        "popen",
        "execv",
        "execve",
        "spawn",
        "start",
        "connect",
        "getenv",
    }
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (node.level == 1 and node.module in relatives) or (
                    node.level == 0 and (node.module or "").split(".")[0] in allowed
                )
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in denied_calls


def test_all_old_sources_packages_ci_and_evidence_are_byte_preserved():
    protected = [
        "src",
        ".github",
        "tests/fixtures/replay",
        "compatibility/containment_backend_harmless",
        "compatibility/containment_guest_collector",
        "compatibility/guest_input_closure",
        "compatibility/friction_native",
    ]
    assert (
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                "bbec08f84d0d08b17075663643ddeba6db46d977",
                "--",
                *protected,
            ],
            cwd=ROOT,
            text=True,
        ).strip()
        == ""
    )
    old_evidence = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "bbec08f84d0d08b17075663643ddeba6db46d977",
            "--",
            "docs/evidence",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert (
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                "bbec08f84d0d08b17075663643ddeba6db46d977",
                "--",
                *old_evidence,
            ],
            cwd=ROOT,
            text=True,
        ).strip()
        == ""
    )
