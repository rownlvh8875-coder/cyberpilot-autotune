"""Exact P3 path permission, never runtime authority or self-authentication."""

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

BASE = "75fd4358a2d42bec55dc85ba85afbb23e8feb6f9"
PREREGISTRATION = "18750676a84a4237576f6c50be3b01fa21053252"
P = "127f485437437b3472659784b7b05857d8fbd896"
P2 = "a7b632f2f331c4029789e2ace7ed8cdb8bb48ca2"
MANIFEST = "docs/evidence/deny_fd_v2_history_successor_v1.json"
MODIFIED = "tests/history_transition/deny_fd_successor.py"
NEW_PATHS = frozenset(
    (
        "docs/deny_fd_v2_contract.md",
        "docs/deny_fd_v2_result.md",
        "docs/evidence/deny_fd_v2_history_successor_v1.json",
        "docs/evidence/deny_fd_v2_schema.json",
        "docs/evidence/deny_fd_v2_sources.json",
        "docs/superpowers/plans/2026-11-01-deny-fd-v2-source.md",
        "docs/superpowers/specs/2026-11-01-deny-fd-v2-producer-design.md",
        "tests/architecture/test_deny_fd_v2_boundary.py",
        "tests/deny_fd_v2/__init__.py",
        "tests/deny_fd_v2/build.py",
        "tests/deny_fd_v2/contracts.py",
        "tests/deny_fd_v2/guest/probe.c",
        "tests/deny_fd_v2/validation.py",
        "tests/deny_fd_v2/wire.py",
        "tests/history_transition/deny_fd_v2_successor.py",
        "tests/test_deny_fd_v2_history_policy.py",
        "tests/test_deny_fd_v2_validation.py",
        "tests/test_deny_fd_v2_wire.py",
    )
)
PERMISSIONS = frozenset(
    (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    )
)


def _need(value, reason):
    if not value:
        raise ValueError("v2 successor: " + reason)


def _environment():
    return dict(
        os.environ, GIT_NO_LAZY_FETCH="1", GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0"
    )


def _git(root, *args, raw=None):
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            input=raw,
            stderr=subprocess.PIPE,
            timeout=30,
            env=_environment(),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("v2 successor Git object unavailable; no fetch or fallback") from error


def _ancestor(root, parent, child):
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", parent, child],
            cwd=root,
            capture_output=True,
            timeout=30,
            env=_environment(),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("v2 successor ancestry unavailable; no fallback") from error
    _need(result.returncode in (0, 1), "ancestry error is not a historical cohort")
    return result.returncode == 0


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, "duplicate manifest key")
        result[key] = value
    return result


def _manifest(root, revision, path):
    return json.loads(_git(root, "show", revision + ":" + path), object_pairs_hook=_unique)


def _tree(root, revision, paths):
    result = {}
    for row in _git(root, "ls-tree", "-rz", revision, "--", *sorted(paths)).split(b"\0"):
        if row:
            header, path = row.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split()
            name = path.decode("utf-8")
            _need(kind == "blob" and name not in result, "invalid tree")
            result[name] = (mode, oid)
    return result


def _blobs(root, oids):
    ordered = sorted(oids)
    data = _git(root, "cat-file", "--batch", raw=("\n".join(ordered) + "\n").encode())
    result = {}
    offset = 0
    for oid in ordered:
        end = data.index(b"\n", offset)
        header = data[offset:end].decode("ascii").split()
        _need(len(header) == 3 and header[:2] == [oid, "blob"], "invalid blob header")
        size = int(header[2])
        offset = end + 1
        raw = data[offset : offset + size]
        offset += size
        _need(size >= 0 and len(raw) == size and data[offset : offset + 1] == b"\n", "blob framing")
        offset += 1
        result[oid] = raw
    _need(offset == len(data), "trailing blob data")
    return result


def _image(raw, mode):
    return {
        "mode": mode,
        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def validate_v2_successor(root: Path) -> frozenset[str]:
    # Exit1 alone means historical. Missing commits/permissions/timeouts are errors.
    _git(root, "rev-parse", "--verify", BASE + "^{commit}")
    _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    if not _ancestor(root, BASE, "HEAD"):
        return frozenset()
    _need(_ancestor(root, P, P2) and _ancestor(root, P2, BASE), "prior lineage")
    _need(
        _git(root, "rev-list", "--parents", "-n", "1", PREREGISTRATION).decode().split()
        == [PREREGISTRATION, BASE],
        "P3 must have sole parent B",
    )
    _need(_ancestor(root, PREREGISTRATION, "HEAD"), "P3 must precede HEAD")
    d = _manifest(root, PREREGISTRATION, MANIFEST)
    _need(
        type(d) is dict
        and set(d)
        == {
            "schema",
            "source_base",
            "prior_P",
            "prior_P2",
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
        d["schema"] == "deny-fd-v2-history-successor-v1"
        and d["source_base"] == BASE
        and d["prior_P"] == P
        and d["prior_P2"] == P2
        and d["digest_meaning"] == "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY"
        and d["runtime_qualified"] is False,
        "manifest semantics",
    )
    _need(
        type(d["permissions"]) is dict
        and set(d["permissions"]) == PERMISSIONS
        and all(v is False for v in d["permissions"].values()),
        "permissions",
    )
    _need(
        type(d["new_paths"]) is list
        and len(d["new_paths"]) == 18
        and all(type(p) is str for p in d["new_paths"])
        and set(d["new_paths"]) == NEW_PATHS,
        "closed18scope",
    )
    old = _manifest(root, P, "docs/evidence/strict_input_history_transition_v1.json")
    prior = _manifest(root, P2, "docs/evidence/deny_fd_history_successor_v1.json")
    paths = {r["path"] for r in old["files"]} | set(old["new_paths"]) | set(prior["new_paths"])
    _need(len(paths) == 40 and MODIFIED in paths and not (paths & NEW_PATHS), "closed prior scope")
    _need(
        type(d["preserved"]) is list
        and len(d["preserved"]) == 39
        and {r["path"] for r in d["preserved"]} == paths - {MODIFIED},
        "preserved scope",
    )
    _need(
        type(d["modified"]) is list
        and len(d["modified"]) == 1
        and d["modified"][0]["path"] == MODIFIED,
        "modified scope",
    )
    base, proof = _tree(root, BASE, paths), _tree(root, PREREGISTRATION, paths)
    _need(set(base) == paths and set(proof) == paths, "pinned tree incomplete")
    blobs = _blobs(root, {oid for _, oid in (*base.values(), *proof.values())})
    for row in d["preserved"]:
        p = row["path"]
        _need(
            set(row) == {"path", "image"}
            and base[p] == proof[p]
            and base[p][0] == "100644"
            and _image(blobs[base[p][1]], base[p][0]) == row["image"],
            "preserved pinned image",
        )
    row = d["modified"][0]
    _need(set(row) == {"path", "preimage", "postimage"}, "modified fields")
    for tree, label in ((base, "preimage"), (proof, "postimage")):
        mode, oid = tree[MODIFIED]
        _need(mode == "100644" and _image(blobs[oid], mode) == row[label], "modified pinned image")
    index = {}
    _need(not _git(root, "ls-files", "--unmerged", "-z"), "unmerged index")
    for entry in _git(root, "ls-files", "--stage", "-z", "--", *sorted(paths)).split(b"\0"):
        if entry:
            header, p = entry.split(b"\t", 1)
            mode, oid, stage = header.decode().split()
            p = p.decode()
            _need(stage == "0" and p not in index, "index shape")
            index[p] = (mode, oid)
    head = _tree(root, "HEAD", paths)
    for p in sorted(paths):
        expected = proof[p] if p == MODIFIED else base[p]
        reason = "POSTIMAGE_CHANGED" if p == MODIFIED else "PRESERVED_FILE_CHANGED"
        _need(head.get(p) == expected and index.get(p) == expected, reason)
        try:
            target = root / p
            status = target.lstat()
            raw = target.read_bytes() if stat.S_ISREG(status.st_mode) else b""
        except OSError as error:
            raise ValueError("v2 successor: " + reason) from error
        _need(stat.S_ISREG(status.st_mode) and not status.st_mode & 0o111, reason)
        frozen = blobs[expected[1]]
        if raw != frozen:
            _need(raw.replace(b"\r\n", b"\n") == frozen, reason)
            clean = _git(root, "hash-object", "--path", p, "--stdin", raw=raw).decode().strip()
            _need(clean == expected[1], reason)
    allowed = {MODIFIED} | set(NEW_PATHS)
    for args in (
        ("diff", "--no-renames", "--name-only", "-z", BASE, "HEAD", "--"),
        ("diff", "--no-renames", "--name-only", "-z", "--cached", BASE, "--"),
        ("diff", "--no-renames", "--name-only", "-z", BASE, "--"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        observed = {p.decode() for p in _git(root, *args).split(b"\0") if p}
        _need(observed <= allowed, "change outside19delta scope")
    return NEW_PATHS
