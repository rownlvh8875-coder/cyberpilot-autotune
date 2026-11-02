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
    c, a = api("contracts"), api("git_reader")
    reader = a.GitReader(req, c.ReadBudget(req.budget))
    tree = reader.object(req.validation_head, "commit").split(b"\n", 1)[0][5:].decode()
    reader.tree(tree)
    reader.budget = c.ReadBudget(replace(req.budget, maximum_entries=8))
    with pytest.raises(c.CaptureFault) as error:
        reader.tree(tree)
    assert error.value.reason == "RESOURCE_LIMIT" and reader.budget.entries == 9


@pytest.mark.parametrize("separator", (b"\r", b"\r\n"))
def test_raw_malformed_commit_cannot_enter_capture_graph(tmp_path, separator):
    from dataclasses import replace

    root = prepared(tmp_path)
    req = request(root)
    tree = git(root, "rev-parse", "HEAD^{tree}").strip()
    raw = b"tree " + tree + separator + b"author Test <t@example.invalid> 0 +0000\n\nTEST\n"
    bad = (
        git(root, "hash-object", "--literally", "-w", "-t", "commit", "--stdin", input=raw)
        .decode()
        .strip()
    )
    result = api("git_reader").read_objects(replace(req, source_oids=(bad,)))
    assert "COMMIT_FORMAT" in result.errors


def test_missing_ancestor_is_not_inferred_from_shallow_or_empty_state(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    req = request(root)
    tree = git(root, "rev-parse", "HEAD^{tree}").strip()
    raw = b"tree " + tree + b"\nparent " + b"0" * 40 + b"\n\nTEST\n"
    source = (
        git(root, "hash-object", "--literally", "-w", "-t", "commit", "--stdin", input=raw)
        .decode()
        .strip()
    )
    result = api("git_reader").read_objects(replace(req, source_oids=(source,)))
    assert result.missing_oids == ("0" * 40,) and result.unavailable


def test_nested_tree_and_binary_and_diagnostic_attribute_vectors(tmp_path):
    root = prepared(tmp_path)
    for name, raw in (
        ("tests/fixtures/actual_binding/x.zip", b"\0ZIP\r\n"),
        ("src/cyberpilot_autotune/diagnostics/x.py", b"# LF\n"),
    ):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "NESTED_TEST")
    result = api("capture").capture_checkout(request(root))
    assert result.consistency == "OBSERVED_STABLE", result.errors
    vectors = dict(result.pass_a.attributes.vectors)
    assert vectors["tests/fixtures/actual_binding/x.zip"] == (
        ("binary", "set"),
        ("diff", "unset"),
        ("merge", "unset"),
        ("text", "unset"),
    )
    assert vectors["src/cyberpilot_autotune/diagnostics/x.py"] == (("eol", "lf"), ("text", "set"))


@pytest.mark.parametrize("name", ("한글 space", "tab\tname", "bad\nname"))
def test_actual_nul_framing_does_not_use_display_quotes(tmp_path, name):
    root = prepared(tmp_path)
    (root / name).write_bytes(b"test")
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "NAMES")
    result = api("git_reader").read_objects(request(root))
    if "\n" in name:
        assert "TREE_FORMAT" in result.errors
    else:
        assert not result.errors and name in dict(result.trees[0].entries)


@pytest.mark.parametrize("kind", ("filter", "fsmonitor", "merge"))
def test_real_helper_canary_never_executes(tmp_path, kind):
    root = prepared(tmp_path)
    req = request(root)
    marker = tmp_path / "EXECUTED"
    key = {
        "filter": '[filter "evil"]\nclean',
        "fsmonitor": "[core]\nfsmonitor",
        "merge": '[merge "evil"]\ndriver',
    }[kind]
    p = root / ".git/config"
    p.write_bytes(p.read_bytes() + f"{key} = touch {marker}\n".encode())
    result = api("git_reader").read_objects(req)
    assert "CUSTOM_HELPER" in result.errors and not marker.exists()


def test_loose_replace_and_promisor_metadata_are_observed(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git/refs/replace"
    p.mkdir()
    (p / ("1" * 40)).write_bytes(b"2" * 40 + b"\n")
    pack = root / ".git/objects/pack"
    (pack / "test.promisor").write_bytes(b"")
    result = api("git_reader").read_objects(req)
    assert "REPLACE_REFS" in result.errors and "PARTIAL_CLONE" in result.unavailable


def test_raw_object_wire_corruption_is_not_treated_as_missing(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    a = api("git_reader")
    reader = a.GitReader(req, api("contracts").ReadBudget(req.budget))
    monkeypatch.setattr(
        reader, "run", lambda args, raw=b"": req.validation_head.encode() + b" commit 1\nx\n"
    )
    with pytest.raises(api("contracts").CaptureFault) as e:
        reader.object(req.validation_head, "commit")
    assert e.value.reason == "OBJECT_HASH"


def test_unavailable_git_executable_is_reported_without_raw_stderr(tmp_path, monkeypatch):
    import subprocess

    root = prepared(tmp_path)
    req = request(root)

    def absent(*args, **kwargs):
        raise FileNotFoundError("SECRET_PATH_NOT_FOR_REPORT")

    monkeypatch.setattr(subprocess, "Popen", absent)
    result = api("git_reader").read_objects(req)
    assert "GIT_IO" in result.unavailable and "SECRET_PATH" not in repr(result)


@pytest.mark.parametrize("raw", (b"HEAD\n", b"HEAD:a\n", b"0" * 40 + b"\nEXTRA\n", b""))
def test_raw_batch_requests_cannot_select_branches_or_paths(tmp_path, raw):
    root = prepared(tmp_path)
    req = request(root)
    reader = api("git_reader").GitReader(req, api("contracts").ReadBudget(req.budget))
    with pytest.raises(api("contracts").CaptureFault) as e:
        reader.run(("cat-file", "--batch"), raw)
    assert e.value.reason == "INPUT_FORBIDDEN"


def test_empty_environment_redirect_is_not_default_or_absent(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    monkeypatch.setenv("GIT_INDEX_FILE", "")
    assert "ENV_REDIRECT" in api("git_reader").read_objects(req).errors


def test_actual_split_index_is_unavailable_and_never_rewritten(tmp_path):
    root = prepared(tmp_path)
    git(root, "update-index", "--split-index")
    raw = (root / ".git/index").read_bytes()
    with pytest.raises(api("contracts").CaptureFault) as e:
        api("worktree_reader").parse_index(raw)
    assert e.value.unavailable is True
    assert (root / ".git/index").read_bytes() == raw


def test_promisor_configuration_is_unsupported_even_with_objects_present(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git/config"
    p.write_bytes(
        p.read_bytes() + b'[remote "origin"]\npromisor = true\npartialCloneFilter = blob:none\n'
    )
    assert "PARTIAL_CLONE" in api("git_reader").read_objects(req).unavailable


@pytest.mark.parametrize("signature", (b"link", b"sdir"))
def test_split_and_sparse_index_markers_are_explicitly_unavailable(signature):
    with pytest.raises(api("contracts").CaptureFault) as e:
        api("worktree_reader").parse_index(index_bytes(extension=signature + struct.pack(">I", 0)))
    assert e.value.unavailable is True


def test_actual_SHA256_repository_is_unavailable_not_bad_SHA1_index(tmp_path):
    from dataclasses import replace

    original = prepared(tmp_path)
    req = request(original)
    other = tmp_path / "sha256"
    other.mkdir()
    git(other, "init", "--quiet", "--object-format=sha256")
    git(other, "config", "user.name", "Test")
    git(other, "config", "user.email", "test@example.invalid")
    (other / "a").write_bytes(b"test")
    git(other, "add", ".")
    git(other, "commit", "--quiet", "-m", "SHA256_TEST")
    layout = replace(
        req.layout,
        worktree_root=str(other),
        git_dir=str(other / ".git"),
        common_dir=str(other / ".git"),
    )
    result = api("capture").capture_checkout(replace(req, layout=layout))
    assert result.consistency == "UNAVAILABLE" and "OBJECT_FORMAT" in result.unavailable


def test_invalid_native_utf8_filename_is_not_normalized(tmp_path):
    import os

    root = prepared(tmp_path)
    fd = os.open(os.fsencode(root) + b"/bad\xff", os.O_CREAT | os.O_WRONLY, 0o644)
    os.close(fd)
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "INVALID_UTF8")
    assert "TREE_FORMAT" in api("git_reader").read_objects(request(root)).errors


def test_existing_but_wrong_gitdir_is_rejected_not_used_as_source(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    base = tmp_path / "other"
    base.mkdir()
    other = prepared(base)
    req = request(root)
    req = replace(
        req, layout=replace(req.layout, git_dir=str(other / ".git"), common_dir=str(other / ".git"))
    )
    assert "WRONG_LAYOUT" in api("git_reader").read_objects(req).errors


def test_cached_and_worktree_attribute_disagreement_is_independently_rejected(tmp_path):
    from tests.fixtures.audit_compatibility_capture import ATTRIBUTES

    root = prepared(tmp_path)
    req = request(root)
    p = root / ".gitattributes"
    p.write_bytes(ATTRIBUTES + b"a other=unknown\n")
    git(root, "add", ".gitattributes")
    p.write_bytes(ATTRIBUTES)
    result = api("capture").capture_checkout(req)
    assert "INDEX_HEAD_MISMATCH" in result.errors and "ATTRIBUTE_OVERRIDE" in result.errors


@pytest.mark.parametrize("raw", (b"../outside\0", b"bad\xff\0", b"missing-nul"))
def test_attribute_stdin_paths_stay_inside_literal_utf8_namespace(tmp_path, raw):
    root = prepared(tmp_path)
    req = request(root)
    reader = api("git_reader").GitReader(req, api("contracts").ReadBudget(req.budget))
    with pytest.raises(api("contracts").CaptureFault) as e:
        reader.run(("check-attr", "-z", "--all", "--stdin"), raw)
    assert e.value.reason == "INPUT_FORBIDDEN"


@pytest.mark.parametrize("key", ("GIT_TRACE", "GIT_TRACE2_EVENT"))
def test_review_child_trace_controls_cannot_write_any_file(tmp_path, monkeypatch, key):
    root = prepared(tmp_path)
    req = request(root)
    marker = tmp_path / "FORBIDDEN_TRACE"
    monkeypatch.setenv(key, str(marker))
    r = api("capture").capture_checkout(req)
    assert "ENV_REDIRECT" in r.errors and not marker.exists()


@pytest.mark.parametrize("during", (False, True))
def test_review_object_store_symlink_escape_is_rejected_when_observed(
    tmp_path, monkeypatch, during
):
    root = prepared(tmp_path)
    req = request(root)
    blob = git(root, "rev-parse", "HEAD:a").decode().strip()
    obj = root / ".git/objects" / blob[:2] / blob[2:]
    outside = tmp_path / "outside-object"
    outside.write_bytes(obj.read_bytes())

    def escape():
        obj.unlink()
        obj.symlink_to(outside)

    if during:
        a = api("git_reader")
        original = a.GitReader.run
        changed = False

        def read(self, args, raw=b""):
            nonlocal changed
            if args == ("cat-file", "--batch") and raw == blob.encode() + b"\n" and not changed:
                changed = True
                escape()
            return original(self, args, raw)

        monkeypatch.setattr(a.GitReader, "run", read)
    else:
        escape()
    result = api("git_reader").read_objects(req)
    assert "UNSAFE_PATH" in result.errors


def test_review_missing_blob_cannot_hide_later_forbidden_tree_mode(tmp_path):
    from dataclasses import replace

    root = prepared(tmp_path)
    req = request(root)
    blob = git(root, "rev-parse", "HEAD:a").strip()
    raw = b"100644 a\0" + b"\0" * 20 + b"100755 b\0" + bytes.fromhex(blob.decode())
    tree = git(root, "hash-object", "--literally", "-t", "tree", "-w", "--stdin", input=raw).strip()
    source = (
        git(
            root,
            "hash-object",
            "--literally",
            "-t",
            "commit",
            "-w",
            "--stdin",
            input=b"tree " + tree + b"\n\nTEST\n",
        )
        .decode()
        .strip()
    )
    result = api("git_reader").read_objects(replace(req, source_oids=(source,)))
    assert "OBJECT_MODE" in result.errors and "OBJECT_MISSING" in result.unavailable
