"""Exact S-only default-ALLOW toy denylist;NOT an H/hostile-code security policy."""

import struct


def seccomp_bytes() -> bytes:
    program = [
        (0x20, 0, 0, 4),
        (0x15, 1, 0, 0xC000003E),
        (0x06, 0, 0, 0x80000000),
        (0x20, 0, 0, 0),
        (0x35, 0, 1, 0x40000000),
        (0x06, 0, 0, 0x80000000),
    ]
    for syscall in (
        *range(41, 56),
        155,
        165,
        166,
        272,
        288,
        299,
        307,
        308,
        428,
        429,
        430,
        431,
        432,
        435,
        442,
    ):
        program.extend(((0x15, 0, 1, syscall), (0x06, 0, 0, 0x00050001)))
    program.append((0x06, 0, 0, 0x7FFF0000))
    return b"".join(struct.pack("<HBBI", *row) for row in program)
