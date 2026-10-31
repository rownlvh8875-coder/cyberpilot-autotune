"""Explicit opt-in fixed guest only. No process runs on import, test or audit."""

import argparse
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

from compatibility.containment_backend_harmless.vm_runner import qemu_arguments, verify_vm
from compatibility.guest_input_closure.elf import inspect_elf
from tests.guest_raw_lifetime.runner import CaptureUnavailable, verify_bytes

from .image import build_image
from .model import CASES, Capture, assess, parse_serial, require

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path("/workspace/scratch/root-scope-producer.wggKv4")
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc")
KERNEL_SHA = "fb06e73c11ee893e5d3bf0e02263362f2893863cb670becff8246bcd91562b7b"
INIT_SHA = "ffcc3b280edf1c645a8605e5ce46648ab61c4c9873664fc3bb3e590a6b2d7627"
SOURCE_INPUTS = {
    "guest/init.c": "5c38e027afdd639d56b1eb8c2fd85b9f19414a0d67b1daabe00d2f1dac477d62",
    "kernel.patch": "0b4df48afa9f9750691026c51b180278532c0c30a50f671d797c7e45a6ac6e6d",
    "kernel.config": "fd558bc27411f7cb2c4a6f7939e5e93e0c5da68d6f297415ede036335e60d611",
    "model.py": "3e47632ff922b433ffc2384c806e4ef0ff6cafdfa5417b89883c160a2fa66922",
    "image.py": "79d43c5a5ee59ed424771593d590b501a57af2787998aea651d3ba81994c107f",
}
IMAGE_SHA = {
    "NORMAL": "ab075f99d0c74e9ce8e3d433b814936cc67bb18663b09c9627f755277ac35d5f",
    "ROOT_BIRTH_LOSS": "7dce85c2db2f09bdb78200d61a4b70d3ffe854f68854615fcced16c214547d1b",
    "SMALL_BUFFER": "dd4484b13db9322d307dde712ba90f267b6c995a6d9e049d08a1f7a403cc1099",
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
    with tempfile.TemporaryDirectory(prefix="fixed-managed-root-") as owned:
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
    return 0 if assess(result).local_accounting_balanced else 2


if __name__ == "__main__":
    raise SystemExit(main())
