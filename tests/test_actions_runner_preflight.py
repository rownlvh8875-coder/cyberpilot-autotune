"""Read-only metadata and closed manual workflow;never an execution qualification."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/actions_runner_preflight.py"
WORKFLOW = ROOT / ".github/workflows/runner-preflight.yml"
MEMBER = b"0::/user.slice/job.scope\n"
MOUNTS = b"29 24 0:27 / /sys/fs/cgroup rw,nosuid - cgroup2 cgroup rw\n"
GROUP = "/sys/fs/cgroup/user.slice/job.scope"


def _require_linux(record_property):
    if sys.platform != "linux" or not all(
        hasattr(os, key)
        for key in (
            "O_CLOEXEC",
            "O_NOFOLLOW",
            "O_NONBLOCK",
            "getuid",
            "getgid",
            "mkfifo",
        )
    ):
        record_property("host_observation", "UNAVAILABLE_NOT_KERNEL_PASS")
        record_property("unavailable", "LINUX_FILE_TEST_UNAVAILABLE")
        return False
    return True


def api():
    assert SOURCE.is_file(), "read-only collector artifact not implemented"
    spec = importlib.util.spec_from_file_location("draft_runner_preflight", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_kernel(m, monkeypatch, *, member=MEMBER, mounts=MOUNTS, procs=b"4242\n"):
    # OS/proc reads are external to these pure parsing tests. Keep complete
    # literal pseudo-files;real descriptor behavior is exercised separately.
    files = {
        "/proc/self/cgroup": member,
        "/proc/self/mountinfo": mounts,
        GROUP + "/cgroup.procs": procs,
        GROUP + "/cpu.max": b"400000 100000\n",
        GROUP + "/memory.max": b"0\n",
        GROUP + "/pids.max": b"max\n",
        GROUP + "/cgroup.controllers": b"cpu memory pids\n",
        GROUP + "/cgroup.subtree_control": b"\n",
        GROUP + "/cgroup.type": b"domain\n",
        GROUP + "/cgroup.max.depth": None,
        GROUP + "/cgroup.max.descendants": b"max\n",
    }
    monkeypatch.setattr(m, "_read", lambda path, limit: files.get(path))
    monkeypatch.setattr(m.os, "getpid", lambda: 4242)
    monkeypatch.setattr(
        m,
        "_metadata",
        lambda path: {"uid": 0, "gid": 0, "mode": "0755", "effective_write_access": False},
    )
    return files


@pytest.mark.parametrize(
    "member,mounts,want",
    [
        (MEMBER, MOUNTS, GROUP),
        (b"0::/\n", MOUNTS, "/sys/fs/cgroup"),
        (None, MOUNTS, None),
        (MEMBER, None, None),
        (b"0::/../escape\n", MOUNTS, None),
        (b"0::/a//b\n", MOUNTS, None),
        (b"0::/a/./b\n", MOUNTS, None),
        (b"0::/bad\\040name\n", MOUNTS, None),
        (b"0::/bad\xff\n", MOUNTS, None),
        (b"0::/a\n0::/b\n", MOUNTS, None),
        (b"1:cpu:/a\n", MOUNTS, None),
        (MEMBER, MOUNTS.replace(b" / /sys", b" /.. /sys"), None),
        (MEMBER, MOUNTS + MOUNTS, None),
        (MEMBER, b"invalid\n", None),
        (MEMBER, b"1 - cgroup2 cgroup rw\n", None),
        (MEMBER, MOUNTS.replace(b"/sys/fs/cgroup", b"/other"), None),
    ],
)
def test_cgroup_mapping_never_guesses_namespace_root(member, mounts, want):
    assert api()._location(member, mounts) == want


def test_membership_and_zero_limits_are_observations_not_private_budgets(monkeypatch):
    m = api()
    fixture_kernel(m, monkeypatch)
    value = m._cgroup()
    assert value["status"] == "MEMBERSHIP_OBSERVED_NOT_DELEGATION"
    assert value["membership_confirmed"] is True and value["atomic"] is False
    assert value["controls"]["memory.max"]["value"] == "0"
    assert value["controls"]["cgroup.max.depth"]["value"] is None
    assert value["controls"]["cgroup.subtree_control"]["value"] == ""
    assert value["controls"]["cpu.max"]["metadata"]["effective_write_access"] is False
    assert value["write_delegation_verified"] is False
    assert GROUP not in json.dumps(value)


@pytest.mark.parametrize("procs,want", [(None, None), (b"99\n", False), (b"garbage\n", None)])
def test_missing_or_wrong_pid_cannot_bind_cgroup_cohort(monkeypatch, procs, want):
    m = api()
    fixture_kernel(m, monkeypatch, procs=procs)
    value = m._cgroup()
    assert value["status"] == "UNAVAILABLE_MEMBERSHIP"
    assert value["membership_confirmed"] is want
    assert value["controls"] is None


@pytest.mark.parametrize("changed", ["member", "mount", "pid"])
def test_cgroup_cohort_drift_discards_control_snapshot(monkeypatch, changed):
    m = api()
    files = fixture_kernel(m, monkeypatch)
    counts = {}

    def changing(path, limit):
        counts[path] = counts.get(path, 0) + 1
        if counts[path] > 1:
            if changed == "member" and path == "/proc/self/cgroup":
                return b"0::/another\n"
            if changed == "mount" and path == "/proc/self/mountinfo":
                return MOUNTS + b"30 24 0:28 / /other rw - tmpfs tmpfs rw\n"
            if changed == "pid" and path == GROUP + "/cgroup.procs":
                return b"99\n"
        return files.get(path)

    monkeypatch.setattr(m, "_read", changing)
    value = m._cgroup()
    assert value["status"] == "UNAVAILABLE_COHORT_DRIFT"
    assert value["controls"] is None and value["membership_confirmed"] is None


def test_unmappable_root_does_not_read_root_limits(monkeypatch):
    m = api()
    seen = []

    def read(path, limit):
        seen.append(path)
        return MEMBER if path == "/proc/self/cgroup" else MOUNTS.replace(b" / /sys", b" /.. /sys")

    monkeypatch.setattr(m, "_read", read)
    value = m._cgroup()
    assert value["status"] == "UNAVAILABLE_MAPPING"
    assert seen == ["/proc/self/cgroup", "/proc/self/mountinfo"]


@pytest.mark.parametrize("bad", [b"SECRET_TOKEN\n::warning::bad", b"\xff", b"a" * 1025])
def test_hostile_control_text_is_not_emitted(monkeypatch, bad):
    m = api()
    files = fixture_kernel(m, monkeypatch)
    files[GROUP + "/cpu.max"] = bad
    value = m._cgroup()
    assert value["controls"]["cpu.max"]["value"] is None
    assert "SECRET_TOKEN" not in json.dumps(value) and "::warning::" not in json.dumps(value)


@pytest.mark.parametrize(
    "name,raw",
    [
        ("cpu.max", b"SECRET_TOKEN\n"),
        ("cpu.max", b"max 0\n"),
        ("cpu.max", b"0 100000\n"),
        ("cpu.max", b"-1 100000\n"),
        ("cpu.max", b"max\n"),
        ("cpu.max", b"\n"),
        ("cpu.max", b"1 100000 extra\n"),
        ("cpu.max", b"01 100000\n"),
        ("memory.max", b"SECRET_TOKEN\n"),
        ("memory.max", b"-1\n"),
        ("memory.max", b"\n"),
        ("memory.max", b"max 0\n"),
        ("memory.max", b"1.5\n"),
        ("memory.max", b"01\n"),
        ("pids.max", b"SECRET_TOKEN\n"),
        ("pids.max", b"NaN\n"),
        ("cgroup.max.depth", b"-1\n"),
        ("cgroup.max.descendants", b"SECRET_TOKEN\n"),
        ("cgroup.controllers", b"SECRET_TOKEN\n"),
        ("cgroup.controllers", b"unknown\n"),
        ("cgroup.controllers", b"cpu cpu\n"),
        ("cgroup.subtree_control", b"cpu SECRET_TOKEN\n"),
        ("cgroup.subtree_control", b"+cpu\n"),
        ("cgroup.type", b"SECRET_TOKEN\n"),
        ("cgroup.type", b"domain unknown\n"),
        ("cgroup.type", b"\n"),
    ],
)
def test_printable_malformed_controls_are_unavailable_in_confirmed_cohort(monkeypatch, name, raw):
    m = api()
    files = fixture_kernel(m, monkeypatch)
    files[GROUP + "/" + name] = raw
    value = m._cgroup()
    assert value["status"] == "MEMBERSHIP_OBSERVED_NOT_DELEGATION"
    assert value["controls"][name]["value"] is None
    assert "SECRET_TOKEN" not in json.dumps(value)


@pytest.mark.parametrize(
    "name,value",
    [
        ("cpu.max", "max 100000"),
        ("cpu.max", "400000 100000"),
        ("memory.max", "0"),
        ("memory.max", "1024"),
        ("memory.max", "max"),
        ("pids.max", "0"),
        ("pids.max", "10"),
        ("pids.max", "max"),
        ("cgroup.max.depth", "0"),
        ("cgroup.max.depth", "2"),
        ("cgroup.max.depth", "max"),
        ("cgroup.max.descendants", "0"),
        ("cgroup.max.descendants", "max"),
        ("cgroup.type", "domain"),
        ("cgroup.type", "domain threaded"),
        ("cgroup.type", "domain invalid"),
        ("cgroup.type", "threaded"),
        ("cgroup.controllers", ""),
        ("cgroup.controllers", "cpu memory pids"),
        ("cgroup.controllers", "cpuset io hugetlb rdma misc dmem"),
        ("cgroup.subtree_control", ""),
        ("cgroup.subtree_control", "cpu memory"),
    ],
)
def test_control_grammar_preserves_valid_zero_max_type_and_controller_lists(
    monkeypatch, name, value
):
    m = api()
    monkeypatch.setattr(m, "_read", lambda path, limit: (value + "\n").encode())
    monkeypatch.setattr(m, "_metadata", lambda path: None)
    assert m._control(GROUP + "/" + name)["value"] == value


def test_unregistered_control_cannot_emit_text(monkeypatch):
    m = api()
    monkeypatch.setattr(m, "_read", lambda path, limit: b"SECRET_TOKEN\n")
    monkeypatch.setattr(m, "_metadata", lambda path: None)
    assert m._control(GROUP + "/unregistered")["value"] is None


def test_nofollow_bounded_reader_rejects_fifo_symlink_and_oversize(tmp_path, record_property):
    if not _require_linux(record_property):
        return
    m = api()
    regular = tmp_path / "regular"
    regular.write_bytes(b"abc")
    assert m._read(str(regular), 3) == b"abc"
    assert m._read(str(regular), 2) is None
    assert m._read(str(tmp_path / "absent"), 3) is None
    assert m._read(str(tmp_path), 3) is None
    link = tmp_path / "link"
    link.symlink_to(regular)
    assert m._read(str(link), 3) is None
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    assert m._read(str(fifo), 3) is None
    # proc reports st_size=0;the streaming cap must still reject extra bytes.
    assert m._read("/proc/self/status", 1) is None


def test_metadata_access_check_is_not_defaulted_to_false(tmp_path, monkeypatch, record_property):
    if not _require_linux(record_property):
        return
    m = api()
    actual = m._metadata(str(tmp_path))
    assert actual["uid"] == os.getuid() and actual["effective_write_access"] is True
    assert m._metadata(str(tmp_path / "absent")) is None
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    assert m._metadata(str(link)) is None

    def unavailable(*args, **kwargs):
        raise NotImplementedError

    monkeypatch.setattr(m.os, "access", unavailable)
    assert m._metadata(str(tmp_path))["effective_write_access"] is None


def test_binary_pin_reports_hash_not_raw_contents(tmp_path, monkeypatch, record_property):
    if not _require_linux(record_property):
        return
    m = api()
    binary = tmp_path / "toy"
    binary.write_bytes(b"abc")
    monkeypatch.setattr(
        m,
        "_PINS",
        (
            (str(binary), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
            (str(tmp_path / "missing"), "0" * 64),
        ),
    )
    value = m._tools()
    assert value[str(binary)]["pin_matches"] is True
    assert value[str(tmp_path / "missing")]["pin_matches"] is None
    binary.write_bytes(b"changed")
    assert m._tools()[str(binary)]["pin_matches"] is False


def test_security_zero_is_not_unavailable(monkeypatch):
    m = api()
    monkeypatch.setattr(
        m,
        "_read",
        lambda path, limit: (
            b"CapEff:\t0000000000000000\nNoNewPrivs:\t0\nSeccomp:\t2\nName:\tSECRET_TOKEN\n"
        ),
    )
    assert m._security() == {"CapEff": "0000000000000000", "NoNewPrivs": 0, "Seccomp": 2}
    monkeypatch.setattr(
        m, "_read", lambda path, limit: b"CapEff: secret\nNoNewPrivs: 9\nSeccomp: nan\n"
    )
    assert m._security() == {"CapEff": None, "NoNewPrivs": None, "Seccomp": None}
    monkeypatch.setattr(m, "_read", lambda path, limit: None)
    assert m._security() == {"CapEff": None, "NoNewPrivs": None, "Seccomp": None}
    monkeypatch.setattr(m, "_read", lambda path, limit: b"\xff")
    assert m._security() == {"CapEff": None, "NoNewPrivs": None, "Seccomp": None}
    monkeypatch.setattr(m, "_read", lambda path, limit: b"CapEff: 0\nCapEff: 1\n")
    assert m._security() == {"CapEff": None, "NoNewPrivs": None, "Seccomp": None}


def test_context_allowlist_does_not_read_credentials(monkeypatch):
    m = api()

    class ClosedEnvironment:
        def get(self, name):
            return {
                "GITHUB_ACTIONS": "true",
                "GITHUB_REPOSITORY": "rownlvh8875-coder/cyberpilot-autotune",
                "GITHUB_RUN_ID": "123",
                "GITHUB_RUN_ATTEMPT": "1",
                "GITHUB_SHA": "a" * 40,
            }[name]

    monkeypatch.setattr(m, "os", SimpleNamespace(environ=ClosedEnvironment()))
    assert m._context() == {
        "actions": True,
        "repository": "rownlvh8875-coder/cyberpilot-autotune",
        "run_id": "123",
        "run_attempt": "1",
        "sha": "a" * 40,
        "trust": "UNVERIFIED_CALLER_METADATA",
    }


@pytest.mark.parametrize("value", ["SECRET_TOKEN\n::warning::bad", "", "-1", "a" * 1000])
def test_invalid_action_context_is_unavailable(monkeypatch, value):
    m = api()
    monkeypatch.setattr(m, "os", SimpleNamespace(environ=SimpleNamespace(get=lambda name: value)))
    assert m._context() == {
        "actions": None,
        "repository": None,
        "run_id": None,
        "run_attempt": None,
        "sha": None,
        "trust": "UNVERIFIED_CALLER_METADATA",
    }


def test_identity_and_native_absence_have_no_fallback(monkeypatch):
    m = api()
    monkeypatch.setattr(m, "os", SimpleNamespace(getuid=lambda: 0))
    assert m._identity("getuid") == 0 and m._identity("getgid") is None
    monkeypatch.setattr(
        m,
        "importlib",
        SimpleNamespace(import_module=lambda name: (_ for _ in ()).throw(ImportError(name))),
    )
    assert m._native()["fcntl"] == {"module_available": False, "required_apis_present": None}
    monkeypatch.setattr(
        m, "importlib", SimpleNamespace(import_module=lambda name: SimpleNamespace())
    )
    assert m._native()["resource"] == {"module_available": True, "required_apis_present": False}
    monkeypatch.setattr(m, "os", SimpleNamespace(getuid=lambda: -1))
    assert m._identity("getuid") is None


def test_collect_never_turns_observations_into_authority(monkeypatch):
    m = api()
    monkeypatch.setenv("HF_TOKEN", "SECRET_TOKEN_MUST_NOT_LEAK")
    value = m.collect()
    assert value["schema"] == "actions-runner-preflight-v1"
    assert value["status"] == "READ_ONLY_OBSERVATION_NOT_QUALIFICATION"
    assert value["global_status"] == "BLOCKED" and value["execution_verdict"] == "NOT_EVALUATED"
    assert value["atomic"] is False and value["H_executed"] is False
    assert value["aggregate_resource_boundary_qualified"] is False
    assert len(value["permissions"]) == 9 and all(v is False for v in value["permissions"].values())
    encoded = json.dumps(value, allow_nan=False)
    assert len(encoded.encode()) <= 32768 and "SECRET_TOKEN_MUST_NOT_LEAK" not in encoded


def test_inert_import_and_collection_have_no_mutation_or_native_probes(tmp_path):
    assert SOURCE.is_file(), "read-only collector artifact not implemented"
    script = r"""
import sys,os,runpy,json
def deny(*args,**kwargs):raise AssertionError('native allocation probe')
os.memfd_create=os.pidfd_open=deny
def guard(event,args):
 if event.startswith(('subprocess.','socket.','ctypes.','os.exec','os.fork')):
  raise AssertionError(event)
 if event in {'os.mkdir','os.remove','os.rename','os.chmod','os.chown','os.rmdir',
  'os.link','os.symlink','os.system','os.truncate','resource.setrlimit'}:
  raise AssertionError(event)
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  raise AssertionError(event)
sys.addaudithook(guard)
m=runpy.run_path(sys.argv[1])
value=m['collect']()
assert not any(value['permissions'].values())
assert not any(n.startswith(('cyberpilot_autotune','tests.audit_compatibility_executor'))
 for n in sys.modules)
print('READ_ONLY_COLLECTOR')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-S", "-c", script, str(SOURCE)],
        cwd=tmp_path,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == b"READ_ONLY_COLLECTOR" and list(tmp_path.iterdir()) == []


def test_closed_cli_outputs_one_json_line_and_rejects_arguments(tmp_path):
    assert SOURCE.is_file(), "read-only collector artifact not implemented"
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-S", str(SOURCE)],
        cwd=tmp_path,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0 and result.stderr == b"", result.stderr
    assert len(result.stdout.splitlines()) == 1
    assert json.loads(result.stdout)["execution_verdict"] == "NOT_EVALUATED"
    bad = subprocess.run(
        [sys.executable, "-I", "-B", "-S", str(SOURCE), "--execute"],
        capture_output=True,
        timeout=15,
    )
    assert bad.returncode == 2 and bad.stdout == bad.stderr == b""
    assert list(tmp_path.iterdir()) == []


def test_main_checks_output_bound_and_nonfinite_before_success(monkeypatch, capsys):
    m = api()
    monkeypatch.setattr(sys, "argv", ["-"])
    assert m.main() == 0
    assert json.loads(capsys.readouterr().out)["execution_verdict"] == "NOT_EVALUATED"
    monkeypatch.setattr(sys, "argv", ["-", "--execute"])
    assert m.main() == 2 and capsys.readouterr().out == ""
    monkeypatch.setattr(sys, "argv", ["-"])
    monkeypatch.setattr(m, "collect", lambda: {"unexpected": "x" * 32769})
    assert m.main() == 2 and capsys.readouterr().out == ""
    monkeypatch.setattr(m, "collect", lambda: {"unexpected": float("nan")})
    with pytest.raises(ValueError):
        m.main()
    assert capsys.readouterr().out == ""


def test_unsupported_uname_and_cli_entry_remain_diagnostic(monkeypatch, capsys):
    import runpy

    m = api()

    def unavailable():
        raise AttributeError

    monkeypatch.setattr(m.os, "uname", unavailable, raising=False)
    assert m.collect()["host"]["system"] is None
    monkeypatch.setattr(sys, "argv", ["-"])
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(SOURCE), run_name="__main__")
    assert (
        result.value.code == 0 and json.loads(capsys.readouterr().out)["global_status"] == "BLOCKED"
    )


def _workflow_run(text):
    # Deliberately accept one complete,reviewed YAML form,not arbitrary YAML.
    # No CI dependency on a local system Python/PyYAML or platform-specific path.
    head = (
        'name: Read-only runner preflight (unregistered draft)\n"on":\n'
        "  workflow_dispatch:\npermissions: {}\njobs:\n  observe:\n"
        "    runs-on: ubuntu-24.04\n    timeout-minutes: 2\n    permissions: {}\n"
        "    steps:\n      - name: Observe without executing a workload\n"
        "        shell: bash\n        run: |\n"
    )
    command = "python3 -I -B -S - <<'PY'\n" + SOURCE.read_text() + "PY\n"
    expected = head + "".join(
        "          " + line if line.strip("\n") else line
        for line in command.splitlines(keepends=True)
    )
    assert text == expected, "workflow capability or inline-source expansion"
    return command


def workflow_run():
    assert WORKFLOW.is_file(), "manual workflow not registered locally"
    assert SOURCE.is_file(), "frozen standalone collector not adopted"
    return _workflow_run(WORKFLOW.read_text())


def test_workflow_can_only_observe_on_manual_dispatch_without_credentials():
    run = workflow_run()
    assert "${{" not in run


def test_workflow_executes_exact_frozen_collector_not_checkout_source(tmp_path):
    run = workflow_run()
    prefix = "python3 -I -B -S - <<'PY'\n"
    assert run.startswith(prefix) and run.endswith("PY\n")
    body = run[len(prefix) : -3]
    assert body == SOURCE.read_text()
    # Exercise the extracted body on every OS,not a parser/text-only assertion.
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-S", "-"],
        input=body.encode(),
        cwd=tmp_path,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0 and result.stderr == b"", result.stderr
    assert len(result.stdout.splitlines()) == 1 and len(result.stdout) <= 32768
    value = json.loads(result.stdout)
    assert value["execution_verdict"] == "NOT_EVALUATED" and value["global_status"] == "BLOCKED"
    assert not any(value["permissions"].values())
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "change", ["trigger", "permission", "action", "inline", "job", "expression"]
)
def test_workflow_capability_mutations_are_rejected(change):
    assert WORKFLOW.is_file(), "manual workflow not registered locally"
    original = WORKFLOW.read_text()
    altered = {
        "trigger": original.replace("  workflow_dispatch:\n", "  push:\n  workflow_dispatch:\n", 1),
        "permission": original.replace("permissions: {}", "permissions: write-all", 1),
        "action": original.replace(
            "    steps:\n", "    steps:\n      - uses: actions/checkout@v4\n", 1
        ),
        "inline": original.replace("READ_ONLY_OBSERVATION_NOT_QUALIFICATION", "READY", 1),
        "job": original + "  extra:\n    runs-on: ubuntu-latest\n",
        "expression": original.replace("python3 -I", "${{ inputs.command }} -I", 1),
    }[change]
    assert altered != original
    with pytest.raises(AssertionError, match="workflow capability"):
        _workflow_run(altered)


def test_linux_bash_wrapper_is_only_a_read_only_observation(tmp_path, record_property):
    if not _require_linux(record_property):
        return
    bash = shutil.which("bash")
    if bash is None:
        record_property("host_observation", "UNAVAILABLE_NOT_KERNEL_PASS")
        record_property("unavailable", "BASH_TEST_UNAVAILABLE")
        return
    run = workflow_run()
    syntax = subprocess.run([bash, "-n"], input=run.encode(), capture_output=True, timeout=5)
    assert syntax.returncode == 0, syntax.stderr
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", run],
        cwd=tmp_path,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0 and result.stderr == b"", result.stderr
    assert len(result.stdout.splitlines()) == 1
    assert json.loads(result.stdout)["execution_verdict"] == "NOT_EVALUATED"
    assert list(tmp_path.iterdir()) == []


def test_native_observations_never_prepare_on_unsupported_host(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    recorded = []

    def record(key, value):
        recorded.append((key, value))

    def forbidden():
        pytest.fail("native test loaded/prepared collector before host gate")

    monkeypatch.setattr(sys.modules[__name__], "api", forbidden)
    test_nofollow_bounded_reader_rejects_fifo_symlink_and_oversize(object(), record)
    test_metadata_access_check_is_not_defaulted_to_false(object(), monkeypatch, record)
    test_binary_pin_reports_hash_not_raw_contents(object(), monkeypatch, record)
    test_linux_bash_wrapper_is_only_a_read_only_observation(object(), record)
    assert (
        recorded
        == [
            ("host_observation", "UNAVAILABLE_NOT_KERNEL_PASS"),
            ("unavailable", "LINUX_FILE_TEST_UNAVAILABLE"),
        ]
        * 4
    )
