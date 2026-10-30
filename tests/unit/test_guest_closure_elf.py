"""ELF dependencies come from bounded program bytes, not filenames or ldd."""

import importlib
import struct

import pytest

from tests.fixtures.guest_closure import elf_bytes


def inspect(data):
    assert importlib.util.find_spec("compatibility.guest_input_closure") is not None
    return importlib.import_module("compatibility.guest_input_closure.elf").inspect_elf(data)


def test_actual_program_header_strings_are_exposed_without_execution():
    result = inspect(elf_bytes(["libc.so.6"], "/lib64/ld-linux-x86-64.so.2", "fixture"))
    assert (result.machine, result.elf_type) == (62, 3)
    assert result.interpreter == "/lib64/ld-linux-x86-64.so.2"
    assert result.needed == ("libc.so.6",) and result.soname == "fixture"
    assert result.rpath is None and result.runpath is None
    assert inspect(elf_bytes(machine=247, elf_type=1)).needed == ()


@pytest.mark.parametrize("tag,field", [(15, "rpath"), (29, "runpath")])
def test_loader_search_directives_are_observed_not_silently_discarded(tag, field):
    assert getattr(inspect(elf_bytes(extra=[(tag, "$ORIGIN/extra")])), field) == "$ORIGIN/extra"


@pytest.mark.parametrize("tag", [0x6FFFFEFA, 0x6FFFFEFB, 0x6FFFFEFC, 0x7FFFFFFD, 0x7FFFFFFF])
def test_loader_configuration_audit_and_filter_directives_are_visible(tag):
    assert inspect(elf_bytes(extra=[(tag, "extra.so")])).loader_directives == (tag,)


@pytest.mark.parametrize(
    "change",
    [
        "magic",
        "class",
        "endian",
        "version",
        "phsize",
        "phcount",
        "offset",
        "segment",
        "string-address",
        "string-size",
        "missing-null",
        "needed-offset",
        "unterminated",
        "duplicate-strtab",
        "duplicate-needed",
        "duplicate-interp",
    ],
)
def test_malformed_program_or_dynamic_bounds_reject_instead_of_closing_graph(change):
    raw = bytearray(elf_bytes(["libc.so.6"], "/lib64/ld-linux-x86-64.so.2"))
    if change in {"magic", "class", "endian", "version"}:
        raw[{"magic": 0, "class": 4, "endian": 5, "version": 6}[change]] = 0
    elif change == "phsize":
        struct.pack_into("<H", raw, 54, 1)
    elif change == "phcount":
        struct.pack_into("<H", raw, 56, 1000)
    elif change == "offset":
        struct.pack_into("<Q", raw, 32, 2**63)
    elif change == "segment":
        struct.pack_into("<Q", raw, 64 + 32, 2**63)
    elif change == "string-address":
        struct.pack_into("<Q", raw, 0x188, 2**63)
    elif change == "string-size":
        struct.pack_into("<Q", raw, 0x198, 2**63)
    elif change == "missing-null":
        struct.pack_into("<qQ", raw, 0x1B0, 1, 1)
    elif change == "needed-offset":
        struct.pack_into("<Q", raw, 0x1A8, 2**63)
    elif change == "unterminated":
        raw[0x30A] = 65
    elif change == "duplicate-strtab":
        struct.pack_into("<qQ", raw, 0x1A0, 5, 0x400300)
    elif change == "duplicate-needed":
        struct.pack_into("<qQ", raw, 0x1B0, 1, 1)
    else:
        raw[120:176] = raw[176:232]
    with pytest.raises(ValueError):
        inspect(bytes(raw))


@pytest.mark.parametrize("data", [b"", b"\x7fELF", elf_bytes()[:63], elf_bytes()[:200]])
def test_short_files_are_unavailable_not_static_executables(data):
    with pytest.raises(ValueError):
        inspect(data)


def test_header_only_file_cannot_impersonate_a_static_native_executable():
    raw = bytearray(elf_bytes())
    struct.pack_into("<H", raw, 56, 0)
    with pytest.raises(ValueError):
        inspect(bytes(raw))


def test_duplicate_needed_dependency_is_not_silently_deduplicated():
    with pytest.raises(ValueError):
        inspect(elf_bytes(["libc.so.6", "libc.so.6"]))


def test_overlapping_load_mappings_cannot_choose_an_arbitrary_string_table():
    raw = bytearray(elf_bytes(["libc.so.6"]))
    struct.pack_into("<H", raw, 56, 3)
    raw[176:232] = raw[64:120]
    with pytest.raises(ValueError):
        inspect(bytes(raw))


@pytest.mark.parametrize("change", ["dynamic-mapping", "address-overflow", "load-alignment"])
def test_file_offsets_cannot_substitute_for_the_actual_loader_address_mapping(change):
    raw = bytearray(elf_bytes(["libc.so.6"]))
    if change == "dynamic-mapping":
        struct.pack_into("<Q", raw, 120 + 16, 0x400000)
    elif change == "address-overflow":
        struct.pack_into("<H", raw, 56, 1)
        struct.pack_into("<Q", raw, 64 + 16, 2**64 - 1)
    else:
        struct.pack_into("<Q", raw, 64 + 48, 3)
    with pytest.raises(ValueError):
        inspect(bytes(raw))
