"""GC018–029 initial index framing;remaining Git transport cases follow."""

import struct
from hashlib import sha1

import pytest

from tests.fixtures.audit_compatibility_capture import api, git, index_bytes, prepared, request


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


def test_read_objects_returns_actual_raw_commits_and_whole_trees(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    result = api("git_reader").read_objects(req)
    assert result.errors == result.unavailable == result.missing_oids == ()
    assert result.raw_commits[0].oid == req.validation_head
    assert {p for p, _ in result.trees[0].entries} == {".gitattributes", "a"}
    assert dict(result.trees[0].entries)["a"].data == b"hello\n"


def test_missing_source_does_not_trigger_fetch_or_hide_other_objects(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    req = replace(request(root), source_oids=("0" * 40,))
    result = api("git_reader").read_objects(req)
    assert result.missing_oids == ("0" * 40,) and result.unavailable
    assert req.validation_head in {c.oid for c in result.raw_commits}


def test_wrong_object_type_is_rejected_not_peeled(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    blob = git(root, "rev-parse", "HEAD:a").decode().strip()
    result = api("git_reader").read_objects(replace(request(root), source_oids=(blob,)))
    assert "OBJECT_TYPE" in result.errors


@pytest.mark.parametrize(
    "command",
    (
        ("status",),
        ("diff",),
        ("fetch",),
        ("checkout", "HEAD"),
        ("hash-object", "--path", "a"),
        ("cat-file", "--filters"),
    ),
)
def test_forbidden_command_family_never_runs(tmp_path, command):
    root = prepared(tmp_path)
    req = request(root)
    c = api("contracts")
    reader = api("git_reader").GitReader(req, c.ReadBudget(req.budget))
    with pytest.raises(c.CaptureFault) as e:
        reader.run(command)
    assert e.value.reason == "COMMAND_FORBIDDEN"


@pytest.mark.parametrize(
    "relative,raw,reason",
    (
        ("info/grafts", b"1" * 40 + b"\n", "GRAFTS"),
        ("shallow", b"1" * 40 + b"\n", "SHALLOW"),
        ("objects/info/alternates", b"/not/to/be/read\n", "ALTERNATES"),
        ("packed-refs", b"1" * 40 + b" refs/replace/" + b"2" * 40 + b"\n", "REPLACE_REFS"),
    ),
)
def test_unsupported_or_forbidden_control_never_changes_repository(tmp_path, relative, raw, reason):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git" / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)
    result = api("git_reader").read_objects(req)
    assert reason in (*result.errors, *result.unavailable)
    assert p.read_bytes() == raw


def test_ambient_redirection_is_rejected(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    monkeypatch.setenv("GIT_INDEX_FILE", "/must/not/read")
    assert "ENV_REDIRECT" in api("git_reader").read_objects(req).errors


def test_linked_worktree_layout_is_explicit_and_supported(tmp_path):
    root = prepared(tmp_path)
    linked = tmp_path / "linked"
    git(root, "worktree", "add", "--detach", str(linked), "HEAD")
    result = api("git_reader").read_objects(request(linked))
    assert result.errors == result.unavailable == ()


def test_bounded_git_output_and_time_are_unavailable_not_partial(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    req = request(root)
    for limits in (
        replace(req.budget, maximum_output_bytes=1),
        replace(req.budget, subprocess_timeout_ns=1),
    ):
        result = api("git_reader").read_objects(replace(req, budget=limits))
        assert result.unavailable and not result.raw_commits


def test_core_worktree_redirect_cannot_be_hidden_by_command_options(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git/config"
    p.write_bytes(p.read_bytes() + b"[core]\nworktree = /must/not/use\n")
    assert "WRONG_LAYOUT" in api("git_reader").read_objects(req).errors


def test_actual_attributes_match_independent_pinned_D_vectors(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    c, a = api("contracts"), api("git_reader")
    reader = a.GitReader(req, c.ReadBudget(req.budget))
    tree = reader.tree(reader.object(req.validation_head, "commit").split(b"\n", 1)[0][5:].decode())
    result = a.read_attributes(reader, tree)
    assert dict(result.vectors)["a"] == ()
    assert dict(result.vectors)[".gitattributes"] == ()


@pytest.mark.parametrize("extra", (b"* filter=evil\n", b"* ident\n", b"* other=unknown\n"))
def test_unknown_or_filter_attributes_reject_without_cleaning(tmp_path, extra):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".gitattributes"
    p.write_bytes(p.read_bytes() + extra)
    c, a = api("contracts"), api("git_reader")
    reader = a.GitReader(req, c.ReadBudget(req.budget))
    objects = a.read_objects(req)
    with pytest.raises(c.CaptureFault) as e:
        a.read_attributes(reader, objects.trees[0])
    assert e.value.unavailable is False


def test_recursive_tree_entries_obey_budget_even_with_cached_blobs(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    for i in range(20):
        (root / f"x{i}").write_bytes(b"same")
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "MANY_SAME_BLOBS")
    req = request(root)
    result = api("git_reader").read_objects(
        replace(req, budget=replace(req.budget, maximum_entries=8))
    )
    assert "RESOURCE_LIMIT" in result.unavailable and not result.trees
