"""Malformed metadata cannot bypass explicit content and resource boundaries."""

import gzip
import struct
from dataclasses import replace

import pytest

from compatibility.guest_input_closure.archive import guest_dependencies, parse_image
from compatibility.guest_input_closure.contracts import (
    ElfInfo,
    ImageMember,
    InputEntry,
    InputSnapshot,
)
from compatibility.guest_input_closure.elf import inspect_elf
from compatibility.guest_input_closure.evaluation import evaluate_closure
from compatibility.guest_input_closure.inventory import parse_snapshot
from tests.fixtures.guest_closure import cpio_bytes, elf_bytes, guest_members, image_bytes


@pytest.mark.parametrize(
    "data",
    [
        '{"version":"guest-input-snapshot-v1","entries":{}}',
        '{"version":"guest-input-snapshot-v1","entries":[{}]}',
    ],
)
def test_unavailable_entry_collection_cannot_be_a_snapshot(data):
    with pytest.raises(ValueError):
        parse_snapshot(data)


@pytest.mark.parametrize(
    "kind,mode,size,sha,target,path",
    [
        ("file", 0o100444, 0, None, None, "."),
        ("directory", 0o040755, 0, "0" * 64, None, "d"),
        ("directory", 0o040755, 1, None, None, "d"),
        ("directory", 0o040755, 0, None, "x", "d"),
        ("symlink", 0o120777, 0, None, "", "link"),
        ("symlink", 0o120777, 1, None, None, "link"),
        ("symlink", 0o120777, 1, None, "\0", "link"),
        ("symlink", 0o120777, 2, None, "x", "link"),
        ("file", 0o177777 + 1, 1, "0" * 64, None, "a"),
    ],
)
def test_entry_kind_and_available_value_are_a_single_consistent_record(
    kind, mode, size, sha, target, path
):
    with pytest.raises(ValueError):
        InputEntry("test", path, kind, mode, size, sha, target)


def test_snapshot_rejects_non_entry_rows():
    with pytest.raises(ValueError):
        InputSnapshot([None])


@pytest.mark.parametrize(
    "changes",
    [
        {"machine": True},
        {"elf_type": 65536},
        {"interpreter": ""},
        {"needed": ["a\0b"]},
        {"loader_directives": [False]},
    ],
)
def test_invalid_elf_metadata_cannot_be_a_dependency_receipt(changes):
    with pytest.raises(ValueError):
        replace(ElfInfo(62, 3, None, (), None, None, None, ()), **changes)


@pytest.mark.parametrize(
    "mode,data,major,minor",
    [
        (True, b"", 0, 0),
        (0o100755, bytearray(), 0, 0),
        (0o100755, b"", True, 0),
        (0o040755, b"not empty", 0, 0),
        (0o120777, b"\xff", 0, 0),
        (0o120777, b"", 0, 0),
        (0o120777, b"\0", 0, 0),
        (0o100755, b"", 1, 3),
    ],
)
def test_image_member_cannot_change_kind_or_acquire_device_semantics(mode, data, major, minor):
    with pytest.raises(ValueError):
        ImageMember("a", mode, data, major, minor)


@pytest.mark.parametrize(
    "changes",
    [
        {"declared_inputs_match": 1},
        {"entry_count": False},
        {"image_digests": ["bad"]},
        {"issues": [None]},
        {"dependency_edges": [["a", "b"]]},
    ],
)
def test_report_values_are_not_coerced_or_exposed_as_mutable_authority(changes):
    report = evaluate_closure(InputSnapshot([]), InputSnapshot([]), (image_bytes(),))
    with pytest.raises(ValueError):
        replace(report, **changes)


@pytest.mark.parametrize("images", [(bytearray(b"x"),), tuple(b"x" for _ in range(25))])
def test_image_selection_cannot_silently_exceed_the_fixed_profile(images):
    with pytest.raises(ValueError):
        evaluate_closure(InputSnapshot([]), InputSnapshot([]), images)


@pytest.mark.parametrize(
    "change",
    [
        "dynamic-size",
        "interp-utf8",
        "interp-relative",
        "strtab-missing",
        "strsize-zero",
        "string-utf8",
    ],
)
def test_bad_elf_text_and_dynamic_layout_remain_unavailable(change):
    raw = bytearray(elf_bytes(["libc.so.6"], "/lib64/ld-linux-x86-64.so.2"))
    if change == "dynamic-size":
        struct.pack_into("<Q", raw, 120 + 32, 15)
    elif change == "interp-utf8":
        raw[0x280] = 255
    elif change == "interp-relative":
        raw[0x280] = 65
    elif change == "strtab-missing":
        struct.pack_into("<q", raw, 0x180, 9)
    elif change == "strsize-zero":
        struct.pack_into("<Q", raw, 0x198, 0)
    else:
        raw[0x301] = 255
    with pytest.raises(ValueError):
        inspect_elf(bytes(raw))


@pytest.mark.parametrize(
    "field,value", [(2, 1), (3, 1), (7, 1), (8, 1), (11, 0), (11, 5000), (12, 1)]
)
def test_archive_fields_cannot_change_owner_namespace_or_read_unbounded_names(field, value):
    raw = bytearray(cpio_bytes(guest_members()))
    raw[6 + 8 * field : 14 + 8 * field] = f"{value:08x}".encode()
    with pytest.raises(ValueError):
        parse_image(gzip.compress(raw, mtime=0))


def test_non_hex_and_non_utf8_archive_metadata_is_rejected():
    raw = bytearray(cpio_bytes(guest_members()))
    raw[7] = ord("z")
    with pytest.raises(ValueError):
        parse_image(gzip.compress(raw, mtime=0))
    raw = bytearray(cpio_bytes(guest_members()))
    raw[110] = 255
    with pytest.raises(ValueError):
        parse_image(gzip.compress(raw, mtime=0))


def test_gzip_and_image_resource_bounds_are_enforced(monkeypatch):
    from compatibility.guest_input_closure import archive

    for raw in (b"", bytearray(b"x"), image_bytes()[:-2]):
        with pytest.raises(ValueError):
            parse_image(raw)
    monkeypatch.setattr(archive, "MAX_IMAGE_BYTES", 2048)
    with pytest.raises(ValueError):
        parse_image(gzip.compress(b"0" * 4096, mtime=0))


@pytest.mark.parametrize(
    "name,data,mode",
    [
        ("harmless-fixtures", elf_bytes(interpreter="/unknown"), 0o100755),
        ("lib64/ld-linux-x86-64.so.2", b"../lib/x86_64-linux-gnu/libc.so.6", 0o120777),
        ("harmless-fixtures", elf_bytes(), 0o100644),
    ],
)
def test_an_available_file_cannot_substitute_for_the_exact_loader_object_or_mode(name, data, mode):
    rows = [(r[0], mode, data, *r[3:]) if r[0] == name else r for r in guest_members()]
    with pytest.raises(ValueError):
        guest_dependencies(parse_image(image_bytes(rows)))
