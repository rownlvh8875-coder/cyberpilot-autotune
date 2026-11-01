"""Real Git policy boundaries for the dedicated transport successor."""

import importlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def api():
    name = "tests.history_transition.deny_fd_v2_transport_successor"
    assert importlib.util.find_spec(name) is not None, "transport successor required"
    return importlib.import_module(name)


def test_predecessor_has_no_transport_permission(tmp_path):
    root = tmp_path / "predecessor"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(root)], check=True
    )
    subprocess.run(
        ["git", "checkout", "--quiet", "27cfdee55d2276f66d899adc07565da717ab554f"],
        cwd=root,
        check=True,
    )
    assert api().validate_transport_successor(root) == frozenset()


@pytest.mark.parametrize("constant", ("BASE", "PREREGISTRATION"))
def test_missing_git_object_cannot_grant_transport_permission(monkeypatch, constant):
    successor = api()
    monkeypatch.setattr(successor, constant, "0" * 40)
    with pytest.raises(ValueError):
        successor.validate_transport_successor(ROOT)


def test_invalid_git_root_cannot_be_treated_as_historical(tmp_path):
    with pytest.raises(ValueError):
        api().validate_transport_successor(tmp_path)


@pytest.mark.parametrize("layer", ("worktree", "index", "HEAD"))
@pytest.mark.parametrize(
    "path",
    (
        "tests/deny_fd_v2/wire.py",
        "tests/history_transition/deny_fd_v2_harness_successor.py",
        "tests/architecture/test_deny_fd_v2_harness_boundary.py",
    ),
)
def test_preserved_and_routing_images_reject_mutation(tmp_path, layer, path):
    from tests.test_deny_fd_v2_harness_history import checkout, git

    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        target = root / path
        target.write_bytes(target.read_bytes() + b"# forbidden drift\n")
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
                "owned mutation",
            )
        with pytest.raises(ValueError, match="IMAGE_CHANGED"):
            v.validate_transport_successor(root)


@pytest.mark.parametrize("layer", ("worktree", "index", "HEAD"))
def test_unlisted_sibling_never_gets_directory_permission(tmp_path, layer):
    from tests.test_deny_fd_v2_harness_history import checkout, git

    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        path = "tests/deny_fd_v2_transport/unlisted.py"
        target = root / path
        target.parent.mkdir(parents=True)
        target.write_bytes(b"# not allowed\n")
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
                "owned mutation",
            )
        if layer == "index":
            target.unlink()
        with pytest.raises(ValueError, match="scope"):
            v.validate_transport_successor(root)


def test_wrong_p5_parent_refused(tmp_path, monkeypatch):
    from tests.test_deny_fd_v2_harness_history import checkout

    v = api()
    with checkout(tmp_path, v.BASE) as root:
        monkeypatch.setattr(v, "PREREGISTRATION", v.BASE)
        with pytest.raises(ValueError, match="sole parent"):
            v.validate_transport_successor(root)


def test_mutable_manifest_cannot_replace_pinned_policy(tmp_path):
    from tests.test_deny_fd_v2_harness_history import checkout

    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        (root / v.MANIFEST).write_bytes(b'{"allow_everything":true}\n')
        assert len(v.validate_transport_successor(root)) == 20


def test_git_ancestry_failure_is_not_historical_permission(tmp_path, monkeypatch):
    from tests.history_transition import deny_fd_v2_successor as prior
    from tests.test_deny_fd_v2_harness_history import checkout

    v = api()
    with checkout(tmp_path, v.BASE) as root:

        def fail(*args):
            raise ValueError("ancestry unavailable")

        monkeypatch.setattr(prior, "_ancestor", fail)
        with pytest.raises(ValueError, match="unavailable"):
            v.validate_transport_successor(root)


def test_unmerged_index_cannot_supply_transport_permission(tmp_path):
    from tests.test_deny_fd_v2_harness_history import checkout, git

    v = api()
    with checkout(tmp_path, v.PREREGISTRATION) as root:
        path = "tests/deny_fd_v2/wire.py"
        oid = git(root, "rev-parse", "HEAD:" + path).decode().strip()
        git(root, "update-index", "--force-remove", "--", path)
        payload = f"100644 {oid} 2\t{path}\n100644 {oid} 3\t{path}\n".encode()
        subprocess.run(
            ["git", "update-index", "--index-info"],
            cwd=root,
            input=payload,
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="unmerged"):
            v.validate_transport_successor(root)


@pytest.mark.parametrize(
    "mutation", ("shape", "schema", "permission", "paths", "preserved", "routing")
)
def test_malformed_pinned_registration_never_grants_permission(tmp_path, monkeypatch, mutation):
    from tests.test_deny_fd_v2_harness_history import checkout, git

    v = api()
    pinned = v.PREREGISTRATION
    with checkout(tmp_path, v.BASE) as root:
        data = json.loads(git(root, "show", pinned + ":" + v.MANIFEST))
        for path in v.MODIFIED:
            (root / path).write_bytes(git(root, "show", pinned + ":" + path))
        if mutation == "shape":
            data["unexpected"] = True
        elif mutation == "schema":
            data["schema"] = "other"
        elif mutation == "permission":
            data["permissions"]["application_authorized"] = 0
        elif mutation == "paths":
            data["new_paths"][-1] = data["new_paths"][0]
        elif mutation == "preserved":
            data["preserved"][0]["image"]["sha256"] = "0" * 64
        else:
            data["modified"][0]["postimage"]["sha256"] = "0" * 64
        (root / v.MANIFEST).write_text(json.dumps(data))
        git(root, "add", "--", v.MANIFEST, *sorted(v.MODIFIED))
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
            "owned malformed preregistration",
        )
        monkeypatch.setattr(v, "PREREGISTRATION", git(root, "rev-parse", "HEAD").decode().strip())
        with pytest.raises(ValueError):
            v.validate_transport_successor(root)
