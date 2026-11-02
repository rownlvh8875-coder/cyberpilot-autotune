"""Closed index decoding and explicit safe filesystem observation (no Git imports)."""

import struct
from hashlib import sha1

from tests.audit_compatibility.git_objects import GitImage, TreeSnapshot

from .contracts import CaptureFault, IndexCapture, IndexEntry, digest, require


def _cache_tree(raw: bytes) -> None:
    def node(pos: int) -> int:
        zero = raw.index(b"\0", pos)
        name = raw[pos:zero]
        require(b"/" not in name and b"\n" not in name, "INDEX_TREE")
        end = raw.index(b"\n", zero)
        count, children = raw[zero + 1 : end].split(b" ")
        require(count == b"-1" or count.isdigit(), "INDEX_TREE")
        require(children.isdigit(), "INDEX_TREE")
        pos = end + 1 + (20 if int(count) >= 0 else 0)
        require(pos <= len(raw), "INDEX_TREE")
        for _ in range(int(children)):
            pos = node(pos)
        return pos

    require(node(0) == len(raw), "INDEX_TREE")


def parse_index(raw: bytes) -> IndexCapture:
    try:
        require(type(raw) is bytes and len(raw) >= 32 and raw[:4] == b"DIRC", "INDEX_FORMAT")
        require(sha1(raw[:-20]).digest() == raw[-20:], "INDEX_CHECKSUM")
        version, count = struct.unpack(">II", raw[4:12])
        require(version in (2, 3), "INDEX_VERSION", unavailable=True)
        pos, rows = 12, []
        for _ in range(count):
            start = pos
            require(pos + 62 <= len(raw) - 20, "INDEX_ENTRY")
            mode = struct.unpack(">I", raw[pos + 24 : pos + 28])[0]
            obj = raw[pos + 40 : pos + 60].hex()
            flags = struct.unpack(">H", raw[pos + 60 : pos + 62])[0]
            require(not flags & 0xF000, "INDEX_FLAGS")
            end = raw.index(b"\0", pos + 62, len(raw) - 20)
            name = raw[pos + 62 : end].decode("utf-8", "strict")
            require(flags & 4095 == min(len(raw[pos + 62 : end]), 4095), "INDEX_NAME")
            pos = start + ((end + 1 - start + 7) // 8) * 8
            require(pos <= len(raw) - 20 and not any(raw[end:pos]), "INDEX_PADDING")
            require(mode == 0o100644, "INDEX_MODE")
            rows.append(IndexEntry(name, "100644", obj, flags))
        # Validate the complete set before an unsupported extension/version can hide errors.
        TreeSnapshot(tuple((r.path, GitImage(r.mode, b"")) for r in rows))
        require([r.path for r in rows] == sorted(r.path for r in rows), "INDEX_ORDER")
        extensions: list[tuple[str, bytes]] = []
        unsupported = version != 2
        while pos < len(raw) - 20:
            require(pos + 8 <= len(raw) - 20, "INDEX_EXTENSION")
            signature, size = raw[pos : pos + 4], struct.unpack(">I", raw[pos + 4 : pos + 8])[0]
            pos += 8
            require(pos + size <= len(raw) - 20, "INDEX_EXTENSION")
            value = raw[pos : pos + size]
            pos += size
            if signature == b"TREE":
                require(not extensions, "INDEX_EXTENSION_DUPLICATE")
                _cache_tree(value)
                extensions.append(("TREE", value))
            else:
                unsupported = True
        require(not unsupported, "INDEX_FEATURE", unavailable=True)
        return IndexCapture(digest(raw), version, tuple(rows), tuple(extensions))
    except (ValueError, struct.error, RecursionError) as error:
        raise CaptureFault("INDEX_FORMAT") from error
