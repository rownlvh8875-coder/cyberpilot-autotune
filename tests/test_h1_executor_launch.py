"""Launch logic versus actual host observations are deliberately separate."""

import importlib
import inspect
import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.audit_compatibility_executor.contracts import SyntheticCase, SyntheticRequest


def runner():
    try:
        return importlib.import_module("tests.audit_compatibility_executor.runner")
    except ModuleNotFoundError:
        pytest.fail("closed owned launcher not implemented")


def _require_host(record_property):
    missing = runner()._preflight()
    if missing:
        record_property("host_observation", "UNAVAILABLE_NOT_KERNEL_PASS")
        record_property("unavailable", missing)
        return False
    return True


def test_required_controls_fail_closed(tmp_path, monkeypatch):
    m = runner()
    monkeypatch.setattr(m, "_preflight", lambda: ("TOOL_PIN_UNAVAILABLE",))
    result = m.run_synthetic(SyntheticRequest(SyntheticCase.FD_CLOSED, "/unused"))
    assert result.outcome == "UNAVAILABLE"
    assert result.run_directory is None and list(tmp_path.iterdir()) == []


def test_no_public_fd_or_argv_override(tmp_path):
    m = runner()
    assert tuple(inspect.signature(m.run_synthetic).parameters) == ("request",)
    with pytest.raises(ValueError):
        m.run_synthetic(object())
    value = SyntheticRequest(SyntheticCase.FD_CLOSED, "/unused")
    object.__setattr__(value, "case", "arbitrary")
    with pytest.raises(ValueError):
        m.run_synthetic(value)
    assert list(tmp_path.iterdir()) == []


def test_fresh_owned_roots_only(tmp_path, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    root = Path(m._prepare(str(tmp_path)))
    assert root.parent == tmp_path and root.stat().st_mode & 0o777 == 0o700
    assert (root / "protected/canary").read_bytes() == b"SYNTHETIC_ONLY_PROTECTED_V1\n"
    assert list((root / "scratch").iterdir()) == []
    assert (root / "payload.py").read_bytes() == m._payload_source().read_bytes()
    second = Path(m._prepare(str(tmp_path)))
    assert second != root
    with pytest.raises(ValueError):
        m._prepare(str(root))
    link = tmp_path / "alias"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        m._prepare(str(link))
    assert (root / "protected/canary").read_bytes() == b"SYNTHETIC_ONLY_PROTECTED_V1\n"


def test_exact_launch_policy(tmp_path, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    import fcntl

    root = m._prepare(str(tmp_path))
    fd = m._sealed_filter()
    try:
        flags = fcntl.fcntl(fd, 1034)  # Linux F_GET_SEALS,independent UAPI value.
        assert flags & 15 == 15
        with pytest.raises(OSError):
            os.write(fd, b"tamper")
        args = m._command(root, SyntheticCase.DIRECTORY_READ_ONLY, fd)
        assert args[:4] == [
            "/usr/bin/setpriv",
            "--no-new-privs",
            "/usr/bin/bwrap",
            "--unshare-user",
        ]
        for flag in (
            "--unshare-pid",
            "--unshare-net",
            "--unshare-ipc",
            "--unshare-uts",
            "--disable-userns",
            "--assert-userns-disabled",
            "--die-with-parent",
            "--new-session",
            "--seccomp",
            "--cap-drop",
        ):
            assert flag in args
        assert args[args.index("--seccomp") + 1] == str(fd)
        assert args[args.index("--") + 1 :] == [
            "/python/bin/python3.12",
            "-I",
            "-B",
            "-S",
            "/payload.py",
            "DIRECTORY_READ_ONLY",
        ]
        assert "--try" not in args and "/workspace" not in args
        assert "/run/docker.sock" not in args and "/var/run/docker.sock" not in args
        assert str(Path(root) / "required-missing") in m._command(
            root, SyntheticCase.MISSING_MOUNT, fd
        )
    finally:
        os.close(fd)


def test_guarded_credential_free_environment(monkeypatch):
    m = runner()
    monkeypatch.setenv("HF_TOKEN", "TEST_ONLY_NOT_A_REAL_SECRET")
    monkeypatch.setenv("PYTHONPATH", "/not-a-trusted-import-root")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy:8080")
    env = m._child_environment()
    assert "HF_TOKEN" not in env and "PYTHONPATH" not in env
    assert env["HTTP_PROXY"] == "http://proxy:8080"
    assert os.environ["HF_TOKEN"] == "TEST_ONLY_NOT_A_REAL_SECRET"
    monkeypatch.setenv("HTTPS_PROXY", "http://user:password@proxy:8080")
    with pytest.raises(ValueError):
        m._child_environment()


def test_preflight_missing_capability_and_bad_pin(monkeypatch):
    m = runner()
    monkeypatch.setattr(m.platform, "machine", lambda: "aarch64")
    assert "UNSUPPORTED_HOST" in m._preflight()
    monkeypatch.setattr(m.platform, "machine", lambda: "x86_64")
    # Pure pin diagnostics,not a host qualification or native API emulation.
    monkeypatch.setattr(m.platform, "system", lambda: "Linux")
    monkeypatch.setattr(m.os, "getuid", lambda: 1000, raising=False)
    monkeypatch.setattr(m.os, "getgid", lambda: 1000, raising=False)
    monkeypatch.setattr(m, "_PINNED", (("/definitely/not/a/tool", "0" * 64),))
    assert "TOOL_PIN_UNAVAILABLE" in m._preflight()
    monkeypatch.setattr(m, "_PINNED", ((str(Path(__file__)), "0" * 64),))
    assert "TOOL_PIN_MISMATCH" in m._preflight()


@pytest.mark.parametrize(
    "module,attribute,reason",
    [
        ("os", "memfd_create", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("os", "MFD_CLOEXEC", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("os", "MFD_ALLOW_SEALING", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("os", "pidfd_open", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("os", "P_PIDFD", "PIDFD_UNAVAILABLE"),
        ("signal", "pidfd_send_signal", "PIDFD_UNAVAILABLE"),
        ("fcntl", "fcntl", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("fcntl", "F_GETFL", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("resource", "setrlimit", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("resource", "RLIMIT_CPU", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("resource", "RLIMIT_AS", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("resource", "RLIMIT_FSIZE", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("resource", "RLIMIT_NOFILE", "REQUIRED_CONTROL_UNAVAILABLE"),
        ("resource", "RLIMIT_CORE", "REQUIRED_CONTROL_UNAVAILABLE"),
    ],
)
def test_missing_native_api_is_diagnosed_before_handles(monkeypatch, module, attribute, reason):
    from types import SimpleNamespace

    m = runner()

    def forbidden(*args, **kwargs):
        pytest.fail("native handle/artifact allocated despite missing control API")

    # Pure dependency-absence test;never changes the real os module or executes
    # a replacement backend. Bad available pin facts must still be retained.
    native = {
        "os": SimpleNamespace(
            getuid=lambda: 1000,
            getgid=lambda: 1000,
            environ=os.environ,
            memfd_create=forbidden,
            pidfd_open=forbidden,
            MFD_CLOEXEC=1,
            MFD_ALLOW_SEALING=2,
            P_PIDFD=3,
        ),
        "signal": SimpleNamespace(pidfd_send_signal=forbidden),
        "fcntl": SimpleNamespace(fcntl=forbidden, F_GETFL=3),
        "resource": SimpleNamespace(
            setrlimit=forbidden,
            RLIMIT_CPU=0,
            RLIMIT_AS=1,
            RLIMIT_FSIZE=2,
            RLIMIT_NOFILE=3,
            RLIMIT_CORE=4,
        ),
    }
    delattr(native[module], attribute)
    monkeypatch.setattr(m.platform, "system", lambda: "Linux")
    monkeypatch.setattr(m.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(m, "os", native["os"])
    monkeypatch.setattr(m, "signal", native["signal"])
    monkeypatch.setattr(m, "importlib", SimpleNamespace(import_module=lambda name: native[name]))
    monkeypatch.setattr(m, "_PINNED", ((str(Path(__file__)), "0" * 64),))
    monkeypatch.setattr(m, "_sealed_filter", forbidden)
    monkeypatch.setattr(m, "_prepare", forbidden)
    result = m.run_synthetic(SyntheticRequest(SyntheticCase.FD_CLOSED, "/unused"))
    assert result.outcome == "UNAVAILABLE" and result.run_directory is None
    assert result.unavailable == ("TOOL_PIN_MISMATCH", reason)


def test_fixture_is_closed_and_inert(tmp_path):
    m = runner()
    module = importlib.import_module("tests.fixtures.h1_synthetic_payload")
    assert module.main(("NOT_REGISTERED",)) == 2
    assert module.main(()) == 2
    assert list(tmp_path.iterdir()) == []
    manifest = m._source_hashes()
    assert len(manifest) == 6 and all(len(value) == 64 for value in manifest.values())


def test_no_historical_subject_in_launch(tmp_path, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    root = m._prepare(str(tmp_path))
    state = json.loads((Path(root) / "state.json").read_bytes())
    assert state["schema"] == "h1-owned-toy-v1"
    assert state["sources"] == m._source_hashes()
    assert set(state) == {"schema", "identity", "sources"}


def test_expected_unsafe_fd_control_is_private_and_actually_writes(tmp_path, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    from tests.audit_compatibility_executor.supervision import _collect

    # Deliberate private violation. Only this new test fixture can be overwritten.
    root = tmp_path / "unsafe-owned-control"
    root.mkdir(mode=0o700)
    (root / "protected").mkdir()
    (root / "scratch").mkdir()
    target = root / "control"
    target.write_bytes(b"ORIGINAL_OWNED_CONTROL\n")
    victim = os.open(target, os.O_RDWR)
    value = os.fstat(victim)
    (root / "identities.json").write_text(
        json.dumps(
            {
                "fd": victim,
                "dev": value.st_dev,
                "ino": value.st_ino,
            }
        )
    )
    (root / "payload.py").write_text("""
import json,os
v=json.load(open('/identities.json'))
s=os.fstat(v['fd'])
assert (s.st_dev,s.st_ino)==(v['dev'],v['ino'])
print(os.write(v['fd'],b'OWNED_FD_ESCAPE_CONTROL\\n'),flush=True)
""")
    fd = m._sealed_filter()
    try:
        child = subprocess.Popen(
            m._command(str(root), SyntheticCase.FD_CLOSED, fd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(fd, victim),
            start_new_session=True,
            env=m._child_environment(),
        )
        pidfd = os.pidfd_open(child.pid)
        try:
            out, err, errors, code = _collect(child, pidfd, 2)
            assert child.wait(timeout=2) == 0, err
            assert not errors and out.strip() == b"24"
            assert target.read_bytes().startswith(b"OWNED_FD_ESCAPE_CONTROL\n")
            record_property("control_label", "EXPECTED_UNSAFE_CONTROL_NOT_SAFE_LAUNCH")
        finally:
            os.close(pidfd)
    finally:
        os.close(fd)
        os.close(victim)


def test_filter_rejects_short_write_or_missing_seals(monkeypatch, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    import fcntl

    real = os.write
    monkeypatch.setattr(m.os, "write", lambda fd, raw: 0)
    with pytest.raises(OSError, match="short filter"):
        m._sealed_filter()
    monkeypatch.setattr(m.os, "write", real)
    real_fcntl = fcntl.fcntl
    monkeypatch.setattr(
        fcntl, "fcntl", lambda fd, op, *args: 0 if op == 1034 else real_fcntl(fd, op, *args)
    )
    with pytest.raises(OSError, match="missing filter seals"):
        m._sealed_filter()


def test_owner_identity_and_missing_controls_cannot_be_waived(
    tmp_path, monkeypatch, record_property
):
    m = runner()
    if not _require_host(record_property):
        return
    with pytest.raises(ValueError):
        m._open_directory("/usr")
    monkeypatch.setattr(m, "_sealed_filter", lambda: (_ for _ in ()).throw(OSError("UNSUPPORTED")))
    assert "REQUIRED_CONTROL_UNAVAILABLE" in m._preflight()
    monkeypatch.setattr(m, "_sealed_filter", lambda: os.open("/dev/null", os.O_RDONLY))
    monkeypatch.delattr(m.os, "P_PIDFD")
    assert "PIDFD_UNAVAILABLE" in m._preflight()


def test_observed_launch_roles_include_access_flags(tmp_path, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    result = m.run_synthetic(SyntheticRequest(SyntheticCase.FD_CLOSED, str(tmp_path)))
    assert result.outcome == "SYNTHETIC_OBSERVATION_COMPLETE", result
    launch = json.loads((Path(result.run_directory) / "launch.json").read_bytes())
    roles = {v["role"]: v for v in launch["roles"]}
    assert roles["stdin_null"]["access_mode"] == os.O_RDONLY
    assert roles["seccomp_sealed"]["access_mode"] == os.O_RDWR
    assert launch["filter_seals"] == 15


def test_changed_fresh_root_identity_is_rejected(tmp_path, monkeypatch, record_property):
    m = runner()
    if not _require_host(record_property):
        return
    real = os.stat

    def drift(path, **kwargs):
        value = real(path, **kwargs)
        if str(path).startswith(str(tmp_path) + "/h1-S-"):
            from types import SimpleNamespace

            return SimpleNamespace(st_ino=value.st_ino + 1)
        return value

    monkeypatch.setattr(m.os, "stat", drift)
    with pytest.raises(ValueError, match="identity changed"):
        m._prepare(str(tmp_path))


@pytest.mark.parametrize(
    "value",
    [
        "synthetic-user:TEST_ONLY_PASSWORD@proxy.invalid:8080",
        "//synthetic-user:TEST_ONLY_PASSWORD@proxy.invalid:8080",
        "proxy.invalid:8080",
        "http://proxy.invalid:8080/?token=TEST_ONLY_PASSWORD",
        "http://proxy.invalid:8080/#TEST_ONLY_PASSWORD",
        "http://proxy.invalid:badport",
    ],
)
def test_ambiguous_or_credential_bearing_proxy_is_unavailable_before_effects(
    tmp_path, monkeypatch, value
):
    m = runner()
    monkeypatch.setenv("HTTP_PROXY", value)
    # The parser itself must reject this even on a host that cannot execute S.
    with pytest.raises(ValueError):
        m._child_environment()
    result = m.run_synthetic(SyntheticRequest(SyntheticCase.FD_CLOSED, "/unused"))
    assert result.outcome == "UNAVAILABLE"
    assert list(tmp_path.iterdir()) == [] and result.run_directory is None
    assert value == os.environ["HTTP_PROXY"]


def test_host_observations_never_launch_unpinned_tools(tmp_path, monkeypatch):
    m = runner()
    monkeypatch.setattr(m, "_preflight", lambda: ("TOOL_PIN_UNAVAILABLE",))
    recorded = []

    def unexpected(*args, **kwargs):
        pytest.fail("host payload launched despite missing registered controls")

    monkeypatch.setattr(
        m.subprocess if hasattr(m, "subprocess") else subprocess, "Popen", unexpected
    )
    test_expected_unsafe_fd_control_is_private_and_actually_writes(
        tmp_path, lambda key, value: recorded.append((key, value))
    )
    test_observed_launch_roles_include_access_flags(
        tmp_path, lambda key, value: recorded.append((key, value))
    )

    def property_record(key, value):
        recorded.append((key, value))

    test_exact_launch_policy(tmp_path, property_record)
    test_filter_rejects_short_write_or_missing_seals(monkeypatch, property_record)
    test_owner_identity_and_missing_controls_cannot_be_waived(
        tmp_path, monkeypatch, property_record
    )
    test_fresh_owned_roots_only(tmp_path, property_record)
    test_no_historical_subject_in_launch(tmp_path, property_record)
    test_changed_fresh_root_identity_is_rejected(tmp_path, monkeypatch, property_record)
    assert (
        recorded
        == [
            ("host_observation", "UNAVAILABLE_NOT_KERNEL_PASS"),
            ("unavailable", ("TOOL_PIN_UNAVAILABLE",)),
        ]
        * 8
    )
    assert list(tmp_path.iterdir()) == []
