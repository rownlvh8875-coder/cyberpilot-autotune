"""Catch I/O in pure contracts, runtime bridges and old-tree mutations."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "compatibility/guest_input_seal"
BASE = "ae7b3644984cd5ecc8fbb23532f5ec7e0da3998f"


def test_pure_contract_has_no_io_or_authority_bridge():
    allowed = {"dataclasses", "re", "hashlib", "json", "typing"}
    for name in ("contracts.py", "wire.py", "evaluation.py"):
        for node in ast.walk(ast.parse((PACKAGE / name).read_text())):
            if isinstance(node, ast.Import):
                assert all(n.name.split(".")[0] in allowed for n in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.level == 1 or (node.module or "").split(".")[0] in allowed
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


def test_no_vehicle_or_unsafe_runtime_imports():
    forbidden = {
        "cereal",
        "openpilot",
        "cyberpilot_autotune",
        "socket",
        "threading",
        "multiprocessing",
        "requests",
        "urllib",
        "ctypes",
    }
    for path in PACKAGE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [n.name for n in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            assert not any(n.split(".")[0] in forbidden for n in names)
            assert not any(
                n
                in {
                    "compatibility.containment_backend_harmless.vm_runner",
                    "compatibility.containment_guest_collector.vm_runner",
                }
                for n in names
            )


def test_prior_runtime_evidence_ci_and_packages_unchanged():
    protected = [
        "src",
        ".github",
        "compatibility/guest_consumption",
        "compatibility/guest_build_receipt",
        "compatibility/guest_input_closure",
        "compatibility/containment_backend_harmless",
        "compatibility/containment_guest_collector",
        "compatibility/friction_native",
        "tests/fixtures",
    ]
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
