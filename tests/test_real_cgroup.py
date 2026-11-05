"""Fixed real-cgroup adapter tests. Test collection never creates a unit."""

import io
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.real_cgroup import build, gate, lab


def fake_job(
    monkeypatch,
    *,
    changed=None,
    code=0,
    timeout=False,
    reverse=False,
    pending=False,
    duplicate=False,
):
    seen = []
    pending_seen = []
    props = dict(
        lab.EXPECTED,
        LoadState="loaded",
        ActiveState="active",
        Transient="yes",
        InvocationID="a" * 32,
    )
    if changed:
        props.update(changed)

    class Job:
        returncode = None

        def __init__(self, args, **kwargs):
            seen.append(("spawn", args, kwargs))
            self.stdin = io.StringIO()
            self.stdout = io.StringIO()
            self.stderr = io.StringIO()

        def poll(self):
            return None

        def communicate(self, data, timeout):
            seen.append(("communicate", data))
            if globals_timeout:
                raise subprocess.TimeoutExpired("fixed", 38)
            self.returncode = code
            records = [
                json.dumps({"gate_pass": True, "kernel_limits": {}, "scope": {}}),
                json.dumps(
                    {
                        "outcome": "REAL_CGROUP_COHORT_COMPLETE",
                        "worker_started": True,
                        "kernel_domain_verified": True,
                        "parent_released": True,
                        "library_close_result": "UNAVAILABLE",
                    }
                ),
            ]
            if duplicate:
                records[0] = '{"gate_pass":false,"gate_pass":true,"kernel_limits":{},"scope":{}}'
            return "\n".join(list(reversed(records)) if reverse else records), ""

    globals_timeout = timeout

    def show(args, **kwargs):
        if "--property=LoadState" in args:
            return SimpleNamespace(returncode=4, stdout="LoadState=not-found\n", stderr="")
        if pending and not pending_seen:
            pending_seen.append(1)
            return SimpleNamespace(returncode=4, stdout="LoadState=not-found\n", stderr="")
        return SimpleNamespace(
            returncode=0, stdout="\n".join(k + "=" + v for k, v in props.items()), stderr=""
        )

    monkeypatch.setattr(lab, "_preflight", lambda: {})
    monkeypatch.setattr(lab, "_build_kit", lambda: Path("/fixed-private-kit"))
    monkeypatch.setattr(lab, "_bus_environment", lambda: {"LANG": "C.UTF-8"})
    monkeypatch.setattr(lab.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(lab.subprocess, "run", show)
    monkeypatch.setattr(lab.subprocess, "Popen", Job)
    return seen


def test_fixed_unit_bounds_and_no_name_cleanup(monkeypatch):
    seen = fake_job(monkeypatch)
    result = lab.run_fixed_real_lab()
    assert result["status"] == "PASS_REAL_CGROUP_LAB"
    args = seen[0][1]
    assert "--slice=-.slice" in args
    for item in [
        "RuntimeMaxSec=30s",
        "TimeoutStopSec=5s",
        "MemoryMax=128M",
        "MemorySwapMax=0",
        "TasksMax=8",
        "CPUQuota=25%",
        "Delegate=yes",
        "NoNewPrivileges=yes",
    ]:
        assert "--property=" + item in args
    assert len([x for x in seen if x[0] == "spawn"]) == 1
    assert seen[1][1].startswith("GO ")
    assert not any(x in args for x in ["stop", "kill", "restart", "enable", "sudo"])
    assert result["external_unit_is_internal_D"] is False
    assert result["custody_qualified"] is False


@pytest.mark.parametrize(
    "key",
    [
        "RuntimeMaxUSec",
        "TimeoutStopUSec",
        "MemoryMax",
        "MemorySwapMax",
        "TasksMax",
        "CPUQuotaPerSecUSec",
        "Delegate",
        "NoNewPrivileges",
        "Slice",
        "Transient",
        "InvocationID",
    ],
)
def test_limits_identity_or_delegation_failure_never_releases_go(monkeypatch, key):
    seen = fake_job(monkeypatch, changed={key: ""})
    result = lab.run_fixed_real_lab()
    assert result["status"] != "PASS_REAL_CGROUP_LAB"
    assert not any(x[0] == "communicate" and x[1].startswith("GO ") for x in seen)


def test_original_job_timeout_is_not_retried(monkeypatch):
    seen = fake_job(monkeypatch, timeout=True)
    result = lab.run_fixed_real_lab()
    assert result["cleanup"] == "UNKNOWN"
    assert len([x for x in seen if x[0] == "spawn"]) == 1
    assert len([x for x in seen if x[0] == "communicate"]) == 1


def test_root_never_builds_or_starts(monkeypatch):
    seen = fake_job(monkeypatch)
    monkeypatch.setattr(lab.os, "geteuid", lambda: 0)
    assert lab.run_fixed_real_lab()["status"] == "BLOCKED_ROOT"
    assert not seen


@pytest.fixture(scope="session")
def kit(tmp_path_factory):
    root = tmp_path_factory.mktemp("real-kit-root")
    original = build.KIT_ROOT
    build.KIT_ROOT = root
    try:
        yield build.build_fixed_kit()
    finally:
        build.KIT_ROOT = original


def test_real_native_scope_rejects_direct_wsl_before_any_child(kit):
    r = subprocess.run(
        [str(kit / "cohort")],
        cwd=kit,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=5,
    )
    report = json.loads(r.stdout)
    assert r.returncode != 0 and report["start_attempts"] == 0
    assert report["worker_started"] is False


def test_kit_manifest_is_canonical_and_source_bound(kit):
    raw = (kit / "manifest.json").read_bytes()
    record = json.loads(raw)
    assert raw == build.canonical(record)
    assert set(record["assets"]) == {"cohort", "fixed-worker"}
    assert set(record["sources"]) == set(build.SOURCES)
    assert kit.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("case", ["normal", "worker_drift", "manifest_extra", "source_drift"])
def test_gate_asset_verification_uses_fixed_files_only(kit, tmp_path, monkeypatch, case):
    private = tmp_path / "kit-local"
    private.mkdir(mode=0o700)
    for name in ["cohort", "fixed-worker", "manifest.json"]:
        (private / name).write_bytes((kit / name).read_bytes())
        (private / name).chmod(0o700 if name != "manifest.json" else 0o600)
    monkeypatch.setattr(build, "KIT_ROOT", tmp_path)
    if case == "worker_drift":
        with (private / "fixed-worker").open("ab") as stream:
            stream.write(b"x")
    if case in ["manifest_extra", "source_drift"]:
        value = json.loads((private / "manifest.json").read_bytes())
        if case == "manifest_extra":
            value["assets"]["/outside"] = "0" * 64
        else:
            value["sources"][build.SOURCES[0]] = "0" * 64
        (private / "manifest.json").write_bytes(build.canonical(value))
    if case == "normal":
        fd = build.verify_open_factory(private)
        assert os.fstat(fd).st_size > 0
        os.close(fd)
    else:
        with pytest.raises((ValueError, OSError)):
            build.verify_open_factory(private)


@pytest.mark.parametrize("case", ["bad_token", "timeout", "bad_scope", "bad_kernel", "bad_asset"])
def test_gate_rejects_before_exec(monkeypatch, case, capsys):
    token = "a" * 32
    monkeypatch.setattr(
        gate.sys, "argv", ["gate", token, "native-e-domain-" + "b" * 32 + ".service", "/private"]
    )
    payload = ("GO " + ("b" * 32 if case == "bad_token" else token) + "\n").encode()
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(payload)))
    monkeypatch.setattr(
        gate.select, "select", lambda *a: ([], [], []) if case == "timeout" else ([1], [], [])
    )

    def check_scope(unit):
        if case == "bad_scope":
            raise ValueError("scope")
        return {}

    def check_kernel():
        if case == "bad_kernel":
            raise ValueError("kernel")
        return {}

    monkeypatch.setattr(gate, "_scope", check_scope)
    monkeypatch.setattr(gate, "_kernel_limits", check_kernel)
    monkeypatch.setattr(gate, "_credentials", lambda: None)

    def verify(path):
        if case == "bad_asset":
            raise ValueError("asset")
        return 42

    monkeypatch.setattr(gate, "verify_open_factory", verify)
    monkeypatch.setattr(gate.os, "execve", lambda *a: pytest.fail("exec before gate"))
    assert gate.main() != 0


def test_valid_gate_execs_original_fd_in_same_pid(monkeypatch, capsys):
    token = "a" * 32
    monkeypatch.setattr(
        gate.sys, "argv", ["gate", token, "native-e-domain-" + "b" * 32 + ".service", "/private"]
    )
    monkeypatch.setattr(
        gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(("GO " + token + "\n").encode()))
    )
    monkeypatch.setattr(gate.select, "select", lambda *a: ([1], [], []))
    monkeypatch.setattr(gate, "_scope", lambda unit: {})
    monkeypatch.setattr(gate, "_kernel_limits", lambda: {})
    monkeypatch.setattr(gate, "_credentials", lambda: None)
    fd = os.open("/dev/null", os.O_RDONLY | os.O_CLOEXEC)
    monkeypatch.setattr(gate, "verify_open_factory", lambda path: fd)
    seen = []

    def execute(actual, args, env):
        seen.append((actual, args, env, os.getpid()))
        raise RuntimeError("EXEC_WITNESS")

    monkeypatch.setattr(gate.os, "execve", execute)
    with pytest.raises(RuntimeError, match="EXEC_WITNESS"):
        gate.main()
    assert seen == [(fd, ["fixed-real-cgroup-cohort"], {"LANG": "C.UTF-8"}, os.getpid())]
    with pytest.raises(OSError):
        os.fstat(fd)


@pytest.mark.parametrize("changed", [{"InvocationID": "bogus"}, {"LoadState": "not-found"}])
def test_malformed_loaded_identity_never_gets_go(monkeypatch, changed):
    seen = fake_job(monkeypatch, changed=changed)
    result = lab.run_fixed_real_lab()
    assert result["status"] != "PASS_REAL_CGROUP_LAB"
    assert not any(x[0] == "communicate" and x[1].startswith("GO ") for x in seen)


def test_reordered_gate_native_frames_reject(monkeypatch):
    fake_job(monkeypatch, reverse=True)
    assert lab.run_fixed_real_lab()["status"] != "PASS_REAL_CGROUP_LAB"


def test_initial_unit_lookup_race_reads_again_without_respawn(monkeypatch):
    seen = fake_job(monkeypatch, pending=True)
    assert lab.run_fixed_real_lab()["status"] == "PASS_REAL_CGROUP_LAB"
    assert len([x for x in seen if x[0] == "spawn"]) == 1


def test_duplicate_json_key_cannot_override_gate_failure(monkeypatch):
    fake_job(monkeypatch, duplicate=True)
    assert lab.run_fixed_real_lab()["status"] != "PASS_REAL_CGROUP_LAB"


@pytest.mark.parametrize(
    "case", ["normal", "delegate", "inactive", "mapping", "cpu", "threaded", "path"]
)
def test_existing_root_preflight_requires_already_enabled_controllers(monkeypatch, case):
    manager = {
        "ActiveState": "active",
        "Delegate": "yes",
        "DelegateControllers": "cpu memory pids",
        "ControlGroup": "/unit-root",
        "MainPID": "321",
    }
    root = {"LoadState": "loaded", "ActiveState": "active", "ControlGroup": "/unit-root"}
    if case == "delegate":
        manager["Delegate"] = "no"
    if case == "inactive":
        root["ActiveState"] = "inactive"
    if case == "mapping":
        root["ControlGroup"] = "/other"
    if case == "path":
        root["ControlGroup"] = manager["ControlGroup"] = "/../escape"
    responses = iter([manager, root])
    monkeypatch.setattr(lab, "_bus_environment", lambda: {"LANG": "C"})
    monkeypatch.setattr(lab, "_show", lambda *a, **k: next(responses))

    def read(path, *a, **k):
        if str(path) == "/proc/321/stat":
            return "321 (systemd) " + " ".join(["S"] + ["0"] * 18 + ["123"])
        return {
            "cgroup.type": "threaded" if case == "threaded" else "domain",
            "cgroup.controllers": "cpu memory pids",
            "cgroup.subtree_control": "memory pids" if case == "cpu" else "cpu memory pids",
        }[path.name]

    monkeypatch.setattr(lab.Path, "read_text", read)
    if case == "normal":
        assert lab._preflight()["manager_starttime"] == "123"
    else:
        with pytest.raises(ValueError):
            lab._preflight()


@pytest.mark.parametrize(
    "nnp,cap,allowed", [("1", "0", True), ("0", "0", False), ("1", "80", False)]
)
def test_gate_checks_actual_self_restrictions(monkeypatch, nnp, cap, allowed):
    monkeypatch.setattr(
        gate.Path, "read_text", lambda *a, **k: f"NoNewPrivs:\t{nnp}\nCapEff:\t{cap}\n"
    )
    if allowed:
        gate._credentials()
    else:
        with pytest.raises(ValueError):
            gate._credentials()


def test_unreadable_manager_is_not_success(monkeypatch):
    monkeypatch.setattr(
        lab.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="")
    )
    with pytest.raises(ValueError):
        lab._show(["fixed"], {})


@pytest.mark.parametrize("case", ["kit_parent", "kit_mode", "asset_mode", "kit_symlink"])
def test_kit_cannot_import_unreviewed_or_writable_resource(kit, tmp_path, monkeypatch, case):
    private = tmp_path / "kit-own"
    private.mkdir(mode=0o700)
    for name in ["cohort", "fixed-worker", "manifest.json"]:
        (private / name).write_bytes((kit / name).read_bytes())
        (private / name).chmod(0o700 if name != "manifest.json" else 0o600)
    monkeypatch.setattr(build, "KIT_ROOT", tmp_path)
    target = private
    if case == "kit_parent":
        monkeypatch.setattr(build, "KIT_ROOT", tmp_path / "unrelated")
    if case == "kit_mode":
        private.chmod(0o755)
    if case == "asset_mode":
        (private / "cohort").chmod(0o777)
    if case == "kit_symlink":
        target = tmp_path / "link"
        target.symlink_to(private, target_is_directory=True)
    with pytest.raises((OSError, ValueError)):
        build.verify_open_factory(target)


def test_legacy_pin_mismatch_never_invokes_compiler(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(build, "DOMAIN_PIN", "0" * 64)
    monkeypatch.setattr(
        build.subprocess, "run", lambda *a, **k: pytest.fail("compiler before source pin")
    )
    with pytest.raises(ValueError, match="LEGACY_SOURCE_DRIFT"):
        build.build_fixed_kit()


def test_compile_failure_is_retained_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "KIT_ROOT", tmp_path)
    calls = []

    def fail(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1, stdout="", stderr="synthetic compiler failure")

    monkeypatch.setattr(build.subprocess, "run", fail)
    with pytest.raises(ValueError, match="BUILD_FAILED"):
        build.build_fixed_kit()
    assert len(calls) == 1
    assert len(list(tmp_path.glob("kit-*/build-log.json"))) == 1


def test_nonzero_unit_never_becomes_pass(monkeypatch):
    fake_job(monkeypatch, code=6)
    assert lab.run_fixed_real_lab()["status"] != "PASS_REAL_CGROUP_LAB"


def test_collision_prevents_any_creation(monkeypatch):
    seen = fake_job(monkeypatch)
    monkeypatch.setattr(
        lab.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="LoadState=loaded\n"),
    )
    assert lab.run_fixed_real_lab()["status"] == "BLOCKED_UNIT_COLLISION_OR_UNKNOWN"
    assert not seen


def test_controller_cancel_does_not_recover_or_respawn(monkeypatch):
    seen = fake_job(monkeypatch)
    original = lab.subprocess.Popen

    class CancelJob(original):
        def communicate(self, data, timeout):
            seen.append(("cancel", data))
            raise KeyboardInterrupt("synthetic cancel")

    monkeypatch.setattr(lab.subprocess, "Popen", CancelJob)
    with pytest.raises(KeyboardInterrupt):
        lab.run_fixed_real_lab()
    assert len([x for x in seen if x[0] == "spawn"]) == 1
    assert len([x for x in seen if x[0] == "cancel"]) == 1


def test_build_source_drift_after_compiler_never_attests_current_new_bytes(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    for name in build.SOURCES:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((build.ROOT / name).read_bytes())
    kits = tmp_path / "kits"
    kits.mkdir()
    monkeypatch.setattr(build, "ROOT", source)
    monkeypatch.setattr(build, "KIT_ROOT", kits)
    real_run = build.subprocess.run

    def compile_then_drift(args, **kwargs):
        result = real_run(args, **kwargs)
        if args[-1].endswith("/cohort"):
            target = source / "research/real_cgroup/factory.c"
            target.write_text(
                target.read_text().replace(
                    "REAL_CGROUP_COHORT_COMPLETE", "REAL_CGROUP_COHORT_DRIFTED"
                )
            )
        return result

    monkeypatch.setattr(build.subprocess, "run", compile_then_drift)
    with pytest.raises(ValueError, match="SOURCE_CHANGED_DURING_BUILD"):
        build.build_fixed_kit()


def test_unknown_close_inside_communicate_is_never_retried(monkeypatch):
    fake_job(monkeypatch)
    original = lab.subprocess.Popen

    class UncertainPipe:
        attempts = 0

        def close(self):
            self.attempts += 1
            if self.attempts == 1:
                raise OSError("synthetic unknown close")

    pipe = UncertainPipe()

    class Job(original):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.stdout = pipe

        def communicate(self, data, timeout):
            self.stdout.close()
            raise AssertionError("unreachable")

    monkeypatch.setattr(lab.subprocess, "Popen", Job)
    result = lab.run_fixed_real_lab()
    assert result["cleanup"] == "UNKNOWN"
    assert pipe.attempts == 1


@pytest.mark.parametrize("trailing", [b"x", b"GO duplicate\n"])
def test_gate_rejects_additional_input_before_verifying_assets(monkeypatch, trailing):
    token = "a" * 32
    monkeypatch.setattr(
        gate.sys, "argv", ["gate", token, "native-e-domain-" + "b" * 32 + ".service", "/private"]
    )
    monkeypatch.setattr(
        gate.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(("GO " + token + "\n").encode() + trailing)),
    )
    monkeypatch.setattr(gate.select, "select", lambda *a: ([1], [], []))
    monkeypatch.setattr(gate, "_scope", lambda unit: {})
    monkeypatch.setattr(gate, "_kernel_limits", lambda: {})
    monkeypatch.setattr(gate, "_credentials", lambda: None)
    monkeypatch.setattr(
        gate, "verify_open_factory", lambda *a: pytest.fail("asset open before strict EOF")
    )
    assert gate.main() != 0


@pytest.mark.parametrize("message", [b"", b"G", b"GO short\n"])
def test_go_partial_or_empty_is_not_eof_success(monkeypatch, message):
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(message)))
    monkeypatch.setattr(gate.select, "select", lambda *a: ([1], [], []))
    assert gate._read_go(b"GO " + b"a" * 32 + b"\n") == 4


def test_go_partial_live_stream_times_out_with_same_deadline(monkeypatch):
    ready = iter([([1], [], []), ([], [], [])])
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"G")))
    monkeypatch.setattr(gate.select, "select", lambda *a: next(ready))
    assert gate._read_go(b"GO " + b"a" * 32 + b"\n") == 3


@pytest.mark.parametrize("name", ["manifest.json", "fixed-worker"])
def test_fifo_kit_is_rejected_before_blocking_read(kit, tmp_path, monkeypatch, name):
    import signal

    private = tmp_path / "kit-fifo"
    private.mkdir(mode=0o700)
    for asset in ["cohort", "fixed-worker", "manifest.json"]:
        if asset == name:
            os.mkfifo(private / asset, 0o600)
        else:
            (private / asset).write_bytes((kit / asset).read_bytes())
            (private / asset).chmod(0o600 if asset == "manifest.json" else 0o700)
    monkeypatch.setattr(build, "KIT_ROOT", tmp_path)
    previous = signal.getsignal(signal.SIGALRM)

    def blocked(*args):
        raise RuntimeError("FIFO_OPEN_BLOCKED")

    signal.signal(signal.SIGALRM, blocked)
    signal.alarm(1)
    try:
        with pytest.raises(ValueError, match="(ASSET|MANIFEST)_TYPE"):
            build.verify_open_factory(private)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def test_unsupported_stdin_type_rejects_before_read(monkeypatch):
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.StringIO("unsupported")))
    monkeypatch.setattr(
        gate.select, "select", lambda *a: pytest.fail("unsupported reader selected")
    )
    assert gate._read_go(b"fixed") == 4
