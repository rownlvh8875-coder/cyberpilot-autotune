"""Pinned successor for one explicit 13-path local change; no runtime authority.

This new loader is intentionally outside the two frozen postimages, so its P2
pin is not self-referential. Its own authenticity rests on exact-head review,
not its content digests. Missing local Git objects never trigger fetch/fallback.
"""

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

from .deny_fd_v2_successor import validate_v2_successor

SOURCE_BASE = "1c4fb3d26db913645cb2292f362396076e47adcb"
PRIOR = "127f485437437b3472659784b7b05857d8fbd896"
PREREGISTRATION = "a7b632f2f331c4029789e2ace7ed8cdb8bb48ca2"
MANIFEST = "docs/evidence/deny_fd_history_successor_v1.json"
PRIOR_MANIFEST = "docs/evidence/strict_input_history_transition_v1.json"
MODIFIED = frozenset(
    ("tests/history_transition/policy.py", "tests/test_history_transition_policy.py")
)
NEW_PATHS = frozenset(
    (
        "docs/deny_fd_provenance_result.md",
        "docs/evidence/deny_fd_history_successor_v1.json",
        "docs/evidence/deny_fd_provenance_schema.json",
        "docs/superpowers/plans/2026-11-01-deny-fd-provenance.md",
        "docs/superpowers/specs/2026-11-01-deny-fd-provenance-design.md",
        "tests/architecture/test_deny_fd_provenance_boundary.py",
        "tests/deny_fd_provenance/__init__.py",
        "tests/deny_fd_provenance/contracts.py",
        "tests/deny_fd_provenance/validation.py",
        "tests/history_transition/deny_fd_successor.py",
        "tests/test_deny_fd_provenance.py",
    )
)


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("denial history successor: " + reason)


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
            "denial successor Git object/state unavailable; no fetch or fallback"
        ) from error


def _unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        _need(key not in result, "duplicate manifest key")
        result[key] = value
    return result


def _tree(root: Path, revision: str, paths: set[str]) -> dict[str, tuple[str, str]]:
    result = {}
    for row in _git(root, "ls-tree", "-rz", revision, "--", *sorted(paths)).split(b"\0"):
        if row:
            head, name = row.split(b"\t", 1)
            mode, _kind, oid = head.decode("ascii").split()
            path = name.decode("utf-8")
            _need(path not in result, "duplicate tree path")
            result[path] = (mode, oid)
    return result


def _blobs(root: Path, oids: set[str]) -> dict[str, bytes]:
    """Batch raw object bytes, never git-archive checkout/newline conversion."""
    ordered = sorted(oids)
    data = _git(root, "cat-file", "--batch", raw=("\n".join(ordered) + "\n").encode("ascii"))
    result = {}
    offset = 0
    for oid in ordered:
        end = data.index(b"\n", offset)
        header = data[offset:end].decode("ascii").split()
        _need(len(header) == 3 and header[:2] == [oid, "blob"], "raw blob unavailable")
        size = int(header[2])
        _need(size >= 0, "invalid blob size")
        offset = end + 1
        raw = data[offset : offset + size]
        offset += size
        _need(len(raw) == size and data[offset : offset + 1] == b"\n", "incomplete raw blob")
        offset += 1
        result[oid] = raw
    _need(offset == len(data), "trailing raw blob data")
    return result


def _image(raw: bytes, mode: str) -> dict[str, str]:
    return {
        "mode": mode,
        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def validate_successor(root: Path) -> frozenset[str]:
    _git(root, "merge-base", "--is-ancestor", PRIOR, SOURCE_BASE)
    _git(root, "merge-base", "--is-ancestor", SOURCE_BASE, PREREGISTRATION)
    _git(root, "merge-base", "--is-ancestor", PREREGISTRATION, "HEAD")
    data = json.loads(
        _git(root, "show", PREREGISTRATION + ":" + MANIFEST), object_pairs_hook=_unique
    )
    _need(
        type(data) is dict
        and set(data)
        == {
            "schema",
            "source_base",
            "prior_preregistration",
            "modified",
            "preserved",
            "digest_meaning",
            "runtime_qualified",
            "permissions",
            "new_paths",
        },
        "manifest shape",
    )
    _need(
        data["schema"] == "deny-fd-history-successor-v1"
        and data["source_base"] == SOURCE_BASE
        and data["prior_preregistration"] == PRIOR
        and data["digest_meaning"] == "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY"
        and data["runtime_qualified"] is False,
        "manifest semantics",
    )
    permissions = data["permissions"]
    _need(
        type(permissions) is dict
        and set(permissions)
        == {
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "owner_proposal_allowed",
        }
        and all(value is False for value in permissions.values()),
        "permissions must stay false",
    )
    _need(
        type(data["new_paths"]) is list
        and len(data["new_paths"]) == 11
        and set(data["new_paths"]) == NEW_PATHS,
        "closed successor additions",
    )
    prior = json.loads(_git(root, "show", PRIOR + ":" + PRIOR_MANIFEST), object_pairs_hook=_unique)
    paths = {row["path"] for row in prior["files"]} | set(prior["new_paths"])
    _need(len(paths) == 29 and MODIFIED <= paths and not (NEW_PATHS & paths), "prior scope")
    preserved = data["preserved"]
    modified = data["modified"]
    _need(
        type(preserved) is list
        and len(preserved) == 27
        and {row["path"] for row in preserved} == paths - MODIFIED,
        "preserved scope",
    )
    _need(
        type(modified) is list
        and len(modified) == 2
        and {row["path"] for row in modified} == MODIFIED,
        "modified scope",
    )
    base = _tree(root, SOURCE_BASE, paths)
    proof = _tree(root, PREREGISTRATION, paths)
    _need(set(base) == paths and set(proof) == paths, "incomplete pinned tree")
    blobs = _blobs(root, {oid for _, oid in (*base.values(), *proof.values())})
    expected = {}
    contents = {}
    for row in preserved:
        path = row["path"]
        _need(set(row) == {"path", "image"}, "preserved fields")
        raw = blobs[base[path][1]]
        _need(
            base[path][0] == "100644"
            and _image(raw, base[path][0]) == row["image"]
            and proof[path] == base[path],
            "preserved preregistration drift",
        )
        expected[path], contents[path] = base[path], raw
    for row in modified:
        path = row["path"]
        _need(set(row) == {"path", "preimage", "postimage"}, "modified fields")
        for entries, label in ((base, "preimage"), (proof, "postimage")):
            _need(
                entries[path][0] == "100644"
                and _image(blobs[entries[path][1]], entries[path][0]) == row[label],
                "modified preregistration drift",
            )
        expected[path], contents[path] = proof[path], blobs[proof[path][1]]
    index = {}
    for row in _git(root, "ls-files", "--stage", "-z", "--", *sorted(paths)).split(b"\0"):
        if row:
            header, name = row.split(b"\t", 1)
            mode, oid, stage = header.decode("ascii").split()
            path = name.decode("utf-8")
            _need(stage == "0" and path not in index, "unmerged/duplicate index")
            index[path] = (mode, oid)
    head = _tree(root, "HEAD", paths)
    for path, entry in expected.items():
        reason = "POSTIMAGE_CHANGED" if path in MODIFIED else "PRESERVED_FILE_CHANGED"
        _need(head.get(path) == entry and index.get(path) == entry, reason)
        try:
            target = root / path
            status = target.lstat()
            raw = target.read_bytes() if stat.S_ISREG(status.st_mode) else b""
        except OSError as error:
            raise ValueError("denial history successor: " + reason) from error
        _need(stat.S_ISREG(status.st_mode) and not status.st_mode & 0o111, reason)
        if raw != contents[path]:
            _need(raw.replace(b"\r\n", b"\n") == contents[path], reason)
            clean = _git(root, "hash-object", "--path", path, "--stdin", raw=raw).decode().strip()
            _need(clean == entry[1], reason)
    return NEW_PATHS | validate_v2_successor(root)
