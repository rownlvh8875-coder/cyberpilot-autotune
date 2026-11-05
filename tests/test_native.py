import array
import dataclasses
import os
import socket
import struct
import subprocess

import pytest

from native_e_lab.protocol import Context, Stage, read_frame, send_frame
from native_e_lab.runner import _binary, run_fixed


def test_real_fixed_bootstrap():
    result = run_fixed()
    assert result.outcome == "SYNTHETIC_COMPLETE", result
    assert result.cleanup == "CONFIRMED" and result.worker_exit == 0
    assert not any(result.flags.values())


@pytest.mark.parametrize(
    "case",
    [
        "empty",
        "partial",
        "oversize",
        "rights",
        "wrong_order",
        "wrong_cohort",
        "wrong_generation",
        "wrong_nonce",
        "duplicate",
        "extra",
        "missing",
        "cancel",
    ],
)
def test_real_native_rejects_protocol_and_cleans_own_child(case):
    a, b = socket.socketpair()
    child = subprocess.Popen(
        [str(_binary())],
        stdin=b,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        env={"LANG": "C.UTF-8"},
    )
    b.close()
    a.settimeout(4)
    ctx = Context.fresh()
    try:
        if case in ("empty", "partial", "oversize", "rights", "wrong_order"):
            if case == "empty":
                a.sendall(struct.pack("!I", 0))
            elif case == "partial":
                a.sendall(b"\x00")
                a.shutdown(socket.SHUT_WR)
            elif case == "oversize":
                a.sendall(struct.pack("!I", 513))
            elif case == "rights":
                fd = os.open("/dev/null", os.O_RDONLY)
                try:
                    a.sendmsg(
                        [struct.pack("!I", 1) + b"x"],
                        [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))],
                    )
                finally:
                    os.close(fd)
            else:
                send_frame(a, ctx.message(Stage.RUN, 0))
        else:
            send_frame(a, ctx.message(Stage.BIND, 0))
            ctx.check(read_frame(a), Stage.OWNED, 1)
            if case.startswith("wrong_"):
                key = case.removeprefix("wrong_")
                value = 77 if key == "generation" else b"x" * 16
                other = dataclasses.replace(ctx, **{key: value})
                send_frame(a, other.message(Stage.RUN, 2))
            elif case == "duplicate":
                send_frame(a, ctx.message(Stage.BIND, 0))
            elif case == "extra":
                send_frame(a, ctx.message(Stage.RUN, 2))
                send_frame(a, ctx.message(Stage.RUN, 2))
            elif case == "cancel":
                a.close()
            # "missing" reaches the native per-message deadline without a RUN.
        assert child.wait(timeout=6) == 20
    finally:
        a.close()
        if child.returncode is None:
            child.wait(timeout=6)
