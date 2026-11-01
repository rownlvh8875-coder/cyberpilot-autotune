"""Fixed ttyS1 image data only; neither construction nor import executes it."""

import gzip
import io

from tests.deny_fd_v2_harness.contracts import case_label, need
from tests.deny_fd_v2_harness.image import SCOPE

from .assets import TransportAssets

INIT = """#!/bin/busybox sh
/bin/busybox mount -t proc proc /proc || exit 2
/bin/busybox mount -t sysfs sysfs /sys || exit 2
/bin/busybox mount -t devtmpfs devtmpfs /dev || exit 2
/bin/busybox test -c /dev/ttyS0 || exit 2
/bin/busybox test -c /dev/ttyS1 || exit 2
/bin/busybox stty -F /dev/ttyS1 raw -echo -opost || exit 2
exec 2>/dev/ttyS0 || exit 2
exec </dev/null >/dev/ttyS1 || exit 2
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


def build_image(assets: TransportAssets, case: str) -> bytes:
    need(type(assets) is TransportAssets, "transport context required")
    assets.__post_init__()
    init = init_bytes(case)
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
    entry("bin/busybox", 0o100755, assets.base.busybox)
    entry("deny-fd-v2-probe", 0o100755, assets.base.probe)
    entry("etc/deny-fd-v2-scope", 0o100444, SCOPE)
    entry("init", 0o100755, init)
    entry("TRAILER!!!", 0)
    raw = gzip.compress(output.getvalue(), mtime=0)
    return raw[:9] + b"\xff" + raw[10:]
