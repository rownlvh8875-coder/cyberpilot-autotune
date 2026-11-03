"""Closed owned-toy launcher. No arbitrary command/source/FD API and no H bridge."""

import hashlib
import importlib
import json
import os
import platform
import signal
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from .contracts import SyntheticCase, SyntheticRequest, SyntheticResult, _result
from .seccomp import seccomp_bytes

_PYTHON_HOME = "/opt/codex/runtimes/codex-primary-runtime/dependencies/python"
_PYTHON = _PYTHON_HOME + "/bin/python3.12"
_PINNED = (
    ("/usr/bin/bwrap", "573236e5328ac2ebb08f59ae3a9805b4f8d12bdef14be8af4450d5463294985f"),
    ("/usr/bin/setpriv", "f7cedc63bbc1df7912b343a1240a77d16db7633563d69897ec8ad2a99c24024b"),
    (_PYTHON, "fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7"),
)
_CANARY = b"SYNTHETIC_ONLY_PROTECTED_V1\n"
# Linux UAPI F_LINUX_SPECIFIC_BASE(1024)+9/+10. This pinned Python omits
# the names,not the fcntl syscall. Failure to apply/verify still fails closed.
_F_ADD_SEALS = 1033
_F_GET_SEALS = 1034


def _payload_source() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures/h1_synthetic_payload.py"


def _source_hashes() -> dict[str, str]:
    directory = Path(__file__).resolve().parent
    files = [
        directory / name
        for name in ("__init__.py", "contracts.py", "seccomp.py", "runner.py", "supervision.py")
    ]
    files.append(_payload_source())
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def _child_environment() -> dict[str, str]:
    # Offline children do not consume outbound identities. Keep proxy/CA guards,
    # never copy the ambient environment or token/auth-header bindings.
    result = {"LANG": "C.UTF-8"}
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    ):
        if name in os.environ:
            value = os.environ[name]
            if name.lower().endswith("proxy") and name.lower() != "no_proxy":
                parsed = urlsplit(value)
                if (
                    parsed.scheme not in ("http", "https")
                    or not parsed.hostname
                    or parsed.username is not None
                    or parsed.password is not None
                    or parsed.path not in ("", "/")
                    or parsed.query
                    or parsed.fragment
                    or value != value.strip()
                ):
                    raise ValueError("CREDENTIAL_FREE_GUARD_INCOMPATIBLE")
                # Reading port also rejects ambiguous/non-numeric/out-of-range
                # authorities. Never normalize a credential-bearing bare string.
                _ = parsed.port
            result[name] = value
    return result


def _sealed_filter() -> int:
    import fcntl

    fd = os.memfd_create("h1-S-only-filter", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        raw = seccomp_bytes()
        if os.write(fd, raw) != len(raw):
            raise OSError("short filter write")
        os.lseek(fd, 0, os.SEEK_SET)
        fcntl.fcntl(fd, _F_ADD_SEALS, 15)
        if fcntl.fcntl(fd, _F_GET_SEALS) != 15:
            raise OSError("missing filter seals")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _preflight() -> tuple[str, ...]:
    # This is still one exact Linux profile,not a portable execution backend.
    # Unsupported hosts must not probe handles,prepare artifacts or spawn.
    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    if (
        platform.system() != "Linux"
        or platform.machine() != "x86_64"
        or getuid is None
        or getgid is None
        or (getuid(), getgid()) != (1000, 1000)
    ):
        return ("UNSUPPORTED_HOST",)
    missing = []
    for path, expected in _PINNED:
        try:
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                missing.append("TOOL_PIN_MISMATCH")
        except OSError:
            missing.append("TOOL_PIN_UNAVAILABLE")
    try:
        _source_hashes()
        _child_environment()
        # Check both native modules before even allocating a sealed filter.
        # Inert imports and pure protocol/value tests need neither module.
        native_fcntl = importlib.import_module("fcntl")
        native_resource = importlib.import_module("resource")
        # Resolve required native APIs before allocating handles. This does not
        # apply worker limits or claim these controls work on an untested host.
        _ = (
            os.memfd_create,
            os.MFD_CLOEXEC,
            os.MFD_ALLOW_SEALING,
            os.pidfd_open,
            native_fcntl.fcntl,
            native_fcntl.F_GETFL,
            native_resource.setrlimit,
            native_resource.RLIMIT_CPU,
            native_resource.RLIMIT_AS,
            native_resource.RLIMIT_FSIZE,
            native_resource.RLIMIT_NOFILE,
            native_resource.RLIMIT_CORE,
        )
        if not hasattr(os, "P_PIDFD") or not hasattr(signal, "pidfd_send_signal"):
            missing.append("PIDFD_UNAVAILABLE")
        else:
            fd = _sealed_filter()
            os.close(fd)
            fd = os.pidfd_open(os.getpid())
            os.close(fd)
    except (ImportError, OSError, ValueError, AttributeError):
        missing.append("REQUIRED_CONTROL_UNAVAILABLE")
    return tuple(dict.fromkeys(missing))


def _open_directory(path: str) -> int:
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.split("/")[1:]:
            following = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd
            )
            os.close(fd)
            fd = following
        if os.fstat(fd).st_uid != os.getuid():
            raise ValueError("owner directory must belong to caller")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _write_new(directory_fd: int, name: str, raw: bytes) -> None:
    fd = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
        dir_fd=directory_fd,
    )
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(raw)
    finally:
        os.close(fd)


def _prepare(owner: str) -> str:
    SyntheticRequest(SyntheticCase.FD_CLOSED, owner).validate()
    try:
        parent = _open_directory(owner)
    except OSError as error:
        raise ValueError("non-symlink existing owner directory required") from error
    try:
        if os.path.exists(f"/proc/self/fd/{parent}/state.json"):
            raise ValueError("cannot reuse an existing run as owner directory")
        # mkdtemp is anchored to a retained directory handle,not a re-resolved link.
        alias = tempfile.mkdtemp(prefix="h1-S-", dir=f"/proc/self/fd/{parent}")
        name = Path(alias).name
        root = owner + "/" + name
        fd = os.open(
            name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
        )
        try:
            identity = os.fstat(fd)
            if os.stat(root, follow_symlinks=False).st_ino != identity.st_ino:
                raise ValueError("run directory identity changed")
            for child in ("protected", "scratch"):
                os.mkdir(child, mode=0o700, dir_fd=fd)
            protected = os.open(
                "protected", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            try:
                _write_new(protected, "canary", _CANARY)
            finally:
                os.close(protected)
            _write_new(fd, "payload.py", _payload_source().read_bytes())
            _write_new(
                fd,
                "state.json",
                json.dumps(
                    {
                        "schema": "h1-owned-toy-v1",
                        "identity": [identity.st_dev, identity.st_ino],
                        "sources": _source_hashes(),
                    },
                    sort_keys=True,
                ).encode(),
            )
        finally:
            os.close(fd)
        return root
    finally:
        os.close(parent)


def _command(root: str, case: SyntheticCase, filter_fd: int) -> list[str]:
    suffix = "/required-missing" if case is SyntheticCase.MISSING_MOUNT else "/protected"
    protected = root + suffix
    return [
        "/usr/bin/setpriv",
        "--no-new-privs",
        "/usr/bin/bwrap",
        "--unshare-user",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-ipc",
        "--unshare-uts",
        "--uid",
        "1000",
        "--gid",
        "1000",
        "--cap-drop",
        "ALL",
        "--disable-userns",
        "--assert-userns-disabled",
        "--die-with-parent",
        "--new-session",
        "--ro-bind",
        "/usr",
        "/usr",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib64",
        "/lib64",
        "--ro-bind",
        _PYTHON_HOME,
        "/python",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--ro-bind",
        protected,
        "/protected",
        "--ro-bind",
        root + "/payload.py",
        "/payload.py",
        "--ro-bind",
        root + "/identities.json",
        "/identities.json",
        "--bind",
        root + "/scratch",
        "/scratch",
        "--chdir",
        "/scratch",
        "--seccomp",
        str(filter_fd),
        "--",
        "/python/bin/python3.12",
        "-I",
        "-B",
        "-S",
        "/payload.py",
        case.value,
    ]


def run_synthetic(request: SyntheticRequest) -> SyntheticResult:
    if type(request) is not SyntheticRequest:
        raise ValueError("exact SyntheticRequest required")
    request.validate()
    missing = _preflight()
    if missing:
        return _result(request.case, unavailable=missing)
    root = _prepare(request.owner_directory)
    from .supervision import supervise

    result = supervise(request.case, root)
    result.validate()
    return result
