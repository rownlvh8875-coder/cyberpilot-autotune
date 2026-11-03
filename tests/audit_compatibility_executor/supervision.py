"""Dedicated owned helper and bounded pipes. Synthetic observations,never H proof."""

import hashlib
import importlib
import json
import os
import selectors
import signal
import socket
import stat
import subprocess
import sys
import time
import types
from pathlib import Path
from typing import Any

# Private helper bootstrap adds ONLY this trusted new sibling,not a repository
# root,site directory,PYTHONPATH or historical import alias.
if __name__ == "__main__":
    package = types.ModuleType("_h1_owned_synthetic")
    package.__path__ = [str(Path(__file__).resolve().parent)]
    sys.modules[package.__name__] = package
    module = importlib.import_module(package.__name__ + ".supervision")
    raise SystemExit(module._helper_main())

from . import runner
from .contracts import SyntheticCase, SyntheticRequest, SyntheticResult, _result


def _json(raw: bytes) -> Any:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate protocol field")
            result[key] = value
        return result

    def invalid(value: str) -> None:
        raise ValueError("nonfinite protocol field")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def _decode(raw: bytes, case: SyntheticCase) -> dict[str, Any]:
    if len(raw) > 4096:
        raise ValueError("protocol too large")
    value = _json(raw)
    if type(value) is not dict or set(value) != {
        "schema",
        "case",
        "errors",
        "unavailable",
        "cleanup",
    }:
        raise ValueError("closed helper protocol required")
    if value["schema"] != "h1-supervisor-v1" or value["case"] != case.value:
        raise ValueError("protocol identity mismatch")
    # Result constructor validates exact reason/cleanup types and precedence.
    _result(
        case, errors=value["errors"], unavailable=value["unavailable"], cleanup=value["cleanup"]
    )
    return value


def _limits() -> None:
    import resource

    for kind, value in (
        (resource.RLIMIT_CPU, 3),
        (resource.RLIMIT_AS, 268435456),
        (resource.RLIMIT_FSIZE, 1048576),
        (resource.RLIMIT_NOFILE, 64),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(kind, (value, value))


def _pidfd_pid(fd: int) -> int:
    try:
        rows = Path(f"/proc/self/fdinfo/{fd}").read_text().splitlines()
        return int(next(row.split(":", 1)[1] for row in rows if row.startswith("Pid:")))
    except (OSError, StopIteration, ValueError) as error:
        raise ValueError("valid retained pidfd required") from error


def _kill_owned(child: subprocess.Popen[bytes], fd: int) -> None:
    if (
        child.pid <= 1
        or child.returncode is not None
        or _pidfd_pid(fd) != child.pid
        or os.getpgid(child.pid) != child.pid
    ):
        raise ValueError("not the owned unreaped group leader")
    os.killpg(child.pid, signal.SIGKILL)


def _exit_code(fd: int) -> int | None:
    info = os.waitid(os.P_PIDFD, fd, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    if info is None:
        return None
    return info.si_status if info.si_code == os.CLD_EXITED else -info.si_status


def _collect(
    child: subprocess.Popen[bytes], fd: int, wall: float, *, group: bool = True
) -> tuple[bytes, bytes, tuple[str, ...], int | None]:
    buffers = [bytearray(), bytearray()]
    errors: list[str] = []
    end = time.monotonic() + wall
    code = None

    def cleanup() -> None:
        def close(stream: Any) -> None:
            if stream is not None:
                stream.close()

        # Nested guards attempt both closes while retaining any body/signal fault.
        with runner._preserve_cleanup(lambda: close(child.stderr)):
            with runner._preserve_cleanup(lambda: close(child.stdout)):
                if errors or code is None:
                    try:
                        if group:
                            _kill_owned(child, fd)
                        else:
                            signal.pidfd_send_signal(fd, signal.SIGKILL)
                    except (OSError, ValueError):
                        errors.append("CLEANUP_SIGNAL_UNCONFIRMED")

    with runner._preserve_cleanup(cleanup):
        try:
            poll = selectors.DefaultSelector()
            with runner._preserve_cleanup(poll.close):
                for index, stream in enumerate((child.stdout, child.stderr)):
                    assert stream is not None
                    os.set_blocking(stream.fileno(), False)
                    poll.register(stream, selectors.EVENT_READ, index)
                while True:
                    code = _exit_code(fd)  # WNOWAIT:leader remains owned/unreaped.
                    if code not in (None, 0) and not errors:
                        errors.append(f"NONZERO_EXIT_{code}")
                    if time.monotonic() >= end:
                        errors.append("TIMEOUT")
                        break
                    for key, _ in poll.select(min(0.02, max(0, end - time.monotonic()))):
                        data = os.read(key.fd, 4096)
                        if not data:
                            poll.unregister(key.fileobj)
                            continue
                        room = 65536 - sum(map(len, buffers))
                        buffers[key.data].extend(data[:room])
                        if len(data) > room:
                            errors.append("OUTPUT_LIMIT")
                            break
                    if errors or (not poll.get_map() and code is not None):
                        break
        except (OSError, ValueError):
            errors.append("STREAM_OR_WAIT_ERROR")
    return bytes(buffers[0]), bytes(buffers[1]), tuple(errors), code


def _reap(child: subprocess.Popen[bytes]) -> bool:
    end = time.monotonic() + 2
    try:
        child.wait(timeout=max(0, end - time.monotonic()))
        while time.monotonic() < end:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                return True
            if pid == 0:
                time.sleep(0.01)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def _finish(
    case: SyntheticCase,
    root: str | None,
    out: bytes,
    err: bytes,
    errors: tuple[str, ...],
    missing: tuple[str, ...],
    cleaned: bool,
) -> SyntheticResult:
    if not cleaned:
        errors += ("CLEANUP_UNCONFIRMED",)
    return _result(
        case,
        root,
        errors=errors,
        unavailable=missing,
        cleanup="CONFIRMED" if cleaned else "UNCONFIRMED",
        stdout=out,
        stderr=err,
    )


def _read_owned(root: str, name: str, limit: int) -> bytes:
    directory = runner._open_directory(root)
    with runner._preserve_cleanup(lambda: os.close(directory)):
        fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=directory
        )
        with runner._preserve_cleanup(lambda: os.close(fd)):
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_nlink != 1
                or info.st_size > limit
            ):
                raise ValueError("bounded owned regular artifact required")
            stream = os.fdopen(fd, "rb", closefd=False)
            with runner._preserve_cleanup(stream.close):
                return stream.read(limit + 1)


def _verify_root(root: str, sources: dict[str, str]) -> None:
    SyntheticRequest(SyntheticCase.FD_CLOSED, root).validate()
    state = _json(_read_owned(root, "state.json", 8192))
    value = os.stat(root, follow_symlinks=False)
    if (
        type(state) is not dict
        or set(state) != {"schema", "identity", "sources"}
        or state["schema"] != "h1-owned-toy-v1"
        or state["identity"] != [value.st_dev, value.st_ino]
        or value.st_mode & 0o777 != 0o700
        or state["sources"] != sources
        or sources != runner._source_hashes()
        or hashlib.sha256(_read_owned(root, "payload.py", 65536)).hexdigest()
        != sources["h1_synthetic_payload.py"]
    ):
        raise ValueError("owned run/source identity mismatch")
    for name in ("protected", "scratch"):
        fd = runner._open_directory(root + "/" + name)
        os.close(fd)


def _check_observation(raw: bytes, host: dict[str, str]) -> bool:
    value = _json(raw)
    for sample in (value, value["descendant"]):
        if (
            sample["controls"]["NoNewPrivs"] != "1"
            or sample["controls"]["Seccomp"] != "2"
            or int(sample["controls"]["CapEff"], 16) != 0
            or sample["denied"]
            != dict.fromkeys(("create", "write", "rename", "unlink", "link"), 30)
            or sample["socket_errno"] != 1
            or sample["userns_errno"] != 1
            or sample["leaked_objects"] != []
            or sample["inherited_filter"] is not False
            or sample["read"] is not True
            or sample["host_hidden"] is not True
            or any(sample["namespaces"][key] == val for key, val in host.items())
            or "HF_TOKEN" in sample["environment_keys"]
            or "PYTHONPATH" in sample["environment_keys"]
            or sample["limits"]
            != {
                "CPU": [3, 3],
                "AS": [268435456, 268435456],
                "FSIZE": [1048576, 1048576],
                "NOFILE": [64, 64],
                "CORE": [0, 0],
            }
        ):
            return False
    return True


def _inner(case: SyntheticCase, root: str) -> dict[str, Any]:
    import fcntl

    filter_fd = runner._sealed_filter()
    directory = runner._open_directory(root)
    handles: list[int] = []
    sockets: list[socket.socket] = []
    try:
        for name in ("victim-one", "victim-two"):
            runner._write_new(directory, name, b"OWNED_FD_CONTROL_ONLY\n")
            handles.append(
                os.open(name, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory)
            )
        sockets.extend(socket.socketpair())
        # They are deliberately inheritable:FD isolation must come from the
        # launch whitelist,not accidentally from Python's CLOEXEC defaults.
        for handle in handles + [connection.fileno() for connection in sockets]:
            os.set_inheritable(handle, True)

        def identity(fd: int) -> list[int]:
            return [os.fstat(fd).st_dev, os.fstat(fd).st_ino]

        host = {
            key: os.readlink("/proc/self/ns/" + key)
            for key in ("user", "pid", "net", "mnt", "ipc", "uts")
        }
        runner._write_new(
            directory,
            "identities.json",
            json.dumps(
                {
                    "victims": [identity(fd) for fd in handles + [s.fileno() for s in sockets]],
                    "filter": identity(filter_fd),
                    "host": host,
                },
                sort_keys=True,
            ).encode(),
        )
        null_fd = os.open("/dev/null", os.O_RDONLY | os.O_CLOEXEC)
        handles.append(null_fd)
        child = subprocess.Popen(
            runner._command(root, case, filter_fd),
            cwd="/",
            stdin=null_fd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(filter_fd,),
            start_new_session=True,
            preexec_fn=_limits,
            env=runner._child_environment(),
        )
        assert child.stdout is not None and child.stderr is not None
        fd = os.pidfd_open(child.pid)
        try:
            roles = []
            for role, handle in (
                ("stdin_null", null_fd),
                ("seccomp_sealed", filter_fd),
                ("stdout_pipe", child.stdout.fileno()),
                ("stderr_pipe", child.stderr.fileno()),
            ):
                info = os.fstat(handle)
                roles.append(
                    {
                        "role": role,
                        "dev": info.st_dev,
                        "ino": info.st_ino,
                        "type": stat.S_IFMT(info.st_mode),
                        "access_mode": fcntl.fcntl(handle, fcntl.F_GETFL) & os.O_ACCMODE,
                    }
                )
            runner._write_new(
                directory,
                "launch.json",
                json.dumps(
                    {
                        "roles": roles,
                        "filter_seals": fcntl.fcntl(filter_fd, runner._F_GET_SEALS),
                        "pid": child.pid,
                        "namespace_host": host,
                        "limits_kind": "PER_PROCESS_NOT_AGGREGATE",
                        "source_hashes": runner._source_hashes(),
                    },
                    sort_keys=True,
                ).encode(),
            )
            if case is SyntheticCase.SUPERVISOR_ABORT:
                end = time.monotonic() + 0.3
                while time.monotonic() < end and not (Path(root) / "scratch/heartbeat").exists():
                    time.sleep(0.01)
                os._exit(31)  # this dedicated helper only;parent reports unknown cleanup.
            wall = 0.4 if case is SyntheticCase.TIMEOUT_SETSID else 5.0
            out, err, errors, _ = _collect(child, fd, wall)
            cleaned = _reap(child)
            if not errors and case in (
                SyntheticCase.FD_CLOSED,
                SyntheticCase.DIRECTORY_READ_ONLY,
                SyntheticCase.DESCENDANT_NETWORK,
            ):
                try:
                    if not _check_observation(out, host):
                        errors += ("OBSERVATION_MISMATCH",)
                except (ValueError, KeyError, TypeError):
                    errors += ("INVALID_OBSERVATION",)
            try:
                if _read_owned(root + "/protected", "canary", 65536) != runner._CANARY:
                    errors += ("PROTECTED_CONTENT_CHANGED",)
            except (OSError, ValueError):
                errors += ("PROTECTED_ARTIFACT_UNAVAILABLE",)
            # A failed artifact must not hide the observed command failure or
            # prevent an independent attempt to preserve the other stream.
            for name, data in (("stdout.bin", out), ("stderr.bin", err)):
                try:
                    runner._write_new(directory, name, data)
                except OSError:
                    errors += ("ARTIFACT_WRITE_UNAVAILABLE_" + name,)
            result = _finish(case, root, out, err, errors, (), cleaned)
            return {
                "schema": "h1-supervisor-v1",
                "case": case.value,
                "errors": result.errors,
                "unavailable": result.unavailable,
                "cleanup": result.cleanup,
            }
        finally:
            os.close(fd)
    finally:
        for fd in handles + [filter_fd, directory]:
            os.close(fd)
        for connection in sockets:
            connection.close()


def _helper_main() -> int:
    import ctypes

    try:
        request = _json(sys.stdin.buffer.read(4097))
        if type(request) is not dict or set(request) != {"schema", "case", "root", "sources"}:
            raise ValueError("closed helper request required")
        if request["schema"] != "h1-helper-request-v1":
            raise ValueError("wrong helper request version")
        case = SyntheticCase(request["case"])
        root = request["root"]
        _verify_root(root, request["sources"])
        if runner._preflight():
            raise ValueError("helper preconditions changed")
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError("subreaper unavailable")
        print(json.dumps(_inner(case, root), sort_keys=True), flush=True)
        return 0
    except (OSError, ValueError, TypeError, KeyError):
        # Do not print arbitrary exception text,paths,ambient values or secrets.
        return 2


def _supervise_started(
    case: SyntheticCase,
    run_root: str,
    request: bytes,
    helper: subprocess.Popen[bytes],
    fd: int,
) -> SyntheticResult:
    """Protocol evaluation; the caller owns helper handles on every exit."""
    assert helper.stdin is not None
    errors: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    out, err = b"", b""
    try:
        helper.stdin.write(request)
        helper.stdin.close()
        wall = 0.4 if case is SyntheticCase.TIMEOUT_SETSID else 5.0
        raw, control_err, control_errors, _ = _collect(helper, fd, wall + 4, group=False)
        errors = tuple(e.replace("NONZERO_EXIT_", "SUPERVISOR_EXIT_") for e in control_errors)
        cleaned = False
        protocol_invalid = False
        if not control_errors:
            try:
                value = _decode(raw, case)
            except ValueError:
                errors += ("CONTROLLER_OR_PROTOCOL_ERROR",)
                protocol_invalid = True
            else:
                # Retain these BEFORE any persistence/read can fail.
                errors += tuple(value["errors"])
                missing = tuple(value["unavailable"])
                cleaned = value["cleanup"] == "CONFIRMED"
        helper.wait(timeout=2)
        directory = runner._open_directory(run_root)
        with runner._preserve_cleanup(lambda: os.close(directory)):
            for name, data in (
                ("controller-stdout.bin", raw),
                ("controller-stderr.bin", control_err),
            ):
                try:
                    runner._write_new(directory, name, data)
                except OSError:
                    errors += ("ARTIFACT_WRITE_UNAVAILABLE_" + name,)
        if control_errors or protocol_invalid:
            return _finish(case, run_root, b"", b"", errors, ("MISSING_PROTOCOL",), False)
        try:
            out = _read_owned(run_root, "stdout.bin", 65536)
        except (OSError, ValueError):
            errors += ("STDOUT_ARTIFACT_UNAVAILABLE",)
            missing += ("STDOUT_ARTIFACT_UNAVAILABLE",)
        try:
            err = _read_owned(run_root, "stderr.bin", 65536 - len(out))
        except (OSError, ValueError):
            errors += ("STDERR_ARTIFACT_UNAVAILABLE",)
            missing += ("STDERR_ARTIFACT_UNAVAILABLE",)
        return _result(
            case,
            run_root,
            errors=errors,
            unavailable=missing,
            cleanup="CONFIRMED" if cleaned else "UNCONFIRMED",
            stdout=out,
            stderr=err,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        try:
            signal.pidfd_send_signal(fd, signal.SIGKILL)
            helper.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            pass
        return _finish(
            case, run_root, out, err, errors + ("CONTROLLER_OR_PROTOCOL_ERROR",), missing, False
        )


def _close_helper_streams(helper: subprocess.Popen[bytes]) -> bool:
    clean = True
    for stream in (helper.stdin, helper.stdout, helper.stderr):
        if stream is not None:
            try:
                stream.close()
            except (OSError, ValueError):
                clean = False
    return clean


def _abort_helper(helper: subprocess.Popen[bytes], fd: int | None, primary: BaseException) -> None:
    # Cleanup is finite best effort. Each operation is independent: a second
    # cancellation must not hide the first or skip the remaining owned handles.
    operations = []
    if helper.stdin is not None:
        operations.append(helper.stdin.close)
    if fd is not None:
        operations.append(lambda: signal.pidfd_send_signal(fd, signal.SIGKILL))
    operations.append(lambda: helper.wait(timeout=2))
    for stream in (helper.stdout, helper.stderr):
        if stream is not None:
            operations.append(stream.close)
    for operation in operations:
        try:
            operation()
        except BaseException:
            pass
    # Reaping the helper alone is not proof that every descendant was cleaned.
    BaseException.add_note(primary, "CLEANUP_UNCONFIRMED")


def _helper_pidfd(helper: subprocess.Popen[bytes]) -> int | None:
    try:
        return os.pidfd_open(helper.pid)
    except OSError:
        return None


def supervise(case: SyntheticCase, run_root: str) -> SyntheticResult:
    sources = runner._source_hashes()
    _verify_root(run_root, sources)
    request = json.dumps(
        {
            "schema": "h1-helper-request-v1",
            "case": case.value,
            "root": run_root,
            "sources": sources,
        },
        sort_keys=True,
    ).encode()
    helper: subprocess.Popen[bytes] | None = None
    fd: int | None = None
    primary: BaseException | None = None
    clean = True
    try:
        helper = subprocess.Popen(
            [runner._PYTHON, "-I", "-B", "-S", __file__],
            cwd="/",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            start_new_session=True,
            env=runner._child_environment(),
        )
        assert helper.stdin is not None
        fd = _helper_pidfd(helper)
        if fd is None:
            # No request was sent. EOF is the safe stop without a retained pidfd.
            helper.stdin.close()
            helper.wait(timeout=2)
            result = _result(
                case, run_root, unavailable=("PIDFD_UNAVAILABLE",), cleanup="UNCONFIRMED"
            )
        else:
            result = _supervise_started(case, run_root, request, helper, fd)
        clean = _close_helper_streams(helper)
    except BaseException as error:
        primary = error
        if helper is not None:
            _abort_helper(helper, fd, error)
        raise
    finally:
        # Retain the pidfd until after stop/reap. Never retry a released or
        # interrupted close, and never mask an already propagating exception.
        if fd is not None:
            try:
                os.close(fd)
            except BaseException as error:
                if primary is not None:
                    BaseException.add_note(primary, "CLEANUP_UNCONFIRMED")
                elif isinstance(error, (OSError, ValueError)):
                    clean = False
                else:
                    BaseException.add_note(error, "CLEANUP_UNCONFIRMED")
                    raise
    if not clean:
        return _result(
            case,
            run_root,
            errors=result.errors + ("CONTROLLER_HANDLE_CLEANUP_UNCONFIRMED",),
            unavailable=result.unavailable,
            cleanup="UNCONFIRMED",
            stdout=result.stdout,
            stderr=result.stderr,
        )
    return result
