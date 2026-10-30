"""Bounded ELF64 little-endian program metadata parser; no loader invocation."""

import struct

from .contracts import ElfInfo

MAX_ELF_BYTES = 64 * 1024 * 1024
LOADER_DIRECTIVES = {0x6FFFFEFA, 0x6FFFFEFB, 0x6FFFFEFC, 0x7FFFFFFD, 0x7FFFFFFF}


def inspect_elf(data: bytes) -> ElfInfo:
    if type(data) is not bytes or not 64 <= len(data) <= MAX_ELF_BYTES:
        raise ValueError("ELF length outside profile")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", data)
    ident, elf_type, machine, version, _, phoff, _, _, ehsize, phsize, count, *_ = header
    if ident[:7] != b"\x7fELF\x02\x01\x01" or version != 1 or ehsize != 64:
        raise ValueError("unsupported ELF header")
    if count > 256 or (count and (phsize != 56 or phoff < 64 or phoff + count * 56 > len(data))):
        raise ValueError("invalid program header table")
    loads: list[tuple[int, int, int]] = []
    dynamic: tuple[int, int, int] | None = None
    interpreter = None
    for index in range(count):
        kind, _, offset, address, _, filesz, memsz, alignment = struct.unpack_from(
            "<IIQQQQQQ", data, phoff + index * 56
        )
        if offset + filesz > len(data) or filesz > memsz or address + memsz > 2**64:
            raise ValueError("invalid program segment bounds")
        if kind == 1:
            if alignment > 1 and (alignment & (alignment - 1) or (address - offset) % alignment):
                raise ValueError("invalid load alignment")
            loads.append((address, offset, filesz))
        elif kind == 2:
            if dynamic is not None or not filesz or filesz % 16 or filesz > 65536:
                raise ValueError("invalid dynamic table")
            dynamic = (offset, filesz, address)
        elif kind == 3:
            raw = data[offset : offset + filesz]
            if interpreter is not None or not 2 <= len(raw) <= 4096 or raw[-1:] != b"\0":
                raise ValueError("invalid interpreter")
            try:
                interpreter = raw[:-1].decode("ascii")
            except UnicodeError as error:
                raise ValueError("invalid interpreter text") from error
            if not interpreter.startswith("/") or "\0" in interpreter:
                raise ValueError("invalid interpreter path")
    if elf_type in {2, 3} and not loads:
        raise ValueError("native executable has no loadable segment")
    tags: dict[int, list[int]] = {}
    if dynamic is not None:
        offset, size, dynamic_address = dynamic
        mapped = [
            file_offset + dynamic_address - start
            for start, file_offset, length in loads
            if start <= dynamic_address and dynamic_address + size <= start + length
        ]
        if mapped != [offset]:
            raise ValueError("ambiguous or inconsistent dynamic address mapping")
        terminated = False
        for index in range(offset, offset + size, 16):
            tag, value = struct.unpack_from("<qQ", data, index)
            if tag == 0:
                terminated = True
                break
            tags.setdefault(tag, []).append(value)
        if not terminated:
            raise ValueError("unterminated dynamic table")

    def single(tag: int) -> int | None:
        values = tags.get(tag, [])
        if len(values) > 1:
            raise ValueError("duplicate singleton dynamic tag")
        return values[0] if values else None

    string_address, string_size = single(5), single(10)
    strings = b""
    if tags:
        if string_address is None or string_size is None or not 0 < string_size <= MAX_ELF_BYTES:
            raise ValueError("missing or invalid dynamic string table")
        offsets = [
            offset + string_address - start
            for start, offset, n in loads
            if start <= string_address and string_address + string_size <= start + n
        ]
        if len(offsets) != 1:
            raise ValueError("unmapped or ambiguous string table")
        strings = data[offsets[0] : offsets[0] + string_size]

    def string(value: int | None) -> str | None:
        if value is None:
            return None
        end = strings.find(b"\0", value)
        if value >= len(strings) or end < 0 or not 0 < end - value <= 4096:
            raise ValueError("invalid dynamic string bounds")
        try:
            return strings[value:end].decode("ascii")
        except UnicodeError as error:
            raise ValueError("invalid dynamic string text") from error

    needed = tuple(string(value) for value in tags.get(1, []))
    return ElfInfo(
        machine,
        elf_type,
        interpreter,
        tuple(value for value in needed if value is not None),
        string(single(14)),
        string(single(15)),
        string(single(29)),
        tuple(sorted(LOADER_DIRECTIVES & tags.keys())),
    )
