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
KERNEL_SHA = "41ff311f04db5a8d4509fd20f45f293f89c5ea854758bf72d653c8a767cc0ace"
INIT_SHA = "5a7798a78d22869d87cfe8a583ce092d3d90cdf1d9bd4f83839120828839fc08"
SOURCE_INPUTS = {
    "contracts.py": "6d3d2acd06752756407985458655661626f1a568147d6981f19d3aff233e7fc2",
    "guest/init.c": "e5049f27d68c0c382270bda5eacdbb9c5f4025694cb7c17ab0c5d11ad0a96ff6",
    "image.py": "d2c8ebfc1eb852fbb47e3cf34dba138b8ff6b355795fa00dcaef9d399eea3a5b",
    "kernel.config": "3b87070e601d3987978861d898ce98475f534b1119d8eca2fc0fa5e021318ef7",
    "kernel.patch": "3eed09131f6ce03dc4a489dfe161cd3d48576ba760abf0978d8846fd3edfc848",
    "model.py": "7fcfea82d52c14e22d4cdc16143abbf0852fe2cc6b9ebe5c5381d1cc409e112e",
    "wire.py": "9051de047145eb539cfc5a16da654f337ee8c899b449ae45dd8eb167a041e510",
}
IMAGE_SHA = {
    "ALLOC_FAIL": "0c087dfa1537fd3176afcd3f24a1f0b7105a857be944ccac52a290ec895b7e24",
    "CONSTRUCTOR_FAIL": "059fde089a7c38dc5d59e3a4880d84f8ee518fd660e9cab598025dfe73bd5611",
    "EARLY_ARM_REJECTED": "71ddcff8120ccef6b13b69b38258ca704ca1d7a9ed61590fa17fe3b81b5aeada",
    "NORMAL": "2c95708d5d06ab2721b48809abd404a7602dc8f79a6b3b7021db194312bfa5e7",
    "RESEED_REJECTED": "1a13a6a487eaa7c85beaff84994c0dcee3aea2ccd63475d3a553604d15fd968c",
    "SEED_FAIL": "dde186f9c7d1fbbf6c5e120136e43b1887dec5f8a8c58a372372a5bb84cfa095",
    "SEED_LOSS": "0251f381ced7d71a2f6ebadccbff5f640c2ab24fa2bd5828e339d9b8b9af4ed1",
    "SMALL_BUFFER": "54934256a85da9870b85bdd6bc6a3eae8b6e1740e7685d277105d3833afe39a0",
    "TASK_FAIL": "1c136f1b429882d2911ee5671fd5e8cd5720e5b0f6279a395845ed1b8e5046ac",
    "UNSEEDED_OFD": "208d2ef820dd1ecad0a48975fce0570fea29a9c1acdc6c53f4040b64abc2f7e6",
}


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
