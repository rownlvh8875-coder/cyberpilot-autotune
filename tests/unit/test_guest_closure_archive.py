"""Untrusted archives are parsed as a virtual namespace, never extracted."""

import gzip
import importlib

import pytest

from tests.fixtures.guest_closure import cpio_bytes, elf_bytes, guest_members, image_bytes


def module():
    assert importlib.util.find_spec("compatibility.guest_input_closure.archive") is not None
    return importlib.import_module("compatibility.guest_input_closure.archive")


def test_literal_fixed_image_has_exact_dependency_edges():
    m = module()
    members = m.parse_image(image_bytes())
    edges = m.guest_dependencies(members)
    assert len(members) == 32
    assert edges == (
        (
            "harmless-fixtures",
            "INTERP:/lib64/ld-linux-x86-64.so.2",
            "lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
        ),
        ("harmless-fixtures", "NEEDED:libc.so.6", "lib/x86_64-linux-gnu/libc.so.6"),
        ("init", "SHEBANG:/bin/busybox", "bin/busybox"),
    )


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a/../b", "a//b", "a\\b", "a\0b"])
def test_archive_name_cannot_alias_or_escape_the_namespace(name):
    with pytest.raises(ValueError):
        module().parse_image(image_bytes([(name, 0o100444, b"x", 0, 0)]))


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "hardlink",
        "no-trailer",
        "bad-magic",
        "short-header",
        "short-content",
        "bad-name-null",
        "trailing",
        "second-gzip",
        "fifo",
        "wrong-node",
    ],
)
def test_malformed_or_ambiguous_archive_is_not_a_complete_image(change):
    rows = guest_members()
    if change == "duplicate":
        rows.append(rows[0])
    if change == "fifo":
        rows.append(("pipe", 0o010600, b"", 0, 0))
    if change == "wrong-node":
        rows.append(("dev/other", 0o020600, b"", 1, 3))
    raw = cpio_bytes(rows, nlink=2 if change == "hardlink" else 1, trailer=change != "no-trailer")
    if change == "bad-magic":
        raw = b"070702" + raw[6:]
    if change == "short-header":
        raw = raw[:50]
    if change == "short-content":
        raw = raw[:-1000]
    if change == "bad-name-null":
        raw = raw[:113] + b"x" + raw[114:]
    if change == "trailing":
        raw += b"hidden archive"
    blob = gzip.compress(raw, mtime=0)
    if change == "second-gzip":
        blob += gzip.compress(b"hidden", mtime=0)
    with pytest.raises(ValueError):
        module().parse_image(blob)


@pytest.mark.parametrize("target", [b"sh", b"../../outside", b"/outside", b"busybox/child"])
def test_guest_links_cannot_choose_host_paths_cycles_or_non_directory_parents(target):
    rows = [(*row[:2], target, *row[3:]) if row[0] == "bin/sh" else row for row in guest_members()]
    m = module()
    with pytest.raises(ValueError):
        m.guest_dependencies(m.parse_image(image_bytes(rows)))


@pytest.mark.parametrize(
    "change",
    [
        "missing-lib",
        "missing-interpreter",
        "machine",
        "bpf",
        "rpath",
        "runpath",
        "audit",
        "filter",
        "needed-slash",
        "soname",
        "script",
        "unknown-executable",
        "loader-config",
    ],
)
def test_unsupported_loader_semantics_cannot_silently_close_the_graph(change):
    rows = guest_members()
    replacements = {
        "machine": elf_bytes(machine=183),
        "rpath": elf_bytes(extra=[(15, "$ORIGIN")]),
        "runpath": elf_bytes(extra=[(29, "/lab")]),
        "audit": elf_bytes(extra=[(0x6FFFFEFC, "audit.so")]),
        "filter": elf_bytes(extra=[(0x7FFFFFFF, "filter.so")]),
        "needed-slash": elf_bytes(["/lab/lib.so"]),
    }
    for index, row in enumerate(rows):
        name, mode, data, major, minor = row
        if name == "harmless-fixtures" and change in replacements:
            data = replacements[change]
        if name == "guard.bpf.o" and change == "bpf":
            data = elf_bytes()
        if name == "lib/x86_64-linux-gnu/libc.so.6" and change == "soname":
            data = elf_bytes(soname="wrong.so")
        if name == "init" and change == "script":
            data = b"#!/usr/bin/env sh\n"
        rows[index] = (name, mode, data, major, minor)
    if change == "missing-lib":
        rows = [r for r in rows if r[0] != "lib/x86_64-linux-gnu/libc.so.6"]
    if change == "missing-interpreter":
        rows = [r for r in rows if r[0] != "lib64/ld-linux-x86-64.so.2"]
    if change == "unknown-executable":
        rows.append(("extra", 0o100755, b"unknown", 0, 0))
    if change == "loader-config":
        rows.append(("etc/ld.so.preload", 0o100444, b"extra.so", 0, 0))
    m = module()
    with pytest.raises(ValueError):
        m.guest_dependencies(m.parse_image(image_bytes(rows)))
