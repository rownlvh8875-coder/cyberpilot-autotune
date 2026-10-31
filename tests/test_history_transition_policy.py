"""Exercise the bounded history exception and frozen historical execution."""

import hashlib
import importlib
import importlib.util
import os
import subprocess

import pytest

from tests.history_transition.frozen_cases import BASE, ROOT, materialize_snapshot, run_frozen_case
from tests.history_transition.policy import GUARD_BASES


@pytest.mark.parametrize(
    "git_settings", (None, ("true", "crlf"), ("false", "crlf"), ("input", "lf"))
)
def test_snapshot_contains_original_coherent_git_tree(tmp_path, monkeypatch, git_settings):
    # A partial copy or current-source overlay would invalidate historical assertions.
    # Host autocrlf/eol must not convert historical bytes, even in a binary tar pipe.
    if git_settings is not None:
        count = int(os.environ.get("GIT_CONFIG_COUNT", "0"))
        for index, (name, value) in enumerate(
            zip(("core.autocrlf", "core.eol"), git_settings, strict=True), count
        ):
            monkeypatch.setenv(f"GIT_CONFIG_KEY_{index}", name)
            monkeypatch.setenv(f"GIT_CONFIG_VALUE_{index}", value)
        monkeypatch.setenv("GIT_CONFIG_COUNT", str(count + 2))
    snapshot = tmp_path / "snapshot"
    materialize_snapshot(snapshot)
    expected = {}
    for row in subprocess.check_output(["git", "ls-tree", "-rz", BASE], cwd=ROOT).split(b"\0"):
        if row:
            header, path = row.split(b"\t", 1)
            expected[path.decode()] = header.split()[2].decode()
    actual = {}
    for path in snapshot.rglob("*"):
        if path.is_file():
            raw = path.read_bytes()
            actual[path.relative_to(snapshot).as_posix()] = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest()
    assert actual == expected
    assert "tests/history_transition/frozen_cases.py" not in actual
    assert (snapshot / "compatibility/native_containment/contracts.py").read_bytes() != (
        ROOT / "compatibility/native_containment/contracts.py"
    ).read_bytes()


@pytest.mark.parametrize("node", ("", "tests/test_other.py", "../escape", "--collect-only", None))
def test_frozen_runner_rejects_non_closed_nodes(node):
    with pytest.raises(ValueError, match="unapproved historical test node"):
        run_frozen_case(node)


def test_snapshot_refuses_to_overwrite_an_existing_directory(tmp_path):
    with pytest.raises(FileExistsError):
        materialize_snapshot(tmp_path)


def test_exact_history_policy_is_implemented():
    # Changed guards must not gain a path-only exception without content checks.
    assert importlib.util.find_spec("tests.history_transition.policy") is not None


@pytest.fixture
def policy_clone(tmp_path):
    from tests.history_transition import policy

    checkout = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(checkout)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "core.autocrlf=false", "checkout", "--quiet", policy.PREREGISTRATION],
        cwd=checkout,
        check=True,
        capture_output=True,
    )
    return checkout


def _git(checkout, *args):
    return subprocess.check_output(["git", *args], cwd=checkout, stderr=subprocess.PIPE)


def _check_policy(checkout, changed=None):
    from tests.history_transition import policy

    policy.assert_history_transition(
        checkout,
        "c477cfc1b30578165405b6cbb3af26b7334064e5",
        {"compatibility/native_containment/contracts.py"} if changed is None else changed,
    )


def test_registered_transition_accepts_all_exact_postimages(policy_clone):
    _check_policy(policy_clone)


@pytest.mark.parametrize("layer", ("worktree", "index", "head"))
@pytest.mark.parametrize("change", ("content", "delete", "rename", "mode"))
def test_unapproved_postimage_rejected_in_each_git_layer(policy_clone, layer, change):
    path = "compatibility/native_containment/contracts.py"
    target = policy_clone / path
    original = target.read_bytes()
    if change == "content":
        target.write_bytes(original + b"\n# unapproved postimage\n")
    elif change == "delete":
        target.unlink()
    elif change == "rename":
        target.rename(target.with_name("unexpected_name.py"))
    elif layer == "worktree" and os.name != "nt":
        target.chmod(0o755)
    else:
        # Index modes are representable even on Windows; no skip-based success.
        _git(policy_clone, "update-index", "--chmod=+x", "--", path)
    if layer != "worktree":
        if change != "mode":
            _git(policy_clone, "add", "-A")
        if layer == "head":
            _git(
                policy_clone,
                "-c",
                "user.name=Policy Test",
                "-c",
                "user.email=policy@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--quiet",
                "-m",
                "unapproved mutant",
            )
        # Hide altered HEAD/index bytes from a working-tree-only validator.
        if target.with_name("unexpected_name.py").exists():
            target.with_name("unexpected_name.py").unlink()
        target.write_bytes(original)
        target.chmod(0o644)
    with pytest.raises((ValueError, AssertionError)):
        _check_policy(policy_clone)


@pytest.mark.parametrize(
    "path",
    (
        "src/cyberpilot_autotune/__init__.py",
        ".github/workflows/ci.yml",
        "tests/fixtures/native_containment.py",
    ),
)
def test_old_paths_outside_exception_remain_protected(policy_clone, path):
    target = policy_clone / path
    target.write_bytes(target.read_bytes() + b"\n# forbidden\n")
    with pytest.raises((ValueError, AssertionError)):
        _check_policy(policy_clone, {path})


def test_mutable_manifest_is_never_policy_authority(policy_clone):
    path = policy_clone / "docs/evidence/strict_input_history_transition_v1.json"
    path.write_text('{"allow_everything":true}')
    _check_policy(policy_clone)  # pinned Git object, not this working file


def test_missing_preregistration_fails_closed_without_fetch(policy_clone, monkeypatch):
    from tests.history_transition import policy

    monkeypatch.setattr(policy, "PREREGISTRATION", "0" * 40)
    with pytest.raises(ValueError, match="unavailable"):
        _check_policy(policy_clone)


def test_unregistered_guard_base_cannot_claim_the_exception(policy_clone):
    from tests.history_transition import policy

    with pytest.raises(ValueError):
        policy.assert_history_transition(
            policy_clone, BASE, {"compatibility/native_containment/contracts.py"}
        )


def test_crlf_is_allowed_only_when_git_cleaning_matches_the_frozen_blob(policy_clone):
    path = "compatibility/native_containment/contracts.py"
    target = policy_clone / path
    raw = target.read_bytes()
    target.write_bytes(raw.replace(b"\n", b"\r\n"))
    _git(policy_clone, "config", "core.autocrlf", "false")
    with pytest.raises(ValueError):
        _check_policy(policy_clone)
    _git(policy_clone, "config", "core.autocrlf", "true")
    _check_policy(policy_clone)
    target.write_bytes(raw.replace(b"\n", b"\r\n") + b"# not just line endings\r\n")
    with pytest.raises(ValueError):
        _check_policy(policy_clone)


@pytest.mark.parametrize("path", tuple(GUARD_BASES))
def test_each_guard_rejects_unlisted_installed_source_edits(policy_clone, path, monkeypatch):
    import ast

    module = importlib.import_module(path.removesuffix(".py").replace("/", "."))
    monkeypatch.setattr(module, "ROOT", policy_clone)
    source = ast.parse((ROOT / path).read_bytes())
    # Find the original history query, not a guessed/reduced substitute criterion.
    function = next(
        item
        for item in source.body
        if isinstance(item, ast.FunctionDef)
        and any(isinstance(node, ast.Constant) and node.value == "diff" for node in ast.walk(item))
    )
    target = policy_clone / "src/cyberpilot_autotune/__init__.py"
    target.write_bytes(target.read_bytes() + b"\n# not authorized\n")
    with pytest.raises(ValueError, match="path outside closed exception"):
        getattr(module, function.name)()


def test_index_only_unlisted_change_cannot_hide_behind_restored_worktree(policy_clone):
    path = "src/cyberpilot_autotune/__init__.py"
    target = policy_clone / path
    original = target.read_bytes()
    target.write_bytes(original + b"\n# forbidden in index\n")
    _git(policy_clone, "add", "--", path)
    target.write_bytes(original)
    with pytest.raises(ValueError, match="29-path scope"):
        _check_policy(policy_clone)
