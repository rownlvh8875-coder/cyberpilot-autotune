"""P4 exact closed delta and original-source replay, never runtime authority."""

import os
import stat
import subprocess
import sys
from pathlib import Path

BASE = "a97321f6bbf5c3e5d6e3205615e0a600b059b89a"
PREREGISTRATION = "06f959c12b2e2fdf3c9a374ee9787001483fc587"
PRIOR_P3 = "18750676a84a4237576f6c50be3b01fa21053252"
MANIFEST = "docs/evidence/deny_fd_v2_harness_history_v1.json"
MODIFIED = frozenset(
    (
        "tests/history_transition/deny_fd_v2_successor.py",
        "tests/architecture/test_deny_fd_v2_boundary.py",
    )
)
NEW_PATHS = frozenset(
    (
        "docs/deny_fd_v2_harness_contract.md",
        "docs/deny_fd_v2_harness_result.md",
        "docs/evidence/deny_fd_v2_harness_assets_v1.json",
        "docs/evidence/deny_fd_v2_harness_history_v1.json",
        "docs/superpowers/plans/2026-11-01-deny-fd-v2-harness.md",
        "docs/superpowers/specs/2026-11-01-deny-fd-v2-harness-design.md",
        "tests/architecture/test_deny_fd_v2_harness_boundary.py",
        "tests/deny_fd_v2_harness/__init__.py",
        "tests/deny_fd_v2_harness/assets.py",
        "tests/deny_fd_v2_harness/capture.py",
        "tests/deny_fd_v2_harness/contracts.py",
        "tests/deny_fd_v2_harness/host_main.py",
        "tests/deny_fd_v2_harness/image.py",
        "tests/deny_fd_v2_harness/runner.py",
        "tests/history_transition/deny_fd_v2_harness_successor.py",
        "tests/test_deny_fd_v2_harness_assets.py",
        "tests/test_deny_fd_v2_harness_capture.py",
        "tests/test_deny_fd_v2_harness_history.py",
        "tests/test_deny_fd_v2_harness_image.py",
        "tests/test_deny_fd_v2_harness_runner.py",
    )
)


def _need(value, reason):
    if not value:
        raise ValueError("harness successor: " + reason)


def validate_harness_successor(root: Path) -> frozenset[str]:
    import importlib.util

    name = "tests.history_transition.deny_fd_v2_transport_successor"
    if importlib.util.find_spec(name) is not None:
        from .deny_fd_v2_transport_successor import validate_transport_successor

        extra = validate_transport_successor(root)
        if extra:
            return NEW_PATHS | extra
    # Lazy import avoids a loader cycle; the already-loaded predecessor owns
    # the unchanged raw Git/clock/error primitives.
    from . import deny_fd_v2_successor as prior

    for revision in (BASE, PREREGISTRATION, "HEAD"):
        prior._git(root, "rev-parse", "--verify", revision + "^{commit}")
    _need(
        prior._git(root, "rev-list", "--parents", "-n", "1", PREREGISTRATION).decode().split()
        == [PREREGISTRATION, BASE],
        "P4 sole parent",
    )
    _need(prior._ancestor(root, PRIOR_P3, BASE), "P3 lineage")
    if not prior._ancestor(root, PREREGISTRATION, "HEAD"):
        return frozenset()
    data = prior._manifest(root, PREREGISTRATION, MANIFEST)
    _need(
        type(data) is dict
        and set(data)
        == {
            "schema",
            "source_base",
            "prior_P3",
            "preserved",
            "modified",
            "new_paths",
            "digest_meaning",
            "runtime_qualified",
            "permissions",
        },
        "manifest shape",
    )
    _need(
        data["schema"] == "deny-fd-v2-harness-history-v1"
        and data["source_base"] == BASE
        and data["prior_P3"] == PRIOR_P3
        and data["digest_meaning"] == "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY"
        and data["runtime_qualified"] is False,
        "manifest semantics",
    )
    _need(
        type(data["permissions"]) is dict
        and set(data["permissions"]) == prior.PERMISSIONS
        and all(v is False for v in data["permissions"].values()),
        "permissions",
    )
    _need(
        type(data["new_paths"]) is list
        and len(data["new_paths"]) == 20
        and all(type(p) is str for p in data["new_paths"])
        and set(data["new_paths"]) == NEW_PATHS,
        "closed20 scope",
    )
    original = prior._manifest(
        root, prior.P, "docs/evidence/strict_input_history_transition_v1.json"
    )
    second = prior._manifest(root, prior.P2, "docs/evidence/deny_fd_history_successor_v1.json")
    paths = {r["path"] for r in original["files"]} | set(original["new_paths"])
    paths |= set(second["new_paths"]) | set(prior.NEW_PATHS)
    _need(len(paths) == 58 and MODIFIED <= paths and not paths & NEW_PATHS, "prior58 scope")
    for key, expected, fields in (
        ("preserved", paths - MODIFIED, {"path", "image"}),
        ("modified", MODIFIED, {"path", "preimage", "postimage"}),
    ):
        rows = data[key]
        _need(
            type(rows) is list
            and len(rows) == len(expected)
            and all(type(r) is dict and set(r) == fields for r in rows)
            and {r["path"] for r in rows} == expected,
            key + " scope",
        )
    before = prior._tree(root, BASE, paths)
    proof = prior._tree(root, PREREGISTRATION, paths)
    _need(set(before) == paths and set(proof) == paths, "incomplete pinned tree")
    blobs = prior._blobs(root, {oid for _, oid in (*before.values(), *proof.values())})
    for row in data["preserved"]:
        p = row["path"]
        _need(
            before[p] == proof[p]
            and before[p][0] == "100644"
            and prior._image(blobs[before[p][1]], before[p][0]) == row["image"],
            "preserved pinned IMAGE_CHANGED",
        )
    for row in data["modified"]:
        for tree, label in ((before, "preimage"), (proof, "postimage")):
            mode, oid = tree[row["path"]]
            _need(
                mode == "100644" and prior._image(blobs[oid], mode) == row[label],
                "routing pinned IMAGE_CHANGED",
            )
    _need(not prior._git(root, "ls-files", "--unmerged", "-z"), "unmerged index")
    index = {}
    for entry in prior._git(root, "ls-files", "--stage", "-z", "--", *sorted(paths)).split(b"\0"):
        if entry:
            header, p = entry.split(b"\t", 1)
            mode, oid, stage = header.decode().split()
            p = p.decode()
            _need(stage == "0" and p not in index, "index shape")
            index[p] = (mode, oid)
    head = prior._tree(root, "HEAD", paths)
    for p in sorted(paths):
        expected = proof[p] if p in MODIFIED else before[p]
        _need(head.get(p) == expected and index.get(p) == expected, "IMAGE_CHANGED")
        try:
            target = root / p
            info = target.lstat()
            raw = target.read_bytes() if stat.S_ISREG(info.st_mode) else b""
        except OSError as error:
            raise ValueError("harness successor: IMAGE_CHANGED") from error
        _need(stat.S_ISREG(info.st_mode) and not info.st_mode & 0o111, "IMAGE_CHANGED")
        if raw != blobs[expected[1]]:
            _need(raw.replace(b"\r\n", b"\n") == blobs[expected[1]], "IMAGE_CHANGED")
            clean = (
                prior._git(root, "hash-object", "--path", p, "--stdin", raw=raw).decode().strip()
            )
            _need(clean == expected[1], "IMAGE_CHANGED")
    allowed = MODIFIED | NEW_PATHS
    for args in (
        ("diff", "--no-renames", "--name-only", "-z", BASE, "HEAD", "--"),
        ("diff", "--no-renames", "--name-only", "-z", "--cached", BASE, "--"),
        ("diff", "--no-renames", "--name-only", "-z", BASE, "--"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        observed = {p.decode() for p in prior._git(root, *args).split(b"\0") if p}
        _need(observed <= allowed, "outside22 scope")
    return NEW_PATHS


def replay_original_scope(root: Path, tmp_path: Path) -> None:
    from _pytest.pathlib import rm_rf

    from . import deny_fd_v2_successor as prior

    source = tmp_path / "original-source"
    prior._git(root, "clone", "--shared", "--quiet", "--no-checkout", str(root), str(source))
    prior._git(source, "-c", "core.autocrlf=false", "checkout", "--quiet", BASE)
    environment = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        GIT_NO_LAZY_FETCH="1",
        GIT_NO_REPLACE_OBJECTS="1",
    )
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_CURRENT_TEST"):
        environment.pop(name, None)
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
            "--basetemp=" + str(tmp_path / "p"),
            "--",
            "tests/architecture/test_deny_fd_v2_boundary.py::"
            "test_final_head_contains_exact_approved_delta_and_preserves_old_images",
        ],
        cwd=source,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    _need(
        result.returncode == 0 and "1 passed" in result.stdout,
        "original19 source replay failed: " + result.stdout + result.stderr,
    )
    rm_rf(source)
    _need(not source.exists(), "owned original source cleanup failed")
