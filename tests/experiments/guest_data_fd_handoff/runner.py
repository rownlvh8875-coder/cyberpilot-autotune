"""Explicit opt-in fixed guest execution. Never runs the ELF on the host."""

import gzip
import hashlib
import io
import subprocess
import tempfile
from pathlib import Path

from compatibility.containment_backend_harmless.guest_image import GUEST_FILES
from compatibility.containment_backend_harmless.guest_image import build_image as base_image
from compatibility.guest_consumption.vm_runner import qemu_arguments as qemu_arguments
from compatibility.guest_input_closure.archive import parse_image
from compatibility.guest_input_closure.contracts import ImageMember
from compatibility.guest_input_closure.elf import inspect_elf
from compatibility.guest_input_closure.filesystem import read_regular
from compatibility.guest_input_seal.vm_runner import load_assets

from .audit import ASSETS, load_build
from .model import CASES, Capture, check_case, parse_serial, require

SCOPE = b"guest-data-fd-handoff-v1: fixed software guest only\n"
INIT = """#!/bin/busybox sh
/bin/busybox --install -s /bin
mount -t proc proc /proc || exit 2
mount -t sysfs sysfs /sys || exit 2
mount -t devtmpfs devtmpfs /dev || exit 2
echo ACTUAL_GUEST_KERNEL=$(uname -r)
sha256sum /sys/kernel/btf/vmlinux
echo HFD_EXEC
/data-fd-handoff-probe --trace CASE_SELECTION
echo HFD_PROBE_EXIT=$?
echo HFD_DONE
reboot -f
"""


def build_image(files: dict[str, tuple[int, bytes]], binary: bytes, case: str) -> bytes:
    require(
        type(case) is str
        and case in CASES
        and set(files) == GUEST_FILES
        and type(binary) is bytes
        and binary.startswith(b"\x7fELF\x02\x01"),
        "fixed guest inputs",
    )
    entries = {e.path: e for e in parse_image(base_image(files, ("HF01",)))}
    entries["init"] = ImageMember("init", 0o100755, INIT.replace("CASE_SELECTION", case).encode())
    entries["data-fd-handoff-probe"] = ImageMember("data-fd-handoff-probe", 0o100755, binary)
    entries["etc/data-fd-handoff-scope"] = ImageMember("etc/data-fd-handoff-scope", 0o100444, SCOPE)
    output = io.BytesIO()
    for inode, entry in enumerate((*entries.values(), ImageMember("TRAILER!!!", 0o100444, b"")), 1):
        label = entry.path.encode() + b"\0"
        fields = (
            inode,
            0 if entry.path == "TRAILER!!!" else entry.mode,
            0,
            0,
            1,
            0,
            len(entry.data),
            0,
            0,
            entry.major,
            entry.minor,
            len(label),
            0,
        )
        output.write(b"070701" + b"".join(f"{v:08x}".encode() for v in fields) + label)
        output.write(b"\0" * (-output.tell() % 4))
        output.write(entry.data)
        output.write(b"\0" * (-output.tell() % 4))
    return gzip.compress(output.getvalue(), mtime=0)


class CaptureUnavailable(ValueError):
    def __init__(
        self, reason: str, raw: bytes, completed: tuple[tuple[Capture, bytes, bytes], ...] = ()
    ):
        super().__init__(reason)
        self.raw = raw
        self.completed = completed


def _capture_cases(
    binary: bytes, program_sha: str, cases: tuple[str, ...], files: dict[str, tuple[int, bytes]]
) -> tuple[tuple[Capture, bytes, bytes], ...]:
    require(
        type(cases) is tuple
        and bool(cases)
        and len(set(cases)) == len(cases)
        and all(type(c) is str and c in CASES for c in cases),
        "fixed unique case set",
    )
    captured: list[tuple[Capture, bytes, bytes]] = []
    for case in cases:
        image = build_image(files, binary, case)
        with tempfile.TemporaryDirectory(prefix="fixed-data-fd-handoff-") as directory:
            path = Path(directory) / "fixed-initrd.gz"
            path.write_bytes(image)
            try:
                run = subprocess.run(
                    qemu_arguments(path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise CaptureUnavailable(
                    "fixed guest timeout (not a qualified watchdog)",
                    exc.stdout or b"",
                    tuple(captured),
                ) from exc
        raw = run.stdout
        try:
            require(run.returncode == 0, "guest process failed")
            capture = parse_serial(raw, case)
            check_case(capture, program_sha)
        except ValueError as exc:
            raise CaptureUnavailable(str(exc), raw, tuple(captured)) from exc
        captured.append((capture, raw, image))
    return tuple(captured)


def capture_cases(cases: tuple[str, ...]) -> tuple[tuple[Capture, bytes, bytes], ...]:
    """Only source/ELF/VM checked frozen assets; no caller payload/command/VM arguments."""
    require(
        type(cases) is tuple
        and bool(cases)
        and len(set(cases)) == len(cases)
        and all(type(c) is str and c in CASES for c in cases),
        "fixed unique case set",
    )
    manifest, _ = load_build()
    binary = read_regular(ASSETS, "data-fd-handoff-probe", 4 * 1024 * 1024)
    require(
        len(binary) == manifest["binary"]["bytes"]
        and hashlib.sha256(binary).hexdigest() == manifest["binary"]["sha256"],
        "fixed source-bound binary changed",
    )
    elf = inspect_elf(binary)
    require(elf.elf_type == 2 and elf.interpreter is None and not elf.needed, "fixed static ELF")
    files, _, _ = load_assets()
    return _capture_cases(binary, manifest["binary"]["sha256"], cases, files)
