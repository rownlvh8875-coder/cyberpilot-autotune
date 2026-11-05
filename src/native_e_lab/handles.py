"""Factory-only live handles; original OFD anchors, never receipt recovery."""

import ctypes
import errno
import os
import platform
import socket
import stat
import tempfile
from pathlib import Path
from typing import NoReturn, SupportsIndex


def _identity(fd: int) -> tuple[int, int, int]:
    info = os.fstat(fd)
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _same_ofd(left: int, right: int) -> bool:
    # Linux x86_64 UAPI __NR_kcmp=312, KCMP_FILE=0; both PIDs are this process.
    # No caller-selectable PID, target process or fallback to metadata equality.
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise OSError(errno.ENOSYS, "OFD comparison unavailable")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    result = libc.syscall(
        ctypes.c_long(312),
        ctypes.c_int(os.getpid()),
        ctypes.c_int(os.getpid()),
        ctypes.c_int(0),
        ctypes.c_ulong(left),
        ctypes.c_ulong(right),
    )
    if result < 0:
        raise OSError(ctypes.get_errno(), "OFD comparison unavailable")
    return bool(result == 0)


def _close_socket(sock: socket.socket) -> None:
    sock.close()


class _NoSerialize:
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("live authority is not serializable")

    def __copy__(self) -> NoReturn:
        raise TypeError("live authority is not copyable")

    def __deepcopy__(self, memo: object) -> NoReturn:
        raise TypeError("live authority is not copyable")


class _Socket(_NoSerialize):
    def __init__(self) -> None:
        raise TypeError("factory only")

    _socket: socket.socket
    _anchor: socket.socket
    _original: tuple[int, int, int]
    _used: bool
    _state: str

    def close(self) -> str:
        if self._used:
            return "ALREADY_CLOSED" if self._state == "CONFIRMED" else self._state
        self._used = True
        self._state = "UNKNOWN"
        loss_state = "LOST"
        try:
            same = (
                _identity(self._socket.fileno()) == self._original
                and _identity(self._anchor.fileno()) == self._original
                and _same_ofd(self._socket.fileno(), self._anchor.fileno())
            )
        except OSError:
            same = False
            loss_state = "UNKNOWN"
        if not same:
            # Neither numeric descriptor is trusted after identity loss.
            # Detach prevents implicit finalizer closes. No retry/reconstruction.
            self._socket.detach()
            self._anchor.detach()
            self._state = loss_state
            return self._state
        primary: BaseException | None = None
        unknown = False
        for sock in (self._socket, self._anchor):
            try:
                _close_socket(sock)
            except BaseException as exc:
                sock.detach()
                unknown = True
                if not isinstance(exc, OSError):
                    primary = primary or exc
        self._state = "UNKNOWN" if unknown else "CONFIRMED"
        if primary is not None:
            primary.add_note("CLEANUP_UNKNOWN")
            raise primary
        return self._state


def _new_pair() -> tuple[_Socket, _Socket]:
    pair = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    originals = list(pair)
    result = []
    try:
        for sock in pair:
            value = object.__new__(_Socket)
            value._socket = sock
            value._original = _identity(sock.fileno())
            value._anchor = sock.dup()
            originals.append(value._anchor)
            value._used = False
            value._state = "OPEN"
            result.append(value)
        return result[0], result[1]
    except BaseException as primary:
        for sock in originals:
            try:
                sock.close()
            except BaseException:
                sock.detach()
                primary.add_note("HANDLE_CLOSE_UNKNOWN")
        raise


class _Directory(_NoSerialize):
    def __init__(self) -> None:
        raise TypeError("factory only")

    _fd: int
    _anchor: int
    _original: tuple[int, int, int]
    _path: Path
    _used: bool
    _state: str
    residue: str | None

    def close(self) -> str:
        if self._used:
            return "ALREADY_CLOSED" if self._state == "CONFIRMED" else self._state
        self._used = True
        self._state = "UNKNOWN"
        loss_state = "LOST"
        try:
            same = (
                _identity(self._fd) == self._original
                and _identity(self._anchor) == self._original
                and _same_ofd(self._fd, self._anchor)
            )
        except OSError:
            same = False
            loss_state = "UNKNOWN"
        if not same:
            self.residue = str(self._path)
            self._state = loss_state
            return self._state
        state = "CONFIRMED"
        try:
            current = self._path.lstat()
            same_name = (
                current.st_dev,
                current.st_ino,
                stat.S_IFMT(current.st_mode),
            ) == self._original
            if not same_name:
                state = "NAME_REPLACED"
            else:
                self._path.rmdir()
        except OSError:
            state = "UNKNOWN"
        primary: BaseException | None = None
        for fd in (self._fd, self._anchor):
            try:
                os.close(fd)
            except BaseException as exc:
                state = "UNKNOWN"
                if not isinstance(exc, OSError):
                    primary = primary or exc
        self._state = state
        if state != "CONFIRMED":
            self.residue = str(self._path)
        if primary is not None:
            primary.add_note("CLEANUP_UNKNOWN")
            raise primary
        return state


def _new_directory() -> _Directory:
    root = Path(__file__).resolve().parents[2] / "lab-fixtures"
    root.mkdir(mode=0o700, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="fixture-", dir=root))
    value = object.__new__(_Directory)
    value._path = path
    value._used = False
    value._state = "OPEN"
    value.residue = None
    acquired: list[int] = []
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        acquired.append(fd)
        value._fd = fd
        value._original = _identity(fd)
        value._anchor = os.dup(fd)
        acquired.append(value._anchor)
        return value
    except BaseException as primary:
        for fd in acquired:
            try:
                os.close(fd)
            except BaseException:
                primary.add_note("HANDLE_CLOSE_UNKNOWN")
        primary.add_note("NEW_EMPTY_FIXTURE_RETAINED")
        raise
