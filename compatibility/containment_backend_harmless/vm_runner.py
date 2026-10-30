"""Opt-in fixed TCG recipe. No host policy syscalls or arbitrary command interface.

Hashes establish cached content identity, never authorization or complete closure.
Missing matching inputs fail before starting a process. Not installed in the wheel.
"""

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .guest_image import GUEST_FILES, build_image
from .host_cases import FIXTURES, check_case, parse_guest_log
from .records import PERMISSIONS

MANIFEST = Path(__file__).with_name("host") / "build_manifest.json"
VM_DIGEST = "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c"


def verify_file(path: Path, expected: str) -> None:
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"INPUT_HASH_MISMATCH: {path}")


def verify_vm(root: Path) -> None:
    data = json.loads((root / "cohort.json").read_text())
    expected = data.pop("content_digest")
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if expected != VM_DIGEST or hashlib.sha256(encoded).hexdigest() != VM_DIGEST:
        raise ValueError("VM_COHORT_MISMATCH")
    tree = data["extracted_tree"]
    if {str(p.relative_to(root)) for p in (root / "sysroot").rglob("*")} != {
        r["path"] for r in tree
    }:
        raise ValueError("VM_TREE_CHANGED")
    for record in tree:
        path = root / record["path"]
        if stat.S_IMODE(path.lstat().st_mode) != record["mode"]:
            raise ValueError("VM_MODE_CHANGED")
        kind = record["kind"]
        if kind == "symlink":
            if not path.is_symlink() or os.readlink(path) != record["target"]:
                raise ValueError("VM_SYMLINK_CHANGED")
        elif kind == "directory":
            if path.is_symlink() or not path.is_dir():
                raise ValueError("VM_DIRECTORY_CHANGED")
        elif path.is_symlink() or not path.is_file():
            raise ValueError("VM_FILE_CHANGED")
        else:
            verify_file(path, record["sha256"])
    for record in data["packages"] + data["assets"] + data["signed_release_metadata"]:
        path = root / record.get("path", record.get("archive"))
        if not path.resolve().is_relative_to(root):
            raise ValueError("VM_INPUT_OUTSIDE_ROOT")
        verify_file(path, record["sha256"])


def validate_manifest_structure(data: dict[str, Any]) -> None:
    if data["scope"] != "SOFTWARE_GUEST_ONLY_NO_DEVICE_ATTEMPT":
        raise ValueError("WRONG_SCOPE")
    if set(data["permissions"]) != set(PERMISSIONS) or any(
        value is not False for value in data["permissions"].values()
    ):
        raise ValueError("QUALIFICATION_NOT_ALLOWED")
    guest_files = data["guest_files"]
    names = [r["guest_path"] for r in guest_files]
    if len(names) != len(set(names)) or set(names) != GUEST_FILES:
        raise ValueError("UNBOUND_GUEST_ENTRY")
    inputs = {r["path"] for r in data["inputs"]}
    if any(r["path"] not in inputs for r in guest_files):
        raise ValueError("UNHASHED_GUEST_ENTRY")


def verified_manifest() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(MANIFEST.read_text())
    validate_manifest_structure(data)
    for record in data["inputs"]:
        path = Path(record["path"])
        if not path.is_absolute():
            path = Path(__file__).parents[2] / path
        verify_file(path, record["sha256"])
    verify_vm(Path(data["vm_root"]))
    return data


def qemu_arguments(root: Path, image: Path) -> list[str]:
    libraries = root / "sysroot/usr/lib/x86_64-linux-gnu"
    return [
        str(libraries / "ld-linux-x86-64.so.2"),
        "--library-path",
        str(libraries),
        str(root / "sysroot/usr/bin/qemu-system-x86_64"),
        "-no-user-config",
        "-nodefaults",
        "-machine",
        "pc-q35-10.0",
        "-accel",
        "tcg,thread=single",
        "-cpu",
        "qemu64",
        "-smp",
        "1",
        "-m",
        "768M",
        "-L",
        str(root / "sysroot/usr/share/qemu"),
        "-bios",
        str(root / "sysroot/usr/share/seabios/bios-256k.bin"),
        "-display",
        "none",
        "-monitor",
        "none",
        "-serial",
        "stdio",
        "-nic",
        "none",
        "-audiodev",
        "none,id=audio0",
        "-kernel",
        str(root / "sysroot/boot/vmlinuz-6.12.113+deb13-cloud-amd64"),
        "-initrd",
        str(image),
        "-append",
        "console=ttyS0 rdinit=/init panic=-1 oops=panic "
        "lsm=landlock,lockdown,yama,integrity,apparmor,bpf",
        "-no-reboot",
    ]


def execute_guest_job(selected: tuple[str, ...]) -> int:
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(x not in FIXTURES for x in selected)
    ):
        return 2
    try:
        data = verified_manifest()
        files = {
            r["guest_path"]: (r["mode"], Path(r["path"]).read_bytes()) for r in data["guest_files"]
        }
        root = Path(data["vm_root"])
        with tempfile.TemporaryDirectory(prefix="hf-guest-", dir="/workspace/scratch") as owned:
            image = Path(owned) / "guest.cpio.gz"
            image.write_bytes(build_image(files, selected))
            result = subprocess.run(
                qemu_arguments(root, image),
                input=b"",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=180,
                check=False,
                env={
                    "QEMU_MODULE_DIR": str(root / "sysroot/usr/lib/x86_64-linux-gnu/qemu"),
                    "LANG": "C",
                    "PATH": "/usr/bin:/bin",
                },
            )
        log = result.stdout.decode("utf-8", errors="strict")
        sys.stdout.write(log)
        if result.returncode:
            return 2
        records = parse_guest_log(log, selected)
        if any(check_case(record) for record in records):
            return 2
        if (
            "ACTUAL_GUEST_KERNEL=6.12.113+deb13-cloud-amd64" not in log
            or data["guest_btf_sha256"] + "  /sys/kernel/btf/vmlinux" not in log
        ):
            return 2
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"GUEST_RUN_UNAVAILABLE: {error}", file=sys.stderr)
        return 2
