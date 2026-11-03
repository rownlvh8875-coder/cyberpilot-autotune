"""Streaming/cleanup logic tests,plus separately labelled bounded host cases."""

import importlib
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.audit_compatibility_executor.contracts import SyntheticCase, SyntheticRequest


def supervision():
    try:
        return importlib.import_module("tests.audit_compatibility_executor.supervision")
    except ModuleNotFoundError:
        pytest.fail("bounded owned process supervision not implemented")


def controlled(code):
    child = subprocess.Popen(
        [sys.executable, "-I", "-B", "-S", "-c", code],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
    )
    return child, os.pidfd_open(child.pid)


def test_combined_output_cap():
    m = supervision()
    child, fd = controlled("import os;os.write(1,b'a'*32768);os.write(2,b'b'*32769)")
    try:
        out, err, errors, code = m._collect(child, fd, 2)
        assert len(out) + len(err) == 65536
        assert "OUTPUT_LIMIT" in errors
        assert child.wait(timeout=2) is not None
    finally:
        os.close(fd)


def test_deadline_with_open_descendant_pipe():
    m = supervision()
    # Same-group short-lived child holds the pipes after its parent exits.
    child, fd = controlled("import os,time;pid=os.fork();time.sleep(1) if pid==0 else None")
    started = time.monotonic()
    try:
        out, err, errors, code = m._collect(child, fd, 0.1)
        assert "TIMEOUT" in errors and time.monotonic() - started < 1
        child.wait(timeout=2)
    finally:
        os.close(fd)


def test_owned_pidfd_only_cleanup(monkeypatch):
    m = supervision()
    child, fd = controlled("import time;time.sleep(.3)")
    try:
        with pytest.raises(ValueError):
            m._kill_owned(child, -1)
        monkeypatch.setattr(m, "_pidfd_pid", lambda _: child.pid + 1)
        with pytest.raises(ValueError):
            m._kill_owned(child, fd)
        assert child.wait(timeout=2) == 0
    finally:
        os.close(fd)


def test_first_failure_survives_cleanup():
    m = supervision()
    child, fd = controlled("import sys;print('FAILED_FIRST',flush=True);sys.exit(7)")
    try:
        out, err, errors, code = m._collect(child, fd, 2)
        assert errors[0] == "NONZERO_EXIT_7" and b"FAILED_FIRST" in out
        result = m._finish(SyntheticCase.NONZERO_EXIT, None, out, err, errors, (), False)
        assert result.outcome == "REJECTED"
        assert result.errors == ("NONZERO_EXIT_7", "CLEANUP_UNCONFIRMED")
        child.wait(timeout=2)
    finally:
        os.close(fd)


def test_abort_and_cleanup_failure():
    m = supervision()
    result = m._finish(
        SyntheticCase.SUPERVISOR_ABORT,
        None,
        b"",
        b"",
        ("SUPERVISOR_EXIT_31",),
        ("MISSING_PROTOCOL",),
        False,
    )
    assert result.errors == ("SUPERVISOR_EXIT_31", "CLEANUP_UNCONFIRMED")
    assert result.unavailable == ("MISSING_PROTOCOL",)
    assert result.cleanup == "UNCONFIRMED" and result.outcome == "REJECTED"


@pytest.mark.parametrize(
    "raw",
    [
        b"{}",
        b'{"schema":"x"}',
        b'{"case":"FD_CLOSED","case":"FD_CLOSED"}',
        b'{"a":NaN}',
        b"[]",
        b"x" * 4097,
    ],
)
def test_closed_helper_protocol_rejects_unknown_duplicate_and_nonfinite(raw):
    m = supervision()
    with pytest.raises(ValueError):
        m._decode(raw, SyntheticCase.FD_CLOSED)


@pytest.mark.parametrize(
    "case,first_error",
    [
        (SyntheticCase.FD_CLOSED, None),
        (SyntheticCase.DIRECTORY_READ_ONLY, None),
        (SyntheticCase.DESCENDANT_NETWORK, None),
        (SyntheticCase.TIMEOUT_SETSID, "TIMEOUT"),
        (SyntheticCase.OUTPUT_FLOOD, "OUTPUT_LIMIT"),
        (SyntheticCase.MISSING_MOUNT, "NONZERO_EXIT_1"),
        (SyntheticCase.NONZERO_EXIT, "NONZERO_EXIT_7"),
        (SyntheticCase.SUPERVISOR_ABORT, "SUPERVISOR_EXIT_31"),
    ],
)
def test_registered_host_case(tmp_path, record_property, case, first_error):
    supervision()
    runner = importlib.import_module("tests.audit_compatibility_executor.runner")
    started = time.monotonic()
    result = runner.run_synthetic(SyntheticRequest(case, str(tmp_path)))
    record_property("observation_scope", "OWNED_SYNTHETIC_ONLY_NOT_H")
    record_property("outcome", result.outcome)
    record_property("unavailable", result.unavailable)
    if result.outcome == "UNAVAILABLE":
        assert result.unavailable
        record_property("host_observation", "UNAVAILABLE_NOT_KERNEL_PASS")
        return
    assert time.monotonic() - started < 10
    assert result.run_directory is not None
    root = Path(result.run_directory)
    assert (root / "protected/canary").read_bytes() == b"SYNTHETIC_ONLY_PROTECTED_V1\n"
    assert all(v is False for _, v in result.permissions) and not result.historical_execution
    if first_error is None:
        assert result.outcome == "SYNTHETIC_OBSERVATION_COMPLETE", result
        observed = json.loads(result.stdout)
        for sample in (observed, observed["descendant"]):
            assert sample["controls"]["NoNewPrivs"] == "1"
            assert sample["controls"]["Seccomp"] == "2"
            assert int(sample["controls"]["CapEff"], 16) == 0
            assert sample["denied"] == dict.fromkeys(
                ("create", "write", "rename", "unlink", "link"), 30
            )
            assert sample["socket_errno"] == sample["userns_errno"] == 1
            assert sample["leaked_objects"] == [] and sample["inherited_filter"] is False
            assert sample["read"] is True and sample["host_hidden"] is True
    else:
        assert result.outcome == "REJECTED", result
        assert result.errors[0] == first_error, result
    if case is SyntheticCase.TIMEOUT_SETSID:
        before = (root / "scratch/heartbeat").read_bytes()
        time.sleep(0.1)
        assert before and (root / "scratch/heartbeat").read_bytes() == before
    if case is SyntheticCase.OUTPUT_FLOOD:
        assert len(result.stdout) + len(result.stderr) == 65536
    if case is SyntheticCase.MISSING_MOUNT:
        assert not (root / "scratch/payload-ran").exists()
    assert result.cleanup == (
        "UNCONFIRMED" if case is SyntheticCase.SUPERVISOR_ABORT else "CONFIRMED"
    )


def sample_payload():
    sample = {
        "controls": {"NoNewPrivs": "1", "Seccomp": "2", "CapEff": "0000000000000000"},
        "denied": dict.fromkeys(("create", "write", "rename", "unlink", "link"), 30),
        "socket_errno": 1,
        "userns_errno": 1,
        "leaked_objects": [],
        "inherited_filter": False,
        "read": True,
        "host_hidden": True,
        "environment_keys": ["LANG"],
        "namespaces": dict.fromkeys(("user", "pid", "net", "mnt", "ipc", "uts"), "child:[1]"),
        "limits": {
            "CPU": [3, 3],
            "AS": [268435456, 268435456],
            "FSIZE": [1048576, 1048576],
            "NOFILE": [64, 64],
            "CORE": [0, 0],
        },
    }
    return {**sample, "descendant": sample}


@pytest.mark.parametrize(
    "field,bad",
    [
        ("read", False),
        ("inherited_filter", True),
        ("leaked_objects", [[1, 2]]),
        ("socket_errno", 0),
        ("userns_errno", 0),
        ("host_hidden", False),
        ("environment_keys", ["HF_TOKEN"]),
        ("environment_keys", ["PYTHONPATH"]),
        ("limits", {}),
        ("denied", {}),
        ("controls", {"NoNewPrivs": "0"}),
    ],
)
def test_observation_return_zero_cannot_hide_missing_controls(field, bad):
    m = supervision()
    value = sample_payload()
    value[field] = bad
    assert m._check_observation(json.dumps(value).encode(), {"user": "host:[2]"}) is False


def test_matching_namespace_is_not_isolation():
    assert not supervision()._check_observation(
        json.dumps(sample_payload()).encode(), {"user": "child:[1]"}
    )


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("valid", ()),
        ("invalid", ("INVALID_OBSERVATION",)),
        ("mismatch", ("OBSERVATION_MISMATCH",)),
        ("cleanup", ("CLEANUP_UNCONFIRMED",)),
        ("canary", ("PROTECTED_CONTENT_CHANGED",)),
        ("abort", ()),
    ],
)
def test_helper_decides_from_observed_facts_not_exit_zero(tmp_path, monkeypatch, mode, expected):
    m = supervision()
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    stdout, stderr = open(os.devnull, "rb"), open(os.devnull, "rb")
    child = SimpleNamespace(pid=os.getpid(), stdout=stdout, stderr=stderr)
    monkeypatch.setattr(m.subprocess, "Popen", lambda *args, **kwargs: child)
    value = sample_payload()
    if mode == "mismatch":
        value["read"] = False
    out = b"invalid" if mode == "invalid" else json.dumps(value).encode()
    monkeypatch.setattr(m, "_collect", lambda *args: (out, b"", (), 0))
    monkeypatch.setattr(m, "_reap", lambda _: mode != "cleanup")
    if mode == "canary":
        (Path(root) / "protected/canary").write_bytes(b"OWNED_NEGATIVE")

    class Abort(Exception):
        pass

    def stop(code):
        assert code == 31
        raise Abort

    monkeypatch.setattr(m.os, "_exit", stop)
    try:
        if mode == "abort":
            with pytest.raises(Abort):
                m._inner(SyntheticCase.SUPERVISOR_ABORT, root)
        else:
            result = m._inner(SyntheticCase.FD_CLOSED, root)
            assert tuple(result["errors"]) == expected
            assert (Path(root) / "stdout.bin").read_bytes() == out
    finally:
        stdout.close()
        stderr.close()


def test_artifact_limits_links_and_run_identity_are_enforced(tmp_path):
    m = supervision()
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    path = Path(root)
    m._verify_root(root, runner._source_hashes())
    (path / "small").write_bytes(b"bounded")
    assert m._read_owned(root, "small", 7) == b"bounded"
    with pytest.raises(ValueError):
        m._read_owned(root, "small", 6)
    (path / "symlink").symlink_to(path / "small")
    with pytest.raises(OSError):
        m._read_owned(root, "symlink", 10)
    os.link(path / "small", path / "hardlink")
    with pytest.raises(ValueError):
        m._read_owned(root, "hardlink", 10)
    with pytest.raises(ValueError):
        m._read_owned(root, "scratch", 10)
    (path / "payload.py").write_bytes(b"CHANGED_OWNED_PAYLOAD")
    with pytest.raises(ValueError):
        m._verify_root(root, runner._source_hashes())


@pytest.mark.parametrize("failure", ["timeout", "oserror", "deadline", "success", "adopted"])
def test_reap_has_bounded_known_or_unknown_result(monkeypatch, failure):
    m = supervision()

    def wait(**kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired("owned", 2)
        if failure == "oserror":
            raise OSError("OWNED_REAP_ERROR")
        return 0

    calls = iter([0, 0, 3, 3])
    if failure == "deadline":
        monkeypatch.setattr(m.time, "monotonic", lambda: next(calls, 3))
    children = iter([(0, 0), (123, 0)] if failure == "adopted" else [])

    def waitpid(*args):
        value = next(children, None)
        if value is None:
            raise ChildProcessError
        return value

    monkeypatch.setattr(m.os, "waitpid", waitpid)
    assert m._reap(SimpleNamespace(wait=wait)) is (failure in ("success", "adopted"))


@pytest.mark.parametrize("bad", ["version", "case", "cleanup", "errors"])
def test_helper_protocol_rechecks_identity_and_reason_types(bad):
    value = {
        "schema": "h1-supervisor-v1",
        "case": "FD_CLOSED",
        "errors": [],
        "unavailable": [],
        "cleanup": "CONFIRMED",
    }
    value["schema" if bad == "version" else bad] = True
    with pytest.raises(ValueError):
        supervision()._decode(json.dumps(value).encode(), SyntheticCase.FD_CLOSED)


@pytest.mark.parametrize("kind", ["valid", "version", "keys", "case", "preflight", "subreaper"])
def test_helper_request_does_not_expand_scope(tmp_path, monkeypatch, capsys, kind):
    import ctypes

    m = supervision()
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    request = {
        "schema": "h1-helper-request-v1",
        "case": "FD_CLOSED",
        "root": root,
        "sources": runner._source_hashes(),
    }
    if kind == "version":
        request["schema"] = "unknown"
    if kind == "case":
        request["case"] = "O-PYTEST"
    if kind == "keys":
        request["argv"] = ["O-PYTEST"]
    monkeypatch.setattr(
        m.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(request).encode()))
    )
    monkeypatch.setattr(runner, "_preflight", lambda: ("MISSING",) if kind == "preflight" else ())
    monkeypatch.setattr(
        ctypes,
        "CDLL",
        lambda *args, **kwargs: SimpleNamespace(
            prctl=lambda *args: -1 if kind == "subreaper" else 0
        ),
    )
    monkeypatch.setattr(m, "_inner", lambda *args: {"schema": "TEST_ONLY_NO_PROCESS"})
    assert m._helper_main() == (0 if kind == "valid" else 2)
    assert ("TEST_ONLY_NO_PROCESS" in capsys.readouterr().out) is (kind == "valid")


def test_controller_refuses_payload_without_pidfd(tmp_path, monkeypatch):
    m = supervision()
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    monkeypatch.setattr(m.os, "pidfd_open", lambda _: (_ for _ in ()).throw(OSError("UNSUPPORTED")))
    result = m.supervise(SyntheticCase.FD_CLOSED, root)
    assert result.outcome == "UNAVAILABLE" and result.cleanup == "UNCONFIRMED"
    assert result.unavailable == ("PIDFD_UNAVAILABLE",)
    assert not (Path(root) / "launch.json").exists()


def test_controller_rejects_corrupted_helper_protocol(tmp_path, monkeypatch):
    m = supervision()
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    real = subprocess.Popen

    def controlled_protocol(args, **kwargs):
        # Intentionally malformed toy helper,not a kernel/runtime observation.
        return real(
            [
                sys.executable,
                "-I",
                "-B",
                "-S",
                "-c",
                "import sys;sys.stdin.buffer.read(4097);print('invalid-protocol')",
            ],
            **kwargs,
        )

    monkeypatch.setattr(m.subprocess, "Popen", controlled_protocol)
    result = m.supervise(SyntheticCase.FD_CLOSED, root)
    assert result.errors[0] == "CONTROLLER_OR_PROTOCOL_ERROR"
    assert result.cleanup == "UNCONFIRMED"
    assert (Path(root) / "controller-stdout.bin").read_bytes() == b"invalid-protocol\n"


def test_control_artifact_failure_does_not_erase_known_helper_failure(tmp_path, monkeypatch):
    m = supervision()
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    real = runner._write_new

    def unavailable(directory, name, raw):
        if name.startswith("controller-"):
            raise OSError("OWNED_ARTIFACT_FAILURE")
        return real(directory, name, raw)

    monkeypatch.setattr(runner, "_write_new", unavailable)
    result = m.supervise(SyntheticCase.SUPERVISOR_ABORT, root)
    assert result.errors[0] == "SUPERVISOR_EXIT_31"


def test_stream_wait_fault_and_cleanup_fault_both_survive(monkeypatch):
    m = supervision()
    child, fd = controlled("import time;time.sleep(.3)")
    try:
        monkeypatch.setattr(m, "_exit_code", lambda _: (_ for _ in ()).throw(OSError("FAULT")))
        real_kill = m._kill_owned

        def fail_after_kill(child, fd):
            real_kill(child, fd)
            raise OSError("CLEANUP_FAULT")

        monkeypatch.setattr(m, "_kill_owned", fail_after_kill)
        out, err, errors, code = m._collect(child, fd, 2)
        assert errors == ("STREAM_OR_WAIT_ERROR", "CLEANUP_SIGNAL_UNCONFIRMED")
        child.wait(timeout=2)
    finally:
        os.close(fd)


def test_nonregular_owned_artifact_cannot_block_controller(tmp_path):
    from tests.audit_compatibility_executor import runner

    root = runner._prepare(str(tmp_path))
    os.mkfifo(Path(root) / "fifo", 0o600)
    code = """
import sys
sys.path.insert(0,sys.argv[1])
from tests.audit_compatibility_executor.supervision import _read_owned
try: _read_owned(sys.argv[2],'fifo',10)
except ValueError: print('NONREGULAR_REJECTED')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-S",
            "-c",
            code,
            str(Path(__file__).resolve().parents[1]),
            root,
        ],
        capture_output=True,
        timeout=0.7,
        check=False,
    )
    assert result.returncode == 0 and result.stdout.strip() == b"NONREGULAR_REJECTED"


def test_private_bootstrap_never_adds_repository_import_roots(monkeypatch):
    import runpy

    m = supervision()
    before = list(sys.path)
    monkeypatch.setitem(sys.modules, "_h1_owned_synthetic", None)
    real = importlib.import_module

    def import_only(name):
        if name == "_h1_owned_synthetic.supervision":
            package = sys.modules["_h1_owned_synthetic"]
            assert package.__path__ == [str(Path(m.__file__).resolve().parent)]
            return SimpleNamespace(_helper_main=lambda: 17)
        return real(name)

    monkeypatch.setattr(importlib, "import_module", import_only)
    with pytest.raises(SystemExit) as result:
        runpy.run_path(m.__file__, run_name="__main__")
    assert result.value.code == 17 and sys.path == before


def test_limit_dispatch_uses_exact_per_process_values_without_mutating_worker(monkeypatch):
    m = supervision()
    limits = {}
    monkeypatch.setattr(m.resource, "setrlimit", lambda kind, pair: limits.update({kind: pair}))
    m._limits()
    r = m.resource
    assert limits == {
        r.RLIMIT_CPU: (3, 3),
        r.RLIMIT_AS: (268435456, 268435456),
        r.RLIMIT_FSIZE: (1048576, 1048576),
        r.RLIMIT_NOFILE: (64, 64),
        r.RLIMIT_CORE: (0, 0),
    }


def test_invalid_pipe_contract_rejects_without_signalling_unowned_process(monkeypatch):
    m = supervision()
    child = SimpleNamespace(stdout=None, stderr=None)
    monkeypatch.setattr(
        m, "_kill_owned", lambda *args: (_ for _ in ()).throw(ValueError("UNOWNED"))
    )
    with pytest.raises(AssertionError):
        m._collect(child, -1, 1)
