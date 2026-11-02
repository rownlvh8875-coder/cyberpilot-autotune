"""HR013–018/024:wrong types,wire confusion or mutable claims must not survive."""

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.audit_compatibility_history import api, complete


def test_frozen_supplied_record_roundtrips_without_authority():
    c = api()
    record, policy = complete()
    raw = c.canonical_record(record)
    assert c.decode_record(raw) == record
    assert record.content_digest == c.decode_record(raw).content_digest
    with pytest.raises(FrozenInstanceError):
        record.run_id = "9" * 32
    decision = c.HistoricalReplayDecision((), ())
    assert decision.consistency == "STRUCTURAL_RECORD_MATCH" and decision.status == "BLOCKED"
    assert decision.integrated_admission is False and decision.content_identity_only is True
    assert (
        decision.atomicity == "NOT_ESTABLISHED"
        and "HISTORICAL_REPLAY" in decision.remaining_blockers
    )
    assert len(decision.permissions) == 9 and all(
        value is False for _, value in decision.permissions
    )
    assert len(policy.content_digest) == 64


@pytest.mark.parametrize("bad", (True, -1, 1.0, float("nan"), float("inf"), None))
def test_coverage_cannot_coerce_counts(bad):
    with pytest.raises(ValueError):
        api().CoverageCounts("src/a.py", bad, 0, 1, 0)


@pytest.mark.parametrize("bad", ("", "A" * 40, "1" * 39, 0, None))
def test_source_pin_is_exact_not_branch_or_default(bad):
    with pytest.raises(ValueError):
        api().SourcePin(bad, "2" * 40)


@pytest.mark.parametrize("path", ("../a", "/a", "a//b", "a/./b", "a\\b", "C:a", "a\0b"))
def test_origin_path_cannot_escape(path):
    with pytest.raises(ValueError):
        api().OriginPin("tests.a", path, "1" * 64, None)


@pytest.mark.parametrize(
    "field,value",
    (("commands", []), ("errors", ["x"]), ("run_id", False), ("policy_digest", "bad")),
)
def test_no_mutable_alias_or_default_types(field, value):
    record, _ = complete()
    with pytest.raises(ValueError):
        replace(record, **{field: value})


def test_unknown_duplicate_and_nonfinite_wire_rejected():
    c = api()
    record, _ = complete()
    raw = c.canonical_record(record)
    for bad in (
        b'{"schema":"x","schema":"y"}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b"[]",
        b"null",
        b"\xff",
        raw[:-1],
        raw[:-1] + b',"application_authorized":true}',
    ):
        with pytest.raises(ValueError):
            c.decode_record(bad)


def test_field_order_is_canonical_but_none_is_not_zero_or_empty():
    c = api()
    record, _ = complete()
    value = json.loads(c.canonical_record(record))
    assert c.canonical_record(
        c.decode_record(json.dumps(value, sort_keys=False, indent=2).encode())
    ) == c.canonical_record(record)
    item = record.commands[0]
    for name, left, right in (
        ("exit_code", None, 0),
        ("argv", None, ()),
        ("collected_nodeids", None, ()),
    ):
        a = replace(record, commands=(replace(item, **{name: left}), *record.commands[1:]))
        b = replace(record, commands=(replace(item, **{name: right}), *record.commands[1:]))
        assert a.content_digest != b.content_digest


@pytest.mark.parametrize("kind", ("source", "command", "run"))
def test_bound_identity_changes_digest(kind):
    record, _ = complete()
    item = record.commands[0]
    if kind == "source":
        changed = replace(item, subject=replace(item.subject, revision="9" * 40))
    elif kind == "command":
        changed = replace(item, argv=("different",))
    else:
        changed = replace(item, run_id="9" * 32)
    assert (
        replace(record, commands=(changed, *record.commands[1:])).content_digest
        != record.content_digest
    )


def test_nested_object_tamper_revalidated_before_serializing():
    c = api()
    record, _ = complete()
    object.__setattr__(record.commands[0].coverage[0], "covered", True)
    with pytest.raises(ValueError):
        c.canonical_record(record)


def test_permission_or_historical_pass_fields_cannot_be_injected():
    c = api()
    record, _ = complete()
    for key in ("permissions", "historical_pass", "integrated_admission", "application_authorized"):
        value = json.loads(c.canonical_record(record))
        value["record"][key] = True
        with pytest.raises(ValueError):
            c.decode_record(json.dumps(value).encode())
