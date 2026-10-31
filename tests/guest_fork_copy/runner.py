"""Opt-in fixed VM only;normal tests/audit/import do not build or boot anything."""

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

from .image import build_image
from .model import CASES, Capture, assess, parse_serial

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path("/workspace/scratch/guest-copy-producer.IGDFFC")
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc")
KERNEL_SHA = "f2a8dce470fb64e42a47294cc46594b3054d36725dd0f50f92b2510d3aa559a7"
INIT_SHA = "a853c2c4de7c062d677d8f9b8584c1a42134c317c4cd0f0f2d2183270b3f9c38"
SOURCE_INPUTS = {
    "guest/init.c": "ffef597b43fb600f75d9d2909bef7264fd81bd89dce657fce1c5704532d18f8a",
    "kernel.patch": "ae13cceb0cc07cd1e4c18478dee80f2b3e490108e8a42781158dbf011917e13c",
    "kernel.config": "7a19e0eaddb14194976fef0e36a08fbbe14194b9a6683b0a5947336cf931750d",
    "model.py": "8e55dc171ffd892e2bbedbaa8b307cc1995dba79f01f8907a7a11fbecb49cf24",
    "image.py": "82a735f2ffbc8e19e550d56459c0163e60a188fac2cc3f8a2920cd41dd57ff79",
}
IMAGE_SHA = {
    "NORMAL": "3bd00a7b807f0621e9f154b16b1ddbc256f7cba16b5c94fd6de7615a9e625a80",
    "READ_LOSS": "48ad0a015847d714d5aa5bba9dc70a4ddc5cfb323d6b39205d4297f5cfbe800d",
    "SMALL_BUFFER": "8b1a752e029a5542e9ba9b14f2b006bd11fe0902e0808bdffc6599325e381028",
    "CONSTRUCTOR_FAIL": "5e2b290e97e9d0fc592551b81aa9b671d38236d69873314cca02339bd87c5014",
    "TASK_FAIL": "22d62535f8cdb5c7027665438eb47ad4f6dae8a02ecb33c9d438f09c0b520c3b",
    "ALLOC_FAIL": "98a6d621b0f0bef8fa67ce021dfc8a46c5c5987b671dcef23a6957e90993a455",
}


def arguments(image: Path) -> list[str]:
    args = qemu_arguments(VM, image)
    args[args.index("-kernel") + 1] = str(ASSETS / "patched-bzImage")
    args[args.index("-m") + 1] = "512M"
    args[args.index("-append") + 1] = "console=ttyS0 rdinit=/init panic=-1 oops=panic"
    return args


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
    with tempfile.TemporaryDirectory(prefix="fixed-per-slot-copy-") as owned:
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
