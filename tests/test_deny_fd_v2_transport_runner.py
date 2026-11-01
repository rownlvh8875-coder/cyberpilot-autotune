"""Dual transport tests use only harmless host writers or explicit VM doubles."""

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def api():
    name = "tests.deny_fd_v2_transport.runner"
    assert importlib.util.find_spec(name) is not None, "dual-stream runner required"
    return importlib.import_module(name)


def test_default_refuses_before_any_output(tmp_path):
    with pytest.raises(ValueError, match="opt-in"):
        api().capture_cases(("DFD01",), tmp_path / "never-created")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("cases", ((), ("DFD01", "DFD01"), ("wrong",), ["DFD01"]))
def test_bad_selection_never_prepares(cases, tmp_path):
    with pytest.raises(ValueError):
        api().capture_cases(cases, tmp_path / "never-created", run_prepared_guest=True)
    assert list(tmp_path.iterdir()) == []


def test_missing_linux_capabilities_rejects_before_preflight(tmp_path, monkeypatch):
    r = api()
    monkeypatch.setattr(r.sys, "platform", "unsupported")
    with pytest.raises(ValueError):
        r.capture_cases(("DFD01",), tmp_path / "never-created", run_prepared_guest=True)
    assert list(tmp_path.iterdir()) == []


def test_cli_default_is_blocked_without_io(capsys):
    assert importlib.util.find_spec("tests.deny_fd_v2_transport.host_main") is not None, (
        "closed CLI required"
    )
    cli = importlib.import_module("tests.deny_fd_v2_transport.host_main")
    assert cli.main([]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "BLOCKED" and result["capture"] == "NOT_STARTED"
    assert len(result["permissions"]) == 9
    assert all(value is False for value in result["permissions"].values())


@pytest.mark.skipif(sys.platform != "linux", reason="Linux owned-group host tests only")
@pytest.mark.parametrize(
    "script,expected",
    (
        ("os.write(fd,b'telemetry');os.write(1,b'kernel')", (b"telemetry", b"kernel", "EXITED")),
        ("os.close(fd);os.close(1);time.sleep(.08)", (b"", b"", "EXITED")),
        ("os.write(fd,b'prefix');time.sleep(3)", (b"prefix", b"", "TIMEOUT")),
        ("os.write(fd,b't');os.write(1,b'c');sys.exit(3)", (b"t", b"c", "NONZERO_EXIT")),
    ),
)
def test_real_dual_host_worker_separation_and_lifecycle(tmp_path, script, expected):
    r = api()
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen(
        [sys.executable, "-c", "import os,sys,time;fd=int(sys.argv[1]);" + script, str(write_fd)],
        pass_fds=(write_fd,),
        stdout=subprocess.PIPE,
        start_new_session=True,
    )
    os.close(write_fd)
    try:
        assert process.stdout is not None
        result = r.supervise(process, read_fd, process.stdout.fileno(), timeout=0.4, grace=0.2)
        assert (result.telemetry.raw, result.console.raw, result.termination) == expected
        assert process.returncode is not None
        assert all(value is False for _, value in result.permissions)
    finally:
        os.close(read_fd)
        if process.stdout is not None:
            process.stdout.close()
        if process.returncode is None:
            os.killpg(process.pid, 9)
            process.wait()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux nonblocking FIFO ownership only")
def test_fifo_anchors_do_not_hide_exit_or_lose_data(tmp_path):
    r = api()
    with r.PreparedFifos(tmp_path) as fifo:
        assert fifo.prefix == tmp_path / "telemetry"
        assert (tmp_path / "telemetry.in").is_fifo()
        assert (tmp_path / "telemetry.out").is_fifo()
        # No writer has connected; retained anchor makes an empty nonblocking
        # read EAGAIN, not final capture EOF.
        with pytest.raises(BlockingIOError):
            os.read(fifo.read_fd, 10)
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import os,sys;f=os.open(sys.argv[1],os.O_WRONLY);"
                "os.write(f,b'actual');os.close(f)",
                str(tmp_path / "telemetry.out"),
            ],
            stdout=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            result = r.supervise(
                process, fifo.read_fd, process.stdout.fileno(), timeout=1, grace=0.2
            )
            assert result.telemetry.raw == b"actual"
            assert result.termination == "EXITED"
        finally:
            process.stdout.close()
            if process.returncode is None:
                os.killpg(process.pid, 9)
                process.wait()
    assert fifo.read_fd is None


@pytest.mark.skipif(sys.platform != "linux", reason="Linux FIFO filesystem boundary only")
@pytest.mark.parametrize("kind", ("file", "link", "fifo"))
def test_existing_fifo_path_is_never_reused(tmp_path, kind):
    r = api()
    path = tmp_path / "telemetry.in"
    if kind == "file":
        path.write_bytes(b"old")
    elif kind == "link":
        path.symlink_to(tmp_path / "elsewhere")
    else:
        os.mkfifo(path, 0o600)
    with pytest.raises((OSError, ValueError)):
        with r.PreparedFifos(tmp_path):
            pytest.fail("existing endpoint was reused")


@pytest.mark.skipif(sys.platform != "linux", reason="Linux aggregate-limit host worker only")
def test_console_flood_is_capped_in_combined_evidence():
    r = api()
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys;f=int(sys.argv[1]);os.write(f,b'telemetry');"
            "\nwhile True: os.write(1,b'c'*65536)",
            str(write_fd),
        ],
        pass_fds=(write_fd,),
        stdout=subprocess.PIPE,
        start_new_session=True,
    )
    os.close(write_fd)
    try:
        result = r.supervise(process, read_fd, process.stdout.fileno(), timeout=2, grace=0.2)
        assert result.termination == "OUTPUT_LIMIT"
        assert result.telemetry.raw == b"telemetry"
        assert len(result.telemetry.raw) + len(result.console.raw) == 1048576
        assert not result.console.complete
    finally:
        os.close(read_fd)
        process.stdout.close()
        if process.returncode is None:
            os.killpg(process.pid, 9)
            process.wait()


def fake_vm(monkeypatch, cases=("DFD01",), close_error=False):
    from tests.deny_fd_v2_transport.assets import TransportAssets
    from tests.deny_fd_v2_transport.contracts import StreamEvidence, TransportProcessResult
    from tests.test_deny_fd_v2_harness_assets import synthetic_assets
    from tests.test_deny_fd_v2_harness_capture import serial

    r = api()
    old, _, _ = synthetic_assets(monkeypatch)
    assets = TransportAssets(old.preflight())
    monkeypatch.setattr(r, "preflight", lambda: assets)
    processes = []

    def launch(argv, **kwargs):
        assert kwargs["shell"] is False and kwargs["close_fds"] is True
        assert kwargs["start_new_session"] is True
        assert "-nic" in argv and "-enable-kvm" not in argv
        prefix = argv[argv.index("-chardev") + 1].split("path=", 1)[1]
        assert Path(prefix + ".in").is_fifo() and Path(prefix + ".out").is_fifo()
        handle = open(Path(prefix).parent / "synthetic-console", "w+b")

        class Console:
            close_calls = 0

            def fileno(self):
                return handle.fileno()

            def close(self):
                self.close_calls += 1
                if close_error == "interrupt" and self.close_calls == 1:
                    raise KeyboardInterrupt("console close interrupted")
                handle.close()
                if close_error is True:
                    raise OSError("late console close failed")

        process = SimpleNamespace(stdout=Console(), returncode=0, index=len(processes))
        processes.append(process)
        return process

    def collect(process, *fds):
        return TransportProcessResult(
            StreamEvidence(serial(assets.base, cases[process.index]), True, None),
            StreamEvidence(b"console noise\n", True, None),
            0,
            "EXITED",
            None,
        )

    monkeypatch.setattr(r.subprocess, "Popen", launch)
    monkeypatch.setattr(r, "supervise", collect)
    return r, processes


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM with real Linux FIFO preparation")
def test_batch_retains_separate_untrusted_stream_files(tmp_path, monkeypatch):
    r, processes = fake_vm(monkeypatch, ("DFD01", "DFD02"))
    destination = tmp_path / "capture"
    records = r.capture_cases(("DFD01", "DFD02"), destination, run_prepared_guest=True)
    assert len(records) == len(processes) == 2
    for record in records:
        directory = destination / record.case
        assert (directory / "telemetry.bin").read_bytes() == record.result.telemetry.raw
        assert (directory / "console.bin").read_bytes() == b"console noise\n"
        assert (
            json.loads((directory / "record.json").read_text())["record"]["schema"]
            == "deny-fd-v2-dual-acquisition-v1"
        )


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM with real Linux FIFO preparation")
def test_storage_failure_retains_both_streams_and_current_record(tmp_path, monkeypatch):
    r, _ = fake_vm(monkeypatch)

    def fail(*args):
        raise OSError("storage full")

    monkeypatch.setattr(r, "_persist", fail)
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
    error = caught.value
    assert error.result.telemetry.raw.startswith(b"boot noise")
    assert error.result.console.raw == b"console noise\n"
    assert error.current_record is not None
    assert "storage full" in error.persistence_error


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM with real Linux FIFO preparation")
def test_late_console_close_invalidates_recorded_collection(tmp_path, monkeypatch):
    r, _ = fake_vm(monkeypatch, close_error=True)
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
    assert "late console close failed" in caught.value.result.error
    assert not caught.value.result.console.complete
    assert caught.value.current_record is not None


@pytest.mark.skipif(sys.platform != "linux", reason="Linux dual read failure host worker")
def test_read_error_retains_both_prefixes_and_identifies_stream(monkeypatch):
    r = api()
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys,time;os.write(int(sys.argv[1]),b'telemetry');"
            "os.write(1,b'console');time.sleep(.2)",
            str(write_fd),
        ],
        pass_fds=(write_fd,),
        stdout=subprocess.PIPE,
        start_new_session=True,
    )
    os.close(write_fd)
    actual_read = os.read
    consumed = False

    def read(fd, count):
        nonlocal consumed
        if fd == read_fd and consumed:
            raise OSError("telemetry read failed")
        result = actual_read(fd, count)
        if fd == read_fd and result:
            consumed = True
        return result

    monkeypatch.setattr(r.os, "read", read)
    try:
        result = r.supervise(process, read_fd, process.stdout.fileno(), timeout=1, grace=0.2)
        assert result.telemetry.raw == b"telemetry"
        assert result.console.raw == b"console"
        assert result.telemetry.error == "telemetry read failed"
        assert not result.telemetry.complete
    finally:
        os.close(read_fd)
        process.stdout.close()
        if process.returncode is None:
            os.killpg(process.pid, 9)
            process.wait()


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM with real Linux FIFO preparation")
def test_first_interrupted_console_close_gets_one_idempotent_retry(tmp_path, monkeypatch):
    r, processes = fake_vm(monkeypatch, close_error="interrupt")
    try:
        with pytest.raises(r.TransportCaptureFailure) as caught:
            r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
        assert processes[0].stdout.close_calls == 2
        assert caught.value.result.telemetry.raw.startswith(b"boot noise")
        assert not caught.value.result.console.complete
    finally:
        if processes and processes[0].stdout.close_calls < 2:
            processes[0].stdout.close()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux spawned-worker interruption cleanup")
def test_spawn_handoff_cleanup_interrupt_escalates_owned_worker_once(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    r, _ = fake_vm(monkeypatch)
    workers = []

    def launch(*args, **kwargs):
        process = real_popen(
            [sys.executable, "-c", "import time;time.sleep(5)"],
            stdout=subprocess.PIPE,
            start_new_session=True,
        )
        workers.append(process)
        return process

    monkeypatch.setattr(r.subprocess, "Popen", launch)

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt("handoff interrupted")

    monkeypatch.setattr(r, "supervise", interrupted)
    cleanup = r.lifecycle._cleanup
    calls = []

    def interrupt_cleanup(process, grace, normal):
        calls.append(normal)
        if len(calls) == 1:
            raise KeyboardInterrupt("cleanup interrupted")
        return cleanup(process, grace, normal)

    monkeypatch.setattr(r.lifecycle, "_cleanup", interrupt_cleanup)
    try:
        with pytest.raises(r.TransportCaptureFailure):
            r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
        assert workers[0].returncode is not None
        assert calls == [False, True]
    finally:
        for process in workers:
            if process.returncode is None:
                os.killpg(process.pid, 9)
                process.wait()
