"""Reproduce an offline native content identity; never register runtime authority.

Only temporary Git objects are written. The source reference, its refs, index,
config and object database are read-only inputs. No source checkout or transport.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from compatibility.friction_native import bundle

ROOT = bundle.ROOT
BASE = "0d1d44c808050835aa5a52c3ddd76d51cb3300b0"
RECORD = ROOT / "docs/evidence/carrot_passive_native_registration.json"
PRIOR = "docs/evidence/carrot_passive_native_patch.json"
SCHEMAS = tuple(sorted(path for path in bundle.reference_paths() if path.endswith(".capnp")))
IDENTITY = "CyberPilot Offline Recipe <offline-recipe@example.invalid> 1793169536 +0000"


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def check_record(record, expected):
    # JSON comparison distinguishes false/0 and null/default. The caller cannot
    # self-approve a record by recomputing just its own digest.
    if canonical(record) != canonical(expected):
        raise ValueError("REGISTRATION_CONTENT_MISMATCH")


def read_record(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_REGISTRATION_KEY")
            result[key] = value
        return result

    record = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    canonical(record)  # Reject non-finite JSON extensions before returning data.
    return record


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _oid(kind, raw):
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def _environment():
    # Do not inherit object/index/worktree selectors, replace refs, config-count
    # or protocol overrides. Network cannot be used even for promisor lazy fetch.
    result = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_NO_LAZY_FETCH="1",
        GIT_ALLOW_PROTOCOL="",
        GIT_TERMINAL_PROMPT="0",
        GIT_OPTIONAL_LOCKS="0",
    )
    return result


def _git(reference, *args, data=None, env=None):
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(reference), *args],
        input=data,
        env=_environment() if env is None else env,
        stderr=subprocess.PIPE,
    )


def _rewrite_tree(git, tree, changes):
    entries = {}
    for entry in git("ls-tree", "-z", tree).split(b"\0"):
        if entry:
            info, name = entry.split(b"\t", 1)
            entries[name] = info
    groups = {}
    for parts, oid in changes.items():
        groups.setdefault(parts[0], {})[parts[1:]] = oid
    for name, children in groups.items():
        old = entries.get(name)
        if () in children:
            if len(children) != 1 or (old is not None and not old.startswith(b"100644 blob ")):
                raise ValueError("UNEXPECTED_TARGET_MODE_OR_TREE")
            entries[name] = b"100644 blob " + children[()].encode()
        else:
            if old is None or not old.startswith(b"040000 tree "):
                raise ValueError("MISSING_BASE_DIRECTORY")
            subtree = _rewrite_tree(git, old.split()[2].decode(), children)
            entries[name] = b"040000 tree " + subtree.encode()
    raw = b"".join(info + b"\t" + name + b"\0" for name, info in entries.items())
    # --missing retains untouched promisor references without fetching blobs.
    # The resulting root is complete; this temporary DB is not a source archive.
    return git("mktree", "--missing", "-z", data=raw).decode().strip()


def prepare(reference):
    """Return a fresh verifiable content record, without changing any allowlist."""
    reference = Path(reference).resolve()
    if _git(reference, "rev-parse", "--show-object-format").strip() != b"sha1":
        raise ValueError("SHA1_NATIVE_REFERENCE_REQUIRED")
    base_commit = _git(reference, "cat-file", "commit", bundle.PIN)
    if _oid("commit", base_commit) != bundle.PIN:
        raise ValueError("NATIVE_BASE_OBJECT_MISMATCH")
    base_tree = base_commit.splitlines()[0].removeprefix(b"tree ").decode()

    frozen = json.loads(_git(ROOT, "show", BASE + ":" + PRIOR))
    check_record(read_record(ROOT / PRIOR), frozen)
    source = {
        path: _git(reference, "show", bundle.PIN + ":" + path) for path in bundle.reference_paths()
    }
    check_record(
        [{"path": path, "sha256": _sha(raw)} for path, raw in source.items()],
        frozen["source_files"],
    )
    before = {path: source[path] for path in bundle.EDIT_PATHS[:-1]}
    after = bundle.instrument(before)
    check_record(
        [{"path": path, "sha256": _sha(after[path])} for path in bundle.EDIT_PATHS],
        frozen["target_files"],
    )
    patch = bundle.patch(before, after).encode()
    if (
        _sha(patch) != frozen["patch_sha256"]
        or (bundle.ASSETS / "instrumentation.patch").read_bytes() != patch
    ):
        raise ValueError("FROZEN_NATIVE_PATCH_DRIFT")

    original_objects = (
        _git(reference, "rev-parse", "--path-format=absolute", "--git-path", "objects")
        .decode()
        .strip()
    )
    with tempfile.TemporaryDirectory(prefix="friction-registration-") as temporary:
        objects = Path(temporary) / "objects"
        objects.mkdir()
        env = _environment()
        env["GIT_OBJECT_DIRECTORY"] = str(objects)
        # Git's C-quoted path syntax handles spaces/path-list separator characters.
        env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = json.dumps(original_objects, ensure_ascii=False)

        def git(*args, data=None):
            return _git(reference, *args, data=data, env=env)

        new_blobs = {
            tuple(path.encode().split(b"/")): git("hash-object", "-w", "--stdin", data=raw)
            .decode()
            .strip()
            for path, raw in after.items()
        }
        applied_tree = _rewrite_tree(git, base_tree, new_blobs)
        payload = (
            f"tree {applied_tree}\nparent {bundle.PIN}\n"
            f"author {IDENTITY}\ncommitter {IDENTITY}\n\n"
            "Offline passive friction receipt candidate\n\n"
            "Synthetic recipe object; not a native branch, deployment, or approval.\n"
        ).encode()
        revision = (
            git("hash-object", "-t", "commit", "-w", "--stdin", data=payload).decode().strip()
        )
        if _oid("commit", payload) != revision or git("cat-file", "commit", revision) != payload:
            raise ValueError("SYNTHETIC_COMMIT_OBJECT_MISMATCH")
        changed = (
            git(
                "diff-tree",
                "--no-commit-id",
                "--no-renames",
                "--name-status",
                "-r",
                bundle.PIN,
                revision,
            )
            .decode()
            .splitlines()
        )
        expected = sorted(
            ("A" if path == bundle.HELPER else "M") + "\t" + path for path in bundle.EDIT_PATHS
        )
        if sorted(changed) != expected:
            raise ValueError("UNEXPECTED_NATIVE_TREE_DIFF")
        for path, raw in after.items():
            if git("show", revision + ":" + path) != raw:
                raise ValueError("APPLIED_BLOB_MISMATCH")

    closure = [
        {"path": path, "git_blob": _oid("blob", raw), "sha256": _sha(raw)}
        for path in SCHEMAS
        for raw in (after.get(path, source[path]),)
    ]
    record = {
        "schema": "passive-native-offline-registration-v1",
        "registration_scope": "OFFLINE_CONTENT_ONLY",
        "cyberpilot_patch_revision": BASE,
        "native_parent": bundle.PIN,
        "native_base_tree": base_tree,
        "native_applied_tree": applied_tree,
        "offline_candidate_revision": revision,
        "synthetic_commit_payload": payload.decode(),
        "patch_sha256": _sha(patch),
        "receipt_schema_version": "friction-observation-v1",
        "source_schema_digest": _sha(after["openpilot/cereal/log.capnp"]),
        "source_schema_digest_semantics": "SHA256_EXACT_APPLIED_LOG_CAPNP_BYTES",
        "schema_closure": closure,
        "schema_closure_digest": _sha(canonical(closure)),
        "semantic_wire_map_sha256": _sha(
            _git(ROOT, "show", BASE + ":docs/evidence/carrot_friction_patch_wire.json")
        ),
        "changed_files": [
            {
                "path": path,
                "action": "A" if path == bundle.HELPER else "M",
                "mode": "100644",
                "before_git_blob": _oid("blob", before[path]) if path in before else None,
                "after_git_blob": _oid("blob", after[path]),
                "sha256": _sha(after[path]),
            }
            for path in bundle.EDIT_PATHS
        ],
        "native_revision_published": False,
        "h7_source_allowlist_updated": False,
        "deployment_performed": False,
        "runtime_qualified": False,
        "empirical_qualified": False,
        "q_observed": None,
        "candidate_generation_allowed": False,
        "application_authorized": False,
        "runtime_accepted": False,
        "owner_proposal_allowed": False,
    }
    record["content_digest"] = _sha(canonical(record))
    return record


def verify(record, reference):
    check_record(record, prepare(reference))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", type=Path, required=True)
    parser.add_argument(
        "--print-record", action="store_true", help="print content JSON; no file/allowlist writes"
    )
    args = parser.parse_args(argv)
    try:
        expected = prepare(args.reference_checkout)
        if args.print_record:
            print(
                json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            )
        else:
            check_record(read_record(RECORD), expected)
            print(
                "OFFLINE_SOURCE_SCHEMA_CONTENT_VERIFIED: no runtime/empirical/application approval"
            )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"OFFLINE_REGISTRATION_REJECTED: {type(error).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
