"""Opt-in fixed harmless guest. Never executes the static probe on the host."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from compatibility.guest_consumption.vm_runner import VM, VM_DIGEST, qemu_arguments
from compatibility.guest_input_closure.elf import inspect_elf
from compatibility.guest_input_closure.filesystem import read_regular
from compatibility.guest_input_closure.inventory import snapshot_digest, unique_object

from .contracts import CASES, PERMISSIONS, SealCapture, uint
from .image import build_image
from .wire import parse_guest_capture

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
ASSETS = Path("/workspace/scratch/input-seal-producer.HKE6j9")
SOURCES = tuple(
    "compatibility/guest_input_seal/" + name
    for name in (
        "__init__.py",
        "contracts.py",
        "wire.py",
        "evaluation.py",
        "image.py",
        "vm_runner.py",
        "host_main.py",
        "guest/probe.c",
    )
) + (
    "compatibility/guest_consumption/guest/sha256.h",
    "compatibility/guest_consumption/vm_runner.py",
)


def _sha(value: Any) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("SHA256 required")


def validate_build_manifest(data: Any) -> None:
    if type(data) is not dict or set(data) != {
        "schema",
        "scope",
        "base_revision",
        "vm_cohort_digest",
        "legacy_snapshot_digest",
        "binary",
        "sources",
        "build_commands",
        "permissions",
        "build_input_closure_qualified",
    }:
        raise ValueError("unsupported producer manifest")
    if (
        data["schema"] != "guest-input-seal-build-v1"
        or data["scope"] != "FIXED_HARMLESS_GUEST_OBJECT_SEALS_ONLY"
        or data["base_revision"] != "ae7b3644984cd5ecc8fbb23532f5ec7e0da3998f"
        or data["vm_cohort_digest"] != VM_DIGEST
        or data["build_input_closure_qualified"] is not False
    ):
        raise ValueError("wrong producer scope/cohort/qualification")
    if (
        type(data["permissions"]) is not dict
        or set(data["permissions"]) != dict(PERMISSIONS).keys()
        or any(v is not False for v in data["permissions"].values())
    ):
        raise ValueError("producer cannot grant permissions")
    _sha(data["legacy_snapshot_digest"])
    binary = data["binary"]
    if (
        type(binary) is not dict
        or set(binary) != {"path", "sha256", "bytes"}
        or binary["path"] != "input-seal-probe"
    ):
        raise ValueError("unbound binary path")
    _sha(binary["sha256"])
    uint(binary["bytes"], positive=True)
    if type(data["sources"]) is not list or len(data["sources"]) != len(SOURCES):
        raise ValueError("unbound source set")
    names = []
    for row in data["sources"]:
        if (
            type(row) is not dict
            or set(row) != {"path", "sha256", "bytes"}
            or type(row["path"]) is not str
        ):
            raise ValueError("invalid source identity")
        names.append(row["path"])
        _sha(row["sha256"])
        uint(row["bytes"])
    if len(set(names)) != len(names) or set(names) != set(SOURCES):
        raise ValueError("unbound/duplicate sources")
    if (
        type(data["build_commands"]) is not list
        or not data["build_commands"]
        or any(type(v) is not str or not v for v in data["build_commands"])
    ):
        raise ValueError("build command provenance unavailable")


def load_assets() -> tuple[dict[str, tuple[int, bytes]], bytes, dict[str, Any]]:
    from compatibility.guest_input_closure.fixed import (
        COLLECTOR_BUILD,
        FIXTURE_BUILD,
        REPO,
        TOOLCHAIN,
        VM_SYSROOT,
        expected_snapshot,
        observe_fixed_inputs,
    )
    from compatibility.guest_input_closure.legacy import load_checked_assets

    data = json.loads(
        read_regular(PACKAGE, "guest/build_manifest.json", 1024 * 1024),
        object_pairs_hook=unique_object,
    )
    validate_build_manifest(data)
    for row in data["sources"]:
        raw = read_regular(ROOT, row["path"], 4 * 1024 * 1024)
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("producer source changed")
    binary = read_regular(ASSETS, "input-seal-probe", 4 * 1024 * 1024)
    if (
        len(binary) != data["binary"]["bytes"]
        or hashlib.sha256(binary).hexdigest() != data["binary"]["sha256"]
    ):
        raise ValueError("producer binary changed")
    elf = inspect_elf(binary)
    if elf.elf_type != 2 or elf.interpreter is not None or elf.needed:
        raise ValueError("fixed static ELF required")
    actual, _ = observe_fixed_inputs()
    if actual != expected_snapshot() or snapshot_digest(actual) != data["legacy_snapshot_digest"]:
        raise ValueError("fixed legacy cohort changed")
    files, _ = load_checked_assets(
        actual,
        {
            "repo_selected": REPO,
            "toolchain_exact_tree": TOOLCHAIN,
            "vm_exact_tree": VM_SYSROOT,
            "fixture_selected": FIXTURE_BUILD,
            "collector_selected": COLLECTOR_BUILD,
            "host_gcc_selected": Path("/"),
        },
    )
    return files, binary, data


class CaptureUnavailable(ValueError):
    def __init__(self, reason: str, raw: bytes, completed: tuple[tuple[SealCapture, bytes], ...]):
        super().__init__(reason)
        self.raw = raw
        self.completed = completed


def capture_cases(cases: tuple[str, ...]) -> tuple[tuple[SealCapture, bytes], ...]:
    if (
        type(cases) is not tuple
        or not cases
        or len(set(cases)) != len(cases)
        or any(type(c) is not str or c not in CASES for c in cases)
    ):
        raise ValueError("unique fixed fixtures required")
    if sys.platform != "linux":
        raise ValueError("prepared Linux software guest only")
    files, binary, _ = load_assets()
    completed: list[tuple[SealCapture, bytes]] = []
    for case in cases:
        with tempfile.TemporaryDirectory(
            prefix="input-seal-guest-", dir="/workspace/scratch"
        ) as owned:
            image = Path(owned) / "guest.cpio.gz"
            image.write_bytes(build_image(files, binary, case))
            try:
                process = subprocess.run(
                    qemu_arguments(image),
                    input=b"",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                    check=False,
                    env={
                        "QEMU_MODULE_DIR": str(VM / "usr/lib/x86_64-linux-gnu/qemu"),
                        "PATH": "/usr/bin:/bin",
                        "LANG": "C",
                    },
                )
            except subprocess.TimeoutExpired as error:
                raise CaptureUnavailable(
                    "guest timeout", error.stdout or b"", tuple(completed)
                ) from error
        try:
            raw = process.stdout.decode("utf-8", errors="strict")
            if process.returncode:
                raise ValueError("guest window incomplete")
            capture = parse_guest_capture(raw)
            if capture.case != case:
                raise ValueError("wrong case capture")
        except (ValueError, UnicodeError) as error:
            raise CaptureUnavailable(str(error), process.stdout, tuple(completed)) from error
        completed.append((capture, process.stdout))
    return tuple(completed)
