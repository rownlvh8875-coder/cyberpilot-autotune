"""Real Git provenance tests; mutation roots are private temporary clones only."""

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "75fd4358a2d42bec55dc85ba85afbb23e8feb6f9"
P2 = "a7b632f2f331c4029789e2ace7ed8cdb8bb48ca2"


def api():
    return importlib.import_module("tests.history_transition.deny_fd_v2_successor")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)


def clone(tmp_path, revision):
    root = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(root)],
        check=True,
        capture_output=True,
    )
    git(root, "-c", "core.autocrlf=false", "checkout", "--quiet", revision)
    return root


def test_new_successor_api_is_required():
    assert importlib.util.find_spec("tests.history_transition.deny_fd_v2_successor") is not None


@pytest.fixture
def current(tmp_path):
    return clone(tmp_path, api().PREREGISTRATION)


def check(root):
    from tests.history_transition.policy import assert_history_transition

    assert_history_transition(
        root,
        "c477cfc1b30578165405b6cbb3af26b7334064e5",
        {"compatibility/native_containment/contracts.py"},
    )


def test_current_preregistration_is_valid_and_not_a_directory_exception(current):
    assert len(api().validate_v2_successor(current)) == 18
    check(current)
    extra = current / "tests/deny_fd_v2/not_approved.py"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_bytes(b"# must not inherit directory permission\n")
    with pytest.raises(ValueError):
        check(current)


def test_historical_p2_and_mutant_head_do_not_grant_new_paths(tmp_path):
    root = clone(tmp_path, P2)
    assert api().validate_v2_successor(root) == frozenset()
    check(root)
    marker = root / "docs/deny_fd_provenance_result.md"
    marker.write_bytes(b"historically mutable new path\n")
    git(root, "add", "--", marker.relative_to(root).as_posix())
    git(root, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "-c",
        "commit.gpgsign=false", "commit", "--quiet", "-m", "historical mutant")
    assert api().validate_v2_successor(root) == frozenset()
    check(root)
    forbidden = root / "tests/deny_fd_v2/wire.py"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_bytes(b"# cannot claim new scope\n")
    with pytest.raises(ValueError):
        check(root)


def test_base_original_source_replays_original_node_in_isolation(tmp_path):
    root = clone(tmp_path, BASE)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_CURRENT_TEST"):
        environment.pop(name, None)
    result = subprocess.run(
        [sys.executable, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--override-ini=addopts=", "--",
         "tests/test_history_transition_policy.py::test_registered_transition_accepts_all_exact_postimages"],
        cwd=root, env=environment, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0 and "1 passed" in result.stdout, result.stdout + result.stderr
    with pytest.raises(ValueError):
        api().validate_v2_successor(root)


@pytest.mark.parametrize("constant", ("BASE", "PREREGISTRATION"))
def test_missing_objects_are_errors_not_legacy_cohort(current, monkeypatch, constant):
    monkeypatch.setattr(api(), constant, "0" * 40)
    with pytest.raises(ValueError):
        api().validate_v2_successor(current)


def test_wrong_preregistration_parent_is_rejected(current, monkeypatch):
    monkeypatch.setattr(api(), "PREREGISTRATION", BASE)
    with pytest.raises(ValueError):
        api().validate_v2_successor(current)


def test_working_manifests_cannot_supply_policy(current):
    v = api()
    (current / v.MANIFEST).write_text('{"allow_everything":true}')
    assert len(v.validate_v2_successor(current)) == 18
    old = current / "docs/evidence/deny_fd_history_successor_v1.json"
    old.write_text('{"allow_everything":true}')
    with pytest.raises(ValueError, match="PRESERVED_FILE_CHANGED"):
        v.validate_v2_successor(current)


def preserved_paths():
    # The approved proposal is replaced by the immutable manifest after P3 exists.
    path = ROOT / "docs/evidence/deny_fd_v2_history_successor_v1.json"
    if not path.exists():
        return ()
    return tuple(row["path"] for row in json.loads(path.read_text())["preserved"])


@pytest.mark.parametrize("path", preserved_paths())
@pytest.mark.parametrize("layer", ("worktree", "index", "head"))
@pytest.mark.parametrize("change", ("content", "delete", "rename", "mode"))
def test_each_preserved_image_all_git_layers(current, path, layer, change):
    mutate_and_reject(current, path, layer, change, "PRESERVED_FILE_CHANGED")


@pytest.mark.parametrize("layer", ("worktree", "index", "head"))
@pytest.mark.parametrize("change", ("content", "delete", "rename", "mode"))
def test_frozen_hook_all_git_layers(current, layer, change):
    mutate_and_reject(current, "tests/history_transition/deny_fd_successor.py", layer, change,
                      "POSTIMAGE_CHANGED")


def mutate_and_reject(root, path, layer, change, reason):
    target = root / path
    raw = target.read_bytes()
    renamed = target.with_name("unapproved_replacement")
    if change == "content":
        target.write_bytes(raw + b"\n# unapproved\n")
    elif change == "delete":
        target.unlink()
    elif change == "rename":
        target.rename(renamed)
    elif layer == "worktree" and os.name != "nt":
        target.chmod(0o755)
    else:
        git(root, "update-index", "--chmod=+x", "--", path)
    if layer != "worktree":
        if change != "mode":
            git(root, "add", "-A")
        if layer == "head":
            git(root, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "-c",
                "commit.gpgsign=false", "commit", "--quiet", "-m", "mutant")
        if renamed.exists():
            renamed.unlink()
        target.write_bytes(raw)
        target.chmod(0o644)
    with pytest.raises(ValueError, match=reason):
        api().validate_v2_successor(root)


@pytest.mark.parametrize("path", ("tests/history_transition/deny_fd_successor.py",
                                  "tests/deny_fd_provenance/contracts.py"))
def test_crlf_requires_real_git_clean_equivalence(current, path):
    target = current / path
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    git(current, "config", "core.autocrlf", "false")
    with pytest.raises(ValueError):
        api().validate_v2_successor(current)
    git(current, "config", "core.autocrlf", "true")
    assert len(api().validate_v2_successor(current)) == 18


def test_unmerged_new_path_is_rejected(current):
    path = "tests/deny_fd_v2/wire.py"
    oid = git(current, "hash-object", "-w", "--stdin").decode().strip()
    subprocess.run(["git", "update-index", "--index-info"], cwd=current,
                   input=f"100644 {oid} 1\t{path}\n".encode(), check=True)
    with pytest.raises(ValueError):
        api().validate_v2_successor(current)


def test_observer_symlink_is_not_a_regular_preserved_file(current):
    path = current / "docs/deny_fd_provenance_result.md"
    path.unlink()
    try:
        path.symlink_to("README.md")
    except OSError:
        # Platforms without symlink privilege still exercise nonregular absence.
        pass
    with pytest.raises(ValueError):
        api().validate_v2_successor(current)
