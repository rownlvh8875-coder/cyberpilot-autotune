"""HR021/025/026:matching claims cannot acquire I/O or remove old admission blocks."""

import ast
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.fixtures.audit_compatibility_history import api, complete


def test_fresh_import_is_inert_and_does_not_load_old_core_or_runtime(tmp_path):
    script = """
import sys,os,importlib
sys.dont_write_bytecode=True
def guard(event,args):
 if (event.startswith(('socket.','subprocess.','os.fork','os.exec','ctypes.'))
     or event in {'os.mkdir','os.remove','os.rename'}):
  raise AssertionError(event)
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  raise AssertionError(event)
sys.addaudithook(guard)
for name in ('contracts','validation'):
 importlib.import_module('tests.audit_compatibility_history.'+name)
for n in sys.modules:
 assert not n.startswith(('cyberpilot_autotune','tests.audit_compatibility.',
                          'tests.audit_compatibility_capture'))
print('INERT_PURE_IMPORT')
"""
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "INERT_PURE_IMPORT" and list(tmp_path.iterdir()) == []


def test_package_uses_only_pure_stdlib_and_sibling_imports():
    root = Path(__file__).resolve().parents[1] / "tests/audit_compatibility_history"
    allowed = {"json", "dataclasses", "hashlib", "typing"}
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (node.level == 1 and node.module == "contracts") or (
                    node.level == 0 and node.module in allowed
                )


def test_h_record_cannot_override_bad_current_C_or_supply_old_IO():
    from tests.audit_compatibility.contracts import IO_UNAVAILABLE, PERMISSIONS
    from tests.audit_compatibility.validation import assess_compatibility
    from tests.fixtures.audit_compatibility_core import complete as core_vector

    h, policy = complete()
    assert api("validation").assess_record(h, policy).consistency == "STRUCTURAL_RECORD_MATCH"
    v = core_vector(candidate_extra={"unregistered.py": b"not approved"})
    current = assess_compatibility(v.bundle, v.manifest)
    assert current.decision == "REJECTED" and set(IO_UNAVAILABLE) <= set(current.unavailable_checks)
    assert current.permissions == h.permissions == PERMISSIONS
    clean = core_vector()
    assert assess_compatibility(clean.bundle, clean.manifest).decision == "UNAVAILABLE"


def test_all_earlier_files_and_guard_bytes_are_preserved():
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"}
    paths = json.loads(
        (
            root / "docs/evidence/audit_compatibility/historical-design-v1/semantics.json"
        ).read_bytes()
    )["future_pure_preparation_paths"]
    changed = (
        subprocess.check_output(
            ["git", "diff", "--name-status", "fa33fbf970adfdcb6b23d35489364158740cc6d9"],
            cwd=root,
            env=env,
        )
        .decode()
        .splitlines()
    )
    assert all(row.startswith("A\t") and row[2:] in paths for row in changed)
    module = importlib.import_module("tests.audit_compatibility.contracts")
    assert module.IO_UNAVAILABLE == (
        "CURRENT_INDEX_WORKTREE",
        "EFFECTIVE_ATTRIBUTES",
        "HISTORICAL_REPLAY",
        "SOURCE_CAPTURE_ATOMICITY",
    )
