"""Pure control tests; no actual delegated unit or cgroup mutation."""

import io
import subprocess
from types import SimpleNamespace

import pytest

from native_e_lab import domain, domain_gate, lab
from native_e_lab.protocol import Context, Stage


def test_direct_exec_cannot_create_domain_outside_factory_unit():
    obs = domain._run_domain_fixed()
    assert obs.outcome == "UNAVAILABLE", obs
    assert obs.cleanup == "CONFIRMED" and obs.domain is None and obs.worker_exit is None
    assert obs.supervisor_exit == 78


def test_new_unit_requires_delegation_before_go(monkeypatch):
    from test_lab_control import _fake_job

    seen = _fake_job(monkeypatch, values={"Delegate": "no"})
    result = domain.run_domain_lab()
    assert result["status"].startswith("UNKNOWN_")
    assert not any(x[0] == "communicate" for x in seen)
    command = seen[0][1][0]
    assert "--property=Delegate=yes" in command
    assert any(x.startswith("--unit=native-e-domain-") for x in command)


def test_new_unit_fixed_gate_and_preserved_limits(monkeypatch):
    from test_lab_control import _fake_job

    seen = _fake_job(monkeypatch, values={"Delegate": "yes"})
    result = domain.run_domain_lab()
    assert result["loaded_limits"] == lab.EXPECTED
    args = seen[0][1][0]
    assert any(x.endswith("/domain_gate.py") for x in args)
    assert args[-1].startswith("native-e-domain-") and args[-1].endswith(".service")
    assert seen[1][1].startswith("GO ")
    assert result["external_unit_is_internal_D"] is False


@pytest.mark.parametrize("phase", ["spawn", "send", "read", "wait"])
def test_domain_cancel_keeps_original_and_never_retries(monkeypatch, phase):
    events = []
    primary = KeyboardInterrupt("fixed")

    class Child:
        def wait(self, timeout):
            events.append("wait")
            if phase == "wait":
                raise primary
            return 20

    def spawn(fd):
        events.append("spawn")
        if phase == "spawn":
            raise primary
        return Child()

    def send(*args):
        if phase == "send":
            raise primary

    def read(*args):
        if phase == "read":
            raise primary
        return None

    monkeypatch.setattr(domain, "_spawn", spawn)
    monkeypatch.setattr(domain, "send_frame", send)
    monkeypatch.setattr(domain, "read_frame", read)
    with pytest.raises(KeyboardInterrupt) as caught:
        domain._run_domain_fixed()
    assert caught.value is primary
    assert events.count("spawn") == 1
    assert events.count("wait") == (0 if phase == "spawn" else 1)


def test_domain_wait_unknown_does_not_become_clean(monkeypatch):
    class Child:
        def wait(self, timeout):
            raise subprocess.TimeoutExpired("fixed", timeout)

    monkeypatch.setattr(domain, "_spawn", lambda fd: Child())
    monkeypatch.setattr(domain, "send_frame", lambda *a: None)
    monkeypatch.setattr(domain, "read_frame", lambda *a: None)
    obs = domain._run_domain_fixed()
    assert obs.cleanup == "UNKNOWN" and obs.domain is None


@pytest.mark.parametrize("bad", ["wrong_unit", "wrong_limits", "bad_token", "timeout"])
def test_domain_gate_blocks_before_native(monkeypatch, bad, capsys):
    token = "a" * 32
    unit = "native-e-domain-" + "b" * 32 + ".service"
    monkeypatch.setattr(domain_gate.sys, "argv", ["gate", token, unit])
    monkeypatch.setattr(domain_gate.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        domain_gate.sys,
        "stdin",
        SimpleNamespace(
            buffer=io.BytesIO(("GO " + (token if bad != "bad_token" else "c" * 32) + "\n").encode())
        ),
    )
    monkeypatch.setattr(
        domain_gate.select, "select", lambda *a: ([], [], []) if bad == "timeout" else ([1], [], [])
    )

    def check():
        if bad == "wrong_limits":
            raise ValueError("bad")
        return {}

    def scope(unit):
        if bad == "wrong_unit":
            raise ValueError("bad")
        return {}

    monkeypatch.setattr(domain_gate, "_kernel_limits", check)
    monkeypatch.setattr(domain_gate, "_scope", scope)
    monkeypatch.setattr(
        domain_gate, "_run_domain_fixed", lambda: pytest.fail("worker before gates")
    )
    assert domain_gate.main() != 0


@pytest.mark.parametrize(
    "path",
    [
        "/init.scope",
        "/native-e-domain-x.service",
        "/native-e-domain-" + "a" * 32 + ".service/owned-d-child",
    ],
)
def test_domain_scope_rejects_other_existing_memberships(monkeypatch, path):
    monkeypatch.setattr(domain_gate.Path, "read_text", lambda *a: "0::" + path + "\n")
    with pytest.raises(ValueError):
        domain_gate._scope("native-e-domain-" + "a" * 32 + ".service")


def test_domain_reader_rejects_missing_truncated_or_additional_report():
    ctx = Context.fresh()
    for raw in (None, b"", ctx.message(Stage.COMPLETE, 4), b"x" * 55):
        with pytest.raises(ValueError):
            domain._domain_report(ctx, raw)


def test_failed_domain_job_preserves_diagnostic_context(monkeypatch):
    from test_lab_control import _fake_job

    _fake_job(monkeypatch, values={"Delegate": "yes"}, code=6)
    result = domain.run_domain_lab()
    assert result["status"] == "BLOCKED_GATE_OR_JOB"
    assert isinstance(result.get("gate_observation"), dict)


def test_domain_reports_loaded_delegation(monkeypatch):
    from test_lab_control import _fake_job

    _fake_job(monkeypatch, values={"Delegate": "yes"})
    result = domain.run_domain_lab()
    assert result["loaded_delegation"] == "yes"


@pytest.mark.parametrize("fault", ["none", "extra", "bad_context", "close_exit", "wait_timeout"])
def test_domain_full_control_result_is_not_promoted_after_uncertainty(monkeypatch, fault):
    import struct

    contexts = []
    calls = []

    class Child:
        def wait(self, timeout):
            calls.append("wait")
            if fault == "wait_timeout":
                raise subprocess.TimeoutExpired("fixed", timeout)
            return 21 if fault == "close_exit" else 0

    monkeypatch.setattr(domain, "_spawn", lambda fd: Child())

    def send(sock, raw):
        if not contexts:
            contexts.append(Context(raw[18:34], int.from_bytes(raw[10:18], "big"), raw[34:50]))

    count = []

    def read(sock):
        i = len(count)
        count.append(1)
        ctx = Context.fresh() if fault == "bad_context" and i == 2 else contexts[0]
        frames = [
            ctx.message(Stage.OWNED, 1),
            ctx.message(Stage.DONE, 3),
            ctx.message(Stage.COMPLETE, 4) + struct.pack("!I", 255),
            b"extra" if fault == "extra" else None,
        ]
        return frames[i]

    monkeypatch.setattr(domain, "send_frame", send)
    monkeypatch.setattr(domain, "read_frame", read)
    obs = domain._run_domain_fixed()
    assert calls == ["wait"]
    assert obs.outcome == ("SYNTHETIC_DOMAIN_STOPPED" if fault == "none" else "REJECTED")
    if fault in ("wait_timeout", "close_exit"):
        assert obs.cleanup == "UNKNOWN"
    assert not any(obs.flags.values())


@pytest.mark.parametrize("bad", ["none", "owner", "type", "unwritable", "symlink"])
def test_scope_checks_fail_closed_without_treating_w_ok_as_qualification(monkeypatch, bad):
    unit = "native-e-domain-" + "a" * 32 + ".service"

    def read(path, *a, **kw):
        return (
            "0::/" + unit + "\n"
            if str(path) == "/proc/self/cgroup"
            else ("threaded\n" if bad == "type" else "domain\n")
        )

    monkeypatch.setattr(domain_gate.Path, "read_text", read)
    monkeypatch.setattr(domain_gate.Path, "is_symlink", lambda p: bad == "symlink")
    monkeypatch.setattr(
        domain_gate.Path, "stat", lambda p: SimpleNamespace(st_uid=2000 if bad == "owner" else 1000)
    )
    monkeypatch.setattr(domain_gate.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(domain_gate.os, "access", lambda *a, **k: bad != "unwritable")
    if bad == "none":
        assert domain_gate._scope(unit)["new_external_scope_checked"] is True
    else:
        with pytest.raises(ValueError):
            domain_gate._scope(unit)


def test_domain_gate_success_is_lab_only(monkeypatch, capsys):
    import json

    token = "a" * 32
    unit = "native-e-domain-" + "b" * 32 + ".service"
    monkeypatch.setattr(domain_gate.sys, "argv", ["gate", token, unit])
    monkeypatch.setattr(domain_gate.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        domain_gate.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(("GO " + token + "\n").encode())),
    )
    monkeypatch.setattr(domain_gate.select, "select", lambda *a: ([1], [], []))
    monkeypatch.setattr(domain_gate, "_kernel_limits", lambda: {})
    monkeypatch.setattr(domain_gate, "_scope", lambda unit: {})
    obs = domain.DomainObservation(
        "SYNTHETIC_DOMAIN_STOPPED", "CONFIRMED", 137, (("E_outside", True),), (), 0
    )
    monkeypatch.setattr(domain_gate, "_run_domain_fixed", lambda: obs)
    assert domain_gate.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["worker_executed"] is True
    assert not any(result["flags"].values()) and result["custody_qualified"] is False


def test_domain_spawn_binds_fixed_exec_worker_before_launch():
    worker = domain._worker_binary()
    assert worker.is_file() and worker.name == "domain_worker"
