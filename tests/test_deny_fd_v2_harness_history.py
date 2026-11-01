"""Real Git successor checks; every mutated checkout is privately owned."""

import importlib
import importlib.util
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest
from _pytest.pathlib import rm_rf

ROOT = Path(__file__).resolve().parents[1]
BASE = "a97321f6bbf5c3e5d6e3205615e0a600b059b89a"


def api():
    name = "tests.history_transition.deny_fd_v2_harness_successor"
    assert importlib.util.find_spec(name) is not None, "closed harness successor required"
    return importlib.import_module(name)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)


@contextmanager
def checkout(tmp_path, revision):
    root = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(root)],
        check=True,
        capture_output=True,
    )
    git(root, "-c", "core.autocrlf=false", "checkout", "--quiet", revision)
    yield root
    rm_rf(root)  # Only reached after a successful test body; retain failed evidence.
    assert not root.exists()


def test_historical_cohort_grants_no_harness_paths(tmp_path):
    v = api()
    with checkout(tmp_path, BASE) as root:
        assert v.validate_harness_successor(root) == frozenset()


def test_preregistered_scope_rejects_an_unlisted_sibling(tmp_path):
    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        assert len(v.validate_harness_successor(root)) == 20
        extra = root / "tests/deny_fd_v2_harness/unlisted.py"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_bytes(b"# no directory exception\n")
        with pytest.raises(ValueError, match="scope"):
            v.validate_harness_successor(root)


def test_original_19_path_node_replays_original_source(tmp_path):
    api().replay_original_scope(ROOT, tmp_path)


@pytest.mark.parametrize("layer", ("worktree", "index", "HEAD"))
@pytest.mark.parametrize(
    "path",
    (
        "tests/history_transition/deny_fd_v2_successor.py",
        "tests/architecture/test_deny_fd_v2_boundary.py",
        "tests/deny_fd_v2/wire.py",
    ),
)
def test_head_index_and_working_images_are_enforced(tmp_path, layer, path):
    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        target = root / path
        target.write_bytes(target.read_bytes() + b"# forbidden image drift\n")
        if layer in ("index", "HEAD"):
            git(root, "add", "--", path)
        if layer == "HEAD":
            git(
                root,
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--quiet",
                "-m",
                "private mutant",
            )
        with pytest.raises(ValueError, match="IMAGE_CHANGED"):
            v.validate_harness_successor(root)


@pytest.mark.parametrize("constant", ("BASE", "PREREGISTRATION"))
def test_missing_objects_are_not_historical_permission(tmp_path, monkeypatch, constant):
    v = api()
    with checkout(tmp_path, BASE) as root:
        monkeypatch.setattr(v, constant, "0" * 40)
        with pytest.raises(ValueError):
            v.validate_harness_successor(root)


def test_wrong_preregistration_parent_is_rejected(tmp_path, monkeypatch):
    v = api()
    with checkout(tmp_path, BASE) as root:
        monkeypatch.setattr(v, "PREREGISTRATION", BASE)
        with pytest.raises(ValueError):
            v.validate_harness_successor(root)


def test_ancestry_transport_error_is_not_a_historical_cohort(tmp_path, monkeypatch):
    v = api()
    from tests.history_transition import deny_fd_v2_successor as prior

    with checkout(tmp_path, BASE) as root:

        def unavailable(*args, **kwargs):
            raise ValueError("ancestry transport unavailable")

        monkeypatch.setattr(prior, "_ancestor", unavailable)
        with pytest.raises(ValueError, match="unavailable"):
            v.validate_harness_successor(root)


def test_mutable_manifest_never_supplies_permission(tmp_path):
    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        (root / v.MANIFEST).write_bytes(b'{"allow_everything":true}\n')
        assert len(v.validate_harness_successor(root)) == 20
        extra = root / "docs/not-approved.md"
        extra.write_bytes(b"unlisted\n")
        git(root, "add", "--", "docs/not-approved.md")
        extra.unlink()
        with pytest.raises(ValueError, match="scope"):
            v.validate_harness_successor(root)
