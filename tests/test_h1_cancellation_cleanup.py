"""Owned-helper lifetime regressions; every process/FD edge is a controlled fake."""

import ast
import importlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def controller(monkeypatch):
    m = importlib.import_module("tests.audit_compatibility_executor.supervision")
    actual_collect, actual_read = m._collect, m._read_owned
    calls = []
    state = SimpleNamespace(
        point=None,
        primary=None,
        fired=False,
        fault=None,
        fault_fired=False,
        known_errors=(),
        signalled=False,
        wait_calls=0,
        fd_close_calls=0,
        fault_type=KeyboardInterrupt,
        fault_error=None,
    )

    def event(name):
        calls.append(name)
        if state.point == name and not state.fired:
            state.fired = True
            raise state.primary
        if state.fault == name and not state.fault_fired:
            state.fault_fired = True
            raise state.fault_error or state.fault_type("SECONDARY_CLEANUP_ONLY")

    state.event, state.actual_collect, state.actual_read = event, actual_collect, actual_read

    class Stream:
        def __init__(self, name):
            self.name = name
            self.closed = False

        def write(self, raw):
            assert self.name == "stdin" and not self.closed
            assert json.loads(raw)["schema"] == "h1-helper-request-v1"
            event("write")
            return len(raw)

        def close(self):
            if not self.closed:
                event(self.name + ".close")
                self.closed = True

    class Helper:
        pid = 4242
        returncode = None

        def __init__(self):
            self.stdin, self.stdout, self.stderr = (
                Stream(n) for n in ("stdin", "stdout", "stderr")
            )

        def wait(self, timeout):
            assert 0 <= timeout <= 2
            state.wait_calls += 1
            event("wait")
            if not self.stdin.closed and not state.signalled:
                raise subprocess.TimeoutExpired("FAKE_EOF_WAIT", timeout)
            self.returncode = 0
            return 0

        def kill(self):
            calls.append("NUMERIC_PID_FORBIDDEN")
            pytest.fail("numeric PID fallback")

        terminate = kill

    helper = Helper()

    def spawn(args, **kwargs):
        assert kwargs["start_new_session"] and kwargs["close_fds"]
        assert kwargs["stdin"] is kwargs["stdout"] is kwargs["stderr"] is subprocess.PIPE
        event("spawn")
        return helper

    def pidfd(pid):
        assert pid == helper.pid
        event("pidfd")
        return 91

    def send(fd, sig):
        assert (fd, sig) == (91, 9)
        event("signal")
        state.signalled = True

    def close(fd):
        assert fd in (91, 92)
        if fd == 91:
            state.fd_close_calls += 1
            assert state.fd_close_calls == 1, "released/uncertain pidfd retried"
            event("fd.close")
        else:
            event("artifact.close")

    def forbidden(*args):
        calls.append("NUMERIC_PID_FORBIDDEN")
        pytest.fail("numeric PID fallback")

    def collect(child, fd, wall, *, group):
        assert child is helper and fd == 91 and wall == 9 and group is False
        event("collect")
        helper.stdout.close()
        helper.stderr.close()
        raw = json.dumps(
            {
                "schema": "h1-supervisor-v1",
                "case": "FD_CLOSED",
                "errors": state.known_errors,
                "unavailable": [],
                "cleanup": "CONFIRMED",
            }
        ).encode()
        return raw, b"", (), 0

    def open_directory(root):
        assert root == "/owned/fake"
        event("artifact")
        return 92

    monkeypatch.setattr(
        m, "os", SimpleNamespace(pidfd_open=pidfd, close=close, kill=forbidden, killpg=forbidden)
    )
    monkeypatch.setattr(m, "signal", SimpleNamespace(SIGKILL=9, pidfd_send_signal=send))
    monkeypatch.setattr(
        m,
        "subprocess",
        SimpleNamespace(
            Popen=spawn, PIPE=subprocess.PIPE, TimeoutExpired=subprocess.TimeoutExpired
        ),
    )
    monkeypatch.setattr(
        m,
        "runner",
        SimpleNamespace(
            _PYTHON="/fake/not-executed",
            _source_hashes=lambda: {},
            _child_environment=lambda: {},
            _open_directory=open_directory,
            _write_new=lambda *args: None,
            _preserve_cleanup=getattr(
                importlib.import_module("tests.audit_compatibility_executor.runner"),
                "_preserve_cleanup",
                None,
            ),
        ),
    )
    monkeypatch.setattr(m, "_verify_root", lambda *args: None)
    monkeypatch.setattr(m, "_collect", collect)
    monkeypatch.setattr(
        m,
        "_read_owned",
        lambda root, name, limit: {"stdout.bin": b"OUT", "stderr.bin": b"ERR"}[name],
    )
    return m, state, helper, calls


@pytest.mark.parametrize("point", ["pidfd", "write", "stdin.close", "collect", "wait", "artifact"])
@pytest.mark.parametrize("kind", [KeyboardInterrupt, SystemExit, RuntimeError])
def test_cancellation_closes_owned_streams_and_reaps_before_pidfd_release(controller, point, kind):
    # A narrow Exception tuple or a close-only finally must fail this contract.
    m, state, helper, calls = controller
    state.point, state.primary = point, kind("PRIMARY_ONLY")
    with pytest.raises(kind) as caught:
        m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert caught.value is state.primary
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert state.wait_calls >= 1
    assert state.signalled is (point != "pidfd")
    assert state.fd_close_calls == (0 if point == "pidfd" else 1)
    if point != "pidfd":
        assert calls.index("signal") < calls.index("fd.close")
        assert max(i for i, name in enumerate(calls) if name == "wait") < calls.index("fd.close")
    assert "NUMERIC_PID_FORBIDDEN" not in calls
    assert any("CLEANUP_UNCONFIRMED" in note for note in caught.value.__notes__)


@pytest.mark.parametrize(
    "fault", ["stdin.close", "stdout.close", "stderr.close", "signal", "wait", "fd.close"]
)
@pytest.mark.parametrize("fault_type", [KeyboardInterrupt, SystemExit, OSError])
def test_secondary_cleanup_cancellation_never_masks_original_or_skips_later_cleanup(
    controller, fault, fault_type
):
    m, state, helper, calls = controller
    state.point, state.primary, state.fault = "write", KeyboardInterrupt("PRIMARY_ONLY"), fault
    state.fault_type = fault_type
    with pytest.raises(KeyboardInterrupt) as caught:
        m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert caught.value is state.primary
    assert state.fault_fired
    assert state.wait_calls >= 1 and state.fd_close_calls == 1
    assert "stdout.close" in calls and "stderr.close" in calls
    assert "NUMERIC_PID_FORBIDDEN" not in calls
    assert any("CLEANUP_UNCONFIRMED" in note for note in caught.value.__notes__)


def test_normal_pidfd_close_failure_invalidates_clean_result_without_retry(controller):
    m, state, helper, calls = controller
    state.fault, state.fault_type = "fd.close", OSError
    result = m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert result.outcome == "REJECTED" and result.cleanup == "UNCONFIRMED"
    assert result.errors == ("CONTROLLER_HANDLE_CLEANUP_UNCONFIRMED",)
    assert (result.stdout, result.stderr) == (b"OUT", b"ERR")
    assert state.fd_close_calls == state.wait_calls == 1 and not state.signalled
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert "NUMERIC_PID_FORBIDDEN" not in calls


@pytest.mark.parametrize("kind", [KeyboardInterrupt, SystemExit, RuntimeError])
@pytest.mark.parametrize("secondary", [OSError, SystemExit])
def test_artifact_write_cancellation_survives_directory_close(
    controller, monkeypatch, kind, secondary
):
    m, state, helper, calls = controller
    primary = kind("NESTED_PRIMARY")

    def write(*args):
        raise primary

    monkeypatch.setattr(m.runner, "_write_new", write)
    state.fault, state.fault_type = "artifact.close", secondary
    with pytest.raises(kind) as caught:
        m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert caught.value is primary and state.fault_fired
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert state.wait_calls >= 2 and state.signalled and state.fd_close_calls == 1
    assert calls.index("signal") < calls.index("fd.close")


@pytest.mark.parametrize("kind", [KeyboardInterrupt, SystemExit, RuntimeError])
@pytest.mark.parametrize("secondary", [OSError, SystemExit])
@pytest.mark.parametrize("fault", ["selector.close", "stdout.close", "stderr.close", "signal"])
def test_actual_collector_preserves_cancellation_through_nested_cleanup(
    controller, monkeypatch, kind, secondary, fault
):
    m, state, helper, calls = controller
    primary = kind("COLLECTION_PRIMARY")

    class Selector:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()
            return False

        def register(self, *args):
            pass

        def close(self):
            state.event("selector.close")

    def exit_code(fd):
        assert fd == 91
        raise primary

    helper.stdout.fileno, helper.stderr.fileno = lambda: 93, lambda: 94
    monkeypatch.setattr(m.os, "set_blocking", lambda *args: None, raising=False)
    monkeypatch.setattr(m, "selectors", SimpleNamespace(DefaultSelector=Selector, EVENT_READ=1))
    monkeypatch.setattr(m, "_exit_code", exit_code)
    monkeypatch.setattr(m, "_collect", state.actual_collect)
    state.fault, state.fault_type = fault, secondary
    with pytest.raises(kind) as caught:
        m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert caught.value is primary and state.fault_fired
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert state.wait_calls >= 1 and state.fd_close_calls == 1
    assert calls.index("signal") < calls.index("fd.close")
    assert "NUMERIC_PID_FORBIDDEN" not in calls


@pytest.mark.parametrize("kind", [KeyboardInterrupt, SystemExit, RuntimeError])
@pytest.mark.parametrize("secondary", [OSError, SystemExit])
@pytest.mark.parametrize("boundary", ["write", "read", "open_directory", "directory_transfer"])
def test_real_artifact_helpers_preserve_primary_across_nested_closes(
    monkeypatch, kind, secondary, boundary
):
    r = importlib.import_module("tests.audit_compatibility_executor.runner")
    m = importlib.import_module("tests.audit_compatibility_executor.supervision")
    primary, calls = kind("ARTIFACT_PRIMARY"), []

    def fail(*args):
        raise primary

    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

        read = write = fail

        def close(self):
            calls.append("stream.close")
            raise secondary("SECONDARY_CLOSE")

    def close(fd):
        calls.append(fd)
        if boundary == "open_directory" and fd == 95:
            return
        if boundary == "directory_transfer" and fd == 95:
            raise primary
        raise secondary("SECONDARY_FD_CLOSE")

    opened = iter((95, 97))
    fake_os = SimpleNamespace(
        O_RDONLY=0,
        O_WRONLY=1,
        O_CREAT=2,
        O_EXCL=4,
        O_NOFOLLOW=8,
        O_CLOEXEC=16,
        O_NONBLOCK=32,
        O_DIRECTORY=64,
        open=lambda *args, **kwargs: next(opened),
        close=close,
        fdopen=lambda *args, **kwargs: Stream(),
        getuid=lambda: 1000,
        fstat=lambda fd: SimpleNamespace(st_mode=0o100600, st_uid=1000, st_nlink=1, st_size=0),
    )
    if boundary in ("open_directory", "directory_transfer"):
        fake_os.fstat = fail
    else:
        monkeypatch.setattr(r, "_open_directory", lambda root: 96)

    def target():
        if boundary in ("open_directory", "directory_transfer"):
            return r._open_directory("/owned")
        if boundary == "write":
            return r._write_new(96, "fake.bin", b"x")
        return m._read_owned("/fake", "fake.bin", 10)

    monkeypatch.setattr(r, "os", fake_os)
    monkeypatch.setattr(m, "os", fake_os)
    with pytest.raises(kind) as caught:
        target()
    assert caught.value is primary
    if boundary in ("open_directory", "directory_transfer"):
        assert calls == [95, 97]
    else:
        assert calls == (["stream.close", 95] if boundary == "write" else ["stream.close", 95, 96])


def test_late_pidfd_close_cancellation_propagates_without_using_released_descriptor(controller):
    m, state, helper, calls = controller
    late = KeyboardInterrupt("LATE_CANCELLATION")
    state.fault, state.fault_error = "fd.close", late
    with pytest.raises(KeyboardInterrupt) as caught:
        m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert caught.value is late and "CLEANUP_UNCONFIRMED" in late.__notes__
    assert state.fd_close_calls == state.wait_calls == 1 and not state.signalled
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert "NUMERIC_PID_FORBIDDEN" not in calls


def test_known_failure_is_preserved_when_final_stream_close_is_unconfirmed(controller):
    m, state, helper, calls = controller
    state.point, state.primary = "write", OSError("PRIMARY_KNOWN_FAILURE")
    state.fault, state.fault_type = "stdout.close", OSError
    result = m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert result.errors[0] == "CONTROLLER_OR_PROTOCOL_ERROR"
    assert "CONTROLLER_HANDLE_CLEANUP_UNCONFIRMED" in result.errors
    assert result.cleanup == "UNCONFIRMED" and result.outcome == "REJECTED"
    assert helper.stdin.closed and helper.stderr.closed and state.fd_close_calls == 1
    assert "NUMERIC_PID_FORBIDDEN" not in calls


def test_unavailable_pidfd_sends_no_request_and_uses_eof_not_numeric_signalling(controller):
    m, state, helper, calls = controller
    state.point, state.primary = "pidfd", OSError("UNAVAILABLE")
    result = m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert result.outcome == "UNAVAILABLE" and result.cleanup == "UNCONFIRMED"
    assert result.unavailable == ("PIDFD_UNAVAILABLE",)
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert state.wait_calls == 1 and not state.signalled and state.fd_close_calls == 0
    assert "write" not in calls and "NUMERIC_PID_FORBIDDEN" not in calls


def test_normal_protocol_output_and_false_permissions_survive_resource_release(controller):
    m, state, helper, calls = controller
    result = m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert result.outcome == "SYNTHETIC_OBSERVATION_COMPLETE"
    assert (result.stdout, result.stderr, result.cleanup) == (b"OUT", b"ERR", "CONFIRMED")
    assert len(result.permissions) == 9 and all(v is False for _, v in result.permissions)
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert state.wait_calls == state.fd_close_calls == 1
    assert not state.signalled and "NUMERIC_PID_FORBIDDEN" not in calls


def test_known_controller_error_remains_primary_and_cleanup_unconfirmed(controller):
    m, state, helper, calls = controller
    state.point, state.primary = "write", OSError("KNOWN_WRITE_FAILURE")
    result = m.supervise(m.SyntheticCase.FD_CLOSED, "/owned/fake")
    assert result.errors[0] == "CONTROLLER_OR_PROTOCOL_ERROR"
    assert result.cleanup == "UNCONFIRMED" and result.outcome == "REJECTED"
    assert helper.stdin.closed and helper.stdout.closed and helper.stderr.closed
    assert state.signalled and state.wait_calls >= 1 and state.fd_close_calls == 1
    assert "NUMERIC_PID_FORBIDDEN" not in calls


ROOT = Path(__file__).resolve().parents[1]
BASE = "209edaa83b398e6204af1097fda4b651807cc815"
ADDITIONS = {
    "docs/superpowers/specs/2026-11-03-h1-cancellation-cleanup-design.md",
    "docs/superpowers/plans/2026-11-03-h1-cancellation-cleanup.md",
    "tests/test_h1_cancellation_cleanup.py",
    "docs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json",
}
MODIFICATIONS = {
    "tests/audit_compatibility_executor/runner.py",
    "tests/audit_compatibility_executor/supervision.py",
    "tests/test_audit_compatibility_history_architecture.py",
    "tests/test_h1_outcome_consistency.py",
    "tests/test_actions_preflight_registration.py",
}


def source_git(*args):
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"},
    )


def scope():
    module = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    check = getattr(module, "_h1_cancellation_changes", None)
    assert callable(check), "separate cancellation successor missing"
    return module, check


def test_successor_accepts_only_the_literal_cancellation_repair_inventory():
    # Removing current scope checks or granting a prefix must fail these consumers.
    module, check = scope()
    rows = source_git("diff", "--no-renames", "--name-status", BASE).decode().splitlines()
    rows += [
        "A\t" + p
        for p in source_git("ls-files", "--others", "--exclude-standard").decode().splitlines()
    ]
    assert sorted(rows) == sorted(
        ["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS]
    )
    check(rows)
    module.test_all_earlier_files_and_guard_bytes_are_preserved()
    path = "docs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json"
    value = json.loads((ROOT / path).read_text())
    old = json.loads(
        source_git(
            "show",
            BASE + ":docs/evidence/audit_compatibility/h1-outcome-consistency-v1/registration.json",
        )
    )
    assert value["base"] == BASE and value["status"] == "BLOCKED"
    assert set(value["new_paths"]) == ADDITIONS and set(value["modified_paths"]) == MODIFICATIONS
    assert value["permissions"] == old["permissions"] and not value["manifest_is_authority"]
    assert not value["historical_execution"] and not value["native_cancellation_cleanup_qualified"]
    assert set(old["retained_blockers"]) <= set(value["retained_blockers"])


@pytest.mark.parametrize(
    "rows",
    [
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\ttests/audit_compatibility_capture/git_reader.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\ttools/actions_runner_preflight.py"],
        ["A\tdocs/UNKNOWN.md"],
        ["D\ttests/audit_compatibility_executor/supervision.py"],
        ["R100\ta.py\ttests/audit_compatibility_executor/supervision.py"],
        ["M\ttests/audit_compatibility_executor/supervision.py"] * 2,
        ["A\t../tests/test_h1_cancellation_cleanup.py"],
        ["A\ttests//test_h1_cancellation_cleanup.py"],
        ["M tests/audit_compatibility_executor/supervision.py"],
    ],
)
def test_successor_rejects_unknown_status_alias_and_duplicate_rows(rows):
    _, check = scope()
    with pytest.raises(AssertionError):
        check(rows)


@pytest.mark.parametrize("tamper", ["frozen", "current", "untracked"])
def test_actual_consumer_rejects_old_and_current_scope_tampering(monkeypatch, tamper):
    module, _ = scope()
    real = module.subprocess.check_output

    def changed(args, **kwargs):
        if tamper == "frozen" and args[1:] == [
            "diff",
            "--no-renames",
            "--name-status",
            "a8b2bf1e6f27a4157212298928a50c8e970babf5",
            BASE,
        ]:
            return b"M\tsrc/cyberpilot_autotune/__init__.py\n"
        if tamper == "current" and args[1:] == ["diff", "--no-renames", "--name-status", BASE]:
            return b"M\tsrc/cyberpilot_autotune/__init__.py\n"
        raw = real(args, **kwargs)
        if tamper == "untracked" and args[1:] == ["ls-files", "--others", "--exclude-standard"]:
            raw += b"UNREGISTERED.py\n"
        return raw

    monkeypatch.setattr(module.subprocess, "check_output", changed)
    with pytest.raises(AssertionError):
        module.test_all_earlier_files_and_guard_bytes_are_preserved()


def test_only_owned_lifetime_and_explicit_scope_consumers_change():
    allowed = {
        "tests/audit_compatibility_executor/supervision.py": {
            "supervise",
            "_collect",
            "_read_owned",
        },
        "tests/audit_compatibility_executor/runner.py": {"_open_directory", "_write_new"},
        "tests/test_audit_compatibility_history_architecture.py": {
            "test_all_earlier_files_and_guard_bytes_are_preserved"
        },
        "tests/test_h1_outcome_consistency.py": {
            "test_scope_is_exact_and_registration_does_not_authorize_it"
        },
        "tests/test_actions_preflight_registration.py": {
            "test_real_consumer_checks_all_legacy_ranges_and_literal_checkpoint"
        },
    }
    for path, exceptions in allowed.items():
        old = ast.parse(source_git("show", BASE + ":" + path))
        new = ast.parse((ROOT / path).read_text())
        current = {n.name: ast.dump(n) for n in new.body if isinstance(n, ast.FunctionDef)}
        for node in old.body:
            if isinstance(node, ast.FunctionDef) and node.name not in exceptions:
                assert current[node.name] == ast.dump(node), (path, node.name)
