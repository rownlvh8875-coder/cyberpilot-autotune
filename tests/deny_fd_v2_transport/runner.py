"""Fixed default-closed dual FIFO collection; never a general VM executor."""

import math
import os
import secrets
import selectors
import stat
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from types import TracebackType

from tests.deny_fd_v2_harness import runner as lifecycle
from tests.deny_fd_v2_harness.assets import VM
from tests.deny_fd_v2_harness.contracts import canonical, case_label, digest, need

from .assets import CONFIG_SHA256, PROFILE, TransportAssets, preflight
from .capture import TransportCaptureFailure, validate_capture
from .contracts import LIMIT, StreamEvidence, TransportAcquisitionRecord, TransportProcessResult
from .image import build_image, init_bytes


def _require_linux() -> None:
    need(
        sys.platform == "linux" and hasattr(os, "mkfifo") and hasattr(os, "O_NOFOLLOW"),
        "fixed Linux FIFO capabilities required",
    )
    lifecycle._require_linux()


def _message(error: BaseException) -> str:
    return lifecycle._message(error)


def _join(*values: str | None) -> str | None:
    return "; ".join(value for value in values if value)[:4000] or None


class PreparedFifos:
    """Exclusively owned endpoints and close-on-exec host anchors, no payload."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.prefix = directory / "telemetry"
        self.read_fd: int | None = None
        self._owned: list[int] = []

    def _open(self, path: Path, flags: int) -> int:
        before = path.lstat()
        need(
            stat.S_ISFIFO(before.st_mode)
            and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == 0o600,
            "fixed owned FIFO required",
        )
        fd = os.open(path, flags | os.O_NONBLOCK | os.O_NOFOLLOW)
        self._owned.append(fd)
        opened = os.fstat(fd)
        after = path.lstat()
        need(
            (before.st_dev, before.st_ino, before.st_mode)
            == (opened.st_dev, opened.st_ino, opened.st_mode)
            == (after.st_dev, after.st_ino, after.st_mode),
            "FIFO binding changed",
        )
        need(not os.get_inheritable(fd), "host FIFO descriptor cannot be inherited")
        return fd

    def __enter__(self) -> "PreparedFifos":
        _require_linux()
        need(
            self.directory.is_absolute() and stat.S_ISDIR(self.directory.lstat().st_mode),
            "owned FIFO directory required",
        )
        try:
            incoming = self.directory / "telemetry.in"
            outgoing = self.directory / "telemetry.out"
            os.mkfifo(incoming, 0o600)
            os.mkfifo(outgoing, 0o600)
            self._open(incoming, os.O_RDWR)
            self.read_fd = self._open(outgoing, os.O_RDONLY)
            self._open(outgoing, os.O_WRONLY)
            return self
        except BaseException as error:
            try:
                self.close()
            except BaseException as cleanup:
                raise ValueError(_join(_message(error), _message(cleanup))) from error
            raise

    def close(self) -> None:
        errors = []
        self.read_fd = None
        while self._owned:
            # Pop before closing: an interrupted close never blindly selects
            # a possibly reused descriptor number on retry.
            fd = self._owned.pop()
            try:
                os.close(fd)
            except BaseException as error:
                errors.append(_message(error))
        if errors:
            raise ValueError(_join(*errors))

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            self.close()
        except BaseException as cleanup:
            raise ValueError(
                _join(_message(error) if error else None, _message(cleanup))
            ) from cleanup


def qemu_arguments(image: Path, prefix: Path) -> tuple[str, ...]:
    need(
        isinstance(prefix, Path)
        and prefix.is_absolute()
        and ".." not in prefix.parts
        and not any(c in str(prefix) for c in (",", "\0", "\n", "\r")),
        "fixed safe FIFO prefix required",
    )
    return lifecycle.qemu_arguments(image) + (
        "-chardev",
        f"pipe,id=telemetry,path={prefix}",
        "-device",
        "isa-serial,index=1,chardev=telemetry",
    )


def supervise(
    process: subprocess.Popen[bytes],
    telemetry_fd: int,
    console_fd: int,
    *,
    timeout: float = 180.0,
    grace: float = 2.0,
) -> TransportProcessResult:
    """Caller owns stream FDs. Retain both prefixes even through cleanup errors."""
    raw = {"telemetry": bytearray(), "console": bytearray()}
    stream_errors: dict[str, str | None] = {"telemetry": None, "console": None}
    normal = False
    termination = "IO_ERROR"
    error_text = None
    code = process.returncode
    cleanup_error = None
    try:
        need(
            type(timeout) in (int, float) and math.isfinite(timeout) and 0 < timeout <= 180,
            "bounded timeout required",
        )
        need(
            type(grace) in (int, float) and math.isfinite(grace) and 0 < grace <= 2,
            "bounded grace required",
        )
        need(
            type(telemetry_fd) is int and type(console_fd) is int and telemetry_fd != console_fd,
            "separate stream descriptors required",
        )
        descriptors = {telemetry_fd: "telemetry", console_fd: "console"}
        for fd in descriptors:
            os.set_blocking(fd, False)
        deadline = time.monotonic() + timeout
        drained: set[str] = set()
        with selectors.DefaultSelector() as selector:
            for fd in descriptors:
                selector.register(fd, selectors.EVENT_READ)
            while True:
                exited = lifecycle._exited(process)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    termination = "TIMEOUT"
                    break
                ready = selector.select(min(0.05, remaining))
                # After the owned leader exits, an anchored FIFO returns EAGAIN
                # rather than EOF. Probe BOTH streams to finish a bounded drain.
                active = list(descriptors) if exited else [key.fd for key, _ in ready]
                progressed = False
                for fd in active:
                    name = descriptors[fd]
                    available = LIMIT - sum(len(value) for value in raw.values())
                    try:
                        chunk = os.read(fd, min(65536, available + 1))
                    except BlockingIOError:
                        if exited:
                            drained.add(name)
                        continue
                    except (Exception, KeyboardInterrupt, SystemExit) as error:
                        stream_errors[name] = _message(error)
                        raise
                    if not chunk:
                        if exited:
                            drained.add(name)
                        continue
                    progressed = True
                    drained.discard(name)
                    raw[name].extend(chunk[:available])
                    if len(chunk) > available:
                        termination = "OUTPUT_LIMIT"
                        break
                if termination == "OUTPUT_LIMIT":
                    break
                if exited and len(drained) == 2:
                    normal = True
                    break
                if not progressed:
                    time.sleep(min(0.01, max(0, deadline - time.monotonic())))
    except (Exception, KeyboardInterrupt, SystemExit) as error:
        normal = False
        error_text = _message(error)
    finally:
        try:
            code, cleanup_error = lifecycle._cleanup(process, min(max(grace, 0.001), 2), normal)
        except (Exception, KeyboardInterrupt, SystemExit) as error:
            normal = False
            error_text = _join(error_text, _message(error))
            try:
                code, cleanup_error = lifecycle._cleanup(process, 2, True)
            except (Exception, KeyboardInterrupt, SystemExit) as retry_error:
                code, cleanup_error = process.returncode, _message(retry_error)
    if cleanup_error is not None:
        normal = False
        termination = "CLEANUP_ERROR"
        error_text = _join(error_text, cleanup_error)
    elif normal:
        termination = "EXITED" if code == 0 else "NONZERO_EXIT"
    return TransportProcessResult(
        StreamEvidence(bytes(raw["telemetry"]), normal, stream_errors["telemetry"]),
        StreamEvidence(bytes(raw["console"]), normal, stream_errors["console"]),
        code,
        termination,
        error_text,
    )


def _empty() -> TransportProcessResult:
    return TransportProcessResult(
        StreamEvidence(b"", False, None), StreamEvidence(b"", False, None), None, "IO_ERROR", None
    )


def _record(
    case: str,
    assets: TransportAssets,
    image: bytes,
    argv: tuple[str, ...],
    result: TransportProcessResult,
    start: int,
    end: int,
) -> TransportAcquisitionRecord:
    base = assets.base
    return TransportAcquisitionRecord(
        case,
        secrets.token_hex(16),
        base.source_revision,
        base.source_manifest_digest,
        digest(base.probe),
        base.vm_cohort_digest,
        base.kernel_sha256,
        CONFIG_SHA256,
        digest(canonical(PROFILE)),
        digest(init_bytes(case)),
        digest(image),
        argv,
        result,
        start,
        end,
    )


def _persist(directory: Path, record: TransportAcquisitionRecord, failure: str | None) -> None:
    lifecycle._write(directory / "telemetry.bin", record.result.telemetry.raw)
    lifecycle._write(directory / "console.bin", record.result.console.raw)
    lifecycle._write(
        directory / "record.json",
        canonical(
            {
                "record": record.metadata(),
                "content_digest": record.content_digest,
                "failure_reason": failure,
            }
        )
        + b"\n",
    )


def capture_cases(
    cases: tuple[str, ...], destination: Path, *, run_prepared_guest: bool = False
) -> tuple[TransportAcquisitionRecord, ...]:
    need(run_prepared_guest is True, "explicit guest opt-in required; default is closed")
    need(
        type(cases) is tuple
        and bool(cases)
        and all(type(c) is str for c in cases)
        and len(set(cases)) == len(cases),
        "unique fixed cases required",
    )
    for case in cases:
        case_label(case)
    _require_linux()
    need(
        isinstance(destination, Path)
        and not any(c in str(destination) for c in (",", "\0", "\r", "\n")),
        "safe destination required",
    )
    assets = preflight()
    lifecycle._new_destination(destination)
    completed: list[TransportAcquisitionRecord] = []
    for case in cases:
        directory = destination / case
        result = _empty()
        image = b""
        argv: tuple[str, ...] = ()
        start = None
        process = None
        collected = False
        stage = "PREPARE"
        failure = None
        try:
            start = time.monotonic_ns()
            directory.mkdir(mode=0o700)
            image = build_image(assets, case)
            image_path = directory / "initrd.cpio.gz"
            lifecycle._write(image_path, image)
            with PreparedFifos(directory) as fifo:
                argv = qemu_arguments(image_path, fifo.prefix)
                need(preflight() == assets, "prepared assets changed")
                lifecycle._image_bound(image_path, image)
                stage = "LAUNCH"
                process = subprocess.Popen(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    start_new_session=True,
                    close_fds=True,
                    env={
                        "QEMU_MODULE_DIR": str(VM / "usr/lib/x86_64-linux-gnu/qemu"),
                        "PATH": "/usr/bin:/bin",
                        "LANG": "C",
                        "LC_ALL": "C",
                    },
                )
                try:
                    need(
                        process.stdout is not None and fifo.read_fd is not None,
                        "owned streams unavailable",
                    )
                    assert process.stdout is not None and fifo.read_fd is not None
                    result = supervise(process, fifo.read_fd, process.stdout.fileno())
                    collected = True
                    stage = "CLOSE"
                finally:
                    if process.stdout is not None:
                        try:
                            process.stdout.close()
                        except (Exception, KeyboardInterrupt, SystemExit) as error:
                            message = _message(error)
                            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                                try:
                                    process.stdout.close()
                                except (Exception, KeyboardInterrupt, SystemExit) as retry_error:
                                    message = _join(message, _message(retry_error)) or message
                            result = replace(
                                result,
                                console=replace(
                                    result.console,
                                    complete=False,
                                    error=_join(result.console.error, message),
                                ),
                                error=_join(result.error, message),
                            )
                            raise
            stage = "VALIDATE"
            validate_capture(result, case, assets)
        except (Exception, KeyboardInterrupt, SystemExit) as error:
            failure = _message(error)
            if collected and stage == "CLOSE":
                result = replace(
                    result,
                    telemetry=replace(result.telemetry, complete=False),
                    console=replace(result.console, complete=False),
                    error=_join(result.error, failure),
                )
        finally:
            if process is not None and process.returncode is None and not collected:
                # Covers interruption after spawn but before the supervisor.
                try:
                    code, cleanup_error = lifecycle._cleanup(process, 2, False)
                except (Exception, KeyboardInterrupt, SystemExit) as error:
                    cleanup_error = _message(error)
                    try:
                        code, returned_cleanup_error = lifecycle._cleanup(process, 2, True)
                        cleanup_error = _join(cleanup_error, returned_cleanup_error)
                    except (Exception, KeyboardInterrupt, SystemExit) as retry_error:
                        code = process.returncode
                        cleanup_error = _join(cleanup_error, _message(retry_error))
                result = replace(
                    result,
                    exit_code=code,
                    error=_join(result.error, cleanup_error),
                    termination="CLEANUP_ERROR" if cleanup_error else "IO_ERROR",
                )
                failure = _join(failure, cleanup_error)
        record = None
        try:
            end = time.monotonic_ns()
            if start is None or not image or not argv:
                raise ValueError(failure or "preparation incomplete")
            record = _record(case, assets, image, argv, result, start, end)
            _persist(directory, record, failure)
        except (Exception, KeyboardInterrupt, SystemExit) as error:
            raise TransportCaptureFailure(
                _message(error),
                result,
                tuple(completed),
                current_record=record,
                acquisition_error=failure,
                persistence_error=_message(error) if record is not None else None,
            ) from error
        if failure is not None:
            raise TransportCaptureFailure(
                failure, result, tuple(completed), current_record=record, acquisition_error=failure
            )
        completed.append(record)
    return tuple(completed)
