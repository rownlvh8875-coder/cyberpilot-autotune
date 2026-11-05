"""Internal D trusted-lab runner. Receipts are passive, never stop authority."""

import hashlib
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .handles import _new_pair
from .protocol import Context, ProtocolError, Stage, read_frame, send_frame
from .runner import FLAGS


@dataclass(frozen=True, slots=True)
class DomainObservation:
    outcome: str
    cleanup: str
    worker_exit: int | None
    domain: tuple[tuple[str, bool], ...] | None
    errors: tuple[str, ...]
    supervisor_exit: int | None = None

    @property
    def flags(self) -> dict[str, bool]:
        return dict.fromkeys(FLAGS, False)

    @property
    def provider_registration(self) -> str:
        return "UNBOUND"


def _domain_report(ctx: Context, raw: bytes | None) -> dict[str, bool]:
    if raw is None or len(raw) != 54:
        raise ProtocolError("DOMAIN_REPORT")
    ctx.check(raw[:50], Stage.COMPLETE, 4)
    (mask,) = struct.unpack("!I", raw[50:])
    if mask != 255:
        raise ProtocolError("DOMAIN_REPORT")
    return dict.fromkeys(
        (
            "created_by_E",
            "worker_born_inside",
            "E_outside",
            "active_worker_stopped",
            "populated_zero",
            "original_D_removed",
            "original_OFD_retained",
            "worker_entry_no_directory_FD",
        ),
        True,
    )


def _binary() -> Path:
    path = Path(__file__).with_name("domain_supervisor")
    expected = path.with_suffix(".sha256").read_text().strip()
    if path.is_symlink() or not path.is_file() or len(expected) != 64:
        raise ValueError("DOMAIN_BINARY_BINDING")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("DOMAIN_BINARY_BINDING")
    return path


def _worker_binary() -> Path:
    path = Path(__file__).with_name("domain_worker")
    expected = path.with_suffix(".sha256").read_text().strip()
    if path.is_symlink() or not path.is_file() or len(expected) != 64:
        raise ValueError("WORKER_BINARY_BINDING")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("WORKER_BINARY_BINDING")
    return path


def _spawn(fd: int) -> subprocess.Popen[bytes]:
    _worker_binary()
    return subprocess.Popen(
        [str(_binary())],
        stdin=fd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        cwd="/",
        env={"LANG": "C.UTF-8"},
    )


def _run_domain_fixed() -> DomainObservation:
    child: subprocess.Popen[bytes] | None = None
    parent, peer = _new_pair()
    primary: BaseException | None = None
    status = "REJECTED"
    cleanup = "UNKNOWN"
    worker_exit = None
    result = None
    code = None
    errors: list[str] = []
    try:
        child = _spawn(peer._socket.fileno())
        if peer.close() != "CONFIRMED":
            raise ProtocolError("PEER_CLOSE_UNKNOWN")
        parent._socket.settimeout(4)
        ctx = Context.fresh()
        send_frame(parent._socket, ctx.message(Stage.BIND, 0))
        raw = read_frame(parent._socket)
        unavailable = bytearray(ctx.message(Stage.BIND, 0))
        unavailable[5] = 255
        if raw is not None and len(raw) == 54 and raw[:50] == bytes(unavailable):
            status = "UNAVAILABLE"
            errors.append("DOMAIN_PREFLIGHT_OR_CREATE_UNAVAILABLE")
        else:
            ctx.check(raw, Stage.OWNED, 1)
            send_frame(parent._socket, ctx.message(Stage.RUN, 2))
            parent._socket.shutdown(1)
            ctx.check(read_frame(parent._socket), Stage.DONE, 3)
            result = tuple(_domain_report(ctx, read_frame(parent._socket)).items())
            worker_exit = 137  # successful report requires waitid CLD_KILLED/SIGKILL
            if read_frame(parent._socket) is not None:
                raise ProtocolError("EXTRA")
            status = "SYNTHETIC_DOMAIN_STOPPED"
    except (OSError, ValueError) as exc:
        errors.append(type(exc).__name__)
    except BaseException as exc:
        primary = exc
        raise
    finally:
        states = []
        secondary: BaseException | None = None
        for handle in (peer, parent):
            try:
                states.append(handle.close())
            except BaseException as exc:
                states.append("UNKNOWN")
                secondary = secondary or exc
        if child is not None:
            try:
                code = child.wait(timeout=6)
                cleanup = "CONFIRMED" if code in (0, 20, 78) else "UNKNOWN"
            except (OSError, subprocess.TimeoutExpired):
                errors.append("WAIT_UNKNOWN")
            except BaseException as exc:
                secondary = secondary or exc
        if any(s not in ("CONFIRMED", "ALREADY_CLOSED") for s in states):
            cleanup = "UNKNOWN"
        if primary is not None and cleanup != "CONFIRMED":
            primary.add_note("CLEANUP_UNKNOWN")
        if primary is None and secondary is not None:
            secondary.add_note("CLEANUP_UNKNOWN")
            raise secondary
    if status == "SYNTHETIC_DOMAIN_STOPPED" and (code != 0 or cleanup != "CONFIRMED"):
        status = "REJECTED"
    return DomainObservation(status, cleanup, worker_exit, result, tuple(errors), code)


def run_domain_lab() -> dict[str, object]:
    """Only public entry: creates one NEW fixed bounded external unit."""
    from .lab import _run_user_lab

    return _run_user_lab(True)
