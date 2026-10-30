"""Deterministic diskless guest archive. The shell body runs in the guest only."""

import gzip
import io

from .host_cases import FIXTURES

GUEST_FILES = frozenset(
    (
        "bin/busybox",
        "harmless-fixtures",
        "exec-helper",
        "guard.bpf.o",
        "lib/x86_64-linux-gnu/libbpf.so.1",
        "lib/x86_64-linux-gnu/libelf.so.1",
        "lib/x86_64-linux-gnu/libz.so.1",
        "lib/x86_64-linux-gnu/libzstd.so.1",
        "lib/x86_64-linux-gnu/libc.so.6",
        "lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
    )
)

INIT = """#!/bin/busybox sh
/bin/busybox --install -s /bin
mount -t proc proc /proc || exit 2
mount -t sysfs sysfs /sys || exit 2
mount -t devtmpfs devtmpfs /dev || exit 2
mount -t tmpfs tmpfs /lab || exit 2
mount -t securityfs securityfs /sys/kernel/security || exit 2
mount -t cgroup2 none /sys/fs/cgroup || exit 2
echo ACTUAL_GUEST_KERNEL=$(uname -r)
sha256sum /sys/kernel/btf/vmlinux
for fixture in FIXTURE_SELECTION; do
  /harmless-fixtures "$fixture"
  echo HARNESS_EXIT "$fixture" "$?"
done
echo GUEST_HARNESS_DONE
sync
reboot -f
"""


def build_image(files: dict[str, tuple[int, bytes]], selected: tuple[str, ...]) -> bytes:
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(x not in FIXTURES for x in selected)
    ):
        raise ValueError("invalid fixture selection")
    if not files.keys() <= GUEST_FILES or any(
        mode != (0o100444 if name == "guard.bpf.o" else 0o100755)
        for name, (mode, _) in files.items()
    ):
        raise ValueError("unbound guest archive entry")
    output = io.BytesIO()
    inode = 0

    def entry(name: str, mode: int, data: bytes = b"", major: int = 0, minor: int = 0) -> None:
        nonlocal inode
        inode += 1
        label = name.encode() + b"\0"
        values = (inode, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(label), 0)
        output.write(b"070701" + b"".join(f"{v:08x}".encode() for v in values) + label)
        output.write(b"\0" * (-output.tell() % 4))
        output.write(data)
        output.write(b"\0" * (-output.tell() % 4))

    for name in (
        "bin",
        "sbin",
        "dev",
        "proc",
        "sys",
        "sys/kernel",
        "sys/kernel/security",
        "sys/fs",
        "sys/fs/cgroup",
        "lab",
        "etc",
        "lib",
        "lib/x86_64-linux-gnu",
        "lib64",
    ):
        entry(name, 0o040755)
    # Archive-only bootstrap pseudo-nodes, not host mknod or device-class fixtures.
    entry("dev/console", 0o020600, major=5, minor=1)
    entry("dev/null", 0o020666, major=1, minor=3)
    entry("bin/sh", 0o120777, b"busybox")
    entry("lib64/ld-linux-x86-64.so.2", 0o120777, b"../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2")
    entry("etc/guest-harmless-scope", 0o100444, b"fixed QEMU TCG guest only; no physical devices\n")
    entry("init", 0o100755, INIT.replace("FIXTURE_SELECTION", " ".join(selected)).encode())
    for name, (mode, content) in sorted(files.items()):
        entry(name, mode, content)
    entry("TRAILER!!!", 0)
    return gzip.compress(output.getvalue(), mtime=0)
