"""GC065–070:imports inert,explicit capture read-only,old pure package unchanged."""

import ast
import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

from tests.fixtures.audit_compatibility_capture import api, prepared, request
from tests.fixtures.audit_compatibility_capture import (
    isolated_capture_config as isolated_capture_config,
)


@pytest.mark.parametrize("function", ("prepared", "request"))
def test_native_fixture_rejects_unsupported_platform_before_IO(tmp_path, monkeypatch, function):
    from tests.fixtures import audit_compatibility_capture as fixtures

    monkeypatch.setattr(api("worktree_reader"), "capable", lambda: False)

    def forbidden(*args, **kwargs):
        raise AssertionError("native fixture executed on unsupported platform")

    monkeypatch.setattr(fixtures, "git", forbidden)
    with pytest.raises(pytest.skip.Exception, match="C1_POSIX_RAW_BYTES_V1"):
        getattr(fixtures, function)(tmp_path)
    assert not (tmp_path / "repo").exists()


def test_import_fresh_has_no_process_network_or_filesystem_writes(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    script = """
import sys,os,importlib
sys.dont_write_bytecode=True
def audit(event,args):
 if (event.startswith(("socket.","subprocess.","os.fork"))
     or event in {"os.mkdir","os.rename","os.remove"}):
  raise AssertionError(event)
 if event=="open" and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  raise AssertionError(event)
sys.addaudithook(audit)
for name in ("contracts","worktree_reader","git_reader","capture"):
 importlib.import_module("tests.audit_compatibility_capture."+name)
print("INERT_IMPORT")
"""
    r = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.stdout.strip() == "INERT_IMPORT" and list(tmp_path.iterdir()) == []


def test_explicit_capture_opens_no_writer_and_uses_only_git_child(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    snapshot = {
        p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    script = """
import os,sys,json,stat
sys.dont_write_bytecode=True
from tests.audit_compatibility_capture.contracts import RepoLayout,CaptureRequest,CaptureBudget
from tests.audit_compatibility_capture.capture import capture_checkout
from tests.fixtures.audit_compatibility_capture import synthetic_config_scope
v=json.loads(sys.argv[1]);r=CaptureRequest(v["head"],v["head"],None,(v["head"],),
 RepoLayout(v["root"],v["gitdir"],v["common"],tuple(v["configs"])),CaptureBudget(8000000,64000000,50000,5000000000))
def audit(event,args):
 if event.startswith(("socket.","os.fork")) or event in {"os.mkdir","os.remove","os.rename"}:
  raise AssertionError(event)
 if event=="open" and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  if not isinstance(args[0],int) or not stat.S_ISFIFO(os.fstat(args[0]).st_mode):
   raise AssertionError("FILESYSTEM_WRITE")
 if event=="subprocess.Popen":
  assert args[0]=="/usr/bin/git"
with synthetic_config_scope(tuple(v["configs"])):
 sys.addaudithook(audit)
 result=capture_checkout(r)
assert result.consistency=="OBSERVED_STABLE",result
assert not any(v for _,v in result.permissions)
print("READ_ONLY_CAPTURE")
"""
    value = dict(
        head=req.validation_head,
        root=str(root),
        gitdir=req.layout.git_dir,
        common=req.layout.common_dir,
        configs=req.layout.control_roots,
    )
    r = subprocess.run(
        [sys.executable, "-c", script, json.dumps(value)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "READ_ONLY_CAPTURE"
    assert snapshot == {
        p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_package_has_no_network_runtime_or_application_dependencies():
    allowed = {
        "os",
        "errno",
        "posixpath",
        "re",
        "stat",
        "struct",
        "contextlib",
        "collections.abc",
        "hashlib",
        "typing",
        "dataclasses",
        "selectors",
        "subprocess",
        "time",
        "json",
    }
    package = Path(__file__).parent / "audit_compatibility_capture"
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(n.name in allowed for n in node.names)
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                assert node.module in allowed or node.module.startswith(
                    "tests.audit_compatibility."
                )


def test_core_source_bytes_remain_at_K1():
    root = Path(__file__).resolve().parents[1]
    for p in (root / "tests/audit_compatibility").glob("*.py"):
        original = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "show",
                "c71e573d3c42c3122c07338cc34135e4aa8efa52:" + p.relative_to(root).as_posix(),
            ]
        )
        assert p.read_bytes() == original


def test_report_digest_is_content_identity_not_authority(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    result = api("capture").capture_checkout(request(root))
    assert len(result.content_digest) == 64 and result.content_digest == result.content_digest
    changed = replace(result, errors=("KNOWN_ERROR",))
    assert changed.content_digest != result.content_digest
    assert changed.integrated_admission is False
