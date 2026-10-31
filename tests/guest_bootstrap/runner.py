"""Explicit opt-in fixed guest execution,never import/test/audit side effects."""

import argparse
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

from compatibility.containment_backend_harmless.vm_runner import qemu_arguments, verify_vm
from compatibility.guest_input_closure.elf import inspect_elf
from tests.guest_raw_lifetime.model import require
from tests.guest_raw_lifetime.runner import CaptureUnavailable, verify_bytes

from .contracts import CASES, Capture
from .image import build_image
from .model import assess
from .wire import parse_serial

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path("/workspace/scratch/guest-bootstrap-producer.O8Npmg")
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc")
KERNEL_SHA = "0" * 64
INIT_SHA = "0" * 64
SOURCE_INPUTS: dict[str, str] = {}
IMAGE_SHA: dict[str, str] = {}


def arguments(image: Path) -> list[str]:
    args = qemu_arguments(VM, image)
    args[args.index("-kernel") + 1] = str(ASSETS / "patched-bzImage")
    args[args.index("-m") + 1] = "512M"
    args[args.index("-append") + 1] = "console=ttyS0 rdinit=/init panic=-1 oops=panic"
    return args


def capture(case: str) -> tuple[Capture, bytes, bytes]:
    require(type(case) is str and case in CASES, "FIXED_CASE_REQUIRED")
    require(
        KERNEL_SHA != "0" * 64
        and INIT_SHA != "0" * 64
        and set(IMAGE_SHA) == set(CASES)
        and set(SOURCE_INPUTS)
        == {
            "guest/init.c",
            "kernel.patch",
            "kernel.config",
            "contracts.py",
            "wire.py",
            "model.py",
            "image.py",
        },
        "FROZEN_INPUTS_UNAVAILABLE",
    )
    for name, sha in SOURCE_INPUTS.items():
        verify_bytes(Path(__file__).parent / name, sha)
    verify_vm(VM)
    verify_bytes(ASSETS / "patched-bzImage", KERNEL_SHA)
    binary = verify_bytes(ASSETS / "init", INIT_SHA)
    elf = inspect_elf(binary)
    require(elf.elf_type == 2 and elf.interpreter is None and not elf.needed, "STATIC_ELF_REQUIRED")
    image = build_image(binary, case)
    require(hashlib.sha256(image).hexdigest() == IMAGE_SHA[case], "FIXED_IMAGE_CHANGED")
    with tempfile.TemporaryDirectory(prefix="fixed-first-observed-") as owned:
        path = Path(owned) / "initrd.gz"
        path.write_bytes(image)
        try:
            run = subprocess.run(
                arguments(path),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
                env={
                    "PATH": os.defpath,
                    "LANG": "C",
                    "QEMU_MODULE_DIR": str(VM / "sysroot/usr/lib/x86_64-linux-gnu/qemu"),
                },
            )
        except subprocess.TimeoutExpired as exc:
            raise CaptureUnavailable(
                "guest timeout,not a qualified watchdog", exc.stdout or b""
            ) from exc
    try:
        require(run.returncode == 0, "FIXED_GUEST_FAILED")
        result = parse_serial(run.stdout)
        require(result.case == case, "WRONG_GUEST_CASE")
    except ValueError as exc:
        raise CaptureUnavailable(str(exc), run.stdout) from exc
    return result, run.stdout, image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-fixed", choices=CASES, required=True)
    args = parser.parse_args()
    result, raw, _ = capture(args.execute_fixed)
    print(raw.decode(), end="")
    return 0 if assess(result).local_accounting_balanced else 2


if __name__ == "__main__":
    raise SystemExit(main())
