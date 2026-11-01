"""Exercise the bounded history exception and frozen historical execution."""

import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys

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


def test_successor_policy_requires_its_separate_immutable_preregistration():
    # The former seven mutable paths cannot implicitly authorize this new scope.
    assert importlib.util.find_spec("tests.history_transition.deny_fd_successor") is not None


def test_exact_history_policy_is_implemented():
    # Changed guards must not gain a path-only exception without content checks.
    assert importlib.util.find_spec("tests.history_transition.policy") is not None


@pytest.fixture
def policy_clone(tmp_path):
    from tests.history_transition.deny_fd_successor import PREREGISTRATION

    checkout = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(checkout)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "core.autocrlf=false", "checkout", "--quiet", PREREGISTRATION],
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
    from tests.history_transition import policy

    pinned = policy._load(policy_clone)
    path = policy_clone / "docs/evidence/strict_input_history_transition_v1.json"
    path.write_text('{"allow_everything":true}')
    assert policy._load(policy_clone) == pinned  # immutable metadata still wins
    with pytest.raises(ValueError, match="PRESERVED_FILE_CHANGED"):
        _check_policy(policy_clone)  # explicitly stronger successor preservation


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


def test_historical_manifest_acceptance(tmp_path):
    """Execute the original acceptance assertion, not a rewritten approximation."""
    checkout = tmp_path / "v1"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(checkout)],
        check=True,
        capture_output=True,
    )
    _git(
        checkout,
        "-c",
        "core.autocrlf=false",
        "checkout",
        "--quiet",
        "1c4fb3d26db913645cb2292f362396076e47adcb",
    )
    environment = dict(os.environ)
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_CURRENT_TEST"):
        environment.pop(name, None)
    environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--override-ini=addopts=",
            "--",
            "tests/test_history_transition_policy.py::test_mutable_manifest_is_never_policy_authority",
        ],
        cwd=checkout,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0 and "1 passed" in result.stdout, result.stdout + result.stderr


def test_successor_cannot_fallback_to_old_or_missing_policy(policy_clone, monkeypatch):
    from tests.history_transition import deny_fd_successor as successor

    for revision in ("0" * 40, "127f485437437b3472659784b7b05857d8fbd896"):
        monkeypatch.setattr(successor, "PREREGISTRATION", revision)
        with pytest.raises(ValueError):
            _check_policy(policy_clone)


def test_working_successor_manifest_does_not_change_policy(policy_clone):
    from tests.history_transition import deny_fd_successor as successor

    path = policy_clone / successor.MANIFEST
    path.write_text('{"allow_everything":true}')
    _check_policy(policy_clone)


def test_every_preserved_old_phase_path_is_still_checked(policy_clone):
    from tests.history_transition import deny_fd_successor as successor

    manifest = json.loads(
        _git(policy_clone, "show", successor.PREREGISTRATION + ":" + successor.MANIFEST)
    )
    assert len(manifest["preserved"]) == 27
    for row in manifest["preserved"]:
        target = policy_clone / row["path"]
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n# unapproved preserved-file change\n")
            with pytest.raises(ValueError, match="PRESERVED_FILE_CHANGED"):
                successor.validate_successor(policy_clone)
        finally:
            target.write_bytes(original)


@pytest.mark.parametrize(
    "path", ("tests/history_transition/policy.py", "tests/test_history_transition_policy.py")
)
@pytest.mark.parametrize("layer", ("worktree", "index", "head"))
@pytest.mark.parametrize("change", ("content", "delete", "rename", "mode"))
def test_successor_updated_paths_are_exact_not_path_whitelisted(policy_clone, path, layer, change):
    from tests.history_transition import deny_fd_successor as successor

    target = policy_clone / path
    renamed = target.with_name("unapproved.py")
    original = target.read_bytes()
    if change == "content":
        target.write_bytes(original + b"\n# unapproved successor postimage\n")
    elif change == "delete":
        target.unlink()
    elif change == "rename":
        target.rename(renamed)
    elif layer == "worktree" and os.name != "nt":
        target.chmod(0o755)
    else:
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
                "unapproved postimage",
            )
        if renamed.exists():
            renamed.unlink()
        target.write_bytes(original)
        target.chmod(0o644)
    with pytest.raises(ValueError, match="POSTIMAGE_CHANGED"):
        successor.validate_successor(policy_clone)


@pytest.mark.parametrize(
    "path", ("tests/history_transition/frozen_cases.py", "tests/history_transition/policy.py")
)
def test_successor_crlf_requires_actual_git_clean_equivalence(policy_clone, path):
    target = policy_clone / path
    raw = target.read_bytes()
    target.write_bytes(raw.replace(b"\n", b"\r\n"))
    _git(policy_clone, "config", "core.autocrlf", "false")
    with pytest.raises(ValueError):
        _check_policy(policy_clone)
    _git(policy_clone, "config", "core.autocrlf", "true")
    _check_policy(policy_clone)


def test_successor_additions_are_closed_not_an_entire_prefix(policy_clone):
    target = policy_clone / "tests/deny_fd_provenance/unapproved.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"# no directory-wide exception\n")
    with pytest.raises(ValueError, match="29-path scope"):
        _check_policy(policy_clone)
