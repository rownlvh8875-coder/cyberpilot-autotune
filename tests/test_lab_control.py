"""Control flow fakes do not create or qualify a systemd unit."""

import io
import json
import subprocess
from types import SimpleNamespace

import pytest

from native_e_lab import gate, lab
from native_e_lab.runner import Observation


def _fake_job(monkeypatch, *, values=None, code=0, wait_error=None):
    seen = []
    props = dict(
        lab.EXPECTED,
        LoadState="loaded",
        ActiveState="active",
        Transient="yes",
        InvocationID="a" * 32,
    )
    if values is not None:
        props.update(values)

    class Job:
        returncode = None

        def __init__(self, *args, **kwargs):
            seen.append(("spawn", args, kwargs))
            self.stdin, self.stdout, self.stderr = io.StringIO(), io.StringIO(), io.StringIO()

        def poll(self):
            return None

        def communicate(self, data, timeout):
            seen.append(("communicate", data, timeout))
            if wait_error:
                raise wait_error
            self.returncode = code
            return json.dumps({"status": "SYNTHETIC_COMPLETE", "worker_executed": True}), ""

    def show(args, **kwargs):
        if "--property=LoadState" in args:
            return SimpleNamespace(returncode=4, stdout="LoadState=not-found\n")
        return SimpleNamespace(
            returncode=0, stdout="\n".join(k + "=" + v for k, v in props.items())
        )

    monkeypatch.setattr(lab.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(lab, "_bus_environment", lambda: {"LANG": "C.UTF-8"})
    monkeypatch.setattr(lab.subprocess, "run", show)
    monkeypatch.setattr(lab.subprocess, "Popen", Job)
    return seen


def test_gated_job_limits_and_no_name_based_stop(monkeypatch):
    seen = _fake_job(monkeypatch)
    result = lab.run_user_lab()
    assert result["loaded_limits"] == lab.EXPECTED
    assert result["external_unit_is_internal_D"] is False
    assert len([x for x in seen if x[0] == "spawn"]) == 1
    assert seen[1][0] == "communicate" and seen[1][1].startswith("GO ")
    command = seen[0][1][0]
    assert command[0] == "/usr/bin/systemd-run"
    assert "--property=TasksMax=8" in command
    assert not any(x in command for x in ("stop", "kill", "restart"))


@pytest.mark.parametrize("key", list(lab.EXPECTED) + ["Transient", "InvocationID"])
def test_unverified_unit_never_receives_go(monkeypatch, key):
    seen = _fake_job(monkeypatch, values={key: ""})
    result = lab.run_user_lab()
    assert result["status"].startswith("UNKNOWN_")
    assert not any(x[0] == "communicate" and x[1].startswith("GO ") for x in seen)


def test_job_timeout_does_not_retry_or_claim_cleanup(monkeypatch):
    seen = _fake_job(monkeypatch, wait_error=subprocess.TimeoutExpired("fixed", 38))
    result = lab.run_user_lab()
    assert result["cleanup"] == "UNKNOWN"
    assert len([x for x in seen if x[0] == "communicate"]) == 1


def test_job_nonzero_not_success(monkeypatch):
    _fake_job(monkeypatch, code=6)
    assert lab.run_user_lab()["status"] == "BLOCKED_GATE_OR_JOB"


def test_root_and_existing_unit_block_before_spawn(monkeypatch):
    seen = _fake_job(monkeypatch)
    monkeypatch.setattr(lab.os, "geteuid", lambda: 0)
    assert lab.run_user_lab()["status"] == "BLOCKED_ROOT"
    assert not seen
    monkeypatch.setattr(lab.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        lab.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="LoadState=loaded\n")
    )
    assert lab.run_user_lab()["status"] == "BLOCKED_UNIT_COLLISION_OR_UNKNOWN"
    assert not seen


def _kernel(monkeypatch, changed=None):
    values = {
        "memory.max": "134217728",
        "memory.swap.max": "0",
        "pids.max": "8",
        "cpu.max": "25000 100000",
    }
    if changed:
        values.update(changed)

    def read(path, *a, **k):
        if str(path) == "/proc/self/cgroup":
            return "0::/test-fixture\n"
        if str(path) == "/proc/self/mountinfo":
            return "10 1 0:1 / /sys/fs/cgroup rw - cgroup2 cgroup2 rw\n"
        return values[path.name]

    monkeypatch.setattr(gate.Path, "read_text", read)
    return values


@pytest.mark.parametrize("key", ["memory.max", "memory.swap.max", "pids.max", "cpu.max"])
def test_kernel_limits_block_bad_values(monkeypatch, key):
    _kernel(monkeypatch, {key: "max"})
    with pytest.raises(ValueError):
        gate._kernel_limits()


def test_kernel_exact_limits(monkeypatch):
    expected = _kernel(monkeypatch)
    assert gate._kernel_limits() == expected


@pytest.mark.parametrize("mode", ["ok", "wrong_token", "timeout", "limits_bad", "native_failed"])
def test_gate_cannot_run_before_checks(monkeypatch, capsys, mode):
    token = "a" * 32
    monkeypatch.setattr(gate.sys, "argv", ["fixed-gate", token])
    monkeypatch.setattr(gate.os, "geteuid", lambda: 1000)
    payload = ("GO " + ("b" * 32 if mode == "wrong_token" else token) + "\n").encode()
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(payload)))
    monkeypatch.setattr(
        gate.select, "select", lambda *a: ([], [], []) if mode == "timeout" else ([1], [], [])
    )
    calls = []
    _kernel(monkeypatch, {"pids.max": "9"} if mode == "limits_bad" else None)

    def fixed():
        calls.append(1)
        return Observation(
            "REJECTED" if mode == "native_failed" else "SYNTHETIC_COMPLETE",
            "CONFIRMED",
            0,
            "a" * 64,
            (),
        )

    monkeypatch.setattr(gate, "run_fixed", fixed)
    code = gate.main()
    assert (
        code == {"ok": 0, "wrong_token": 4, "timeout": 3, "limits_bad": 5, "native_failed": 6}[mode]
    )
    assert len(calls) == (1 if mode in ("ok", "native_failed") else 0)


def test_gate_argument_validation(monkeypatch):
    monkeypatch.setattr(gate.sys, "argv", ["fixed", "bad"])
    assert gate.main() == 2


@pytest.mark.parametrize("invalid", ["membership", "mount"])
def test_kernel_path_mapping_unknown_blocks(monkeypatch, invalid):
    def read(path, *args, **kwargs):
        if str(path) == "/proc/self/cgroup":
            return "0::/../foreign" if invalid == "membership" else "0::/test"
        return "10 1 0:1 /namespace /other rw - cgroup2 cgroup2 rw"

    monkeypatch.setattr(gate.Path, "read_text", read)
    with pytest.raises(ValueError, match="CGROUP_MAPPING_UNKNOWN"):
        gate._kernel_limits()


@pytest.mark.parametrize("mode", ["good", "symlink", "wrong_owner"])
def test_user_bus_scoped_identity(monkeypatch, mode):
    import stat

    monkeypatch.setattr(lab.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(lab.Path, "is_symlink", lambda p: mode == "symlink")
    monkeypatch.setattr(
        lab.Path,
        "stat",
        lambda p: SimpleNamespace(
            st_mode=stat.S_IFSOCK, st_uid=1001 if mode == "wrong_owner" else 1000
        ),
    )
    if mode == "good":
        env = lab._bus_environment()
        assert set(env) == {"PATH", "LANG", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"}
    else:
        with pytest.raises(ValueError):
            lab._bus_environment()


def test_released_job_timeout_does_not_claim_worker_never_ran(monkeypatch):
    _fake_job(monkeypatch, wait_error=subprocess.TimeoutExpired("fixed", 38))
    result = lab.run_user_lab()
    assert result["worker_executed"] == "UNKNOWN"
