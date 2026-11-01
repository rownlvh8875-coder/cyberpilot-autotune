"""Explicit successor delta; no historical guard is silently skipped."""

import ast
import importlib
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def violations(raw):
    forbidden = {
        "socket",
        "requests",
        "httpx",
        "threading",
        "multiprocessing",
        "cereal",
        "openpilot",
    }
    result = []
    for node in ast.walk(ast.parse(raw)):
        names = (
            [n.name for n in node.names]
            if isinstance(node, ast.Import)
            else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        )
        if any(
            n.split(".")[0] in forbidden
            or any(
                part in n
                for part in (
                    "cyberpilot_autotune.application",
                    "cyberpilot_autotune.owner",
                    "cyberpilot_autotune.research",
                    "guest_data_fd_handoff",
                    "vm_runner",
                )
            )
            for n in names
        ):
            result.append("forbidden dependency")
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            )
            if name in {"Params", "exec", "eval", "system", "compile_fixed_probe"}:
                result.append("forbidden capability")
            if any(
                k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True
                for k in node.keywords
            ):
                result.append("shell capability")
    return result


def test_harness_has_no_legacy_runtime_application_or_network_bridge():
    for path in (ROOT / "tests/deny_fd_v2_harness").glob("*.py"):
        assert violations(path.read_bytes()) == [], path.name


def test_architecture_guard_rejects_operational_capabilities():
    for raw in (
        "import socket",
        "import threading",
        "from cereal import messaging",
        "from cyberpilot_autotune.application import AuthorizationGrant",
        "from tests.experiments.guest_data_fd_handoff import runner",
        "Params()",
        "subprocess.Popen(args,shell=True)",
        "compile_fixed_probe(path)",
    ):
        assert violations(raw)


def test_current_delta_is_exact_22():
    name = "tests.history_transition.deny_fd_v2_harness_successor"
    assert importlib.util.find_spec(name) is not None, "closed harness successor required"
    v = importlib.import_module(name)
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", v.BASE, "HEAD"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    assert changed == set(v.NEW_PATHS) | set(v.MODIFIED)
    assert len(changed) == 22
    assert len(v.validate_harness_successor(ROOT)) == 20
