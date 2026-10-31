"""Memory-only deterministic newc initramfs for ten fixed guest modes."""

import gzip
import io

from tests.guest_raw_lifetime.model import require

from .contracts import CASES


def build_image(binary: bytes, case: str) -> bytes:
    require(type(case) is str and case in CASES, "FIXED_CASE_REQUIRED")
    require(
        type(binary) is bytes
        and 6 <= len(binary) <= 4 * 1024 * 1024
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
    stream = io.BytesIO()
    for inode, (name, mode, data, major, minor) in enumerate(entries, 1):
        label = name.encode() + b"\0"
        fields = (inode, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(label), 0)
        stream.write(b"070701" + b"".join(f"{n:08x}".encode() for n in fields) + label)
        stream.write(b"\0" * (-stream.tell() % 4))
        stream.write(data)
        stream.write(b"\0" * (-stream.tell() % 4))
    return gzip.compress(stream.getvalue(), mtime=0)
