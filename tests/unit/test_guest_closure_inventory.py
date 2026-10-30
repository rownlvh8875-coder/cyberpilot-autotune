"""Content, mode and link drift must not disappear behind a matching filename."""

import importlib
import json
from dataclasses import FrozenInstanceError, asdict, replace

import pytest


def api():
    assert importlib.util.find_spec("compatibility.guest_input_closure") is not None
    return (
        importlib.import_module("compatibility.guest_input_closure.contracts"),
        importlib.import_module("compatibility.guest_input_closure.inventory"),
    )


def entry():
    c, _ = api()
    return c.InputEntry(
        "source",
        "a.c",
        "file",
        0o100444,
        1,
        "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
        None,
    )


@pytest.mark.parametrize(
    "changes,want",
    [
        ({"mode": 0o100644}, "MODE_CHANGED:source/a.c"),
        ({"sha256": "0" * 64}, "CONTENT_CHANGED:source/a.c"),
        ({"size": 0}, "SIZE_CHANGED:source/a.c"),
        (
            {"kind": "directory", "mode": 0o040755, "size": 0, "sha256": None},
            "KIND_CHANGED:source/a.c",
        ),
    ],
)
def test_named_drift_is_not_accepted_as_matching(changes, want):
    c, m = api()
    original = entry()
    assert want in m.compare_snapshots(
        c.InputSnapshot([original]), c.InputSnapshot([replace(original, **changes)])
    )


def test_unlisted_and_missing_paths_are_reported_not_ignored():
    c, m = api()
    a = entry()
    assert m.compare_snapshots(c.InputSnapshot([a]), c.InputSnapshot([])) == (
        "INPUT_MISSING:source/a.c",
    )
    assert m.compare_snapshots(c.InputSnapshot([]), c.InputSnapshot([a])) == (
        "UNDECLARED_INPUT:source/a.c",
    )


def test_link_target_identity_is_not_the_content_of_its_current_target():
    c, m = api()
    a = c.InputEntry("source", "alias", "symlink", 0o120777, 3, None, "a.c")
    b = replace(a, target="b.c")
    assert m.compare_snapshots(c.InputSnapshot([a]), c.InputSnapshot([b])) == (
        "LINK_CHANGED:source/alias",
    )


def test_canonical_order_and_defensive_copies_preserve_content_identity():
    c, m = api()
    entries = [entry(), replace(entry(), path="b.c")]
    snapshot = c.InputSnapshot(entries)
    entries.clear()
    assert len(snapshot.entries) == 2
    assert m.snapshot_digest(snapshot) == m.snapshot_digest(
        c.InputSnapshot(reversed(snapshot.entries))
    )
    assert m.compare_snapshots(snapshot, snapshot) == ()
    with pytest.raises(FrozenInstanceError):
        snapshot.entries = ()
    assert m.snapshot_digest(snapshot) != m.snapshot_digest(c.InputSnapshot([entry()]))


@pytest.mark.parametrize("path", ["", "/a", "../a", "a/../b", "a//b", "a/./b", "a\\b", "a\0b"])
def test_paths_cannot_escape_or_alias_the_declared_namespace(path):
    with pytest.raises(ValueError):
        replace(entry(), path=path)


@pytest.mark.parametrize(
    "changes",
    [
        {"size": True},
        {"size": -1},
        {"size": None},
        {"sha256": None},
        {"mode": False},
        {"mode": 0o040444},
        {"root": "../host"},
        {"kind": "device"},
        {"target": "a"},
    ],
)
def test_unknown_or_inconsistent_metadata_is_not_coerced_to_zero(changes):
    with pytest.raises(ValueError):
        replace(entry(), **changes)


def test_snapshot_parser_rejects_unknown_keys_duplicate_keys_and_versions():
    c, m = api()
    data = {"version": "guest-input-snapshot-v1", "entries": [asdict(entry())]}
    raw = json.dumps(data)
    assert m.parse_snapshot(raw) == c.InputSnapshot([entry()])
    for changed in (
        raw.replace('"version":', '"extra":false,"version":'),
        raw.replace('"size": 1', '"size":1,"size":1'),
        raw.replace("guest-input-snapshot-v1", "future"),
        raw.replace('"size": 1', '"size":NaN'),
    ):
        with pytest.raises(ValueError):
            m.parse_snapshot(changed)
    with pytest.raises(ValueError):
        c.InputSnapshot([entry(), entry()])


def test_unavailable_needed_name_cannot_be_a_valid_elf_dependency():
    c, _ = api()
    with pytest.raises(ValueError):
        c.ElfInfo(62, 3, None, [None], None, None, None, [])
