"""Fixed private build kit; no unit or payload execution on import."""

import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT_ROOT = ROOT.parent / "real-cgroup-lab-logs"
SOURCES = (
    "research/real_cgroup/build.py",
    "research/real_cgroup/gate.py",
    "research/real_cgroup/lab.py",
    "research/real_cgroup/factory.c",
    "research/real_cgroup/scope.c",
    "research/real_cgroup/normal.c",
    "research/real_cgroup/__init__.py",
    "src/native_e_lab/domain_supervisor.c",
    "src/native_e_lab/supervisor.c",
    "research/domain_cohort/internal.h",
    "research/domain_cohort/policy.c",
    "research/domain_cohort/peer.c",
    "research/domain_cohort/worker.c",
    "research/worker_entry/integration.c",
    "research/worker_entry/entry_credential.c",
    "research/worker_entry/entry_credential.h",
    "research/worker_entry/fixed_worker.c",
    "research/credential_seal/seal.c",
    "research/credential_seal/seal.h",
    "research/parent_handoff/handoff.c",
    "research/cohort_integration/cohort.c",
    "research/factory_manager/factory.c",
    "research/factory_manager/request.c",
    "research/factory_manager/internal.h",
    "research/factory_manager/sdbus_abi.h",
    "tests/native/cohort_manager.c",
    "tests/native/factory_fake_manager.c",
    "tests/native/worker_entry_credential_shim.c",
    "src/native_e_lab/gate.py",
    "src/native_e_lab/domain_gate.py",
    "src/native_e_lab/lab.py",
)
DOMAIN_PIN = "e19ebd8c77df6bb47fdb1dd5e3561ee4caacb0e8515a946e78c14bdbc078898b"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def _source_snapshot() -> dict[str, bytes]:
    data: dict[str, bytes] = {}
    for name in SOURCES:
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("SOURCE_PATH")
        data[name] = path.read_bytes()
    return data


def build_fixed_kit() -> Path:
    if os.geteuid() == 0:
        raise ValueError("ROOT")
    folder = Path(tempfile.mkdtemp(prefix="kit-", dir=KIT_ROOT))
    before = _source_snapshot()
    source_name = "src/native_e_lab/domain_supervisor.c"
    if hashlib.sha256(before[source_name]).hexdigest() != DOMAIN_PIN:
        raise ValueError("LEGACY_SOURCE_DRIFT")
    original = before[source_name].decode()
    snapshot = folder / "sources"
    for name, data in before.items():
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o400)
    if original.count("int main(int argc, char **argv)") != 1:
        raise ValueError("SOURCE_ENTRY")
    for name, entry in [
        ("domain_reference.c", "dr_reference_main"),
        ("scope_reference.c", "rl_scope_reference_main"),
    ]:
        reference = original.replace(
            "int main(int argc, char **argv)", f"int {entry}(int argc, char **argv)"
        )
        if name == "scope_reference.c":
            reference = reference.replace("direct_supervisor_main", "rl_scope_direct_reference")
        (folder / name).write_text(reference)
    cc = [
        "/usr/bin/cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(folder),
        "-I",
        str(snapshot / "src/native_e_lab"),
    ]
    commands = [
        cc
        + [
            "-nostdlib",
            "-static",
            "-fno-pie",
            "-no-pie",
            "-fno-stack-protector",
            "-fno-builtin",
            "-Wl,-e,_start",
            str(snapshot / "research/domain_cohort/worker.c"),
            "-o",
            str(folder / "fixed-worker"),
        ],
        cc
        + [
            "-Dsyscall=entry_test_syscall",
            "-c",
            str(snapshot / "research/worker_entry/entry_credential.c"),
            "-o",
            str(folder / "credential.o"),
        ],
        cc
        + [
            str(snapshot / "research/real_cgroup/factory.c"),
            str(snapshot / "research/real_cgroup/scope.c"),
            str(snapshot / "research/real_cgroup/normal.c"),
            str(snapshot / "tests/native/cohort_manager.c"),
            str(snapshot / "research/domain_cohort/peer.c"),
            str(snapshot / "research/domain_cohort/policy.c"),
            str(snapshot / "tests/native/worker_entry_credential_shim.c"),
            str(folder / "credential.o"),
            str(snapshot / "research/factory_manager/request.c"),
            "-l:libsystemd.so.0",
            "-o",
            str(folder / "cohort"),
        ],
    ]
    results = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        results.append(
            {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if result.returncode:
            (folder / "build-log.json").write_bytes(canonical(results))
            raise ValueError("BUILD_FAILED")
    if _source_snapshot() != before or any(
        (snapshot / name).read_bytes() != data for name, data in before.items()
    ):
        raise ValueError("SOURCE_CHANGED_DURING_BUILD")
    for name in ["cohort", "fixed-worker"]:
        (folder / name).chmod(0o700)
    manifest = {
        "schema": 1,
        "assets": {
            n: hashlib.sha256((folder / n).read_bytes()).hexdigest()
            for n in ["cohort", "fixed-worker"]
        },
        "sources": {n: hashlib.sha256(before[n]).hexdigest() for n in SOURCES},
    }
    fd = os.open(
        folder / "manifest.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(manifest))
        stream.flush()
        os.fsync(stream.fileno())
    (folder / "build-log.json").write_bytes(canonical(results))
    return folder


def _asset(directory: int, name: str, digest: str) -> int:
    fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o6022
            or not info.st_mode & 0o100
            or not 4 <= info.st_size <= 4 * 1024 * 1024
        ):
            raise ValueError("ASSET_TYPE_MODE")
        data = b""
        while len(data) <= 4 * 1024 * 1024:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            data += chunk
        if not data.startswith(b"\x7fELF") or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("ASSET_DRIFT")
        result = fd
        fd = -1
        return result
    finally:
        if fd >= 0:
            owned = fd
            fd = -1
            os.close(owned)


def verify_open_factory(folder: Path) -> int:
    if folder.is_symlink() or folder.parent.resolve() != KIT_ROOT.resolve():
        raise ValueError("KIT_PARENT")
    directory = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    manifest_fd = factory = worker = -1
    try:
        info = os.fstat(directory)
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("KIT_OWNER_MODE")
        manifest_fd = os.open(
            "manifest.json",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=directory,
        )
        manifest_info = os.fstat(manifest_fd)
        if (
            not stat.S_ISREG(manifest_info.st_mode)
            or manifest_info.st_uid != os.geteuid()
            or manifest_info.st_mode & 0o077
        ):
            raise ValueError("MANIFEST_TYPE_MODE")
        raw = os.read(manifest_fd, 32769)
        if len(raw) > 32768:
            raise ValueError("MANIFEST_SIZE")
        owned = manifest_fd
        manifest_fd = -1
        os.close(owned)
        record = json.loads(raw)
        if (
            raw != canonical(record)
            or set(record) != {"schema", "assets", "sources"}
            or record["schema"] != 1
            or set(record["assets"]) != {"cohort", "fixed-worker"}
            or set(record["sources"]) != set(SOURCES)
        ):
            raise ValueError("MANIFEST_SCHEMA")
        if any(
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != record["sources"][name]
            for name in SOURCES
        ):
            raise ValueError("SOURCE_DRIFT")
        factory = _asset(directory, "cohort", record["assets"]["cohort"])
        worker = _asset(directory, "fixed-worker", record["assets"]["fixed-worker"])
        owned = worker
        worker = -1
        os.close(owned)
        owned = directory
        directory = -1
        os.close(owned)
        result = factory
        factory = -1
        return result
    finally:
        for label in ["manifest", "worker", "factory", "directory"]:
            fd = {
                "manifest": manifest_fd,
                "worker": worker,
                "factory": factory,
                "directory": directory,
            }[label]
            if fd >= 0:
                if label == "manifest":
                    manifest_fd = -1
                elif label == "worker":
                    worker = -1
                elif label == "factory":
                    factory = -1
                else:
                    directory = -1
                os.close(fd)
