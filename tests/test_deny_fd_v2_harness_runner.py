"""Fake VM boundary and real harmless host workers; never runs QEMU or the probe."""

import importlib
import importlib.util
import json
import os
import runpy
import signal
import stat
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


def image_stat_cohorts(monkeypatch, tmp_path, platform):
    """Control only OS metadata origins; keep file creation/open/read/bytes real."""
    r = api()
    path = tmp_path / "identity-image"
    raw = b"fixed image"
    path.write_bytes(raw)
    lstat = Path.lstat
    open_file = Path.open
    fstat = os.fstat
    native = lstat(path)
    complete = {name: getattr(native, name) for name in dir(native) if name.startswith("st_")}
    complete.update(
        st_dev=11,
        st_ino=22,
        st_mode=stat.S_IFREG | 0o600,
        st_size=11,
        st_mtime_ns=500,
        st_ctime_ns=100,
        st_birthtime_ns=100,
        st_birthtime=0.0000001,
        st_file_attributes=32,
        st_reparse_tag=0,
    )
    snapshots = [SimpleNamespace(**complete) for _ in range(4)]
    if platform == "win32":
        snapshots[1].st_ctime_ns = snapshots[2].st_ctime_ns = 200
    path_reads = 0
    handle_reads = 0
    target_fd = None

    def read_path(candidate, *args, **kwargs):
        nonlocal path_reads
        if candidate != path:
            return lstat(candidate, *args, **kwargs)
        index = 0 if path_reads == 0 else 3
        path_reads += 1
        return snapshots[index]

    def opened(candidate, *args, **kwargs):
        nonlocal target_fd
        stream = open_file(candidate, *args, **kwargs)
        if candidate == path:
            target_fd = stream.fileno()
        return stream

    def read_handle(fd):
        nonlocal handle_reads
        if fd != target_fd:
            return fstat(fd)
        index = 1 if handle_reads == 0 else 2
        handle_reads += 1
        return snapshots[index]

    monkeypatch.setattr(r.sys, "platform", platform)
    monkeypatch.setattr(Path, "lstat", read_path)
    monkeypatch.setattr(Path, "open", opened)
    monkeypatch.setattr(r.os, "fstat", read_handle)
    return r, path, raw, snapshots


@pytest.mark.parametrize("birth,handle_change", ((100, 200), (0, 200), (100, 100)))
def test_windows_static_image_does_not_compare_different_clock_meanings(
    tmp_path, monkeypatch, birth, handle_change
):
    r, path, raw, samples = image_stat_cohorts(monkeypatch, tmp_path, "win32")
    for sample in samples:
        sample.st_birthtime_ns = birth
    samples[0].st_ctime_ns = samples[3].st_ctime_ns = birth
    samples[1].st_ctime_ns = samples[2].st_ctime_ns = handle_change
    r._image_bound(path, raw)


@pytest.mark.parametrize("platform", ("linux", "win32"))
@pytest.mark.parametrize(
    "field,value",
    (
        ("st_dev", 12),
        ("st_ino", 23),
        ("st_mode", stat.S_IFREG | 0o644),
        ("st_size", 12),
        ("st_mtime_ns", 501),
        ("binding_time", 101),
    ),
)
def test_image_cross_origin_binding_rejects_each_identity_change(
    tmp_path, monkeypatch, platform, field, value
):
    r, path, raw, samples = image_stat_cohorts(monkeypatch, tmp_path, platform)
    if field == "binding_time":
        field = "st_birthtime_ns" if platform == "win32" else "st_ctime_ns"
    setattr(samples[1], field, value)
    with pytest.raises(ValueError):
        r._image_bound(path, raw)


@pytest.mark.parametrize("platform", ("linux", "win32"))
@pytest.mark.parametrize("origin", ("handle", "path"))
@pytest.mark.parametrize(
    "field,value",
    (
        ("st_dev", 12),
        ("st_ino", 23),
        ("st_mode", stat.S_IFREG | 0o644),
        ("st_size", 12),
        ("st_mtime_ns", 501),
        ("st_ctime_ns", 201),
    ),
)
def test_image_raw_metadata_stays_strict_within_each_origin(
    tmp_path, monkeypatch, platform, origin, field, value
):
    r, path, raw, samples = image_stat_cohorts(monkeypatch, tmp_path, platform)
    setattr(samples[2 if origin == "handle" else 3], field, value)
    with pytest.raises(ValueError):
        r._image_bound(path, raw)


@pytest.mark.parametrize("origin", ("handle", "path", "both"))
def test_windows_birth_identity_cannot_change_after_open(tmp_path, monkeypatch, origin):
    r, path, raw, samples = image_stat_cohorts(monkeypatch, tmp_path, "win32")
    for index in (2, 3) if origin == "both" else (2 if origin == "handle" else 3,):
        samples[index].st_birthtime_ns = 101
    with pytest.raises(ValueError):
        r._image_bound(path, raw)


@pytest.mark.parametrize("birth", ("missing", None, False, 100.0, float("nan")))
def test_windows_unknown_birth_identity_is_not_an_invented_default(tmp_path, monkeypatch, birth):
    r, path, raw, samples = image_stat_cohorts(monkeypatch, tmp_path, "win32")
    for sample in samples:
        sample.st_ctime_ns = 100  # Remove the old unrelated ctime mismatch.
        if birth == "missing":
            delattr(sample, "st_birthtime_ns")
        else:
            sample.st_birthtime_ns = birth
    with pytest.raises(ValueError):
        r._image_bound(path, raw)


@pytest.mark.parametrize("platform", ("linux", "win32"))
@pytest.mark.parametrize("changed", (b"other image", b"fixed image!"))
def test_matching_metadata_cannot_substitute_changed_image_bytes(
    tmp_path, monkeypatch, platform, changed
):
    r, path, raw, _ = image_stat_cohorts(monkeypatch, tmp_path, platform)
    path.write_bytes(changed)
    with pytest.raises(ValueError):
        r._image_bound(path, raw)


@pytest.mark.parametrize("platform", ("linux", "win32"))
@pytest.mark.parametrize("kind", (stat.S_IFLNK, stat.S_IFDIR))
def test_nonregular_image_cannot_become_a_regular_receipt(tmp_path, monkeypatch, platform, kind):
    r, path, raw, samples = image_stat_cohorts(monkeypatch, tmp_path, platform)
    for sample in samples:
        sample.st_mode = kind | 0o600
    with pytest.raises(ValueError):
        r._image_bound(path, raw)


def test_real_prepared_file_retains_its_native_image_binding(tmp_path):
    r = api()
    path = tmp_path / "native-image"
    path.write_bytes(b"fixed image")
    r._image_bound(path, b"fixed image")


def test_missing_group_api_rejects_before_preparation(tmp_path, monkeypatch):
    r = api()
    monkeypatch.delattr(r.os, "killpg", raising=False)
    monkeypatch.setattr(r, "preflight", lambda: pytest.fail("unsupported host must not prepare"))
    output = tmp_path / "never-created"
    with pytest.raises(ValueError, match="no fallback"):
        r.capture_cases(("DFD01",), output, run_prepared_guest=True)
    assert not output.exists()


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
    assert error.value.current_record.termination == termination
    assert error.value.acquisition_error == "synthetic boundary failure"
    assert error.value.persistence_error is None
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


@pytest.mark.parametrize("filename", ("serial.bin", "record.json"))
@pytest.mark.parametrize("termination", ("CLEANUP_ERROR", "TIMEOUT", "EXITED"))
def test_later_persistence_failure_retains_current_record_and_both_errors(
    tmp_path, monkeypatch, filename, termination
):
    r, bundle, processes = fake_vm(monkeypatch, ("DFD01", "DFD02"))
    current_raw = serial(bundle, "DFD02") if termination == "EXITED" else b"current-prefix\n"
    acquisition_error = None if termination == "EXITED" else "owned group outcome unavailable"

    def collect(process, **kwargs):
        if processes.index(process) == 0:
            return r.ProcessResult(serial(bundle), 0, "EXITED", True, None)
        return r.ProcessResult(
            current_raw,
            0 if termination == "EXITED" else None,
            termination,
            termination == "EXITED",
            acquisition_error,
        )

    monkeypatch.setattr(r, "_supervise", collect)
    original = Path.open

    def failing_open(path, *args, **kwargs):
        if path.parent.name == "DFD02" and path.name == filename:
            raise OSError("synthetic evidence volume full")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    output = tmp_path / "evidence"
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01", "DFD02"), output, run_prepared_guest=True)
    failure = error.value
    assert [record.case for record in failure.completed] == ["DFD01"]
    assert failure.raw == current_raw and failure.raw_complete is (termination == "EXITED")
    assert failure.acquisition_error == acquisition_error
    assert failure.persistence_error == "synthetic evidence volume full"
    assert str(failure) == failure.persistence_error
    record = failure.current_record
    assert record is not None and record.case == "DFD02"
    assert record.raw == current_raw and record.termination == termination
    assert record.exit_code == (0 if termination == "EXITED" else None)
    assert record.host_end_ns >= record.host_start_ns > 0
    assert len(record.attempt_id) == 32 and record.source_revision == bundle.source_revision
    assert record.vm_cohort_digest == bundle.vm_cohort_digest
    assert record.image_sha256 and record.init_sha256 and record.argv
    assert record.status == "BLOCKED" and all(value is False for _, value in record.permissions)
    assert (output / "DFD01/serial.bin").read_bytes() == serial(bundle)
    assert not (output / "DFD02/record.json").exists()


@pytest.mark.parametrize("filename", ("serial.bin", "record.json"))
def test_cli_exposes_cleanup_record_even_when_persistence_fails(
    tmp_path, monkeypatch, capsys, filename
):
    r, _, _ = fake_vm(monkeypatch)
    from tests.deny_fd_v2_harness.host_main import main

    monkeypatch.setattr(
        r,
        "_supervise",
        lambda *a: r.ProcessResult(b"prefix", None, "CLEANUP_ERROR", False, "cleanup unconfirmed"),
    )
    original = Path.open

    def failing_open(path, *args, **kwargs):
        if path.name == filename:
            raise OSError("volume full")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    assert (
        main(
            ["--run-prepared-guest", "--case", "DFD01", "--destination", str(tmp_path / "evidence")]
        )
        == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result["capture"] == "FAILED" and result["status"] == "BLOCKED"
    assert result["acquisition_error"] == "cleanup unconfirmed"
    assert result["persistence_error"] == result["reason"] == "volume full"
    assert result["current_record"]["termination"] == "CLEANUP_ERROR"
    assert result["current_record"]["exit_code"] is None
    assert result["current_record"]["raw_size"] == 6
    assert len(result["current_record_digest"]) == 64
    assert all(value is False for value in result["permissions"].values())


def test_completed_exit_with_collection_error_is_not_a_complete_batch(tmp_path, monkeypatch):
    r, bundle, processes = fake_vm(monkeypatch, ("DFD01", "DFD02"))

    def collect(process, **kwargs):
        case = "DFD01" if processes.index(process) == 0 else "DFD02"
        error = None if case == "DFD01" else "selector teardown failure"
        return r.ProcessResult(serial(bundle, case), 0, "EXITED", True, error)

    monkeypatch.setattr(r, "_supervise", collect)
    output = tmp_path / "evidence"
    with pytest.raises(r.CaptureFailure) as error:
        r.capture_cases(("DFD01", "DFD02"), output, run_prepared_guest=True)
    failure = error.value
    assert [record.case for record in failure.completed] == ["DFD01"]
    assert failure.current_record.case == "DFD02"
    assert failure.raw == serial(bundle, "DFD02")
    assert failure.acquisition_error == "selector teardown failure"
    assert failure.persistence_error is None
    data = json.loads((output / "DFD02/record.json").read_bytes())
    assert data["failure_reason"] == failure.acquisition_error
    assert data["record"]["status"] == "BLOCKED"


def test_cli_cannot_erase_error_from_completed_exit(tmp_path, monkeypatch, capsys):
    r, bundle, _ = fake_vm(monkeypatch)
    from tests.deny_fd_v2_harness.host_main import main

    monkeypatch.setattr(
        r,
        "_supervise",
        lambda *a: r.ProcessResult(serial(bundle), 0, "EXITED", True, "selector teardown failure"),
    )
    assert (
        main(
            ["--run-prepared-guest", "--case", "DFD01", "--destination", str(tmp_path / "evidence")]
        )
        == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result["capture"] == "FAILED" and result["status"] == "BLOCKED"
    assert result["acquisition_error"] == "selector teardown failure"
    assert result["current_record"]["case"] == "DFD01"
    assert all(value is False for value in result["permissions"].values())


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux selector teardown ordering only")
def test_selector_teardown_failure_invalidates_normal_exit_and_reaps_worker(monkeypatch):
    r = api()
    a, _, _ = synthetic_assets(monkeypatch)
    raw = serial(a.preflight())
    selector_type = r.selectors.DefaultSelector

    class CloseFailure:
        def __enter__(self):
            self.selector = selector_type()
            return self.selector

        def __exit__(self, *args):
            self.selector.close()
            raise OSError("selector teardown failure")

    monkeypatch.setattr(r.selectors, "DefaultSelector", CloseFailure)
    worker = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys;sys.stdout.buffer.write({raw!r});sys.stdout.flush()",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        result = r._supervise(worker, timeout=1.0, grace=0.2)
        assert result.raw == raw and result.exit_code == 0
        assert result.termination == "IO_ERROR" and result.raw_complete is False
        assert result.error == "selector teardown failure"
        assert worker.returncode == 0
    finally:
        if worker.poll() is None:
            os.killpg(worker.pid, signal.SIGKILL)
            worker.wait(timeout=2)


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux first-interrupt process handling")
@pytest.mark.parametrize(
    "phase", ("collection", "pipe_close", "pipe_retry_error", "cleanup", "grace", "retry_failure")
)
def test_first_interrupt_preserves_batch_prefix_and_owned_cleanup(tmp_path, monkeypatch, phase):
    original_supervise = api()._supervise
    launcher = subprocess.Popen
    r, bundle, tokens = fake_vm(monkeypatch, ("DFD01", "DFD02"))
    workers = []
    streams = []
    fired = False

    def interrupt():
        nonlocal fired
        fired = True
        signal.raise_signal(signal.SIGINT)

    def collect(token, **kwargs):
        if tokens.index(token) == 0:
            return r.ProcessResult(serial(bundle), 0, "EXITED", True, None)
        worker = launcher(
            [
                sys.executable,
                "-I",
                "-c",
                "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                "print('current-prefix',flush=True);time.sleep(20)",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        workers.append(worker)
        stream = worker.stdout
        streams.append(stream)
        original_cleanup = r._cleanup
        original_sleep = r.time.sleep
        original_read = r.os.read
        selector_type = r.selectors.DefaultSelector
        observed = bytearray()

        def read(fd, size):
            raw = original_read(fd, size)
            if fd == stream.fileno():
                observed.extend(raw)
            return raw

        class Selector:
            def __init__(self):
                self.actual = selector_type()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.actual.close()

            def register(self, *args):
                return self.actual.register(*args)

            def unregister(self, *args):
                return self.actual.unregister(*args)

            def select(self, timeout):
                if phase == "collection" and observed and not fired:
                    interrupt()
                return self.actual.select(timeout)

        class Stream:
            def fileno(self):
                return stream.fileno()

            def close(self):
                if phase in ("pipe_close", "pipe_retry_error"):
                    if not fired:
                        interrupt()
                    if phase == "pipe_retry_error":
                        raise OSError("pipe close unavailable after interruption")
                stream.close()

        def cleanup(*args):
            if phase in ("cleanup", "retry_failure"):
                if not fired:
                    interrupt()
                if phase == "retry_failure":
                    raise OSError("owned cleanup unavailable after interruption")
            return original_cleanup(*args)

        def sleep(delay):
            if phase == "grace" and not fired:
                interrupt()
            return original_sleep(delay)

        worker.stdout = Stream()
        monkeypatch.setattr(r.os, "read", read)
        monkeypatch.setattr(r.selectors, "DefaultSelector", Selector)
        monkeypatch.setattr(r, "_cleanup", cleanup)
        monkeypatch.setattr(r.time, "sleep", sleep)
        return original_supervise(worker, timeout=0.3, grace=0.1)

    monkeypatch.setattr(r, "_supervise", collect)
    output = tmp_path / "evidence"
    try:
        with pytest.raises(r.CaptureFailure) as caught:
            r.capture_cases(("DFD01", "DFD02"), output, run_prepared_guest=True)
        failure = caught.value
        assert fired and failure.raw == b"current-prefix\n" and failure.raw_complete is False
        assert [record.case for record in failure.completed] == ["DFD01"]
        assert failure.current_record.raw == failure.raw
        assert "KeyboardInterrupt" in failure.acquisition_error
        assert (output / "DFD02/serial.bin").read_bytes() == failure.raw
        assert all(value is False for _, value in failure.current_record.permissions)
        if phase == "pipe_retry_error":
            assert "pipe close unavailable" in failure.acquisition_error
        else:
            assert streams[0].closed
        if phase == "retry_failure":
            assert failure.current_record.termination == "CLEANUP_ERROR"
            assert "owned cleanup unavailable" in failure.acquisition_error
        else:
            assert workers[0].returncode is not None
            assert failure.current_record.termination in ("TIMEOUT", "IO_ERROR")
    finally:
        for worker in workers:
            if worker.poll() is None:
                os.killpg(worker.pid, signal.SIGKILL)
                worker.wait(timeout=2)
        for stream in streams:
            stream.close()


@pytest.mark.parametrize("boundary", ("start", "end", "persist"))
@pytest.mark.parametrize("interruption", (KeyboardInterrupt, SystemExit))
def test_later_handoff_interruption_retains_explicit_available_context(
    tmp_path, monkeypatch, boundary, interruption
):
    r, bundle, tokens = fake_vm(monkeypatch, ("DFD01", "DFD02"))
    original_clock = r.time.monotonic_ns
    original_persist = r._persist
    calls = 0

    def clock():
        nonlocal calls
        calls += 1
        if calls == (3 if boundary == "start" else 4) and boundary != "persist":
            raise interruption("single handoff interruption")
        return original_clock()

    def persist(directory, record, error):
        if record.case == "DFD02":
            raise interruption("single handoff interruption")
        return original_persist(directory, record, error)

    monkeypatch.setattr(r.time, "monotonic_ns", clock)
    if boundary == "persist":
        monkeypatch.setattr(r, "_persist", persist)
    output = tmp_path / "evidence"
    with pytest.raises((r.CaptureFailure, KeyboardInterrupt, SystemExit)) as caught:
        r.capture_cases(("DFD01", "DFD02"), output, run_prepared_guest=True)
    assert isinstance(caught.value, r.CaptureFailure), "bare interruption loses evidence payload"
    failure = caught.value
    assert [record.case for record in failure.completed] == ["DFD01"]
    assert failure.raw == (b"" if boundary == "start" else serial(bundle, "DFD02"))
    assert failure.raw_complete is (boundary != "start")
    assert (output / "DFD01/serial.bin").read_bytes() == serial(bundle)
    if boundary == "persist":
        assert failure.current_record.case == "DFD02"
        assert failure.persistence_error == "single handoff interruption"
        assert failure.acquisition_error is None
    else:
        assert failure.current_record is None
        assert failure.persistence_error is None
        assert failure.acquisition_error == "single handoff interruption"
    assert len(tokens) == (1 if boundary == "start" else 2)


@pytest.mark.skipif(sys.platform != "linux", reason="new Linux double-slash alias regression")
@pytest.mark.parametrize("alias", (False, True))
@pytest.mark.parametrize("inside", ("primary", "worktree"))
def test_canonical_and_double_slash_checkout_destinations_are_rejected(
    tmp_path, monkeypatch, alias, inside
):
    r, _, tokens = fake_vm(monkeypatch)
    primary = tmp_path / "synthetic-checkout"
    worktree = primary / ".worktrees/current"
    worktree.mkdir(parents=True)
    monkeypatch.setattr(r, "ROOT", worktree)
    actual = (primary if inside == "primary" else worktree) / "must-not-create"
    destination = Path("/" + str(actual)) if alias else actual
    with pytest.raises(ValueError, match="outside checkout"):
        r.capture_cases(("DFD01",), destination, run_prepared_guest=True)
    assert not actual.exists() and tokens == []


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
    assert error.value.current_record is None
    assert error.value.acquisition_error == "image write failed"
    assert error.value.persistence_error is None


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
        r.os, "killpg", lambda *a: pytest.fail("unowned group must not be signalled"), raising=False
    )
    code, error = r._cleanup(SimpleNamespace(returncode=0, pid=123), 0.1, False)
    assert code == 0 and "already reaped" in error


def test_vanished_group_does_not_trigger_an_alternate_target(monkeypatch):
    r = api()
    seen = []

    def gone(pid, sig):
        seen.append((pid, sig))
        raise ProcessLookupError("gone")

    monkeypatch.setattr(r.os, "killpg", gone, raising=False)
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
