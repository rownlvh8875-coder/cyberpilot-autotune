import array
import dataclasses
import socket
import struct

import pytest

from native_e_lab.protocol import Context, ProtocolError, Stage, read_frame, send_frame


def test_context_fixed_stages_and_roundtrip():
    c = Context.fresh()
    for seq, stage in enumerate(Stage):
        assert c.check(c.message(stage, seq), stage, seq) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("cohort", b"x" * 16),
        ("nonce", b"y" * 16),
        ("generation", 99),
    ],
)
def test_wrong_context(field, value):
    c = Context.fresh()
    other = dataclasses.replace(c, **{field: value})
    with pytest.raises(ProtocolError):
        c.check(other.message(Stage.BIND, 0), Stage.BIND, 0)


@pytest.mark.parametrize("stage,seq", [(Stage.RUN, 0), (Stage.BIND, 1), (Stage.DONE, 3)])
def test_order_and_duplicate_rejected(stage, seq):
    c = Context.fresh()
    with pytest.raises(ProtocolError):
        c.check(c.message(stage, seq), Stage.BIND, 0)


@pytest.mark.parametrize(
    "raw,reason",
    [
        (b"", None),
        (struct.pack("!I", 0), "EMPTY"),
        (struct.pack("!I", 513), "OVERSIZE"),
        (b"\x00", "PARTIAL"),
        (struct.pack("!I", 2) + b"x", "PARTIAL"),
    ],
)
def test_eof_is_not_empty_or_partial(raw, reason):
    a, b = socket.socketpair()
    with a, b:
        a.sendall(raw)
        a.shutdown(socket.SHUT_WR)
        if reason is None:
            assert read_frame(b) is None
        else:
            with pytest.raises(ProtocolError, match=reason):
                read_frame(b)


def test_received_rights_closed_and_rejected(monkeypatch):
    import os

    import native_e_lab.protocol as p

    a, b = socket.socketpair()
    fd = os.open("/dev/null", os.O_RDONLY)
    closed = []
    original = os.close

    def tracked(value):
        closed.append(value)
        original(value)

    try:
        monkeypatch.setattr(p.os, "close", tracked)
        with a, b:
            a.sendmsg(
                [struct.pack("!I", 1) + b"x"],
                [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))],
            )
            with pytest.raises(ProtocolError, match="ANCILLARY"):
                read_frame(b)
            assert len(closed) == 1 and closed[0] != fd
            os.fstat(fd)
    finally:
        original(fd)


def test_frame_roundtrip():
    a, b = socket.socketpair()
    with a, b:
        send_frame(a, b"fixed")
        assert read_frame(b) == b"fixed"


def test_truncated_rights_never_leak_fds():
    import os
    from pathlib import Path

    a, b = socket.socketpair()
    fd = os.open("/dev/null", os.O_RDONLY)
    before = len(list(Path("/proc/self/fd").iterdir()))
    try:
        a.sendmsg(
            [struct.pack("!I", 1) + b"x"],
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd] * 64))],
        )
        with pytest.raises(ProtocolError, match="ANCILLARY"):
            read_frame(b)
        assert len(list(Path("/proc/self/fd").iterdir())) == before
    finally:
        a.close()
        b.close()
        os.close(fd)


def test_wrong_version_or_trailing_context_rejected():
    c = Context.fresh()
    raw = bytearray(c.message(Stage.BIND, 0))
    raw[4] = 2
    for data in (bytes(raw), c.message(Stage.BIND, 0) + b"extra", b""):
        with pytest.raises(ProtocolError):
            c.check(data, Stage.BIND, 0)


@pytest.mark.parametrize("data", [b"", b"x" * 513])
def test_send_bounds(data):
    a, b = socket.socketpair()
    with a, b, pytest.raises(ProtocolError):
        send_frame(a, data)
