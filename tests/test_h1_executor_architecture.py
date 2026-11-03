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
            "git",
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
        run(m.SyntheticRequest(m.SyntheticCase.FD_CLOSED, "/not-used"), argv=("anything",))
    assert list(tmp_path.iterdir()) == []


_BLOCK_NATIVE = r"""
import importlib.abc,sys
class MissingNative(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in blocked:
   raise ModuleNotFoundError(fullname,name=fullname)
for name in blocked:
 sys.modules.pop(name,None)
sys.meta_path.insert(0,MissingNative())
"""


def _fresh_portability_check(tmp_path, script):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(root)],
        cwd=tmp_path,
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (result.stdout + result.stderr).decode(errors="replace")
    assert result.stdout.rstrip().endswith(b"PORTABILITY_CHECK_COMPLETE")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("blocked", [("fcntl",), ("resource",), ("fcntl", "resource")])
def test_missing_native_modules_are_unavailable_before_effects(tmp_path, blocked):
    script = (
        f"blocked={blocked!r}\n"
        + _BLOCK_NATIVE
        + r"""
sys.path.insert(0,sys.argv[1])
import os,importlib
from tests.audit_compatibility_executor import runner,supervision,contracts
from tests.fixtures import h1_synthetic_payload
runner.platform.system=lambda: 'Linux'
runner.platform.machine=lambda: 'x86_64'
runner.os.getuid=runner.os.getgid=lambda: 1000
def forbidden(*args,**kwargs):
 raise AssertionError('effect before native prerequisites')
runner._prepare=forbidden
runner._sealed_filter=forbidden
os.pidfd_open=forbidden
result=runner.run_synthetic(contracts.SyntheticRequest(contracts.SyntheticCase.FD_CLOSED,'/unused'))
assert result.outcome=='UNAVAILABLE' and result.run_directory is None
assert 'REQUIRED_CONTROL_UNAVAILABLE' in result.unavailable
assert result.status=='BLOCKED' and not any(v for _,v in result.permissions)
assert h1_synthetic_payload.main(())==2
try:
 supervision._decode(b'not JSON',contracts.SyntheticCase.FD_CLOSED)
except ValueError:
 pass
else:
 raise AssertionError('invalid protocol accepted')
print('PORTABILITY_CHECK_COMPLETE')
"""
    )
    _fresh_portability_check(tmp_path, script)


@pytest.mark.parametrize(
    "host", ["Windows", "Darwin", "aarch64", "no-getuid", "no-getgid", "uid-zero", "gid-zero"]
)
def test_unsupported_hosts_return_before_any_native_probe(tmp_path, host):
    script = (
        f"host={host!r}\nblocked=('fcntl','resource')\n"
        + _BLOCK_NATIVE
        + r"""
sys.path.insert(0,sys.argv[1])
from tests.audit_compatibility_executor import runner,contracts
runner.platform.system=lambda: host if host in ('Windows','Darwin') else 'Linux'
runner.platform.machine=lambda: 'aarch64' if host=='aarch64' else 'x86_64'
runner.os.getuid=lambda: 0 if host=='uid-zero' else 1000
runner.os.getgid=lambda: 0 if host=='gid-zero' else 1000
if host.startswith('no-'):
 delattr(runner.os,host[3:])
def forbidden(*args,**kwargs):
 raise AssertionError('unsupported host touched native control/source/artifact')
runner._sealed_filter=runner._source_hashes=runner._prepare=forbidden
runner.os.pidfd_open=forbidden
assert runner._preflight()==('UNSUPPORTED_HOST',)
result=runner.run_synthetic(contracts.SyntheticRequest(contracts.SyntheticCase.FD_CLOSED,'/unused'))
assert result.outcome=='UNAVAILABLE' and result.run_directory is None
try:
 runner.run_synthetic(object())
except ValueError:
 pass
else:
 raise AssertionError('request validation bypassed')
print('PORTABILITY_CHECK_COMPLETE')
"""
    )
    _fresh_portability_check(tmp_path, script)


def test_all_harness_tests_collect_without_native_modules(tmp_path):
    script = (
        "import pytest\nblocked=('fcntl','resource')\n"
        + _BLOCK_NATIVE
        + r"""
sys.path.insert(0,sys.argv[1])
files=[sys.argv[1]+'/tests/test_h1_executor_'+name+'.py'
 for name in ('values','launch','supervision','architecture')]
assert pytest.main(['--collect-only','-q','-p','no:cacheprovider',*files])==0
print('PORTABILITY_CHECK_COMPLETE')
"""
    )
    _fresh_portability_check(tmp_path, script)
