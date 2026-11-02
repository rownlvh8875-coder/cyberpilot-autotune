"""Mutation tests of provided content only, not runtime or historical evidence."""

import copy
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.audit_compatibility.contracts import (
    IO_UNAVAILABLE,
    AuditCompatibilityDecision,
)
from tests.audit_compatibility.git_objects import CommitObject, GitImage, TreeSnapshot
from tests.audit_compatibility.schema import canonical, decode
from tests.audit_compatibility.validation import assess_compatibility
from tests.fixtures.audit_compatibility_core import commit, complete, encoded


def files(v, name):
    return dict(next(t for t in v.bundle.trees if t.oid == v.named[name].tree).entries)


def extend(v, *, commits=(), trees=(), **fields):
    cs = {c.oid: c for c in (*v.bundle.commits, *commits)}
    ts = {t.oid: t for t in (*v.bundle.trees, *trees)}
    v.bundle = replace(v.bundle, commits=tuple(cs.values()), trees=tuple(ts.values()), **fields)
    return v


def rewrite(v, name, images=None, parents=None):
    """Rehash registrations/descendants without blessing any changed semantic value."""
    t = TreeSnapshot(tuple((files(v, name) if images is None else images).items()))
    old = v.named[name]
    ps = tuple(v.named[n] for n in ({"R": ("D",), "Q": ("R",), "I": ("Q", "O")}[name]))
    new = commit(t, ps if parents is None else parents)
    v.named[name] = new
    extend(v, commits=(new,), trees=(t,))
    if name == "R":
        v.manifest = replace(v.manifest, r=new.oid)
        q = files(v, "Q")
        q.update({p: t for p, t in t.entries if p in v.manifest.semantic_paths})
        content = json.loads(q[v.manifest.manifest_path].data)
        content["semantic_registration_R"] = new.oid
        q[v.manifest.manifest_path] = GitImage("100644", encoded(content))
        rewrite(v, "Q", q)
    elif name == "Q":
        current = files(v, "I")
        current.update({p: image for p, image in t.entries if p not in v.manifest.active_paths})
        rewrite(v, "I", current)
    else:
        v.bundle = replace(v.bundle, candidate_head=new.oid, validation_head=new.oid)
    assert old.oid != new.oid or images is None
    return v


def mutate_content(v, transform):
    q = files(v, "Q")
    value = copy.deepcopy(v.content)
    transform(value)
    q[v.manifest.manifest_path] = GitImage("100644", encoded(value))
    return rewrite(v, "Q", q)


def decision(v):
    return assess_compatibility(v.bundle, v.manifest)


@pytest.mark.parametrize("paths", (("a/x", "A/y"), ("X/a", "x/b")))
def test_directory_case_collisions_not_only_full_paths(paths):
    with pytest.raises(ValueError):
        TreeSnapshot(tuple((p, GitImage("100644", b"")) for p in paths))


def test_commit_parser_never_ignores_late_parent_header():
    with pytest.raises(ValueError):
        CommitObject(b"tree " + b"1" * 40 + b"\nauthor X\nparent " + b"2" * 40 + b"\n\nM")


def test_known_q_extra_survives_missing_source_commit():
    v = complete(q_extra={"unlisted.py": b"not registered"})
    v.bundle = replace(v.bundle, commits=tuple(c for c in v.bundle.commits if c != v.named["M"]))
    assert "Q_DELTA" in decision(v).errors


@pytest.mark.parametrize("missing_role", ("M", "D", "O", "R", "Q", "I"))
def test_missing_commit_never_becomes_content_match(missing_role):
    v = complete()
    v.bundle = replace(
        v.bundle, commits=tuple(c for c in v.bundle.commits if c != v.named[missing_role])
    )
    result = decision(v)
    assert result.decision != "CONTENT_MATCH" and result.structural_content_status == "UNAVAILABLE"


@pytest.mark.parametrize("missing_role", ("M", "D", "O", "R", "Q", "I"))
def test_missing_tree_never_becomes_content_match(missing_role):
    v = complete()
    v.bundle = replace(
        v.bundle, trees=tuple(t for t in v.bundle.trees if t.oid != v.named[missing_role].tree)
    )
    assert decision(v).structural_content_status == "UNAVAILABLE"


@pytest.mark.parametrize(
    "role,parents,reason",
    (
        ("R", ("M",), "R_PARENT"),
        ("Q", ("D",), "Q_PARENT"),
        ("I", ("O", "Q"), "I_PARENT_ORDER"),
        ("I", ("Q",), "I_PARENT_ORDER"),
        ("I", (), "I_PARENT_ORDER"),
    ),
)
def test_parent_order_and_exact_registration_parent(role, parents, reason):
    v = complete()
    rewrite(v, role, parents=tuple(v.named[n] for n in parents))
    assert reason in decision(v).errors


@pytest.mark.parametrize(
    "changes",
    (
        {"permissions": {}},
        {"permissions": {"application_authorized": True}},
        {"transition_rows": None},
        {"transition_rows": [None]},
        {"transition_rows": [[]]},
        {"runtime_qualified": 0},
        {"profile_id": "ENTRY_COMPOSITION_V2"},
    ),
)
def test_closed_q_schema_does_not_use_python_false_zero_equality(changes):
    assert "Q_SCHEMA" in decision(complete(content_changes=changes)).errors


@pytest.mark.parametrize(
    "key,value",
    (
        ("path", "../escape"),
        ("path", "GUARD.py"),
        ("path", ["guard.py"]),
        ("operation", "NOOP"),
        ("source_preimages", {}),
        ("source_preimages", None),
        ("postimage", {}),
        ("postimage", None),
        ("inert_postimage_path", "../outside"),
        ("inert_postimage_path", None),
        ("inert_postimage_path", "meta/frozen/wrong.blob"),
    ),
)
def test_transition_fields_mutated_independently(key, value):
    v = mutate_content(complete(), lambda c: c["transition_rows"][0].update({key: value}))
    assert decision(v).decision == "REJECTED"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda r: r.update(extra=False),
        lambda r: r["source_preimages"]["D"].update(bytes=False),
        lambda r: r["source_preimages"]["D"].update(git_blob="0" * 40),
        lambda r: r["postimage"].update(bytes=False),
        lambda r: r["postimage"].update(mode="100755"),
        lambda r: r["postimage"].update(sha256="0" * 64),
    ),
)
def test_descriptor_and_unknown_field_mutations(mutation):
    v = mutate_content(complete(), lambda c: mutation(c["transition_rows"][0]))
    assert decision(v).decision == "REJECTED"


def test_duplicate_transition_row_rejects():
    v = mutate_content(complete(), lambda c: c["transition_rows"].append(c["transition_rows"][0]))
    assert "Q_SCHEMA" in decision(v).errors


@pytest.mark.parametrize(
    "raw",
    (
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":1.0}',
        b"[]",
        b"\xff",
        b'{"a":1} ',
        b'{ "a":1}',
        b'{"z":1,"a":2}',
        b"[" * 1100 + b"]" * 1100,
    ),
)
def test_noncanonical_ambiguous_or_nonfinite_wire_rejects(raw):
    with pytest.raises(ValueError):
        decode(raw, wire=True)


def test_r_human_readable_json_is_value_checked_and_byte_identity_still_changes():
    v = complete()
    old_r = v.manifest.r
    rf = files(v, "R")
    rf[v.manifest.semantic_path] = GitImage("100644", json.dumps(v.metadata, indent=2).encode())
    rewrite(v, "R", rf)
    assert v.manifest.r != old_r
    assert decision(v).structural_content_status == "CONTENT_MATCH"


@pytest.mark.parametrize(
    "change",
    (
        {"stage": "INTEGRATED"},
        {"unknown": False},
        {"historical_replay_implemented": True},
        {"permissions": {}},
        {"old_PR_heads_must_remain_unchanged": 1},
    ),
)
def test_r_semantic_mutation_rejected_after_valid_rehash(change):
    v = complete()
    rf = files(v, "R")
    rf[v.manifest.semantic_path] = GitImage("100644", encoded(v.metadata | change))
    rewrite(v, "R", rf)
    assert "R_SEMANTICS" in decision(v).errors


@pytest.mark.parametrize(
    "role,path", (("R", "kept.py"), ("Q", "kept.py"), ("I", "kept.py"), ("I", "obs.py"))
)
def test_inherited_file_deletion_detected(role, path):
    v = complete()
    fs = files(v, role)
    del fs[path]
    rewrite(v, role, fs)
    assert decision(v).decision == "REJECTED"


@pytest.mark.parametrize("role,path", (("R", "meta/semantics.json"), ("Q", "meta/content.json")))
def test_missing_required_registration_json_is_contradiction_not_default(role, path):
    v = complete()
    fs = files(v, role)
    del fs[path]
    # Avoid the helper's automatic content-reference repair for this deliberately absent JSON.
    if role == "R":
        fs[path] = GitImage("100755", b"invalid")
    rewrite(v, role, fs)
    assert decision(v).decision == "REJECTED"


def test_source_absent_from_root_graph_is_rejected_not_assumed_ancestor():
    v = complete()
    v.manifest = replace(v.manifest, m="0" * 40)
    assert "SOURCE_ANCESTRY_D" in decision(v).errors


def test_unknown_source_ancestor_is_unavailable():
    v = complete()
    # Remove D; the walk cannot establish its parents without that raw object.
    v.bundle = replace(v.bundle, commits=tuple(c for c in v.bundle.commits if c != v.named["D"]))
    assert "ANCESTRY_D" in decision(v).unavailable_checks


@pytest.mark.parametrize(
    "kind",
    ("valid", "wrong_base", "wrong_candidate", "single_parent", "missing_base", "changed_tree"),
)
def test_virtual_validation_head_is_bound_to_exact_candidate_and_full_tree(kind):
    v = complete()
    ps = (v.named["O"], v.named["I"])
    declared = v.named["O"].oid
    if kind == "wrong_base":
        declared = v.named["D"].oid
    if kind == "wrong_candidate":
        ps = (v.named["O"], v.named["D"])
    if kind == "single_parent":
        ps = (v.named["I"],)
    if kind == "missing_base":
        declared = None
    images = files(v, "I") | (
        {"unexpected": GitImage("100644", b"x")} if kind == "changed_tree" else {}
    )
    t = TreeSnapshot(tuple(images.items()))
    c = commit(t, ps, "TEST_ONLY_VIRTUAL")
    extend(v, commits=(c,), trees=(t,), validation_head=c.oid, declared_base=declared)
    r = decision(v)
    if kind == "valid":
        assert r.structural_content_status == "CONTENT_MATCH"
    elif kind == "missing_base":
        assert r.structural_content_status == "UNAVAILABLE"
    else:
        assert r.decision == "REJECTED"


def test_missing_manifest_and_heads_never_yield_success():
    v = complete()
    assert assess_compatibility(v.bundle, None).structural_content_status == "UNAVAILABLE"
    v.bundle = replace(v.bundle, candidate_head=None, validation_head=None)
    assert decision(v).structural_content_status == "UNAVAILABLE"


@pytest.mark.parametrize(
    "field,value",
    (
        ("commits", []),
        ("commits", (object(),)),
        ("trees", []),
        ("trees", (object(),)),
        ("candidate_head", True),
        ("validation_head", "UPPER"),
        ("declared_base", "a"),
    ),
)
def test_foreign_mutable_and_wrongly_typed_bundle_inputs_reject(field, value):
    with pytest.raises(ValueError):
        replace(complete().bundle, **{field: value})


@pytest.mark.parametrize("field", ("commits", "trees"))
def test_duplicate_input_object_identity_reject(field):
    b = complete().bundle
    with pytest.raises(ValueError):
        replace(b, **{field: (*getattr(b, field), getattr(b, field)[0])})


@pytest.mark.parametrize(
    "change",
    (
        {"r": True},
        {"semantic_paths": []},
        {"active_paths": ("A", "a")},
        {"semantic_path": "absent"},
        {"manifest_path": "../escape"},
        {"active_paths": ("meta/semantics.json",)},
        {"inert_root": "meta/content.json"},
        {"active_paths": ("meta",)},
    ),
)
def test_invalid_pinned_manifest_boundary(change):
    with pytest.raises(ValueError):
        replace(complete().manifest, **change)


def test_inputs_and_results_are_frozen_and_revalidated_at_assessment():
    v = complete()
    with pytest.raises(FrozenInstanceError):
        v.bundle.candidate_head = "0" * 40
    with pytest.raises(FrozenInstanceError):
        decision(v).errors = ()
    with pytest.raises(ValueError):
        assess_compatibility(object(), v.manifest)
    with pytest.raises(ValueError):
        assess_compatibility(v.bundle, object())
    object.__setattr__(v.bundle, "trees", [])
    with pytest.raises(ValueError):
        decision(v)


@pytest.mark.parametrize(
    "errors,missing",
    ((["x"], IO_UNAVAILABLE), (("z", "a"), IO_UNAVAILABLE), (("a", "a"), IO_UNAVAILABLE), ((), ())),
)
def test_diagnostics_cannot_erase_required_unavailable_or_duplicate_reasons(errors, missing):
    with pytest.raises(ValueError):
        AuditCompatibilityDecision(errors, tuple(sorted(missing)))


def test_canonical_key_order_is_irrelevant_but_none_false_zero_are_distinct():
    assert canonical({"a": 1, "b": 2}) == canonical({"b": 2, "a": 1})
    assert len({canonical({"v": v}) for v in (None, False, 0, "")}) == 4


def test_actual_current_tree_substitution_cannot_hide_q_extra_file():
    v = complete(q_extra={"test_relaxation.py": b"unregistered"})
    assert {"Q_DELTA"} <= set(decision(v).errors)


@pytest.mark.parametrize("operation", ("ADD", "DELETE"))
def test_registered_add_and_delete_keep_whole_tree_bound(operation):
    v = complete(operation=operation)
    assert decision(v).structural_content_status == "CONTENT_MATCH"
    assert decision(v).decision == "UNAVAILABLE"
    if operation == "DELETE":
        assert "guard.py" not in files(v, "I")
    else:
        assert v.content["transition_rows"][0]["source_preimages"]["D"] is None


def test_missing_source_preserves_known_other_preimage_contradiction():
    v = mutate_content(
        complete(), lambda c: c["transition_rows"][0]["source_preimages"].update(D=None)
    )
    v.bundle = replace(v.bundle, commits=tuple(c for c in v.bundle.commits if c != v.named["M"]))
    r = decision(v)
    assert r.structural_content_status == "REJECTED" and "Q_TRANSITIONS" in r.errors


def test_cross_side_case_collision_is_rejected_even_without_active_conflict():
    v = complete()
    # A different incoming root without M ancestry is already a contradiction; the
    # full-tree collision must independently be detected, not silently normalized.
    of = files(v, "O") | {"META/other.json": GitImage("100644", b"incoming")}
    ot = TreeSnapshot(tuple(of.items()))
    oc = commit(ot, (v.named["M"],), "TEST_ONLY_INCOMING")
    v.named["O"] = oc
    extend(v, commits=(oc,), trees=(ot,))
    v.manifest = replace(v.manifest, o=oc.oid)
    rewrite(v, "I", parents=(v.named["Q"], oc))
    assert "THREE_WAY_CONFLICT" in decision(v).errors


def test_source_ancestry_walk_handles_shared_dag_without_inventing_ancestor():
    v = complete()
    v.manifest = replace(v.manifest, m="0" * 40, d=v.named["I"].oid)
    assert "SOURCE_ANCESTRY_D" in decision(v).errors


@pytest.mark.parametrize(
    "raw",
    (
        b"tree \xff\n\nmessage",
        b"tree " + b"1" * 40 + b"\nparent \xff\n\nmessage",
        b"tree " + b"1" * 40 + b"\nparent " + b"2" * 40 + b"\nparent " + b"2" * 40 + b"\n\nM",
    ),
)
def test_nonascii_and_duplicate_parent_headers_reject(raw):
    with pytest.raises(ValueError):
        CommitObject(raw)


def test_surrogate_path_cannot_be_hashed_as_portable_utf8():
    with pytest.raises(ValueError):
        TreeSnapshot((("bad\ud800", GitImage("100644", b"")),))


def test_complete_manifest_and_raw_commit_hashes_are_content_sensitive():
    v = complete()
    assert {c.oid for c in v.bundle.commits} == set(v.named[n].oid for n in v.named)
    assert decision(v) == decision(v)
    changed = replace(
        v.bundle, commits=tuple(reversed(v.bundle.commits)), trees=tuple(reversed(v.bundle.trees))
    )
    assert assess_compatibility(changed, v.manifest) == decision(v)
