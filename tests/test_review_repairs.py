"""Regressions for independent whole-change review of 200b4f9."""

import io
from types import SimpleNamespace

import pytest

from native_e_lab import gate, handles, lab
from native_e_lab.runner import Observation


def test_interrupted_socket_close_detaches_without_finalizer_retry(monkeypatch):
    a, b = handles._new_pair()
    raw = a._socket.fileno()
    primary = KeyboardInterrupt("fixed cancellation")
    calls = []

    def interrupted(sock):
        calls.append(1)
        raise primary

    monkeypatch.setattr(handles, "_close_socket", interrupted)
    with pytest.raises(KeyboardInterrupt) as caught:
        a.close()
    assert caught.value is primary
    assert a._socket.fileno() == -1
    assert a.close() == "UNKNOWN" and calls == [1, 1]
    # Deliberately do not retry this uncertain original FD. Kernel closes it at test exit.
    assert raw >= 0
    # This test's second independently retained factory socket is still owned.
    monkeypatch.undo()
    b.close()


def test_job_close_attempts_every_pipe_and_preserves_primary(monkeypatch):
    from test_lab_control import _fake_job

    primary = KeyboardInterrupt("fixed cancellation")
    events = []
    _fake_job(monkeypatch, wait_error=primary)
    original_factory = lab.subprocess.Popen

    class Pipe:
        def __init__(self, name):
            self.name = name

        def close(self):
            events.append(self.name)
            if self.name == "stdin":
                raise OSError("fixed close uncertainty")

    def spawn(*args, **kwargs):
        job = original_factory(*args, **kwargs)
        job.stdin, job.stdout, job.stderr = (Pipe(x) for x in ("stdin", "stdout", "stderr"))
        return job

    monkeypatch.setattr(lab.subprocess, "Popen", spawn)
    with pytest.raises(KeyboardInterrupt) as caught:
        lab.run_user_lab()
    assert caught.value is primary
    assert events == ["stdin", "stdout", "stderr"]
    assert "CLEANUP_UNKNOWN" in primary.__notes__


def test_gate_does_not_promote_invocation_to_worker_execution(monkeypatch, capsys):
    token = "a" * 32
    monkeypatch.setattr(gate.sys, "argv", ["gate", token])
    monkeypatch.setattr(gate.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(("GO " + token + "\n").encode()))
    )
    monkeypatch.setattr(gate.select, "select", lambda *args: ([1], [], []))
    monkeypatch.setattr(gate, "_kernel_limits", lambda: {})
    monkeypatch.setattr(
        gate,
        "run_fixed",
        lambda: Observation("UNAVAILABLE", "CONFIRMED", None, None, ("CLONE3_UNAVAILABLE",), 78),
    )
    assert gate.main() == 6
    import json

    assert json.loads(capsys.readouterr().out)["worker_executed"] is False


def test_normal_pipe_close_failure_cannot_return_success(monkeypatch):
    from test_lab_control import _fake_job

    _fake_job(monkeypatch)
    original_factory = lab.subprocess.Popen
    events = []

    class Pipe:
        def __init__(self, name):
            self.name = name

        def close(self):
            events.append(self.name)
            if self.name == "stdin":
                raise OSError("fixed uncertainty")

    def spawn(*args, **kwargs):
        job = original_factory(*args, **kwargs)
        job.stdin, job.stdout, job.stderr = (Pipe(n) for n in ("stdin", "stdout", "stderr"))
        return job

    monkeypatch.setattr(lab.subprocess, "Popen", spawn)
    with pytest.raises(OSError) as caught:
        lab.run_user_lab()
    assert "CLEANUP_UNKNOWN" in caught.value.__notes__
    assert events == ["stdin", "stdout", "stderr"]
