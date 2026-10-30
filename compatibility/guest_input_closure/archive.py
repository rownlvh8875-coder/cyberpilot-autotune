"""Strict newc byte parsing and a fixed virtual ELF namespace; no extraction."""

import stat
import zlib
from collections import deque

from .contracts import ImageMember
from .elf import inspect_elf

MAX_IMAGE_BYTES = 32 * 1024 * 1024
DIRECTORIES = frozenset(
    (
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
)
EXECUTABLES = frozenset(("bin/busybox", "exec-helper", "harmless-fixtures", "syscall-collector"))
LIBDIR = "lib/x86_64-linux-gnu/"
LIBRARIES = frozenset(
    LIBDIR + name
    for name in (
        "libbpf.so.1",
        "libelf.so.1",
        "libz.so.1",
        "libzstd.so.1",
        "libc.so.6",
        "ld-linux-x86-64.so.2",
    )
)
LINKS = frozenset(("bin/sh", "lib64/ld-linux-x86-64.so.2"))
DATA_FILES = frozenset(("etc/guest-harmless-scope", "etc/guest-collector-scope", "guard.bpf.o"))
PSEUDO_NODES = frozenset(("dev/console", "dev/null"))
IMAGE_PATHS = DIRECTORIES | EXECUTABLES | LIBRARIES | LINKS | DATA_FILES | PSEUDO_NODES | {"init"}


def parse_image(data: bytes) -> tuple[ImageMember, ...]:
    if type(data) is not bytes or not 1 <= len(data) <= MAX_IMAGE_BYTES:
        raise ValueError("image outside resource bounds")
    decoder = zlib.decompressobj(31)
    try:
        raw = decoder.decompress(data, MAX_IMAGE_BYTES + 1)
    except zlib.error as error:
        raise ValueError("invalid gzip image") from error
    if (
        len(raw) > MAX_IMAGE_BYTES
        or decoder.unconsumed_tail
        or decoder.unused_data
        or not decoder.eof
    ):
        raise ValueError("image truncated, concatenated or exceeds bounds")
    offset = 0
    members: list[ImageMember] = []
    names: set[str] = set()
    inodes: set[int] = set()
    while offset < len(raw) and len(members) <= 10000:
        if raw[offset : offset + 6] != b"070701" or offset + 110 > len(raw):
            raise ValueError("invalid newc header")
        fields = []
        for index in range(13):
            text = raw[offset + 6 + index * 8 : offset + 14 + index * 8]
            if any(v not in b"0123456789abcdefABCDEF" for v in text):
                raise ValueError("invalid newc integer")
            fields.append(int(text, 16))
        inode, mode, uid, gid, nlink, _, size, devmajor, devminor, major, minor, namelen, check = (
            fields
        )
        if not 2 <= namelen <= 4097 or offset + 110 + namelen > len(raw):
            raise ValueError("invalid archive name length")
        label = raw[offset + 110 : offset + 110 + namelen]
        if label[-1:] != b"\0" or b"\0" in label[:-1]:
            raise ValueError("invalid archive name termination")
        try:
            name = label[:-1].decode("utf-8")
        except UnicodeError as error:
            raise ValueError("invalid archive name text") from error
        offset = (offset + 110 + namelen + 3) & ~3
        if offset + size > len(raw):
            raise ValueError("truncated archive content")
        content = raw[offset : offset + size]
        offset = (offset + size + 3) & ~3
        if uid or gid or check or devmajor or devminor:
            raise ValueError("unsupported archive metadata")
        if name == "TRAILER!!!":
            if mode or size or major or minor or len(raw) - offset > 511 or any(raw[offset:]):
                raise ValueError("invalid archive trailer")
            return tuple(members)
        if nlink != 1 or inode == 0 or inode in inodes or name in names:
            raise ValueError("duplicate name/inode or hardlink ambiguity")
        names.add(name)
        inodes.add(inode)
        members.append(ImageMember(name, mode, content, major, minor))
    raise ValueError("archive trailer missing or entry bound exceeded")


def _resolve(path: str, members: dict[str, ImageMember]) -> ImageMember:
    pending = deque(path.split("/"))
    resolved: list[str] = []
    links = 0
    seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
    while pending:
        part = pending.popleft()
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                raise ValueError("link escapes guest namespace")
            resolved.pop()
            continue
        name = "/".join((*resolved, part))
        entry = members.get(name)
        if entry is None:
            raise ValueError("guest dependency missing: " + name)
        if stat.S_ISLNK(entry.mode):
            state = (tuple(resolved), tuple((part, *pending)))
            if state in seen or links >= 40:
                raise ValueError("guest symlink cycle or expansion bound exceeded")
            seen.add(state)
            links += 1
            target = entry.data.decode("utf-8")
            if target.startswith("/"):
                resolved.clear()
            pending.extendleft(reversed(target.split("/")))
        else:
            if pending and not stat.S_ISDIR(entry.mode):
                raise ValueError("guest path parent is not a directory")
            resolved.append(part)
    final = members.get("/".join(resolved))
    if final is None:
        raise ValueError("guest namespace root is not a code object")
    return final


def guest_dependencies(members: tuple[ImageMember, ...]) -> tuple[tuple[str, str, str], ...]:
    by_name = {entry.path: entry for entry in members}
    if len(by_name) != len(members) or by_name.keys() != IMAGE_PATHS:
        raise ValueError("archive does not match fixed guest namespace")
    for entry in members:
        entry.__post_init__()
        expected_mode = (
            0o040755
            if entry.path in DIRECTORIES
            else 0o120777
            if entry.path in LINKS
            else 0o100444
            if entry.path in DATA_FILES
            else (0o020600 if entry.path == "dev/console" else 0o020666)
            if entry.path in PSEUDO_NODES
            else 0o100755
        )
        if entry.mode != expected_mode:
            raise ValueError("guest entry mode mismatch")
        if entry.path in LINKS:
            resolved = _resolve(entry.path, by_name)
            required = "bin/busybox" if entry.path == "bin/sh" else LIBDIR + "ld-linux-x86-64.so.2"
            if resolved.path != required:
                raise ValueError("bootstrap link resolves to wrong object")
    if not by_name["init"].data.startswith(b"#!/bin/busybox sh\n"):
        raise ValueError("unsupported init interpreter")
    bpf = inspect_elf(by_name["guard.bpf.o"].data)
    if bpf.machine != 247 or bpf.elf_type != 1 or bpf.interpreter or bpf.needed:
        raise ValueError("wrong BPF object identity")
    edges = {("init", "SHEBANG:/bin/busybox", "bin/busybox")}
    for name in sorted(EXECUTABLES | LIBRARIES):
        info = inspect_elf(by_name[name].data)
        if info.machine != 62 or info.elf_type not in {2, 3}:
            raise ValueError("wrong native ELF identity")
        if name in LIBRARIES and info.elf_type != 3:
            raise ValueError("dependency is not a shared ELF object")
        if info.flags & ~0x18 or info.flags_1 & ~0x8000001:
            raise ValueError("unsupported ELF dynamic search flags")
        if info.rpath is not None or info.runpath is not None or info.loader_directives:
            raise ValueError("unsupported loader search/configuration/audit/filter")
        if name in LIBRARIES and info.soname not in {None, name.removeprefix(LIBDIR)}:
            raise ValueError("library SONAME mismatch")
        if info.interpreter is not None:
            if info.interpreter != "/lib64/ld-linux-x86-64.so.2":
                raise ValueError("unsupported native interpreter")
            target = _resolve(info.interpreter, by_name)
            if target.path != LIBDIR + "ld-linux-x86-64.so.2":
                raise ValueError("wrong interpreter object")
            edges.add((name, "INTERP:" + info.interpreter, target.path))
        for needed in info.needed:
            if "/" in needed or needed in {".", ".."}:
                raise ValueError("dependency outside fixed library search")
            target = _resolve(LIBDIR + needed, by_name)
            if target.path not in LIBRARIES:
                raise ValueError("dependency is not a declared library")
            edges.add((name, "NEEDED:" + needed, target.path))
    return tuple(sorted(edges))
