"""Fake VM boundary and real harmless host workers; never runs QEMU or the probe."""

import importlib
import importlib.util
import json
import os
import runpy
import signal
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_deny_fd_v2_harness_assets import synthetic_assets
from tests.test_deny_fd_v2_harness_capture import serial


def api():
    name = "tests.deny_fd_v2_harness.runner"
    assert importlib.util.find_spec(name) is not None, "closed-default fixed runner required"
    return importlib.import_module(name)


def fake_vm(monkeypatch, cases=("DFD01",)):
    r = api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    monkeypatch.setattr(r, "_require_linux", lambda: None)
    monkeypatch.setattr(r, "preflight", a.preflight)
    processes = []

    def launch(argv, **kwargs):
        assert kwargs["shell"] is False and kwargs["start_new_session"] is True
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["stdout"] == subprocess.PIPE and kwargs["stderr"] == subprocess.STDOUT
        assert kwargs["close_fds"] is True
        assert kwargs["env"]["LANG"] == "C" and kwargs["env"]["PATH"] == "/usr/bin:/bin"
        assert str(r.VM / "usr/bin/qemu-system-x86_64") in argv
        assert "-enable-kvm" not in argv and "-drive" not in argv
        token = object()
        processes.append(token)
        return token

    def collect(process, **kwargs):
        index = processes.index(process)
        return r.ProcessResult(serial(bundle, cases[index]), 0, "EXITED", True, None)

    monkeypatch.setattr(r.subprocess, "Popen", launch)
    monkeypatch.setattr(r, "_supervise", collect)
    return r, bundle, processes


def test_default_cli_and_import_never_spawn_or_write(tmp_path, monkeypatch, capsys):
    api()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("unexpected launch"))
    from tests.deny_fd_v2_harness.host_main import main

    assert main([]) == 2
    assert json.loads(capsys.readouterr().out)["capture"] == "NOT_STARTED"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("optin", (False, None, 0, 1, "yes"))
def test_nonboolean_or_missing_optin_does_not_prepare(tmp_path, monkeypatch, optin):
    r = api()
    monkeypatch.setattr(r, "preflight", lambda: pytest.fail("default must not read assets"))
    output = tmp_path / "new"
    with pytest.raises(ValueError):
        r.capture_cases(("DFD01",), output, run_prepared_guest=optin)
    assert not output.exists()


@pytest.mark.parametrize("cases", ((), ("DFD01", "DFD01"), ("OTHER",), ["DFD01"], (True,)))
def test_unlisted_or_duplicate_cases_never_prepare(tmp_path, monkeypatch, cases):
    r = api()
    monkeypatch.setattr(r, "preflight", lambda: pytest.fail("invalid case must not prepare"))
    with pytest.raises(ValueError):
        r.capture_cases(cases, tmp_path / "new", run_prepared_guest=True)
    assert not (tmp_path / "new").exists()


def test_only_fixed_tcg_argv_allowed(tmp_path):
    r = api()
    image = tmp_path / "image.cpio.gz"
    argv = r.qemu_arguments(image)
    assert argv[:4] == (
        str(r.VM / "usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"),
        "--library-path",
        str(r.VM / "usr/lib/x86_64-linux-gnu"),
        str(r.VM / "usr/bin/qemu-system-x86_64"),
    )
    for flag, value in (
        ("-accel", "tcg,thread=single"),
        ("-machine", "pc-q35-10.0"),
        ("-cpu", "qemu64"),
        ("-smp", "1"),
        ("-m", "768M"),
        ("-nic", "none"),
        ("-monitor", "none"),
        ("-initrd", str(image)),
    ):
        assert argv[argv.index(flag) + 1] == value
    assert {"-no-user-config", "-nodefaults", "-no-reboot"} <= set(argv)
    assert not {"-enable-kvm", "-drive", "-blockdev", "-fsdev", "-virtfs", "-device"} & set(argv)
    with pytest.raises(ValueError):
        r.qemu_arguments(Path("relative"))


def test_recorded_bytes_match_synthetic_vm_output_not_authority(tmp_path, monkeypatch):
    r, bundle, processes = fake_vm(monkeypatch, ("DFD01", "DFD02"))
    output = tmp_path / "evidence"
    records = r.capture_cases(("DFD01", "DFD02"), output, run_prepared_guest=True)
    assert len(records) == len(processes) == 2
    for record in records:
        case_dir = output / record.case
        assert (case_dir / "serial.bin").read_bytes() == serial(bundle, record.case)
        data = json.loads((case_dir / "record.json").read_bytes())
        assert data["record"]["raw_sha256"] == record.raw_sha256
        assert data["content_digest"] == record.content_digest
        assert data["record"]["status"] == "BLOCKED"
        assert all(v is False for v in data["record"]["permissions"].values())


def test_prelaunch_asset_drift_denies_spawn(tmp_path, monkeypatch):
    r, _, processes = fake_vm(monkeypatch)
    original = r.preflight
    calls = 0

    def drift():
        nonlocal calls
        calls += 1
        if calls > 1:
            raise ValueError("VM asset drift before launch")
        return original()

    monkeypatch.setattr(r, "preflight", drift)
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01",), tmp_path / "evidence", run_prepared_guest=True)
    assert processes == [] and error.value.raw == b"" and error.value.raw_complete is False


def test_image_modified_during_prelaunch_verification_denies_spawn(tmp_path, monkeypatch):
    r, _, processes = fake_vm(monkeypatch)
    output = tmp_path / "evidence"
    original = r.preflight
    calls = 0

    def drift():
        nonlocal calls
        calls += 1
        if calls > 1:
            image = output / "DFD01/initrd.cpio.gz"
            image.write_bytes(image.read_bytes() + b"unexpected bytes")
        return original()

    monkeypatch.setattr(r, "preflight", drift)
    with pytest.raises(r.CaptureFailure):
        r.capture_cases(("DFD01",), output, run_prepared_guest=True)
    assert processes == []


@pytest.mark.parametrize(
    "termination", ("NONZERO_EXIT", "TIMEOUT", "OUTPUT_LIMIT", "IO_ERROR", "CLEANUP_ERROR")
)
def test_failure_preserves_prefix_and_completed_cases(tmp_path, monkeypatch, termination):
    r, bundle, processes = fake_vm(monkeypatch, ("DFD01", "DFD02"))

    def collect(process, **kwargs):
        if processes.index(process) == 0:
            return r.ProcessResult(serial(bundle), 0, "EXITED", True, None)
        return r.ProcessResult(
            b"partial\n",
            2 if termination == "NONZERO_EXIT" else None,
            termination,
            termination == "NONZERO_EXIT",
            "synthetic boundary failure",
        )

    monkeypatch.setattr(r, "_supervise", collect)
    output = tmp_path / "evidence"
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01", "DFD02"), output, run_prepared_guest=True)
    assert error.value.raw == b"partial\n" and len(error.value.completed) == 1
    assert (output / "DFD01/serial.bin").read_bytes() == serial(bundle)
    assert (output / "DFD02/serial.bin").read_bytes() == b"partial\n"


def test_write_failure_is_not_success_and_retains_raw(tmp_path, monkeypatch):
    r, bundle, _ = fake_vm(monkeypatch)
    original = Path.open

    def failing_open(path, *args, **kwargs):
        if path.name == "record.json":
            raise OSError("synthetic full evidence volume")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01",), tmp_path / "evidence", run_prepared_guest=True)
    assert error.value.raw == serial(bundle) and error.value.completed == ()


def test_existing_or_checkout_output_is_not_overwritten(tmp_path, monkeypatch):
    r, _, processes = fake_vm(monkeypatch)
    marker = tmp_path / "keep"
    marker.write_bytes(b"user-owned")
    for output in (tmp_path, r.ROOT / "must-not-create"):
        with pytest.raises(ValueError):
            r.capture_cases(("DFD01",), output, run_prepared_guest=True)
    assert marker.read_bytes() == b"user-owned" and processes == []


def test_complete_invalid_wire_is_retained_not_accepted(tmp_path, monkeypatch):
    r, _, _ = fake_vm(monkeypatch)
    monkeypatch.setattr(
        r, "_supervise", lambda *a, **k: r.ProcessResult(b"bad wire\n", 0, "EXITED", True, None)
    )
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01",), tmp_path / "evidence", run_prepared_guest=True)
    assert error.value.raw == b"bad wire\n" and error.value.raw_complete is True
    assert error.value.completed == ()


def test_image_write_failure_does_not_create_a_fake_receipt(tmp_path, monkeypatch):
    r, _, processes = fake_vm(monkeypatch)
    monkeypatch.setattr(
        r, "_write", lambda *a: (_ for _ in ()).throw(OSError("image write failed"))
    )
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01",), tmp_path / "evidence", run_prepared_guest=True)
    assert error.value.raw == b"" and error.value.raw_complete is False and processes == []


@pytest.mark.parametrize("mode", ("recorded", "unavailable", "failure"))
def test_explicit_cli_still_returns_blocked_with_reasoned_outcome(
    tmp_path, monkeypatch, capsys, mode
):
    r, _, _ = fake_vm(monkeypatch)
    from tests.deny_fd_v2_harness.host_main import main

    if mode != "recorded":

        def fail(*args, **kwargs):
            if mode == "unavailable":
                raise ValueError("fixed asset unavailable")
            raise r.CaptureFailure("synthetic capture failure", b"prefix", False)

        monkeypatch.setattr(r, "capture_cases", fail)
    assert (
        main(
            ["--run-prepared-guest", "--case", "DFD01", "--destination", str(tmp_path / "evidence")]
        )
        == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "BLOCKED" and all(v is False for v in result["permissions"].values())
    assert (
        result["capture"]
        == {"recorded": "RECORDED_UNTRUSTED", "unavailable": "UNAVAILABLE", "failure": "FAILED"}[
            mode
        ]
    )


def test_module_entrypoint_defaults_to_not_started(monkeypatch, capsys):
    api()
    name = "tests.deny_fd_v2_harness.host_main"
    monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(sys, "argv", ["fixed-harness"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module(name, run_name="__main__")
    assert error.value.code == 2
    assert json.loads(capsys.readouterr().out)["capture"] == "NOT_STARTED"


def test_unsupported_platform_never_selects_a_fallback(monkeypatch):
    r = api()
    monkeypatch.setattr(r.sys, "platform", "unsupported")
    with pytest.raises(ValueError, match="no fallback"):
        r._require_linux()


def test_cleanup_never_signals_a_reaped_or_unowned_leader(monkeypatch):
    r = api()
    monkeypatch.setattr(
        r.os, "killpg", lambda *a: pytest.fail("unowned group must not be signalled")
    )
    code, error = r._cleanup(SimpleNamespace(returncode=0, pid=123), 0.1, False)
    assert code == 0 and "already reaped" in error


def test_vanished_group_does_not_trigger_an_alternate_target(monkeypatch):
    r = api()
    seen = []

    def gone(pid, sig):
        seen.append((pid, sig))
        raise ProcessLookupError("gone")

    monkeypatch.setattr(r.os, "killpg", gone)
    r._signal_group(SimpleNamespace(pid=123), signal.SIGTERM)
    assert seen == [(123, signal.SIGTERM)]


def test_missing_pipe_is_incomplete_and_cleanup_error_is_visible(monkeypatch):
    r = api()
    monkeypatch.setattr(r, "_cleanup", lambda *a: (None, "ownership unavailable"))
    result = r._supervise(SimpleNamespace(stdout=None), timeout=0.1, grace=0.1)
    assert result.termination == "CLEANUP_ERROR" and result.raw_complete is False
    assert result.raw == b"" and result.exit_code is None


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux process-group primitive only")
@pytest.mark.parametrize(
    "source,termination,expected_raw",
    (
        ("print('complete',flush=True)", "EXITED", b"complete\n"),
        ("import time;print('prefix',flush=True);time.sleep(20)", "TIMEOUT", b"prefix\n"),
        ("import os,time;os.close(1);os.close(2);time.sleep(20)", "TIMEOUT", b""),
        ("import os;os.write(1,b'x'*2000000)", "OUTPUT_LIMIT", b"x" * (1024 * 1024)),
    ),
)
def test_real_harmless_host_worker_is_bounded_and_reaped(source, termination, expected_raw):
    r = api()
    worker = subprocess.Popen(
        [sys.executable, "-I", "-c", source],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        result = r._supervise(worker, timeout=0.4, grace=0.1)
        assert result.termination == termination
        assert len(result.raw) <= 1024 * 1024
        assert worker.returncode is not None
        assert result.raw_complete is (termination == "EXITED")
        assert result.raw == expected_raw
    finally:
        if worker.poll() is None:
            os.killpg(worker.pid, signal.SIGKILL)
            worker.wait(timeout=2)


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux waitid/process-group semantics only")
def test_owned_group_member_outliving_leader_cannot_hold_pipe_forever():
    r = api()
    read_fd, write_fd = os.pipe()
    leader = subprocess.Popen(
        [sys.executable, "-I", "-c", "print('leader',flush=True)"],
        stdout=write_fd,
        stderr=subprocess.STDOUT,
        process_group=0,
    )
    holder = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time;time.sleep(20)"],
        stdout=write_fd,
        stderr=subprocess.STDOUT,
        process_group=leader.pid,
    )
    os.close(write_fd)
    leader.stdout = os.fdopen(read_fd, "rb")
    try:
        result = r._supervise(leader, timeout=0.4, grace=0.1)
        assert result.termination == "TIMEOUT" and result.raw_complete is False
        assert leader.returncode == 0
        assert holder.wait(timeout=2) < 0  # direct test child is explicitly reaped
    finally:
        if leader.poll() is None or holder.poll() is None:
            try:
                os.killpg(leader.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        leader.wait(timeout=2)
        holder.wait(timeout=2)


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux owned-process cleanup only")
def test_unexpected_collector_exception_still_reaps_owned_worker(monkeypatch):
    r = api()

    def broken_selector():
        raise RuntimeError("synthetic unexpected collector failure")

    monkeypatch.setattr(r.selectors, "DefaultSelector", broken_selector)
    worker = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time;time.sleep(20)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        result = r._supervise(worker, timeout=0.4, grace=0.1)
        assert result.termination == "IO_ERROR" and result.raw_complete is False
        assert "collector failure" in result.error
        assert worker.returncode is not None
    finally:
        if worker.poll() is None:
            os.killpg(worker.pid, signal.SIGKILL)
            worker.wait(timeout=2)


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux nonblocking pipe primitive only")
def test_transient_would_block_does_not_lose_output(monkeypatch):
    r = api()
    worker = subprocess.Popen(
        [sys.executable, "-I", "-c", "print('output',flush=True)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    original = os.read
    reads = 0

    def transient(fd, size):
        nonlocal reads
        reads += 1
        if reads == 1:
            raise BlockingIOError()
        return original(fd, size)

    monkeypatch.setattr(r.os, "read", transient)
    try:
        result = r._supervise(worker, timeout=0.4, grace=0.1)
        assert result.termination == "EXITED" and result.raw == b"output\n"
    finally:
        if worker.poll() is None:
            os.killpg(worker.pid, signal.SIGKILL)
            worker.wait(timeout=2)


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux pipe close/cleanup only")
def test_pipe_close_error_cannot_claim_complete_capture():
    r = api()
    worker = subprocess.Popen(
        [sys.executable, "-I", "-c", "print('output',flush=True)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    stream = worker.stdout

    class CloseFailure:
        def fileno(self):
            return stream.fileno()

        def close(self):
            stream.close()
            raise OSError("synthetic close failure")

    worker.stdout = CloseFailure()
    try:
        result = r._supervise(worker, timeout=0.4, grace=0.1)
        assert result.termination == "IO_ERROR" and result.raw_complete is False
        assert worker.returncode is not None
    finally:
        if worker.poll() is None:
            os.killpg(worker.pid, signal.SIGKILL)
            worker.wait(timeout=2)
