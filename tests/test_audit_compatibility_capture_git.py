"""GC018–029 initial index framing;remaining Git transport cases follow."""

import struct
from hashlib import sha1

import pytest

from tests.fixtures.audit_compatibility_capture import api, git, index_bytes, prepared


def test_hand_framed_v2_index_and_actual_git_index():
    a = api("worktree_reader")
    result = a.parse_index(index_bytes())
    assert result.version == 2 and len(result.entries) == 1
    assert result.entries[0].path == "a"
    assert result.entries[0].oid == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


def test_actual_git_index_matches_complete_stage_rows(tmp_path):
    root = prepared(tmp_path)
    value = api("worktree_reader").parse_index((root / ".git/index").read_bytes())
    expected = git(root, "ls-files", "--stage", "-z")
    actual = b"".join(f"{r.mode} {r.oid} 0\t{r.path}\0".encode() for r in value.entries)
    assert actual == expected


@pytest.mark.parametrize("raw", (b"", index_bytes()[:-1], b"BAD!" + index_bytes()[4:]))
def test_malformed_index_never_becomes_empty(raw):
    c = api("contracts")
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").parse_index(raw)
    assert e.value.unavailable is False


@pytest.mark.parametrize("flags", (0x8000, 0x1000, 0x2000, 0x3000, 0x4000))
def test_hidden_unmerged_and_extended_flags_reject(flags):
    c = api("contracts")
    raw = index_bytes((("a", 0o100644, "1" * 40, flags),))
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").parse_index(raw)
    assert e.value.unavailable is False


@pytest.mark.parametrize("version", (3, 4))
def test_unsupported_index_versions_are_unavailable_not_rewritten(version):
    c = api("contracts")
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").parse_index(index_bytes(version=version))
    assert e.value.unavailable is True


@pytest.mark.parametrize("names", (("a", "a"), ("A", "a"), ("a", "a/b"), ("../bad",)))
def test_duplicate_case_or_unsafe_index_paths_reject(names):
    c = api("contracts")
    with pytest.raises(c.CaptureFault):
        api("worktree_reader").parse_index(
            index_bytes(tuple((n, 0o100644, "1" * 40, 0) for n in names))
        )


def test_mode_and_unknown_extension_do_not_gain_support():
    c = api("contracts")
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").parse_index(index_bytes((("a", 0o100755, "1" * 40, 0),)))
    assert e.value.unavailable is False
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").parse_index(index_bytes(extension=b"UNKN" + struct.pack(">I", 0)))
    assert e.value.unavailable is True


def test_extension_length_and_checksum_corruption_reject():
    c = api("contracts")
    for raw in (
        index_bytes(extension=b"TREE" + struct.pack(">I", 8) + b"x"),
        index_bytes()[:-20] + b"0" * 20,
    ):
        with pytest.raises(c.CaptureFault) as e:
            api("worktree_reader").parse_index(raw)
        assert e.value.unavailable is False


def test_v3_known_intent_to_add_is_rejected_even_when_version_unsupported():
    c = api("contracts")
    raw = bytearray(index_bytes(version=3))
    raw[72:74] = struct.pack(">H", 0x4001)
    raw[74:76] = struct.pack(">H", 0x2000)
    raw = raw[:-20] + sha1(raw[:-20]).digest()
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").parse_index(bytes(raw))
    assert e.value.unavailable is False
