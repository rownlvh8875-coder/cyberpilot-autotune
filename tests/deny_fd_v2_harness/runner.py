"""Future explicit fixed VM diagnostic. Default-denied, no host probe execution."""

import os
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .assets import ROOT, VM, preflight
from .capture import CaptureFailure, validate_capture
from .contracts import AcquisitionRecord, AssetBundle, canonical, case_label, digest, need
from .image import build_image, init_bytes

LIMIT = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ProcessResult:
    raw: bytes
    exit_code: int | None
    termination: str
    raw_complete: bool
    error: str | None


def _message(error: BaseException) -> str:
    return (str(error).replace("\0", "") or type(error).__name__)[:4000]


def _require_linux() -> None:
    need(
        sys.platform == "linux"
        and all(
            hasattr(os, name)
            for name in (
                "waitid",
                "WNOWAIT",
                "WEXITED",
                "WNOHANG",
                "P_PID",
                "killpg",
            )
        ),
        "fixed Linux waitid/process-group host required; no fallback",
    )


def qemu_arguments(image_path: Path) -> tuple[str, ...]:
    need(
        isinstance(image_path, Path)
        and image_path.is_absolute()
        and ".." not in image_path.parts
        and "\0" not in str(image_path),
        "owned absolute image required",
    )
    libraries = VM / "usr/lib/x86_64-linux-gnu"
    return (
        str(libraries / "ld-linux-x86-64.so.2"),
        "--library-path",
        str(libraries),
        str(VM / "usr/bin/qemu-system-x86_64"),
        "-no-user-config",
        "-nodefaults",
        "-machine",
        "pc-q35-10.0",
        "-accel",
        "tcg,thread=single",
        "-cpu",
        "qemu64",
        "-smp",
        "1",
        "-m",
        "768M",
        "-L",
        str(VM / "usr/share/qemu"),
        "-bios",
        str(VM / "usr/share/seabios/bios-256k.bin"),
        "-display",
        "none",
        "-monitor",
        "none",
        "-serial",
        "stdio",
        "-nic",
        "none",
        "-audiodev",
        "none,id=audio0",
        "-kernel",
        str(VM / "boot/vmlinuz-6.12.113+deb13-cloud-amd64"),
        "-initrd",
        str(image_path),
        "-append",
        "console=ttyS0 rdinit=/init panic=-1 oops=panic "
        "lsm=landlock,lockdown,yama,integrity,apparmor,bpf",
        "-no-reboot",
    )


def _exited(process: subprocess.Popen[bytes]) -> bool:
    # Do not poll/reap here: retain the leader PID until the last group signal.
    need(process.returncode is None, "leader already reaped; group identity unavailable")
    return os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None


def _signal_group(process: subprocess.Popen[bytes], sig: signal.Signals) -> None:
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass  # A vanished group is not an alternate PID/group selection.


def _cleanup(
    process: subprocess.Popen[bytes], grace: float, normal: bool
) -> tuple[int | None, str | None]:
    try:
        _exited(process)  # Prove this is still our unreaped child before any signal.
        if not normal:
            _signal_group(process, signal.SIGTERM)
            deadline = time.monotonic() + grace
            while not _exited(process) and time.monotonic() < deadline:
                time.sleep(0.01)
        _signal_group(process, signal.SIGKILL)
        return process.wait(timeout=grace), None
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return process.returncode, _message(error)


def _supervise(
    process: subprocess.Popen[bytes], *, timeout: float = 180.0, grace: float = 2.0
) -> ProcessResult:
    raw = bytearray()
    termination = "IO_ERROR"
    error_text = None
    normal = False
    stream = process.stdout
    try:
        need(stream is not None, "owned serial pipe unavailable")
        assert stream is not None
        fd = stream.fileno()
        os.set_blocking(fd, False)
        deadline = time.monotonic() + timeout
        eof = False
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while True:
                exited = _exited(process)
                if eof and exited:
                    normal = True
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    termination = "TIMEOUT"
                    break
                if eof:
                    time.sleep(min(0.01, remaining))
                    continue
                if not selector.select(min(0.05, remaining)):
                    continue
                try:
                    chunk = os.read(fd, min(65536, LIMIT - len(raw) + 1))
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(fd)
                    eof = True
                    continue
                available = LIMIT - len(raw)
                raw.extend(chunk[:available])
                if len(chunk) > available:
                    termination = "OUTPUT_LIMIT"
                    break
    except (Exception, KeyboardInterrupt, SystemExit) as error:
        error_text = _message(error)
    finally:
        if stream is not None:
            try:
                stream.close()
            except OSError as error:
                normal = False
                error_text = _message(error)
        code, cleanup_error = _cleanup(process, grace, normal)
    if cleanup_error is not None:
        return ProcessResult(
            bytes(raw),
            code,
            "CLEANUP_ERROR",
            False,
            "; ".join(v for v in (error_text, cleanup_error) if v)[:4000],
        )
    if normal:
        termination = "EXITED" if code == 0 else "NONZERO_EXIT"
    return ProcessResult(bytes(raw), code, termination, normal, error_text)


def _new_destination(destination: Path) -> None:
    need(
        isinstance(destination, Path)
        and destination.is_absolute()
        and ".." not in destination.parts,
        "new absolute destination required",
    )
    primary = ROOT.parent.parent if ROOT.parent.name == ".worktrees" else ROOT
    need(
        not destination.is_relative_to(primary) and not destination.is_relative_to(ROOT),
        "output must be outside checkout",
    )
    for parent in destination.parents:
        need(stat.S_ISDIR(parent.lstat().st_mode), "output parent cannot be a link or special node")
    destination.mkdir(mode=0o700)  # Existing directories/files/symlinks are never overwritten.


def _write(path: Path, raw: bytes) -> None:
    with path.open("xb") as stream:
        need(stream.write(raw) == len(raw), "incomplete evidence write")


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _image_bound(path: Path, expected: bytes) -> None:
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size == len(expected), "prepared image changed")
    with path.open("rb") as stream:
        need(
            _file_identity(os.fstat(stream.fileno())) == _file_identity(before),
            "prepared image binding changed",
        )
        observed = stream.read(len(expected) + 1)
        after = os.fstat(stream.fileno())
    need(
        observed == expected
        and _file_identity(after) == _file_identity(before)
        and _file_identity(path.lstat()) == _file_identity(before),
        "prepared image changed",
    )


def _persist(directory: Path, record: AcquisitionRecord, error: str | None) -> None:
    _write(directory / "serial.bin", record.raw)
    _write(
        directory / "record.json",
        canonical(
            {
                "record": record.metadata(),
                "content_digest": record.content_digest,
                "failure_reason": error,
            }
        )
        + b"\n",
    )


def _record(
    case: str,
    attempt: str,
    assets: AssetBundle,
    image: bytes,
    argv: tuple[str, ...],
    result: ProcessResult,
    start: int,
    end: int,
) -> AcquisitionRecord:
    return AcquisitionRecord(
        case,
        attempt,
        assets.source_revision,
        assets.source_manifest_digest,
        digest(assets.probe),
        assets.vm_cohort_digest,
        assets.kernel_sha256,
        digest(init_bytes(case)),
        digest(image),
        argv,
        result.raw,
        result.exit_code,
        result.termination,
        result.raw_complete,
        start,
        end,
    )


def capture_cases(
    cases: tuple[str, ...], destination: Path, *, run_prepared_guest: bool = False
) -> tuple[AcquisitionRecord, ...]:
    need(run_prepared_guest is True, "explicit future guest opt-in required; no default execution")
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
    assets = preflight()
    try:
        _new_destination(destination)
    except OSError as error:
        raise ValueError("new owned output unavailable; no overwrite") from error
    completed: list[AcquisitionRecord] = []
    for case in cases:
        directory = destination / case
        raw_result = ProcessResult(b"", None, "IO_ERROR", False, None)
        image = b""
        argv: tuple[str, ...] = ()
        start = time.monotonic_ns()
        try:
            directory.mkdir(mode=0o700)
            image = build_image(assets, case)
            image_path = directory / "initrd.cpio.gz"
            _write(image_path, image)
            argv = qemu_arguments(image_path)
            # Recheck all fixed assets after preparation and before each launch.
            need(preflight() == assets, "prepared assets changed before launch")
            _image_bound(image_path, image)
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
            raw_result = _supervise(process)
            if raw_result.termination == "EXITED":
                validate_capture(raw_result.raw, case, assets)
                failure = None
            else:
                failure = raw_result.error or raw_result.termination
        except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            failure = _message(error)
        end = time.monotonic_ns()
        record = None
        try:
            # A pre-image/setup failure has no invented image or argv receipt.
            if not image or not argv:
                raise CaptureFailure(
                    failure or "preparation incomplete",
                    raw_result.raw,
                    raw_result.raw_complete,
                    completed,
                )
            record = _record(
                case, secrets.token_hex(16), assets, image, argv, raw_result, start, end
            )
            _persist(directory, record, failure)
        except (OSError, ValueError) as error:
            raise CaptureFailure(
                _message(error),
                raw_result.raw,
                raw_result.raw_complete,
                completed,
                current_record=record,
                acquisition_error=failure,
                persistence_error=_message(error) if record is not None else None,
            ) from error
        if failure is not None:
            raise CaptureFailure(
                failure,
                raw_result.raw,
                raw_result.raw_complete,
                completed,
                current_record=record,
                acquisition_error=failure,
            )
        completed.append(record)
    return tuple(completed)
