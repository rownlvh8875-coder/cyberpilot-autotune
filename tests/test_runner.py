import dataclasses
import inspect
import json
import pickle

import pytest

from native_e_lab.runner import Observation, run_fixed


def test_public_api_closed():
    assert not inspect.signature(run_fixed).parameters
    for kw in ("path", "pid", "fd", "command", "unit", "receipt"):
        with pytest.raises(TypeError):
            run_fixed(**{kw: "forged"})


def test_passive_observation_no_flags_no_recovery_api():
    obs = Observation("UNAVAILABLE", "UNKNOWN", None, None, ("not run",))
    assert not any(obs.flags.values())
    assert obs.provider_registration == "UNBOUND"
    assert obs.required_evidence == "UNAVAILABLE"
    plain = dataclasses.asdict(pickle.loads(pickle.dumps(obs)))
    json.dumps(plain)
    assert not any(hasattr(obs, name) for name in ("run", "stop", "recover", "close"))
    assert "receipt" not in inspect.signature(run_fixed).parameters


@pytest.mark.parametrize("where", ["spawn", "send", "read", "wait"])
def test_cancellation_preserves_primary_and_owned_cleanup(monkeypatch, where):
    import native_e_lab.runner as r

    events = []
    primary = KeyboardInterrupt("synthetic cancellation")

    class Child:
        def wait(self, timeout):
            events.append("wait")
            if where == "wait" and events.count("wait") == 1:
                raise primary
            return 20

    def spawn(fd):
        events.append("spawn")
        if where == "spawn":
            raise primary
        return Child()

    def send(*args):
        events.append("send")
        if where == "send":
            raise primary

    def read(*args):
        events.append("read")
        if where == "read":
            raise primary
        return None

    monkeypatch.setattr(r, "_spawn", spawn)
    monkeypatch.setattr(r, "send_frame", send)
    monkeypatch.setattr(r, "read_frame", read)
    with pytest.raises(KeyboardInterrupt) as caught:
        r.run_fixed()
    assert caught.value is primary
    assert events.count("spawn") == 1
    assert events.count("wait") == (0 if where == "spawn" else 1)


def test_wait_unknown_never_retried(monkeypatch):
    import subprocess

    import native_e_lab.runner as r

    calls = []

    class Child:
        def wait(self, timeout):
            calls.append("wait")
            raise subprocess.TimeoutExpired("fixed", timeout)

    monkeypatch.setattr(r, "_spawn", lambda fd: Child())
    monkeypatch.setattr(r, "send_frame", lambda *args: None)
    monkeypatch.setattr(r, "read_frame", lambda *args: None)
    obs = r.run_fixed()
    assert obs.outcome == "REJECTED" and obs.cleanup == "UNKNOWN"
    assert calls == ["wait"]


def test_secondary_close_error_does_not_mask_cancellation(monkeypatch):
    import native_e_lab.handles as h
    import native_e_lab.runner as r

    primary = KeyboardInterrupt("original")
    actual = h._close_socket
    calls = []

    class Secondary(BaseException):
        pass

    def uncertain(sock):
        calls.append(1)
        actual(sock)
        raise Secondary()

    def spawn(fd):
        raise primary

    monkeypatch.setattr(r, "_spawn", spawn)
    monkeypatch.setattr(h, "_close_socket", uncertain)
    with pytest.raises(KeyboardInterrupt) as caught:
        r.run_fixed()
    assert caught.value is primary
    assert len(calls) == 4
    assert "CLEANUP_UNKNOWN" in primary.__notes__


def test_unsupported_host_does_not_spawn(monkeypatch):
    import native_e_lab.runner as r

    monkeypatch.setattr(r.platform, "system", lambda: "Windows")
    result = r.run_fixed()
    assert result.outcome == "UNAVAILABLE" and result.cleanup == "NOT_CREATED"
    assert result.worker_exit is None


def test_binary_binding_rejects_replacement(tmp_path, monkeypatch):
    import native_e_lab.runner as r

    monkeypatch.setattr(r, "__file__", str(tmp_path / "runner.py"))
    (tmp_path / "supervisor").write_bytes(b"not-the-original")
    (tmp_path / "supervisor.sha256").write_text("a" * 64)
    with pytest.raises(ValueError, match="BINARY_BINDING"):
        r._binary()
    (tmp_path / "supervisor.sha256").write_text("unknown")
    with pytest.raises(ValueError, match="BINARY_BINDING"):
        r._binary()


def test_unavailable_is_not_a_worker_exit_observation(monkeypatch):
    import struct

    import native_e_lab.runner as r

    messages = []

    class Child:
        def wait(self, timeout):
            return 78

    def send(sock, message):
        messages.append(message)

    def read(sock):
        value = bytearray(messages[0])
        value[5] = 255
        return bytes(value) + struct.pack("!I", 38)

    monkeypatch.setattr(r, "_spawn", lambda fd: Child())
    monkeypatch.setattr(r, "send_frame", send)
    monkeypatch.setattr(r, "read_frame", read)
    obs = r.run_fixed()
    assert obs.outcome == "UNAVAILABLE"
    assert obs.worker_exit is None
    assert obs.supervisor_exit == 78


def test_uncertain_peer_close_cannot_become_confirmed_on_second_close(monkeypatch):
    import native_e_lab.handles as h
    import native_e_lab.runner as r

    actual = h._close_socket
    calls = []

    class Child:
        def wait(self, timeout):
            return 20

    def close(sock):
        calls.append(1)
        actual(sock)
        if len(calls) == 1:
            raise OSError("unknown completion")

    monkeypatch.setattr(r, "_spawn", lambda fd: Child())
    monkeypatch.setattr(h, "_close_socket", close)
    obs = r.run_fixed()
    assert obs.cleanup == "UNKNOWN"
    assert calls == [1, 1, 1, 1]
