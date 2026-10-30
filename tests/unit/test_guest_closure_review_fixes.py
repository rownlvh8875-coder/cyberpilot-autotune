"""Independent review counterexamples must reject, even with overall BLOCKED."""

import hashlib
import json
import struct
import sys

import pytest

from compatibility.guest_input_closure.contracts import InputSnapshot
from compatibility.guest_input_closure.evaluation import evaluate_closure
from tests.fixtures.guest_closure import elf_bytes, guest_members, image_bytes


def assessment(name, raw):
    rows = [(r[0], r[1], bytes(raw), *r[3:]) if r[0] == name else r for r in guest_members()]
    return evaluate_closure(InputSnapshot([]), InputSnapshot([]), (image_bytes(rows),))


@pytest.mark.skipif(sys.platform != "linux", reason="Linux anchored reader")
def test_no_legacy_symlink_bytes_are_read_before_anchored_observation(tmp_path, monkeypatch):
    from compatibility.containment_guest_collector import vm_runner
    from compatibility.containment_guest_collector.contracts import PERMISSIONS
    from compatibility.guest_input_closure import fixed

    outside = tmp_path / "outside"
    outside.write_bytes(b"outside-selected-roots")
    link = tmp_path / "declared-input"
    link.symlink_to(outside)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "scope": "SAME_SOFTWARE_GUEST_SYSCALL_CAPTURE_ONLY",
                "permissions": {p: False for p in PERMISSIONS},
                "base_manifest_sha256": hashlib.sha256(
                    vm_runner.BASE_MANIFEST.read_bytes()
                ).hexdigest(),
                "collector_path": str(link),
                "inputs": [{"path": str(link), "sha256": "0" * 64}],
            }
        )
    )
    monkeypatch.setattr(vm_runner, "MANIFEST", manifest)
    seen = []
    original = hashlib.file_digest

    def track(stream, algorithm):
        seen.append(stream.read())
        stream.seek(0)
        return original(stream, algorithm)

    def stop(*args):
        raise ValueError("stop at anchored observation")

    monkeypatch.setattr(hashlib, "file_digest", track)
    monkeypatch.setattr(fixed, "scan_tree", stop)
    with pytest.raises(ValueError):
        fixed.observe_fixed_inputs()
    assert seen == []


@pytest.mark.skipif(sys.platform != "linux", reason="Linux anchored reader")
@pytest.mark.parametrize("operation", ["selected", "bounded-read"])
def test_nested_parent_replacement_rejects_even_when_root_and_file_descriptor_match(
    tmp_path, monkeypatch, operation
):
    from compatibility.guest_input_closure import filesystem as m

    (tmp_path / "a/b").mkdir(parents=True)
    (tmp_path / "a/b/file").write_bytes(b"original")
    original = m.os.open
    changed = False

    def replace_parent(path, flags, *args, **kwargs):
        nonlocal changed
        fd = original(path, flags, *args, **kwargs)
        if path == "b" and not changed:
            changed = True
            (tmp_path / "a/b").rename(tmp_path / "a/old")
            (tmp_path / "a/b").mkdir()
            (tmp_path / "a/b/file").write_bytes(b"replacement")
        return fd

    monkeypatch.setattr(m.os, "open", replace_parent)
    with pytest.raises(ValueError, match="parent|directory"):
        if operation == "selected":
            m.scan_selected("test", tmp_path, ("a/b/file",))
        else:
            m.read_regular(tmp_path, "a/b/file", 100)


@pytest.mark.parametrize("tag,value", [(0x6FFFFFFB, 0x800), (30, 1)])
def test_unsupported_dynamic_search_flags_cannot_use_default_library_resolution(tag, value):
    raw = bytearray(elf_bytes(["libc.so.6"], extra=[(tag, "unused")]))
    struct.pack_into("<Q", raw, 0x1B8, value)
    result = assessment("harmless-fixtures", raw)
    assert not result.guest_elf_dependencies_closed and result.issues


def test_duplicate_singleton_search_flags_cannot_hide_conflicting_values():
    raw = bytearray(elf_bytes(["libc.so.6"], extra=[(0x6FFFFFFB, "a"), (0x6FFFFFFB, "b")]))
    struct.pack_into("<Q", raw, 0x1B8, 0)
    struct.pack_into("<Q", raw, 0x1C8, 0x800)
    assert not assessment("harmless-fixtures", raw).guest_elf_dependencies_closed


@pytest.mark.parametrize("address,size", [(0x400300, 0x100), (0x4002FF, 2)])
def test_zero_filled_or_partial_load_overlap_is_not_unique_dynamic_metadata(address, size):
    raw = bytearray(elf_bytes(["libc.so.6"]))
    struct.pack_into("<H", raw, 56, 3)
    struct.pack_into("<IIQQQQQQ", raw, 176, 1, 6, 4096, address, 0, 0, size, 1)
    assert not assessment("harmless-fixtures", raw).guest_elf_dependencies_closed


@pytest.mark.parametrize("change", ["freebsd", "abi-version", "executable-library"])
def test_shared_dependency_requires_supported_abi_and_shared_object_role(change):
    raw = bytearray(elf_bytes(soname="libc.so.6"))
    if change == "freebsd":
        raw[7] = 9
    elif change == "abi-version":
        raw[8] = 1
    else:
        struct.pack_into("<H", raw, 16, 2)
    assert not assessment("lib/x86_64-linux-gnu/libc.so.6", raw).guest_elf_dependencies_closed


@pytest.mark.parametrize("name", ["dev/null", "dev/console"])
@pytest.mark.parametrize("kind", ["link", "file"])
def test_bootstrap_node_cannot_be_a_regular_file_or_conceal_a_link_cycle(name, kind):
    rows = [
        (
            r[0],
            0o120777 if kind == "link" else 0o100666,
            name.rsplit("/", 1)[-1].encode() if kind == "link" else b"",
            0,
            0,
        )
        if r[0] == name
        else r
        for r in guest_members()
    ]
    result = evaluate_closure(InputSnapshot([]), InputSnapshot([]), (image_bytes(rows),))
    assert not result.guest_elf_dependencies_closed and result.issues
