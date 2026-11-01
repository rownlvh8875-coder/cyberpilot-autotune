"""One user-approved exact-content history transition, not runtime authority.

The immutable preregistration precedes this helper. Missing local objects fail
closed, without fetch. A final review/CI of this helper is still required; no
self-hash or manifest digest pretends to authenticate the executing program.
"""

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

from .deny_fd_successor import validate_successor

BASE = "cfc31c36c1fa99c7d00d9609c5360b9e07894d7e"
PREREGISTRATION = "127f485437437b3472659784b7b05857d8fbd896"
MANIFEST = "docs/evidence/strict_input_history_transition_v1.json"
REPAIR_PATHS = frozenset(
    (
        "compatibility/native_containment/contracts.py",
        "tests/audit/validate_guest_input_handoff_design.py",
        "tests/test_strict_containment_input.py",
        "tests/test_strict_handoff_limits.py",
    )
)
GUARD_BASES = {
    f"tests/architecture/test_{name}_boundary.py": revision
    for name, revision in (
        ("bootstrap_tag_audit", "37c0e614f01e13b5e6078178b3712c0ec6ba4495"),
        ("copy_reference_publication", "5581049957088b348498eb5ef0b1061f76d19b7c"),
        ("epoch_decoder_bridge", "4371dfe5e69878665abcb9133cc20d5e0451949d"),
        ("epoch_encoding_design", "72362dcf235f91cbce30501aeeb72b66ee6c124c"),
        ("fd_ofd_lifetime_design", "3a831fdd423aa98638082eba126519db19f432d6"),
        ("fork_copy_design", "420538d7c20edcfca3eadf136b30b622ca2bede9"),
        ("guest_bootstrap", "2d11becc2f5b3b71558db6c944de74ddf18354b3"),
        ("guest_epoch_u64", "1d9207723ac63c90d8a2173bd401e3115abe2edf"),
        ("guest_fork_copy", "4a04a5a38a68970624380c10113c97a752af4aa8"),
        ("guest_input_handoff", "0652c87c5e1da83d2cf4a3336713b9839e929ae3"),
        ("guest_raw_lifetime", "57b2c942d38f26343bb73fa8cf0f813c58f920a5"),
        ("guest_root_scope", "06e218ca9e17af9547fc7871df70d2b9415f2cb9"),
        ("guest_tag_snapshot", "eba2e74759cefa65a941ebce09ce2a4cfa33ec21"),
        ("inherited_ofd_design", "21a542eba9e889323b2cb1b7d7c75d9c9cab1025"),
        ("kernel_lifetime_feasibility", "a982d1bec759916013981f9cbc76ced6679c71ea"),
        ("strict_containment_input", "0095e64fbe8cf9815e14226f527bf654315a12dc"),
        ("strict_handoff_limits", "c477cfc1b30578165405b6cbb3af26b7334064e5"),
        ("tag_read_protocol", "e01cdc127bbb17073aa47967b926b68088f57ded"),
    )
}
NEW_PATHS = frozenset(
    [
        "docs/evidence/strict_input_history_transition_v1.json",
        "docs/strict_input_original_repair_result.md",
        "tests/history_transition/__init__.py",
        "tests/history_transition/frozen_cases.py",
        "tests/history_transition/policy.py",
        "tests/test_history_transition_policy.py",
        "tests/test_original_strict_input_repairs.py",
    ]
)


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("unapproved history transition: " + message)


def _git(root: Path, *args: str, raw: bytes | None = None) -> bytes:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            input=raw,
            stderr=subprocess.PIPE,
            timeout=30,
            env=dict(
                os.environ,
                GIT_NO_LAZY_FETCH="1",
                GIT_NO_REPLACE_OBJECTS="1",
                GIT_OPTIONAL_LOCKS="0",
            ),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(
            "history policy Git object/state unavailable; no fetch or fallback"
        ) from error


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        _need(key not in result, "duplicate manifest key")
        result[key] = value
    return result


def _image(raw: bytes, mode: str) -> dict[str, str]:
    return {
        "mode": mode,
        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _tree(root: Path, revision: str, paths: set[str]) -> dict[str, tuple[str, str]]:
    result = {}
    for row in _git(root, "ls-tree", "-rz", revision, "--", *sorted(paths)).split(b"\0"):
        if not row:
            continue
        header, name = row.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        _need(kind == "blob" and mode == "100644", "unsupported tracked mode/type")
        path = name.decode("utf-8")
        _need(path not in result, "duplicate tracked path")
        result[path] = (mode, oid)
    return result


def _load(root: Path) -> dict:
    # No mutable working-manifest read, symbolic ref, branch-name or wall-clock pin.
    _need(_git(root, "rev-parse", PREREGISTRATION + "^").decode().strip() == BASE, "wrong parent")
    _git(root, "merge-base", "--is-ancestor", PREREGISTRATION, "HEAD")
    manifest = json.loads(
        _git(root, "show", PREREGISTRATION + ":" + MANIFEST), object_pairs_hook=_unique
    )
    _need(type(manifest) is dict, "manifest object required")
    _need(
        set(manifest)
        == {
            "schema",
            "source_revision",
            "evidence_kind",
            "digest_meaning",
            "files",
            "guards",
            "new_paths",
            "runtime_qualified",
            "permissions",
        },
        "manifest fields",
    )
    _need(
        manifest["schema"] == "strict-input-history-transition-v1"
        and manifest["source_revision"] == BASE
        and manifest["evidence_kind"] == "POLICY_CONTENT_METADATA_NOT_RUNTIME_EVIDENCE"
        and manifest["digest_meaning"] == "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY"
        and manifest["runtime_qualified"] is False,
        "manifest semantics",
    )
    _need(
        type(manifest["permissions"]) is dict
        and set(manifest["permissions"])
        == {
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "owner_proposal_allowed",
        }
        and all(value is False for value in manifest["permissions"].values()),
        "permissions must remain false",
    )
    _need(type(manifest["new_paths"]) is list and len(manifest["new_paths"]) == 7, "new path count")
    _need(set(manifest["new_paths"]) == NEW_PATHS, "new path scope")
    guards = manifest["guards"]
    _need(type(guards) is list and len(guards) == len(GUARD_BASES), "guard count")
    _need({row["path"]: row["base_revision"] for row in guards} == GUARD_BASES, "guard identities")
    return manifest


def assert_history_transition(root: Path, guard_base: str, changed: set[str]) -> None:
    """Retain the caller's original BASE/scope; admit only this exact transition."""
    paths = set(REPAIR_PATHS) | set(GUARD_BASES)
    _need(guard_base in GUARD_BASES.values(), "unregistered guard base")
    _need(type(changed) is set and changed <= paths, "path outside closed exception")
    manifest = _load(root)
    rows = manifest["files"]
    _need(type(rows) is list and len(rows) == len(paths), "file count")
    _need({row["path"] for row in rows} == paths, "file scope")
    before, frozen = _tree(root, BASE, paths), _tree(root, PREREGISTRATION, paths)
    _need(set(before) == paths and set(frozen) == paths, "missing frozen path")
    postimages = {}
    for row in rows:
        path = row["path"]
        _need(set(row) == {"path", "preimage", "postimage"}, "file record fields")
        for revision, image, entries in (
            (BASE, "preimage", before),
            (PREREGISTRATION, "postimage", frozen),
        ):
            raw = _git(root, "cat-file", "blob", revision + ":" + path)
            _need(_image(raw, entries[path][0]) == row[image], image + " content/mode mismatch")
            if image == "postimage":
                postimages[path] = raw
    # Existing protected blobs present at each old BASE must retain their preimages.
    old = _tree(root, guard_base, paths)
    _need(all(before[path] == value for path, value in old.items()), "old BASE preimage drift")
    _need(_tree(root, "HEAD", paths) == frozen, "HEAD postimage mismatch")
    index = {}
    for row in _git(root, "ls-files", "--stage", "-z", "--", *sorted(paths)).split(b"\0"):
        if not row:
            continue
        header, name = row.split(b"\t", 1)
        mode, oid, stage = header.decode("ascii").split()
        path = name.decode("utf-8")
        _need(stage == "0" and path not in index, "unmerged/duplicate index path")
        index[path] = (mode, oid)
    _need(index == frozen, "index postimage mismatch")
    for path, expected in postimages.items():
        target = root / path
        try:
            status = target.lstat()
            raw = target.read_bytes() if stat.S_ISREG(status.st_mode) else b""
        except OSError as error:
            raise ValueError("unapproved history transition: worktree path unavailable") from error
        _need(stat.S_ISREG(status.st_mode), "worktree path is not a regular file")
        _need(not status.st_mode & 0o111, "worktree executable mode changed")
        if raw != expected:
            # Only actual Git-clean CRLF normalization is accepted, not arbitrary filters.
            _need(raw.replace(b"\r\n", b"\n") == expected, "worktree postimage mismatch")
            cleaned = _git(root, "hash-object", "--path", path, "--stdin", raw=raw).decode().strip()
            _need(cleaned == frozen[path][1], "worktree CRLF not Git-clean equivalent")
    allowed = paths | set(NEW_PATHS) | set(validate_successor(root))
    for args in (
        ("diff", "--no-renames", "--name-only", "-z", BASE, "HEAD", "--"),
        ("diff", "--no-renames", "--name-only", "-z", "--cached", BASE, "--"),
        ("diff", "--no-renames", "--name-only", "-z", BASE, "--"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        observed = {name.decode("utf-8") for name in _git(root, *args).split(b"\0") if name}
        _need(observed <= allowed, "change outside approved 29-path scope and pinned successor")
