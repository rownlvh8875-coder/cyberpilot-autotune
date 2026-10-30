"""The observed experiment adds no production/runtime/controller capability."""

import ast
from pathlib import Path


def test_pure_observed_checker_has_no_io_or_operational_imports():
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / "tests/experiments/guest_data_fd_handoff/model.py").read_text())
    allowed = {"dataclasses", "hashlib", "json", "re", "typing"}
    forbidden = {
        "open",
        "exec",
        "eval",
        "__import__",
        "write_text",
        "write_bytes",
        "connect",
        "start",
        "system",
        "popen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(n.name.split(".")[0] in allowed for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed
        elif isinstance(node, ast.Call):
            call = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            )
            assert call not in forbidden
