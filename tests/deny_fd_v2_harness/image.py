"""Minimal deterministic archive bytes only; never extracts or executes an image."""

import gzip
import io

from .assets import validate_bundle
from .contracts import AssetBundle, case_label

SCOPE = b"deny-fd-v2: fixed pre-exec inventory probe only\n"
INIT = """#!/bin/busybox sh
/bin/busybox mount -t proc proc /proc || exit 2
/bin/busybox mount -t sysfs sysfs /sys || exit 2
/bin/busybox mount -t devtmpfs devtmpfs /dev || exit 2
echo ACTUAL_GUEST_KERNEL=$(/bin/busybox uname -r)
echo DFD2_EXEC
/deny-fd-v2-probe --probe CASE_SELECTION
probe_status=$?
echo DFD2_PROBE_EXIT=$probe_status
echo DFD2_DONE
/bin/busybox reboot -f
"""


def init_bytes(case: str) -> bytes:
    return INIT.replace("CASE_SELECTION", case_label(case)).encode("ascii")


def build_image(assets: AssetBundle, case: str) -> bytes:
    case_label(case)
    validate_bundle(assets)
    output = io.BytesIO()
    inode = 0

    def entry(name: str, mode: int, raw: bytes = b"", major: int = 0, minor: int = 0) -> None:
        nonlocal inode
        inode += 1
        label = name.encode("ascii") + b"\0"
        fields = (inode, mode, 0, 0, 1, 0, len(raw), 0, 0, major, minor, len(label), 0)
        output.write(b"070701" + b"".join(f"{v:08x}".encode() for v in fields) + label)
        output.write(b"\0" * (-output.tell() % 4))
        output.write(raw)
        output.write(b"\0" * (-output.tell() % 4))

    for directory in ("bin", "dev", "proc", "sys", "etc"):
        entry(directory, 0o040755)
    entry("dev/console", 0o020600, major=5, minor=1)
    entry("dev/null", 0o020666, major=1, minor=3)
    entry("bin/busybox", 0o100755, assets.busybox)
    entry("deny-fd-v2-probe", 0o100755, assets.probe)
    entry("etc/deny-fd-v2-scope", 0o100444, SCOPE)
    entry("init", 0o100755, init_bytes(case))
    entry("TRAILER!!!", 0)
    compressed = gzip.compress(output.getvalue(), mtime=0)
    return compressed[:9] + b"\xff" + compressed[10:]  # fixed gzip OS byte, no host timestamp
