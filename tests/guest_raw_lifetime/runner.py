"""Explicit fixed guest only; no VM execution on import, pytest, or offline audit."""

import argparse
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

from compatibility.containment_backend_harmless.vm_runner import qemu_arguments, verify_vm
from compatibility.guest_input_closure.elf import inspect_elf

from .image import build_image
from .model import CASES, Capture, assess, parse_serial, require

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path("/workspace/scratch/raw-lifetime-producer.mfFU7h")
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc")
KERNEL_SHA = "61956f2ba7131b8d442d304194a7568732c0201cca0f0355db45955585684246"
INIT_SHA = "032053b561af85a6a5f3b02bdf7eea6d2825289a1ba8f20aded85bf0ac142001"
SOURCE_INPUTS = {
    "guest/init.c": "475682274dd43651f7ab5955650b70772a2dca681dc07e4da3d0d629166d5573",
    "kernel.patch": "95276198613e05f6ea0bc7a94daccec21a8a1caba589fd97b768e51c22b9a4c4",
    "kernel.config": "5b806c70666ffdcdcdf3e3f6f87754ae0025863d3ff80657ba796ac80c75f9ac",
    "model.py": "360b0b4cf76c61a18afa57e00fe1e70d40096eb85aed258801fad424133f726a",
    "image.py": "5cf02b1f7125d997b92a95bee81f684a9010286b0b6254d4bff7ade3800cb495",
}
IMAGE_SHA = {
    "NORMAL": "e4b6a43db51b321c01325fc20d9017ead594b54a26f7bc45e44418cafdce92f0",
    "FORCED_LOSS": "dfa152dc18d7283c25b72c8e42f3b47a0bdebd031145c09138519030aada93a7",
    "SMALL_BUFFER": "4965f981b3f14a1363055c14a395017aef41bfa0430a604c6d8c87ba245f5700",
}


def verify_bytes(path: Path, expected: str) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(8 * 1024 * 1024 + 1)
    require(
        len(raw) <= 8 * 1024 * 1024 and hashlib.sha256(raw).hexdigest() == expected,
        "FIXED_INPUT_CHANGED",
    )
    return raw


def arguments(image: Path) -> list[str]:
    args = qemu_arguments(VM, image)
    args[args.index("-kernel") + 1] = str(ASSETS / "patched-bzImage")
    args[args.index("-m") + 1] = "512M"
    args[args.index("-append") + 1] = "console=ttyS0 rdinit=/init panic=-1 oops=panic"
    return args


class CaptureUnavailable(ValueError):
    def __init__(self, reason: str, raw: bytes):
        super().__init__(reason)
        self.raw = raw


def capture(case: str) -> tuple[Capture, bytes, bytes]:
    require(type(case) is str and case in CASES, "FIXED_CASE_REQUIRED")
    for name, sha in SOURCE_INPUTS.items():
        verify_bytes(Path(__file__).parent / name, sha)
    verify_vm(VM)
    verify_bytes(ASSETS / "patched-bzImage", KERNEL_SHA)
    binary = verify_bytes(ASSETS / "init", INIT_SHA)
    elf = inspect_elf(binary)
    require(elf.elf_type == 2 and elf.interpreter is None and not elf.needed, "STATIC_ELF_REQUIRED")
    image = build_image(binary, case)
    require(hashlib.sha256(image).hexdigest() == IMAGE_SHA[case], "FIXED_IMAGE_CHANGED")
    with tempfile.TemporaryDirectory(prefix="fixed-raw-lifetime-") as owned:
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
                "bounded guest timeout, not a watchdog", exc.stdout or b""
            ) from exc
    raw = run.stdout
    try:
        require(run.returncode == 0, "FIXED_GUEST_FAILED")
        result = parse_serial(raw)
        require(result.case == case, "WRONG_GUEST_CASE")
    except ValueError as exc:
        raise CaptureUnavailable(str(exc), raw) from exc
    return result, raw, image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-fixed", choices=CASES, required=True)
    args = parser.parse_args()
    result, raw, _ = capture(args.execute_fixed)
    print(raw.decode(), end="")
    decision = assess(result)
    return 0 if decision.local_accounting_balanced else 2


if __name__ == "__main__":
    raise SystemExit(main())
