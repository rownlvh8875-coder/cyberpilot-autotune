"""Deterministic memory-only initramfs for the seven closed diagnostic cases."""

import gzip
import io

from tests.guest_raw_lifetime.model import require

from .contracts import CASES


def build_image(binary: bytes, case: str) -> bytes:
    require(type(case) is str and case in CASES, "FIXED_CASE_REQUIRED")
    require(
        type(binary) is bytes
        and 6 <= len(binary) <= 2**22
        and binary.startswith(b"\x7fELF\x02\x01"),
        "STATIC_ELF_INPUT_REQUIRED",
    )
    entries = (
        ("dev", 0o040755, b"", 0, 0),
        ("proc", 0o040755, b"", 0, 0),
        ("dev/console", 0o020600, b"", 5, 1),
        ("init", 0o100755, binary, 0, 0),
        ("case", 0o100444, case.encode(), 0, 0),
        ("TRAILER!!!", 0, b"", 0, 0),
    )
    output = io.BytesIO()
    for inode, (name, mode, data, major, minor) in enumerate(entries, 1):
        label = name.encode() + b"\0"
        fields = (inode, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(label), 0)
        output.write(b"070701" + b"".join(f"{n:08x}".encode() for n in fields) + label)
        output.write(b"\0" * (-output.tell() % 4))
        output.write(data)
        output.write(b"\0" * (-output.tell() % 4))
    return gzip.compress(output.getvalue(), mtime=0)
