"""Synthetic object graphs only. Not actual registrations or replay evidence."""

import json
from dataclasses import dataclass
from hashlib import sha256

from tests.audit_compatibility.contracts import (
    CompatibilityInputBundle,
    PinnedCompatibilityManifest,
)
from tests.audit_compatibility.git_objects import CommitObject, GitImage, TreeSnapshot


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tree(files):
    return TreeSnapshot(tuple((p, GitImage("100644", b)) for p, b in files.items()))


def commit(t, parents=(), message="TEST_ONLY"):
    raw = (
        "tree "
        + t.oid
        + "\n"
        + "".join("parent " + p.oid + "\n" for p in parents)
        + "\n"
        + message
        + "\n"
    ).encode()
    return CommitObject(raw)


def descriptor(image):
    return (
        None
        if image is None
        else {
            "mode": image.mode,
            "git_blob": image.oid,
            "sha256": image.sha256,
            "bytes": len(image.data),
        }
    )


@dataclass
class Vector:
    bundle: CompatibilityInputBundle
    manifest: PinnedCompatibilityManifest
    named: dict
    content: dict
    metadata: dict


def complete(*, content_changes=None, r_extra=None, q_extra=None, candidate_extra=None):
    m = tree({"kept.py": b"preserve", "guard.py": b"base"})
    cm = commit(m)
    d = tree({"kept.py": b"preserve", "guard.py": b"diagnostic", "MANIFEST.in": b"ZIP include"})
    cd = commit(d, (cm,))
    o = tree({"kept.py": b"preserve", "guard.py": b"observation", "obs.py": b"observation"})
    co = commit(o, (cm,))
    permissions = dict.fromkeys(
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
        ),
        False,
    )
    meta = {
        "schema": "history-audit-compatibility-semantics-v1",
        "profile_id": "ENTRY_COMPOSITION_V1",
        "stage": "PURE_CORE_PREPARATION_NOT_REGISTERED_INTEGRATION",
        "basis": {"M": cm.oid, "D": cd.oid, "O": co.oid},
        "semantic_paths": ["meta/semantics.json"],
        "active_paths": ["guard.py"],
        "manifest_path": "meta/content.json",
        "inert_root": "meta/frozen",
        "permissions": permissions,
        "historical_replay_implemented": False,
        "current_capture_implemented": False,
        "Q_registered": False,
        "I_created": False,
        "old_PR_heads_must_remain_unchanged": True,
    }
    rfiles = {p: b.data for p, b in d.entries} | {"meta/semantics.json": encoded(meta)}
    r = tree(rfiles | (r_extra or {}))
    cr = commit(r, (cd,))
    post = GitImage("100644", b"exact composed guard")
    inert = "meta/frozen/" + sha256(post.data).hexdigest() + ".blob"
    content = {
        "schema": "history-audit-compatibility-content-v1",
        "profile_id": "ENTRY_COMPOSITION_V1",
        "semantic_registration_R": cr.oid,
        "runtime_qualified": False,
        "permissions": permissions,
        "transition_rows": [
            {
                "path": "guard.py",
                "operation": "MODIFY",
                "source_preimages": {
                    n: descriptor(dict(t.entries).get("guard.py"))
                    for n, t in (("M", m), ("D", d), ("O", o))
                },
                "postimage": descriptor(post),
                "inert_postimage_path": inert,
            }
        ],
    }
    content.update(content_changes or {})
    qfiles = rfiles | {inert: post.data, "meta/content.json": encoded(content)} | (r_extra or {})
    q = tree(qfiles | (q_extra or {}))
    cq = commit(q, (cr,))
    expected = qfiles | {"obs.py": b"observation", "guard.py": post.data}
    candidate = tree(expected | (q_extra or {}) | (candidate_extra or {}))
    ci = commit(candidate, (cq, co))
    ts = {t.oid: t for t in (m, d, o, r, q, candidate)}
    bundle = CompatibilityInputBundle(
        (cm, cd, co, cr, cq, ci), tuple(ts.values()), ci.oid, ci.oid, None
    )
    manifest = PinnedCompatibilityManifest(
        cr.oid,
        cm.oid,
        cd.oid,
        co.oid,
        "meta/semantics.json",
        ("meta/semantics.json",),
        ("guard.py",),
        "meta/content.json",
        "meta/frozen",
    )
    return Vector(bundle, manifest, dict(M=cm, D=cd, O=co, R=cr, Q=cq, I=ci), content, meta)
