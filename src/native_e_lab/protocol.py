"""Bounded stream framing. EOF is distinct from a zero-length message."""

import array
import os
import secrets
import socket
import struct
import time
from dataclasses import dataclass
from enum import IntEnum

MAX_FRAME = 512
HEADER = struct.Struct("!4sBBIQ16s16s")


class ProtocolError(ValueError):
    pass


class Stage(IntEnum):
    BIND = 1
    OWNED = 2
    RUN = 3
    DONE = 4
    COMPLETE = 5


@dataclass(frozen=True, slots=True)
class Context:
    cohort: bytes
    generation: int
    nonce: bytes

    @classmethod
    def fresh(cls) -> "Context":
        return cls(secrets.token_bytes(16), time.monotonic_ns(), secrets.token_bytes(16))

    def message(self, stage: Stage, sequence: int) -> bytes:
        return HEADER.pack(b"NEL1", 1, stage, sequence, self.generation, self.cohort, self.nonce)

    def check(self, raw: bytes | None, stage: Stage, sequence: int) -> None:
        if raw != self.message(stage, sequence):
            raise ProtocolError("CONTEXT_OR_ORDER")


def _receive(sock: socket.socket, size: int, *, boundary: bool = False) -> bytes | None:
    out = bytearray()
    while len(out) < size:
        data, ancillary, flags, _ = sock.recvmsg(
            size - len(out), socket.CMSG_SPACE(32 * array.array("i").itemsize)
        )
        if ancillary or flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC):
            uncertain = False
            for level, kind, raw in ancillary:
                if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                    fds = array.array("i")
                    fds.frombytes(raw[: len(raw) - len(raw) % fds.itemsize])
                    for fd in fds:
                        try:
                            os.close(fd)
                        except OSError:
                            uncertain = True
            raise ProtocolError("ANCILLARY_CLOSE_UNKNOWN" if uncertain else "ANCILLARY")
        if not data:
            if boundary and not out:
                return None
            raise ProtocolError("PARTIAL")
        out.extend(data)
    return bytes(out)


def read_frame(sock: socket.socket) -> bytes | None:
    prefix = _receive(sock, 4, boundary=True)
    if prefix is None:
        return None
    (size,) = struct.unpack("!I", prefix)
    if size == 0:
        raise ProtocolError("EMPTY")
    if size > MAX_FRAME:
        raise ProtocolError("OVERSIZE")
    return _receive(sock, size)


def send_frame(sock: socket.socket, data: bytes) -> None:
    if not data:
        raise ProtocolError("EMPTY")
    if len(data) > MAX_FRAME:
        raise ProtocolError("OVERSIZE")
    sock.sendall(struct.pack("!I", len(data)) + data)
