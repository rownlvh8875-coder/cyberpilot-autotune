"""Fixed Linux synthetic supervisor. Passive observations grant no authority."""

import hashlib
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .handles import _new_pair
from .protocol import Context, ProtocolError, Stage, read_frame, send_frame

FLAGS = (
    "application_authorized",
    "build_execution_allowed",
    "candidate_generation_allowed",
    "device_class_qualified",
    "owner_proposal_allowed",
    "policy_adopted",
    "promotion_authorized",
    "runtime_accepted",
    "runtime_qualified",
    "actual_payload_released",
    "cleanup_allowed",
    "recovery_execution_authorized",
    "H_executed",
    "HREQ004_qualified",
)
FIXTURE = b"NATIVE_E_FIXED_SYNTHETIC_V1\n"


@dataclass(frozen=True, slots=True)
class Observation:
    outcome: str
    cleanup: str
    worker_exit: int | None
    fixture_sha256: str | None
    errors: tuple[str, ...]
    supervisor_exit: int | None = None

    @property
    def flags(self) -> dict[str, bool]:
        return dict.fromkeys(FLAGS, False)

    @property
    def provider_registration(self) -> str:
        return "UNBOUND"

    @property
    def required_evidence(self) -> str:
        return "UNAVAILABLE"


def _binary() -> Path:
    path = Path(__file__).with_name("supervisor")
    expected = path.with_suffix(".sha256").read_text().strip()
    if not path.is_file() or path.is_symlink() or len(expected) != 64:
        raise ValueError("BINARY_BINDING")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("BINARY_BINDING")
    return path


def _spawn(sock_fd: int) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(_binary())],
        stdin=sock_fd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        env={"LANG": "C.UTF-8"},
        cwd="/",
    )


def run_fixed() -> Observation:
    if platform.system() != "Linux" or os.geteuid() == 0:
        return Observation("UNAVAILABLE", "NOT_CREATED", None, None, ("HOST_UNSUPPORTED",))
    child: subprocess.Popen[bytes] | None = None
    parent, peer = _new_pair()
    errors: list[str] = []
    outcome = "REJECTED"
    cleanup = "UNKNOWN"
    exit_code: int | None = None
    worker_exit: int | None = None
    primary: BaseException | None = None
    try:
        # Original E owns the worker's clone3 pidfd even if this controller is cancelled.
        child = _spawn(peer._socket.fileno())
        if peer.close() != "CONFIRMED":
            raise ProtocolError("PEER_CLOSE_UNKNOWN")
        parent._socket.settimeout(3.0)
        ctx = Context.fresh()
        send_frame(parent._socket, ctx.message(Stage.BIND, 0))
        raw = read_frame(parent._socket)
        if raw is not None and len(raw) == 54 and raw[5] == 255:
            expected = bytearray(ctx.message(Stage.BIND, 0))
            expected[5] = 255
            if raw[:50] != bytes(expected):
                raise ProtocolError("CONTEXT_OR_ORDER")
            errors.append("CLONE3_UNAVAILABLE")
            outcome = "UNAVAILABLE"
        else:
            ctx.check(raw, Stage.OWNED, 1)
            send_frame(parent._socket, ctx.message(Stage.RUN, 2))
            parent._socket.shutdown(1)
            ctx.check(read_frame(parent._socket), Stage.DONE, 3)
            ctx.check(read_frame(parent._socket), Stage.COMPLETE, 4)
            worker_exit = 0  # native COMPLETE requires successful waitid of the fixed worker.
            if read_frame(parent._socket) is not None:
                raise ProtocolError("EXTRA")
            outcome = "SYNTHETIC_COMPLETE"
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
                exit_code = child.wait(timeout=5)
                cleanup = "CONFIRMED" if exit_code in (0, 20, 78) else "UNKNOWN"
            except (OSError, subprocess.TimeoutExpired):
                errors.append("WAIT_UNKNOWN")
            except BaseException as exc:
                errors.append("WAIT_UNKNOWN")
                secondary = secondary or exc
        if any(s not in ("CONFIRMED", "ALREADY_CLOSED") for s in states):
            cleanup = "UNKNOWN"
            errors.append("HANDLE_CLOSE_UNKNOWN")
        if primary is not None and cleanup != "CONFIRMED":
            primary.add_note("CLEANUP_UNKNOWN")
        if primary is None and secondary is not None:
            secondary.add_note("CLEANUP_UNKNOWN")
            raise secondary
    if outcome == "SYNTHETIC_COMPLETE" and (exit_code != 0 or cleanup != "CONFIRMED"):
        outcome = "REJECTED"
    return Observation(
        outcome,
        cleanup,
        worker_exit,
        hashlib.sha256(FIXTURE).hexdigest() if outcome == "SYNTHETIC_COMPLETE" else None,
        tuple(errors),
        exit_code,
    )
