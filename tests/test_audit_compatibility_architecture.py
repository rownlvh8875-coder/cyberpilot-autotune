"""Audit-only package boundaries, first import and first assessment side effects."""

import ast
import os
import subprocess
import sys
from pathlib import Path


def test_audit_core_imports_only_closed_stdlib_and_local_modules():
    root = Path(__file__).parent / "audit_compatibility"
    allowed = {"dataclasses", "hashlib", "json", "re", "typing"}
    local = {"contracts", "git_objects", "schema"}
    forbidden_calls = {"open", "eval", "exec", "compile", "__import__", "getattr", "setattr"}
    for path in root.glob("*.py"):
        module = ast.parse(path.read_text())
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                assert all(name.name in allowed for name in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert node.module in (local if node.level == 1 else allowed), path
            if isinstance(node, ast.Call):
                assert not (isinstance(node.func, ast.Name) and node.func.id in forbidden_calls), (
                    path
                )
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in {
                        "write",
                        "write_text",
                        "write_bytes",
                        "unlink",
                        "mkdir",
                        "rename",
                        "system",
                        "start",
                        "submit",
                    }


def test_fresh_import_and_first_assessment_without_external_effects(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    script = """
import os, sys
sys.dont_write_bytecode = True
events = []
def audit(event, args):
    if event.startswith(("socket.", "subprocess.", "os.exec", "os.fork")):
        raise AssertionError(event)
    if event in {"os.mkdir", "os.remove", "os.rename", "os.rmdir"}:
        raise AssertionError(event)
    if event == "open":
        path, mode, flags = args
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError((event, path))
    events.append(event)
sys.addaudithook(audit)
from tests.audit_compatibility.validation import assess_compatibility
from tests.fixtures.audit_compatibility_core import complete
v = complete()
result = assess_compatibility(v.bundle, v.manifest)
assert result.structural_content_status == "CONTENT_MATCH"
assert result.decision == "UNAVAILABLE" and result.status == "BLOCKED"
assert not any(value for _, value in result.permissions)
assert not any(name.startswith(("cyberpilot_autotune.application", "openpilot", "cereal"))
               for name in sys.modules)
print("FIRST_IMPORT_AND_ASSESSMENT_NO_EXTERNAL_EFFECTS")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "FIRST_IMPORT_AND_ASSESSMENT_NO_EXTERNAL_EFFECTS"
    assert list(tmp_path.iterdir()) == []
