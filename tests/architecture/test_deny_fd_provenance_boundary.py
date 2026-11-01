"""The synthetic receipt has no producer, legacy adapter or installed capability."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def violations(source):
    allowed = {"dataclasses", "enum", "hashlib", "json", "re"}
    forbidden = {
        "open",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
        "connect",
        "run",
        "Popen",
        "system",
        "Thread",
        "Process",
        "start",
        "Params",
        "exec",
        "eval",
        "__import__",
        "import_module",
        "capture_cases",
        "parse_serial",
        "print",
    }
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if any(item.name not in allowed for item in node.names):
                found.append("import")
        elif isinstance(node, ast.ImportFrom):
            if not (
                (node.level == 1 and node.module == "contracts")
                or (node.level == 0 and node.module in allowed)
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
            if name == "__setattr__" and not (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "object"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "self"
            ):
                found.append("mutation")
    return found


def test_neutral_package_is_pure_and_has_no_legacy_or_application_bridge():
    for path in (ROOT / "tests/deny_fd_provenance").glob("*.py"):
        assert not violations(path.read_text()), path
    for path in (ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_bytes())):
            names = (
                [item.name for item in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            assert all("deny_fd_provenance" not in name for name in names)


@pytest.mark.parametrize(
    "source",
    [
        "import socket",
        "from openpilot.common.params import Params",
        "import cereal",
        "from tests.experiments.guest_data_fd_handoff.model import parse_serial",
        "from cyberpilot_autotune.application import AuthorizationGrant",
        "from subprocess import run",
        "open('file','w')",
        "capture_cases(('HH03',))",
        "value.write_bytes(b'x')",
        "object.__setattr__(other, 'application_authorized', True)",
    ],
)
def test_guard_rejects_operational_imports_and_mutations(source):
    assert violations(source)
