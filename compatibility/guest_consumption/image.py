"""Fixed derived diskless archive. Shell and native code run only in the guest."""

import gzip
import io

from compatibility.containment_backend_harmless.guest_image import GUEST_FILES
from compatibility.containment_backend_harmless.guest_image import build_image as base_image
from compatibility.guest_input_closure.archive import parse_image
from compatibility.guest_input_closure.contracts import ImageMember

from .contracts import CASES

INPUT = b"0123456789ABCDEF\n"
SCOPE = b"guest-consumption-prototype-v1: fixed software guest only\n"
INIT = """#!/bin/busybox sh
/bin/busybox --install -s /bin
mount -t proc proc /proc || exit 2
mount -t sysfs sysfs /sys || exit 2
mount -t devtmpfs devtmpfs /dev || exit 2
echo ACTUAL_GUEST_KERNEL=$(uname -r)
sha256sum /sys/kernel/btf/vmlinux
/consumption-probe --trace CASE_SELECTION
echo CONSUMPTION_PROBE_EXIT "$?"
echo CONSUMPTION_GUEST_DONE
reboot -f
"""


def build_image(files: dict[str, tuple[int, bytes]], binary: bytes, case: str) -> bytes:
    if (
        type(case) is not str
        or case not in CASES
        or set(files) != GUEST_FILES
        or type(binary) is not bytes
        or not binary.startswith(b"\x7fELF\x02\x01")
    ):
        raise ValueError("fixed complete guest inputs and case required")
    entries = {e.path: e for e in parse_image(base_image(files, ("HF01",)))}
    entries["init"] = ImageMember("init", 0o100755, INIT.replace("CASE_SELECTION", case).encode())
    entries["consumption-probe"] = ImageMember("consumption-probe", 0o100755, binary)
    entries["etc/guest-consumption-scope"] = ImageMember(
        "etc/guest-consumption-scope", 0o100444, SCOPE
    )
    entries["input"] = ImageMember("input", 0o040755, b"")
    entries["input/sample.bin"] = ImageMember("input/sample.bin", 0o100444, INPUT)
    out = io.BytesIO()
    for inode, entry in enumerate((*entries.values(), ImageMember("TRAILER!!!", 0o100444, b"")), 1):
        trailer = entry.path == "TRAILER!!!"
        label = entry.path.encode() + b"\0"
        fields = (
            inode,
            0 if trailer else entry.mode,
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
        out.write(b"070701" + b"".join(f"{v:08x}".encode() for v in fields) + label)
        out.write(b"\0" * (-out.tell() % 4))
        out.write(entry.data)
        out.write(b"\0" * (-out.tell() % 4))
    return gzip.compress(out.getvalue(), mtime=0)
