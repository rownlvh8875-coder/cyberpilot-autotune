"""Safe real filesystem/config observations;unknown contents must not be read."""

import os
from dataclasses import replace

import pytest

from tests.fixtures.audit_compatibility_capture import ATTRIBUTES, api, prepared, request
from tests.fixtures.audit_compatibility_capture import (
    isolated_capture_config as isolated_capture_config,
)


def budget(req):
    return api("contracts").ReadBudget(req.budget)


def test_safe_regular_nested_file_read(tmp_path):
    root = prepared(tmp_path)
    (root / "nested").mkdir()
    path = root / "nested/a"
    path.write_bytes(b"literal\r\n\0binary")
    value, identity = api("worktree_reader").read_file(str(path), budget(request(root)))
    assert value == b"literal\r\n\0binary" and identity


@pytest.mark.parametrize("kind", ("leaf", "ancestor", "fifo"))
def test_no_follow_or_special_file_open(tmp_path, kind):
    root = prepared(tmp_path)
    other = tmp_path / "outside"
    other.mkdir()
    (other / "secret").write_bytes(b"must not read")
    if kind == "leaf":
        target = root / "leaf"
        target.symlink_to(other / "secret")
    elif kind == "ancestor":
        (root / "link").symlink_to(other, target_is_directory=True)
        target = root / "link/secret"
    else:
        target = root / "pipe"
        os.mkfifo(target)
    c = api("contracts")
    with pytest.raises(c.CaptureFault) as e:
        api("worktree_reader").read_file(str(target), budget(request(root)))
    assert e.value.unavailable is False


def test_missing_optional_is_none_not_empty_bytes(tmp_path):
    root = prepared(tmp_path)
    a = api("worktree_reader")
    assert a.read_file(str(root / "absent"), budget(request(root)), missing_ok=True)[0] is None
    (root / "empty").write_bytes(b"")
    assert a.read_file(str(root / "empty"), budget(request(root)))[0] == b""


@pytest.mark.parametrize(
    "line,reason",
    (
        (b"[include]\npath = /must/not/follow\n", "CONFIG_INCLUDE"),
        (b"[core]\nattributesFile = /must/not/follow\n", "ATTRIBUTE_OVERRIDE"),
        (b"[core]\nfsmonitor = /must/not/execute\n", "CUSTOM_HELPER"),
        (b'[filter "evil"]\nclean = /must/not/execute\n', "CUSTOM_HELPER"),
        (b'[diff "evil"]\ntextconv = /must/not/execute\n', "CUSTOM_HELPER"),
    ),
)
def test_config_forbidden_helpers_and_unsupported_include_are_explicit(tmp_path, line, reason):
    root = prepared(tmp_path)
    req = request(root)
    config = root / ".git/config"
    config.write_bytes(config.read_bytes() + line)
    result = api("worktree_reader").preflight(req, budget(req))
    assert reason in (*result.errors, *result.unavailable)
    assert "must/not" not in repr(result)


def test_complete_inventory_includes_ignored_secret_without_opening_it(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    (root / ".gitignore").write_bytes(b"secret\n")
    (root / "secret").write_bytes(b"DO_NOT_READ_OR_REPORT")
    a = api("worktree_reader")
    real_read = a.read_file

    def guarded(path, *args, **kwargs):
        assert not path.endswith("/secret")
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(a, "read_file", guarded)
    expected = ((".gitattributes", ATTRIBUTES), ("a", b"hello\n"))
    result = a.read_worktree(request(root), expected, budget(request(root)))
    assert "UNTRACKED_PATH" in result.errors
    assert len(result.untracked_including_ignored) == 2
    assert "secret" not in repr(result) and "DO_NOT_READ_OR_REPORT" not in repr(result)


@pytest.mark.parametrize("mutation", ("delete", "CRLF", "exec", "attr", "nested_repo"))
def test_worktree_mismatches_are_not_cleaned_or_hidden(tmp_path, mutation):
    root = prepared(tmp_path)
    if mutation == "delete":
        (root / "a").unlink()
    elif mutation == "CRLF":
        (root / "a").write_bytes(b"hello\r\n")
    elif mutation == "exec":
        (root / "a").chmod(0o755)
    elif mutation == "attr":
        (root / ".gitattributes").write_bytes(b"* filter=evil\n")
    else:
        (root / "nested/.git").mkdir(parents=True)
    result = api("worktree_reader").read_worktree(
        request(root), ((".gitattributes", ATTRIBUTES), ("a", b"hello\n")), budget(request(root))
    )
    assert result.errors


def test_config_unknown_does_not_hide_known_invalid(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git/config"
    p.write_bytes(p.read_bytes() + b"unknown syntax\n[core]\nfsmonitor = evil\n")
    result = api("worktree_reader").preflight(req, budget(req))
    assert "CUSTOM_HELPER" in result.errors and "CONFIG_SYNTAX" in result.unavailable


def test_resource_exhaustion_is_not_empty_success(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    limits = replace(req.budget, maximum_total_read_bytes=1)
    with pytest.raises(api("contracts").CaptureFault) as e:
        api("worktree_reader").read_file(str(root / "a"), api("contracts").ReadBudget(limits))
    assert e.value.unavailable is True


def test_preflight_config_secret_values_never_enter_report(tmp_path):
    root = prepared(tmp_path)
    p = root / ".git/config"
    p.write_bytes(
        p.read_bytes() + b'[remote "origin"]\nurl = https://SECRET_TOKEN@example.invalid/repo\n'
    )
    report = api("worktree_reader").preflight(request(root), budget(request(root)))
    assert "SECRET_TOKEN" not in repr(report)


@pytest.mark.parametrize(
    "raw,reason",
    (
        (b"\xff", "CONFIG_SYNTAX"),
        (b"[bad\nkey=x\n", "CONFIG_SYNTAX"),
        (b'[core "sub"]\nfilemode=true\n', "CONFIG_SYNTAX"),
        (b'[core]\neditor="unfinished\n', "CONFIG_SYNTAX"),
        (b'[core]\neditor="bad\\q"\n', "CONFIG_SYNTAX"),
        (b"[core]\nunknown=true\n", "CONFIG_SYNTAX"),
        (b"[unknown]\nkey=true\n", "CONFIG_SYNTAX"),
        (b"[core]\nbare=true\n", "WRONG_LAYOUT"),
        (b"[core]\nsparseCheckout=true\n", "CONFIG_FEATURE"),
        (b"[extensions]\nobjectFormat=sha256\n", "OBJECT_FORMAT"),
        (b"[extensions]\npartialClone=origin\n", "CONFIG_FEATURE"),
    ),
)
def test_closed_config_grammar_and_features_are_never_approximated(tmp_path, raw, reason):
    root = prepared(tmp_path)
    req = request(root)
    errors, missing = set(), set()
    api("worktree_reader").inspect_config(raw, errors, missing, req.layout)
    assert reason in errors | missing


def test_supported_config_escapes_bare_boolean_comments_and_inert_values(tmp_path):
    root = prepared(tmp_path)
    errors, missing = set(), set()
    raw = (
        b'# comment\n[core]\nfilemode\neditor="a\\t\\n\\b\\\\\\"b" ; tail\n'
        b"[extensions]\nobjectFormat=sha1\nworktreeConfig=true\n"
    )
    api("worktree_reader").inspect_config(raw, errors, missing, request(root).layout)
    assert not errors and not missing


def test_missing_declared_config_scope_remains_unavailable(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    req = replace(req, layout=replace(req.layout, control_roots=()))
    r = api("worktree_reader").preflight(req, budget(req))
    assert "CONFIG_SCOPE" in r.unavailable


@pytest.mark.parametrize("suffix", ("/info/attributes", "/info/grafts", "/config", "/packed-refs"))
def test_control_read_errors_are_not_silently_absent(tmp_path, monkeypatch, suffix):
    root = prepared(tmp_path)
    req = request(root)
    a = api("worktree_reader")
    real = a.read_file

    def unavailable(path, *args, **kwargs):
        if path == str(root / ".git") + suffix:
            raise api("contracts").CaptureFault("TEST_READ_UNAVAILABLE", True)
        return real(path, *args, **kwargs)

    monkeypatch.setattr(a, "read_file", unavailable)
    assert "TEST_READ_UNAVAILABLE" in a.preflight(req, budget(req)).unavailable


def test_attribute_policy_default_source_checked_not_hidden_by_sanitization(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    configs = (str(tmp_path / "system"), str(tmp_path / "user"), str(tmp_path / "git/config"))
    (tmp_path / "git").mkdir()
    (tmp_path / "git/attributes").write_bytes(b"* filter=evil\n")
    req = replace(req, layout=replace(req.layout, control_roots=configs))
    a = api("worktree_reader")
    monkeypatch.setattr(a, "config_candidates", lambda layout: configs)
    assert "ATTRIBUTE_OVERRIDE" in a.preflight(req, budget(req)).errors


@pytest.mark.parametrize("mutation", ("replace", "root_rename", "read_error"))
def test_safe_read_detects_real_leaf_or_root_changes_and_IO_failure(
    tmp_path, monkeypatch, mutation
):
    root = prepared(tmp_path)
    req = request(root)
    target = root / "a"
    inode = target.stat().st_ino
    a = api("worktree_reader")
    real = os.read
    changed = False

    def read(fd, size):
        nonlocal changed
        if not changed and os.fstat(fd).st_ino == inode:
            changed = True
            if mutation == "read_error":
                raise PermissionError("TEST_ONLY")
            if mutation == "replace":
                new = root / "replacement"
                new.write_bytes(b"other")
                new.replace(target)
            else:
                root.rename(tmp_path / "moved")
        return real(fd, size)

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(api("contracts").CaptureFault) as e:
        a.read_file(str(target), budget(req))
    assert e.value.reason in ("FILE_CHANGED", "FILE_IO", "ROOT_CHANGED")


def test_inventory_empty_directories_do_not_become_untracked_files(tmp_path):
    root = prepared(tmp_path)
    (root / "empty").mkdir()
    req = request(root)
    r = api("worktree_reader").read_worktree(
        req, ((".gitattributes", ATTRIBUTES), ("a", b"hello\n")), budget(req)
    )
    assert not r.errors and not r.untracked_including_ignored


def test_unsafe_tracked_path_never_opens_outside_root(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    r = api("worktree_reader").read_worktree(req, (("../secret", b""),), budget(req))
    assert "UNSAFE_PATH" in r.errors


def test_control_directory_symlink_is_known_rejection_not_missing(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".git/refs/replace").symlink_to(outside, target_is_directory=True)
    assert "UNSAFE_PATH" in api("worktree_reader").preflight(req, budget(req)).errors


@pytest.mark.parametrize(
    "kind", ("layout", "ambient_attribute", "control_directory", "inventory", "tracked_leaf")
)
def test_unavailable_read_component_never_becomes_an_empty_success(tmp_path, monkeypatch, kind):
    root = prepared(tmp_path)
    req = request(root)
    a = api("worktree_reader")
    if kind == "layout":
        (root / ".git").rename(root / ".moved_git")
        r = a.preflight(req, budget(req))
        assert r.unavailable
        return
    if kind in ("ambient_attribute", "tracked_leaf"):
        real = a.read_file

        def unavailable(path, *args, **kwargs):
            if (kind == "ambient_attribute" and path == "/etc/gitattributes") or (
                kind == "tracked_leaf" and path == str(root / "a")
            ):
                raise api("contracts").CaptureFault("TEST_UNAVAILABLE", True)
            return real(path, *args, **kwargs)

        monkeypatch.setattr(a, "read_file", unavailable)
    else:
        real = a.directory_names
        inode = (root / ".git/objects/pack" if kind == "control_directory" else root).stat().st_ino

        def unavailable(fd, counter):
            if os.fstat(fd).st_ino == inode:
                raise PermissionError("TEST_ONLY")
            return real(fd, counter)

        monkeypatch.setattr(a, "directory_names", unavailable)
    if kind in ("ambient_attribute", "control_directory"):
        r = a.preflight(req, budget(req))
    else:
        r = a.read_worktree(req, ((".gitattributes", ATTRIBUTES), ("a", b"hello\n")), budget(req))
    assert r.unavailable


def test_duplicate_directory_iteration_is_rejected_not_collapsed(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    inode = root.stat().st_ino
    a = api("worktree_reader")
    real = a.directory_names

    def duplicate(fd, counter):
        names = real(fd, counter)
        return [*names, "a"] if os.fstat(fd).st_ino == inode else names

    monkeypatch.setattr(a, "directory_names", duplicate)
    r = api("worktree_reader").read_worktree(
        req, ((".gitattributes", ATTRIBUTES), ("a", b"hello\n")), budget(req)
    )
    assert "DUPLICATE_PATH" in r.errors


def test_review_recursive_namespace_exhaustion_is_unavailable(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    a = api("worktree_reader")

    def exhausted(fd, counter):
        raise RecursionError("TEST_ONLY")

    monkeypatch.setattr(a, "directory_names", exhausted)
    result = a.read_worktree(req, (("a", b"hello\n"),), budget(req))
    assert "RESOURCE_LIMIT" in result.unavailable


def test_actual_case_conflict_does_not_get_normalized(tmp_path):
    root = prepared(tmp_path)
    (root / "A").write_bytes(b"other")
    req = request(root)
    r = api("worktree_reader").read_worktree(
        req, ((".gitattributes", ATTRIBUTES), ("a", b"hello\n")), budget(req)
    )
    assert "UNSAFE_PATH" in r.errors


@pytest.mark.parametrize("path", (".venv/cache", ".cache/hidden"))
def test_cache_prefix_is_not_an_untracked_exception(tmp_path, path):
    root = prepared(tmp_path)
    p = root / path
    p.parent.mkdir()
    p.write_bytes(b"not read")
    r = api("capture").capture_checkout(request(root))
    assert "UNTRACKED_PATH" in r.errors


def test_nonempty_info_attributes_are_rejected_before_Git(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    (root / ".git/info/attributes").write_bytes(b"* filter=evil\n")
    r = api("git_reader").read_objects(req)
    assert "ATTRIBUTE_OVERRIDE" in r.errors


def test_same_size_and_restored_mtime_does_not_hide_raw_byte_drift(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    p = root / "a"
    before = p.stat()
    p.write_bytes(b"drift\n")
    os.utime(p, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert p.stat().st_size == before.st_size and p.stat().st_mtime_ns == before.st_mtime_ns
    assert "RAW_BYTES_CHANGED" in api("capture").capture_checkout(req).errors


@pytest.mark.parametrize(
    "raw", ('" "', '"trailing "', '" leading"', '"a\\t"', '"quoted # value" # comment')
)
def test_supported_config_value_grammar_has_actual_Git_parity(tmp_path, raw):
    from tests.fixtures.audit_compatibility_capture import git

    root = prepared(tmp_path)
    config = tmp_path / "value.config"
    config.write_bytes(("[core]\neditor=" + raw + "\n").encode())
    expected = (
        git(root, "config", "--file", str(config), "--get", "core.editor")
        .decode()
        .removesuffix("\n")
    )
    assert api("worktree_reader")._value(raw) == expected


def test_quoted_empty_looking_attribute_path_is_not_ignored(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git/config"
    p.write_bytes(p.read_bytes() + b'[core]\nattributesFile=" "\n')
    assert "ATTRIBUTE_OVERRIDE" in api("worktree_reader").preflight(req, budget(req)).errors


@pytest.mark.parametrize("value", ("\u00a0", "\u2000", "\u202f"))
def test_review_unquoted_unicode_whitespace_has_native_Git_semantics(tmp_path, value):
    from tests.fixtures.audit_compatibility_capture import git

    root = prepared(tmp_path)
    req = request(root)
    p = root / ".git/config"
    p.write_bytes(p.read_bytes() + ("[core]\nattributesFile = " + value + "\n").encode())
    native = git(root, "config", "--get", "core.attributesFile").decode().removesuffix("\n")
    assert native == value
    assert "ATTRIBUTE_OVERRIDE" in api("worktree_reader").preflight(req, budget(req)).errors


def test_review_directory_names_are_charged_before_materialization(tmp_path, monkeypatch):
    from types import SimpleNamespace

    root = prepared(tmp_path)
    req = request(root)
    a = api("worktree_reader")
    limits = replace(req.budget, maximum_entries=1)
    count = 0

    class Entries:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __iter__(self):
            nonlocal count
            for n in range(1000):
                count += 1
                yield SimpleNamespace(name=f"item{n}")

    with a.directory(str(root / ".git/objects/pack")) as fd:
        monkeypatch.setattr(os, "scandir", lambda unused: Entries())
        with pytest.raises(api("contracts").CaptureFault) as e:
            a.directory_names(fd, api("contracts").ReadBudget(limits))
    assert e.value.unavailable is True and count <= 2


def test_review_full_capture_does_not_use_unbounded_listdir(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)

    def forbidden(*args):
        raise AssertionError("UNBOUNDED_LISTDIR")

    monkeypatch.setattr(os, "listdir", forbidden)
    assert api("capture").capture_checkout(req).consistency == "OBSERVED_STABLE"


def test_review_known_untracked_survives_later_directory_failure(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    (root / "a_secret").write_bytes(b"never read")
    bad = root / "z_bad"
    bad.mkdir()
    inode = bad.stat().st_ino
    original = os.scandir

    def unreadable(fd):
        if type(fd) is int and os.fstat(fd).st_ino == inode:
            raise PermissionError("TEST_ONLY")
        return original(fd)

    monkeypatch.setattr(os, "scandir", unreadable)
    result = api("capture").capture_checkout(req)
    assert "UNTRACKED_PATH" in result.errors and "WORKTREE_IO" in result.unavailable
