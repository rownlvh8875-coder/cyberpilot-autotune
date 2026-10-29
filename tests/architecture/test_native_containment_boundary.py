"""Keep the synthetic checker repository-only, pure and capability-free."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def violations(source):
    allowed = {"dataclasses", "enum", "hashlib", "json", "re", "typing"}
    local = {"contracts", "validation"}
    forbidden = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "Params",
        "SubMaster",
        "PubMaster",
        "socket",
        "Thread",
        "Process",
        "Popen",
        "run",
        "system",
        "exec",
        "eval",
        "__import__",
        "import_module",
        "print",
        "send",
        "put",
        "start",
        "SteeringRequest",
        "AuthorizationGrant",
        "mkdir",
        "mknod",
    }
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if any(n.name.split(".")[0] not in allowed for n in node.names):
                found.append("import")
        elif isinstance(node, ast.ImportFrom):
            if not (
                (node.level == 1 and node.module in local)
                or (node.level == 0 and (node.module or "").split(".")[0] in allowed)
            ):
                found.append("import")
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            if name in forbidden:
                found.append("call")
    return found


def test_checker_has_only_neutral_imports_and_no_io_or_execution_calls():
    sources = list((ROOT / "compatibility/native_containment").glob("*.py"))
    assert sources
    for path in sources:
        assert not violations(path.read_text()), path


@pytest.mark.parametrize(
    "source",
    [
        "import socket",
        "import subprocess as innocent",
        "from threading import Thread",
        "from openpilot.common.params import Params",
        "import cereal",
        "from pathlib import Path",
        "from cyberpilot_autotune.application import AuthorizationGrant",
        "from cyberpilot_autotune.owner_protocol import contracts",
        "from compatibility.friction_native import run",
        "open('file', 'w')",
        "target.write_bytes(b'x')",
        "__import__('socket')",
        "eval('code')",
        "exec('code')",
    ],
)
def test_boundary_guard_detects_forbidden_dependency_or_side_effect(source):
    assert violations(source)


def test_installed_package_does_not_bridge_to_synthetic_checker():
    for path in (ROOT / "src/cyberpilot_autotune").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all("native_containment" not in item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert "native_containment" not in (node.module or "")
