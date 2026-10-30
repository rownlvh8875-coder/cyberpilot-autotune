"""Opt-in single fixed guest. No host tracer, arbitrary command or repair fallback."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from compatibility.guest_build_receipt.models import BuildIdentity, MaterialRole, sha, uint
from compatibility.guest_input_closure.elf import inspect_elf
from compatibility.guest_input_closure.filesystem import read_regular
from compatibility.guest_input_closure.inventory import snapshot_digest, unique_object

from .contracts import CASES, ConsumptionProfile, KnownMaterial
from .image import INPUT, SCOPE, build_image
from .producer import ProducedObservation, produce_receipt
from .wire import capture_digest, parse_capture

PACKAGE = Path(__file__).resolve().parent
ASSETS = Path("/workspace/scratch/consumption-producer.RaAz1x")
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc/sysroot")
VM_DIGEST = "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c"
SOURCES = (
    "__init__.py",
    "contracts.py",
    "wire.py",
    "producer.py",
    "checks.py",
    "image.py",
    "vm_runner.py",
    "host_main.py",
    "guest/probe.c",
    "guest/sha256.h",
)
PERMISSIONS = (
    "build_execution_allowed",
    "promotion_authorized",
    "runtime_qualified",
    "device_class_qualified",
    "policy_adopted",
    "candidate_generation_allowed",
    "application_authorized",
    "runtime_accepted",
    "owner_proposal_allowed",
)


class CaptureUnavailable(ValueError):
    """Preserve original serial bytes, including invalid/truncated captures."""

    def __init__(self, reason: str, raw: bytes):
        super().__init__(reason)
        self.raw = raw


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
        data["schema"] != "guest-consumption-build-v1"
        or data["scope"] != "FIXED_HARMLESS_GUEST_CONSUMPTION_ONLY"
        or data["base_revision"] != "c5b824f4f37e05bcac81769f1d01a55a51c26e1d"
        or data["vm_cohort_digest"] != VM_DIGEST
        or data["build_input_closure_qualified"] is not False
    ):
        raise ValueError("wrong producer scope/cohort/qualification")
    if (
        type(data["permissions"]) is not dict
        or set(data["permissions"]) != set(PERMISSIONS)
        or any(v is not False for v in data["permissions"].values())
    ):
        raise ValueError("producer cannot grant permissions")
    sha(data["legacy_snapshot_digest"])
    if (
        type(data["binary"]) is not dict
        or set(data["binary"]) != {"path", "sha256", "bytes"}
        or data["binary"]["path"] != "consumption-probe"
    ):
        raise ValueError("unbound binary path")
    sha(data["binary"]["sha256"])
    uint(data["binary"]["bytes"], positive=True)
    if type(data["sources"]) is not list or len(data["sources"]) != len(SOURCES):
        raise ValueError("unbound producer source set")
    names = []
    for record in data["sources"]:
        if (
            type(record) is not dict
            or set(record) != {"path", "sha256", "bytes"}
            or type(record["path"]) is not str
        ):
            raise ValueError("invalid producer source identity")
        names.append(record["path"])
        sha(record["sha256"])
        uint(record["bytes"])
    if (
        set(names) != set(SOURCES)
        or len(set(names)) != len(names)
        or type(data["build_commands"]) is not list
    ):
        raise ValueError("unbound/duplicate producer source")


def qemu_arguments(image: Path) -> list[str]:
    libraries = VM / "usr/lib/x86_64-linux-gnu"
    return [
        str(libraries / "ld-linux-x86-64.so.2"),
        "--library-path",
        str(libraries),
        str(VM / "usr/bin/qemu-system-x86_64"),
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
        str(VM / "usr/share/qemu"),
        "-bios",
        str(VM / "usr/share/seabios/bios-256k.bin"),
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
        str(VM / "boot/vmlinuz-6.12.113+deb13-cloud-amd64"),
        "-initrd",
        str(image),
        "-append",
        "console=ttyS0 rdinit=/init panic=-1 oops=panic "
        "lsm=landlock,lockdown,yama,integrity,apparmor,bpf",
        "-no-reboot",
    ]


def _load_assets() -> tuple[dict[str, tuple[int, bytes]], bytes, dict[str, Any]]:
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
        raw = read_regular(PACKAGE, row["path"], 4 * 1024 * 1024)
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("producer source changed")
    binary = read_regular(ASSETS, "consumption-probe", 4 * 1024 * 1024)
    if (
        len(binary) != data["binary"]["bytes"]
        or hashlib.sha256(binary).hexdigest() != data["binary"]["sha256"]
    ):
        raise ValueError("producer binary changed")
    elf = inspect_elf(binary)
    if elf.interpreter is not None or elf.needed or elf.elf_type != 2:
        raise ValueError("fixed static ELF required")
    actual, _ = observe_fixed_inputs()
    expected = expected_snapshot()
    if actual != expected or snapshot_digest(actual) != data["legacy_snapshot_digest"]:
        raise ValueError("fixed legacy input cohort changed")
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


def observation_from_log(raw: str, binary_digest: str, binary_size: int) -> ProducedObservation:
    capture = parse_capture(raw)
    digest = capture_digest(capture)
    # Size AND digest come from the independently selected profile, not the
    # untrusted capture's declaration, a path or an argv request.
    sha(binary_digest)
    uint(binary_size, positive=True)
    if not any(
        e.kind == "OBJECT" and e.values[3] == binary_size and e.values[4] == binary_digest
        for e in capture.events
    ):
        raise ValueError("actual program object unavailable/ambiguous")
    identity = BuildIdentity(
        "capture-" + digest[:48],
        capture.case,
        hashlib.sha256(INPUT).hexdigest(),
        binary_digest,
        hashlib.sha256(("fixed-consumption:" + capture.case).encode()).hexdigest(),
        VM_DIGEST,
        binary_digest,
        "GUEST_TRACER_OBSERVATION_MONOTONIC_NS",
    )
    profile = ConsumptionProfile(
        identity,
        (
            KnownMaterial(
                "program",
                MaterialRole.TOOLCHAIN,
                "consumption-probe",
                binary_size,
                binary_digest,
            ),
            KnownMaterial(
                "input",
                MaterialRole.SOURCE,
                "input/sample.bin",
                len(INPUT),
                hashlib.sha256(INPUT).hexdigest(),
            ),
            KnownMaterial(
                "scope",
                MaterialRole.CONFIG,
                "etc/guest-consumption-scope",
                len(SCOPE),
                hashlib.sha256(SCOPE).hexdigest(),
            ),
        ),
    )
    return produce_receipt(capture, profile)


def capture_case(case: str) -> tuple[ProducedObservation, str]:
    if type(case) is not str or case not in CASES:
        raise ValueError("unknown fixed fixture")
    if sys.platform != "linux":
        raise ValueError("prepared Linux software guest only")
    files, binary, data = _load_assets()
    with tempfile.TemporaryDirectory(prefix="cp-guest-", dir="/workspace/scratch") as owned:
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
                "guest timeout, capture unavailable", error.stdout or b""
            ) from error
    try:
        raw = process.stdout.decode("utf-8", errors="strict")
        if (
            process.returncode
            or "ACTUAL_GUEST_KERNEL=6.12.113+deb13-cloud-amd64" not in raw
            or "CONSUMPTION_PROBE_EXIT 0" not in raw
            or "CONSUMPTION_GUEST_DONE" not in raw
        ):
            raise ValueError("guest run/window not completed")
        observation = observation_from_log(raw, data["binary"]["sha256"], data["binary"]["bytes"])
        if observation.capture.case != case:
            raise ValueError("wrong guest fixture receipt")
    except ValueError as error:
        raise CaptureUnavailable(str(error), process.stdout) from error
    return observation, raw
