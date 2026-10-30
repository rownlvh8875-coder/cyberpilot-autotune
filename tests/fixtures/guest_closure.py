"""Small independently authored ELF/archive bytes, never executable test payloads."""

import struct


def elf_bytes(needed=(), interpreter=None, soname=None, extra=(), machine=62, elf_type=3):
    ident = b"\x7fELF\x02\x01\x01" + bytes(9)
    if elf_type == 1:
        return struct.pack("<16sHHIQQQIHHHHHH", ident, 1, machine, 1, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0)
    strings = bytearray(b"\0")
    dynamic = []
    for tag, value in [(1, s) for s in needed] + ([(14, soname)] if soname else []) + list(extra):
        offset = len(strings)
        strings.extend(value.encode() + b"\0")
        dynamic.append((tag, offset))
    dynamic = [(5, 0x400300), (10, len(strings)), *dynamic, (0, 0)]
    raw = bytearray(4096)
    segments = [(1, 5, 0, 0x400000, 0, len(raw), len(raw), 4096)]
    table = b"".join(struct.pack("<qQ", *item) for item in dynamic)
    segments.append((2, 6, 0x180, 0x400180, 0, len(table), len(table), 8))
    raw[0x180 : 0x180 + len(table)] = table
    if interpreter is not None:
        text = interpreter.encode() + b"\0"
        raw[0x280 : 0x280 + len(text)] = text
        segments.append((3, 4, 0x280, 0x400280, 0, len(text), len(text), 1))
    raw[0x300 : 0x300 + len(strings)] = strings
    raw[:64] = struct.pack(
        "<16sHHIQQQIHHHHHH",
        ident,
        elf_type,
        machine,
        1,
        0,
        64,
        0,
        0,
        64,
        56,
        len(segments),
        0,
        0,
        0,
    )
    for index, segment in enumerate(segments):
        raw[64 + index * 56 : 120 + index * 56] = struct.pack("<IIQQQQQQ", *segment)
    return bytes(raw)
