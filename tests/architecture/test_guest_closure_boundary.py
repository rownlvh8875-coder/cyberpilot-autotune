"""Offline closure verification cannot launch code or confer runtime authority."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "compatibility/guest_input_closure"


def test_closure_package_cannot_launch_network_threads_processes_or_application():
    assert PACKAGE.is_dir()
    forbidden = {
        "subprocess",
        "socket",
        "threading",
        "multiprocessing",
        "ctypes",
        "requests",
        "urllib",
        "cereal",
        "openpilot",
        "cyberpilot_autotune",
    }
    for path in PACKAGE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(n.split(".")[0] in forbidden for n in names)
            assert not any(
                n
                in {
                    "compatibility.containment_backend_harmless.vm_runner",
                    "compatibility.containment_guest_collector.vm_runner",
                }
                for n in names
            )
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
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
                }


def test_prior_source_evidence_ci_and_fixture_packages_are_unchanged():
    paths = [
        "src",
        ".github",
        "compatibility/containment_backend_harmless",
        "compatibility/containment_guest_collector",
        "docs/evidence/guest_collector_results.json",
        "docs/evidence/containment_backend_harmless_results.json",
        "tests/fixtures/replay",
    ]
    assert (
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                "9aeb4aeda3297d25b0df7d5dbb909265847f597a",
                "--",
                *paths,
            ],
            cwd=ROOT,
            text=True,
        ).strip()
        == ""
    )
