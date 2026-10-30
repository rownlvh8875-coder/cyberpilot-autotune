"""Derived diskless image; preserve all frozen fixture assets byte-for-byte."""

import gzip
import io

from compatibility.containment_backend_harmless.guest_image import GUEST_FILES, build_image


def build_collector_image(
    files: dict[str, tuple[int, bytes]], collector: bytes, selected: tuple[str, ...]
) -> bytes:
    if set(files) != GUEST_FILES or type(collector) is not bytes:
        raise ValueError("fixed complete guest assets required")
    base = gzip.decompress(build_image(files, selected))
    output = io.BytesIO()

    def emit(name: str, fields: list[int], content: bytes) -> None:
        label = name.encode() + b"\0"
        fields[6] = len(content)
        fields[11] = len(label)
        output.write(b"070701" + b"".join(f"{n:08x}".encode() for n in fields) + label)
        output.write(b"\0" * (-output.tell() % 4))
        output.write(content)
        output.write(b"\0" * (-output.tell() % 4))

    offset = 0
    while base[offset : offset + 6] == b"070701":
        fields = [int(base[offset + 6 + 8 * i : offset + 14 + 8 * i], 16) for i in range(13)]
        name = base[offset + 110 : offset + 109 + fields[11]].decode()
        offset = (offset + 110 + fields[11] + 3) & ~3
        content = base[offset : offset + fields[6]]
        offset = (offset + fields[6] + 3) & ~3
        if name == "TRAILER!!!":
            break
        if name == "init":
            original = b'/harmless-fixtures "$fixture"'
            if content.count(original) != 1:
                raise ValueError("frozen init semantics changed")
            content = content.replace(original, b'/syscall-collector "$fixture"')
        emit(name, fields, content)
    emit("syscall-collector", [99999, 0o100755, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], collector)
    emit(
        "etc/guest-collector-scope",
        [99998, 0o100444, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        b"guest-syscall-fd-v1: fixed same software guest only\n",
    )
    emit("TRAILER!!!", [0] * 13, b"")
    return gzip.compress(output.getvalue(), mtime=0)
