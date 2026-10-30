"""New observation code cannot mutate old code or grow an application bridge."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "compatibility/guest_consumption"


def test_pure_consumer_has_no_io_process_native_or_application_imports():
    allowed = {"re", "dataclasses", "typing", "hashlib", "json"}
    for name in ("contracts.py", "wire.py", "producer.py", "checks.py"):
        tree = ast.parse((PACKAGE / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name.split(".")[0] in allowed for a in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (
                    node.level == 1
                    or (node.module or "").split(".")[0] in allowed
                    or (node.module or "").startswith("compatibility.guest_build_receipt.")
                )
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
                    "system",
                    "popen",
                    "connect",
                    "start",
                }


def test_operational_surface_does_not_import_unsafe_legacy_runners_or_vehicle_runtime():
    for path in PACKAGE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(
                n.split(".")[0]
                in {
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
                for n in names
            )
            assert not any(
                n
                in {
                    "compatibility.containment_backend_harmless.vm_runner",
                    "compatibility.containment_guest_collector.vm_runner",
                }
                for n in names
            )


def test_existing_packages_runtime_ci_old_evidence_and_fixtures_remain_exact():
    protected = [
        "src",
        ".github",
        "compatibility/guest_build_receipt",
        "compatibility/guest_input_closure",
        "compatibility/containment_backend_harmless",
        "compatibility/containment_guest_collector",
        "compatibility/friction_native",
        "tests/fixtures/replay",
    ]
    old_evidence = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "c5b824f4f37e05bcac81769f1d01a55a51c26e1d",
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
                "c5b824f4f37e05bcac81769f1d01a55a51c26e1d",
                "--",
                *protected,
                *old_evidence,
            ],
            cwd=ROOT,
            text=True,
        ).strip()
        == ""
    )
