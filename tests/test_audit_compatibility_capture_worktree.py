"""Safe real filesystem/config observations;unknown contents must not be read."""

import os
from dataclasses import replace

import pytest

from tests.fixtures.audit_compatibility_capture import ATTRIBUTES, api, prepared, request


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
