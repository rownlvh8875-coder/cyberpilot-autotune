"""Inert imports,closed capabilities and separately frozen historical ceilings."""

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_fresh_import_has_no_effects_or_old_bridges(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = r"""
import sys,os,importlib
sys.path.insert(0,sys.argv[1])
def guard(event,args):
 if event.startswith(('socket.','subprocess.','os.fork','os.exec','ctypes.')):
  raise AssertionError(event)
 if event in {'os.mkdir','os.remove','os.rename','os.truncate','os.chmod'}:
  raise AssertionError(event)
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  raise AssertionError(event)
sys.addaudithook(guard)
for name in ('contracts','seccomp','runner','supervision'):
 importlib.import_module('tests.audit_compatibility_executor.'+name)
importlib.import_module('tests.fixtures.h1_synthetic_payload')
for name in sys.modules:
 assert not name.startswith(('cyberpilot_autotune','tests.audit_compatibility.',
  'tests.audit_compatibility_history','tests.audit_compatibility_capture'))
print('INERT_CLOSED_SYNTHETIC_IMPORT')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-S", "-c", script, str(root)],
        cwd=tmp_path,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == b"INERT_CLOSED_SYNTHETIC_IMPORT"
    assert list(tmp_path.iterdir()) == []


def test_only_stdlib_and_new_sibling_dependencies():
    root = Path(__file__).resolve().parent / "audit_compatibility_executor"
    allowed = {
        "ctypes",
        "fcntl",
        "hashlib",
        "importlib",
        "json",
        "os",
        "platform",
        "resource",
        "selectors",
        "signal",
        "socket",
        "stat",
        "subprocess",
        "sys",
        "tempfile",
        "time",
        "types",
        "pathlib",
        "typing",
        "urllib",
        "dataclasses",
        "enum",
        "struct",
    }
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(n.name.split(".")[0] in allowed for n in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.level == 1 or node.module.split(".")[0] in allowed


def test_old_non_guard_functions_and_all_other_bytes_unchanged():
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"}
    old = subprocess.check_output(
        [
            "/usr/bin/git",
            "show",
            "ac6adf32ab163fa1fe9eaeb635644037c0de8cde:"
            "tests/test_audit_compatibility_history_architecture.py",
        ],
        cwd=root,
        env=env,
    ).decode()
    new = (root / "tests/test_audit_compatibility_history_architecture.py").read_text()
    current = {
        n.name: ast.get_source_segment(new, n)
        for n in ast.parse(new).body
        if isinstance(n, ast.FunctionDef)
    }
    for node in ast.parse(old).body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name != "test_all_earlier_files_and_guard_bytes_are_preserved"
        ):
            assert current[node.name] == ast.get_source_segment(old, node)
    # Exercise the amended consumer,including untracked paths and frozen ranges.
    guard = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    guard.test_all_earlier_files_and_guard_bytes_are_preserved()


def test_no_historical_command_or_permission_can_be_supplied(tmp_path):
    m = importlib.import_module("tests.audit_compatibility_executor.contracts")
    run = importlib.import_module("tests.audit_compatibility_executor.runner").run_synthetic
    for command in ("O-PYTEST", "O-H6", "D-PYTEST", "D-COVERAGE", "STACK", "H"):
        with pytest.raises(ValueError):
            m.SyntheticCase(command)
    with pytest.raises(TypeError):
        run(m.SyntheticRequest(m.SyntheticCase.FD_CLOSED, str(tmp_path)), argv=("anything",))
    assert list(tmp_path.iterdir()) == []
