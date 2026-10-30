"""Small independently authored ELF/archive bytes, never executable test payloads."""

import gzip
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


def guest_members():
    result = [
        (name, 0o040755, b"", 0, 0)
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
        )
    ]
    result += [
        ("dev/console", 0o020600, b"", 5, 1),
        ("dev/null", 0o020666, b"", 1, 3),
        ("bin/sh", 0o120777, b"busybox", 0, 0),
        (
            "lib64/ld-linux-x86-64.so.2",
            0o120777,
            b"../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
            0,
            0,
        ),
        ("init", 0o100755, b"#!/bin/busybox sh\necho synthetic\n", 0, 0),
        ("etc/guest-harmless-scope", 0o100444, b"synthetic", 0, 0),
        ("etc/guest-collector-scope", 0o100444, b"synthetic", 0, 0),
        ("bin/busybox", 0o100755, elf_bytes(elf_type=2), 0, 0),
        ("exec-helper", 0o100755, elf_bytes(elf_type=2), 0, 0),
        ("syscall-collector", 0o100755, elf_bytes(elf_type=2), 0, 0),
        (
            "harmless-fixtures",
            0o100755,
            elf_bytes(["libc.so.6"], "/lib64/ld-linux-x86-64.so.2"),
            0,
            0,
        ),
        ("guard.bpf.o", 0o100444, elf_bytes(machine=247, elf_type=1), 0, 0),
    ]
    for soname in (
        "libbpf.so.1",
        "libelf.so.1",
        "libz.so.1",
        "libzstd.so.1",
        "libc.so.6",
        "ld-linux-x86-64.so.2",
    ):
        result.append(("lib/x86_64-linux-gnu/" + soname, 0o100755, elf_bytes(soname=soname), 0, 0))
    return result


def cpio_bytes(members, *, nlink=1, trailer=True):
    raw = bytearray()
    for inode, (name, mode, data, major, minor) in enumerate(members, 1):
        label = name.encode() + b"\0"
        fields = (inode, mode, 0, 0, nlink, 0, len(data), 0, 0, major, minor, len(label), 0)
        raw.extend(b"070701" + b"".join(f"{v:08x}".encode() for v in fields) + label)
        raw.extend(bytes(-len(raw) % 4))
        raw.extend(data)
        raw.extend(bytes(-len(raw) % 4))
    if trailer:
        label = b"TRAILER!!!\0"
        fields = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, len(label), 0)
        raw.extend(b"070701" + b"".join(f"{v:08x}".encode() for v in fields) + label)
        raw.extend(bytes(-len(raw) % 4))
    return bytes(raw)


def image_bytes(members=None, **kwargs):
    return gzip.compress(
        cpio_bytes(guest_members() if members is None else members, **kwargs), mtime=0
    )
