"""Dual transport tests use only harmless host writers or explicit VM doubles."""

import base64
import importlib
import importlib.util
import json
import os
import runpy
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
                if close_error == "repeated_interrupt" and self.close_calls == 1:
                    raise KeyboardInterrupt("console close interrupted")
                handle.close()
                if close_error == "repeated_interrupt":
                    raise OSError("retry close failed")
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
@pytest.mark.parametrize("mode", ("normal", "retry_error"))
def test_spawn_handoff_cleanup_interrupt_escalates_owned_worker_once(tmp_path, monkeypatch, mode):
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
        outcome = cleanup(process, grace, normal)
        if mode == "retry_error":
            raise OSError("cleanup retry failed")
        return outcome

    monkeypatch.setattr(r.lifecycle, "_cleanup", interrupt_cleanup)
    try:
        with pytest.raises(r.TransportCaptureFailure) as caught:
            r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
        assert workers[0].returncode is not None
        assert calls == [False, True]
        if mode == "retry_error":
            assert "cleanup retry failed" in caught.value.result.error
    finally:
        for process in workers:
            if process.returncode is None:
                os.killpg(process.pid, 9)
                process.wait()


@pytest.mark.parametrize("mode", ("success", "failure", "unavailable"))
def test_cli_reports_untrusted_or_explicit_failure_only(tmp_path, monkeypatch, capsys, mode):
    from tests.test_deny_fd_v2_transport_capture import record

    r = api()
    cli = importlib.import_module("tests.deny_fd_v2_transport.host_main")
    current = record(monkeypatch)

    def collect(cases, destination, *, run_prepared_guest):
        assert cases == ("DFD01", "DFD02", "DFD03", "DFD04", "DFD05", "DFD06")
        assert destination == tmp_path / "never-created" and run_prepared_guest is True
        if mode == "failure":
            raise r.TransportCaptureFailure(
                "failed",
                current.result,
                (current,),
                current_record=current,
                acquisition_error="bad source",
                persistence_error="disk",
            )
        if mode == "unavailable":
            raise ValueError("missing assets")
        return (current,)

    monkeypatch.setattr(r, "capture_cases", collect)
    assert (
        cli.main(
            [
                "--run-prepared-guest",
                "--all-cases",
                "--destination",
                str(tmp_path / "never-created"),
            ]
        )
        == 2
    )
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "BLOCKED"
    assert all(value is False for value in output["permissions"].values())
    assert (
        output["capture"]
        == {"success": "RECORDED_UNTRUSTED", "failure": "FAILED", "unavailable": "UNAVAILABLE"}[
            mode
        ]
    )
    if mode == "failure":
        assert output["completed"] == 1
        assert output["acquisition_error"] == "bad source" and output["persistence_error"] == "disk"
        assert output["current_record"]["schema"] == "deny-fd-v2-dual-acquisition-v1"
    assert not (tmp_path / "never-created").exists()


def test_real_cli_entry_defaults_blocked():
    result = subprocess.run(
        [sys.executable, "-m", "tests.deny_fd_v2_transport.host_main"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["capture"] == "NOT_STARTED"


@pytest.mark.skipif(sys.platform != "linux", reason="Linux FIFO ownership/error provenance")
@pytest.mark.parametrize("during_setup", (False, True))
def test_fifo_close_error_keeps_original_context_and_closes_owned_fds(
    tmp_path, monkeypatch, during_setup
):
    r = api()
    actual_close = os.close
    actual_open = r.PreparedFifos._open
    owned = []

    def opened(self, path, flags):
        if during_setup and owned:
            raise ValueError("setup failed")
        fd = actual_open(self, path, flags)
        owned.append(fd)
        return fd

    monkeypatch.setattr(r.PreparedFifos, "_open", opened)
    raised = False

    def close(fd):
        nonlocal raised
        actual_close(fd)
        if fd in owned and not raised:
            raised = True
            raise OSError("close failed")

    monkeypatch.setattr(r.os, "close", close)
    with pytest.raises(ValueError, match="close failed") as caught:
        with r.PreparedFifos(tmp_path):
            raise ValueError("body failed")
    assert ("setup failed" if during_setup else "body failed") in str(caught.value)
    for fd in owned:
        with pytest.raises(OSError):
            os.fstat(fd)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux owned cleanup failure host worker")
@pytest.mark.parametrize("mode", ("returned_error", "first_interrupt", "retry_error"))
def test_supervisor_cleanup_uncertainty_never_reports_complete(monkeypatch, mode):
    r = api()
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys;os.write(int(sys.argv[1]),b't');os.write(1,b'c')",
            str(write_fd),
        ],
        pass_fds=(write_fd,),
        stdout=subprocess.PIPE,
        start_new_session=True,
    )
    os.close(write_fd)
    cleanup = r.lifecycle._cleanup
    calls = 0

    def fail(process, grace, normal):
        nonlocal calls
        calls += 1
        if mode != "returned_error" and calls == 1:
            raise KeyboardInterrupt("cleanup interrupted")
        code, error = cleanup(process, grace, normal)
        if mode == "returned_error":
            return code, "cleanup uncertain"
        if mode == "retry_error":
            raise OSError("retry uncertain")
        return code, error

    monkeypatch.setattr(r.lifecycle, "_cleanup", fail)
    try:
        result = r.supervise(process, read_fd, process.stdout.fileno(), timeout=1, grace=0.2)
        assert result.telemetry.raw == b"t" and result.console.raw == b"c"
        assert not result.telemetry.complete and not result.console.complete
        assert result.error is not None
        assert process.returncode is not None
    finally:
        os.close(read_fd)
        process.stdout.close()
        if process.returncode is None:
            os.killpg(process.pid, 9)
            process.wait()


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM preparation failure")
def test_preparation_failure_has_no_fabricated_record(tmp_path, monkeypatch):
    r, _ = fake_vm(monkeypatch)

    def fail(*args):
        raise OSError("image unavailable")

    monkeypatch.setattr(r, "build_image", fail)
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
    assert caught.value.current_record is None
    assert caught.value.result.exit_code is None
    assert caught.value.result.telemetry.raw == caught.value.result.console.raw == b""


def test_inprocess_cli_entry_has_no_implicit_guest_flag(monkeypatch, capsys):
    monkeypatch.delitem(sys.modules, "tests.deny_fd_v2_transport.host_main", raising=False)
    monkeypatch.setattr(sys, "argv", ["host_main"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("tests.deny_fd_v2_transport.host_main", run_name="__main__")
    assert caught.value.code == 2
    assert json.loads(capsys.readouterr().out)["capture"] == "NOT_STARTED"


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM close retry failure")
def test_second_console_close_error_is_retained_without_more_retries(tmp_path, monkeypatch):
    r, processes = fake_vm(monkeypatch, close_error="repeated_interrupt")
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
    assert processes[0].stdout.close_calls == 2
    assert "retry close failed" in caught.value.result.error
    assert not caught.value.result.console.complete


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM missing pipe refusal")
def test_missing_spawned_stdout_is_not_a_successful_empty_capture(tmp_path, monkeypatch):
    r, _ = fake_vm(monkeypatch)
    monkeypatch.setattr(
        r.subprocess, "Popen", lambda *args, **kwargs: SimpleNamespace(stdout=None, returncode=0)
    )
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01",), tmp_path / "capture", run_prepared_guest=True)
    assert not caught.value.result.console.complete
    assert "owned streams unavailable" in caught.value.acquisition_error


@pytest.mark.skipif(sys.platform != "linux", reason="Linux spurious readiness host worker")
def test_spurious_ready_read_eagain_does_not_drop_telemetry(monkeypatch):
    r = api()
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys,time;os.write(int(sys.argv[1]),b't');time.sleep(.2);os.write(1,b'c')",
            str(write_fd),
        ],
        pass_fds=(write_fd,),
        stdout=subprocess.PIPE,
        start_new_session=True,
    )
    os.close(write_fd)
    actual_read = os.read
    spurious = False

    def read(fd, count):
        nonlocal spurious
        if fd == read_fd and not spurious:
            spurious = True
            raise BlockingIOError()
        return actual_read(fd, count)

    monkeypatch.setattr(r.os, "read", read)
    try:
        result = r.supervise(process, read_fd, process.stdout.fileno(), timeout=1, grace=0.2)
        assert result.telemetry.raw == b"t" and result.console.raw == b"c"
        assert result.termination == "EXITED" and spurious
    finally:
        os.close(read_fd)
        process.stdout.close()
        if process.returncode is None:
            os.killpg(process.pid, 9)
            process.wait()


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM end-clock evidence recovery")
@pytest.mark.parametrize("through_cli", (False, True))
def test_end_clock_failure_preserves_raw_files_without_fabricated_record(
    tmp_path, monkeypatch, capsys, through_cli
):
    from tests.test_deny_fd_v2_harness_capture import serial

    r, _ = fake_vm(monkeypatch)
    expected = serial(r.preflight().base)
    calls = 0

    def clock():
        nonlocal calls
        calls += 1
        if calls == 1:
            return 10
        raise OSError("end clock unavailable")

    monkeypatch.setattr(r.time, "monotonic_ns", clock)
    destination = tmp_path / "capture"
    if through_cli:
        cli = importlib.import_module("tests.deny_fd_v2_transport.host_main")
        assert (
            cli.main(["--run-prepared-guest", "--case", "DFD01", "--destination", str(destination)])
            == 2
        )
        output = json.loads(capsys.readouterr().out)
        assert output["capture"] == "FAILED" and output["current_record"] is None
    else:
        with pytest.raises(r.TransportCaptureFailure) as caught:
            r.capture_cases(("DFD01",), destination, run_prepared_guest=True)
        assert caught.value.current_record is None
        assert "end clock unavailable" in caught.value.acquisition_error
        assert caught.value.persistence_error is None
    directory = destination / "DFD01"
    assert (directory / "telemetry.bin").exists(), "clock failure discarded telemetry"
    assert (directory / "telemetry.bin").read_bytes() == expected
    assert (directory / "console.bin").read_bytes() == b"console noise\n"
    assert json.loads((directory / "record.json").read_text())["record"] is None


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM independent write recovery")
@pytest.mark.parametrize("failed_name", ("telemetry.bin", "console.bin", "record.json", "all"))
@pytest.mark.parametrize("through_cli", (False, True))
def test_each_write_is_attempted_and_cli_preserves_lossless_raw(
    tmp_path, monkeypatch, capsys, failed_name, through_cli
):
    from tests.test_deny_fd_v2_harness_capture import serial

    r, _ = fake_vm(monkeypatch)
    expected = {"telemetry": serial(r.preflight().base), "console": b"console noise\n"}
    actual_write = r.lifecycle._write
    attempted = []

    def write(path, raw):
        attempted.append(path.name)
        if path.name != "initrd.cpio.gz" and (failed_name == "all" or path.name == failed_name):
            raise OSError("injected storage error")
        return actual_write(path, raw)

    monkeypatch.setattr(r.lifecycle, "_write", write)
    destination = tmp_path / "capture"
    if through_cli:
        cli = importlib.import_module("tests.deny_fd_v2_transport.host_main")
        assert (
            cli.main(["--run-prepared-guest", "--case", "DFD01", "--destination", str(destination)])
            == 2
        )
        output = json.loads(capsys.readouterr().out)
        assert output["capture"] == "FAILED"
        assert isinstance(output.get("raw_evidence"), dict), "CLI discarded unwritten bytes"
        assert output["raw_evidence"]["encoding"] == "base64"
        for role, raw in expected.items():
            assert base64.b64decode(output["raw_evidence"][role], validate=True) == raw
        assert output["acquisition_error"] is None
        assert "injected storage error" in output["persistence_error"]
        assert all(value is False for value in output["permissions"].values())
    else:
        with pytest.raises(r.TransportCaptureFailure) as caught:
            r.capture_cases(("DFD01",), destination, run_prepared_guest=True)
        assert caught.value.result.telemetry.raw == expected["telemetry"]
        assert caught.value.result.console.raw == expected["console"]
        assert caught.value.current_record is not None
        assert caught.value.acquisition_error is None
        assert "injected storage error" in caught.value.persistence_error
    assert attempted == ["initrd.cpio.gz", "telemetry.bin", "console.bin", "record.json"]
    for role, raw in expected.items():
        name = role + ".bin"
        if failed_name not in (name, "all"):
            assert (destination / "DFD01" / name).read_bytes() == raw


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM record construction failure")
def test_record_validation_failure_keeps_raw_and_null_record(tmp_path, monkeypatch):
    from tests.test_deny_fd_v2_harness_capture import serial

    r, _ = fake_vm(monkeypatch)
    expected = serial(r.preflight().base)

    def invalid(*args):
        raise ValueError("record context unavailable")

    monkeypatch.setattr(r, "_record", invalid)
    destination = tmp_path / "capture"
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01",), destination, run_prepared_guest=True)
    assert caught.value.current_record is None
    assert (destination / "DFD01/telemetry.bin").read_bytes() == expected
    assert (destination / "DFD01/console.bin").read_bytes() == b"console noise\n"
    assert json.loads((destination / "DFD01/record.json").read_text())["record"] is None


@pytest.mark.skipif(sys.platform != "linux", reason="synthetic VM multi-case clock failure")
def test_second_case_clock_failure_preserves_first_record_and_both_current_streams(
    tmp_path, monkeypatch
):
    r, _ = fake_vm(monkeypatch, ("DFD01", "DFD02"))
    calls = 0

    def clock():
        nonlocal calls
        calls += 1
        if calls == 4:
            raise OSError("second case end clock unavailable")
        return calls

    monkeypatch.setattr(r.time, "monotonic_ns", clock)
    destination = tmp_path / "capture"
    with pytest.raises(r.TransportCaptureFailure) as caught:
        r.capture_cases(("DFD01", "DFD02"), destination, run_prepared_guest=True)
    assert len(caught.value.completed) == 1
    first = caught.value.completed[0]
    assert (destination / "DFD01/telemetry.bin").read_bytes() == first.result.telemetry.raw
    assert (destination / "DFD02/telemetry.bin").read_bytes() == caught.value.result.telemetry.raw
    assert (destination / "DFD02/console.bin").read_bytes() == caught.value.result.console.raw
    assert caught.value.current_record is None


def test_cli_lossless_fallback_remains_bounded_by_raw_aggregate_limit(
    tmp_path, monkeypatch, capsys
):
    from tests.deny_fd_v2_transport.contracts import StreamEvidence, TransportProcessResult

    r = api()
    cli = importlib.import_module("tests.deny_fd_v2_transport.host_main")
    raw = b"t" * 1048576
    result = TransportProcessResult(
        StreamEvidence(raw, False, None), StreamEvidence(b"", False, None), None, "IO_ERROR", None
    )

    def failed(*args, **kwargs):
        raise r.TransportCaptureFailure("all files unavailable", result, persistence_error="disk")

    monkeypatch.setattr(r, "capture_cases", failed)
    assert (
        cli.main(
            [
                "--run-prepared-guest",
                "--case",
                "DFD01",
                "--destination",
                str(tmp_path / "never-created"),
            ]
        )
        == 2
    )
    output = json.loads(capsys.readouterr().out)
    fallback = output["raw_evidence"]
    assert len(fallback["telemetry"]) == 1398104
    assert base64.b64decode(fallback["telemetry"], validate=True) == raw
    assert base64.b64decode(fallback["console"], validate=True) == b""
    assert output["current_record"] is None and output["capture"] == "FAILED"
