"""Resource, byte-stage and incomplete-capture adversaries without guest execution."""

import json
from dataclasses import replace

import pytest

from tests.fixtures.guest_consumption import PROGRAM_SHA, module, profile, rows, text


def produce(r=None, p=None):
    return module("producer").produce_receipt(
        module("wire").parse_capture(text(r)), profile() if p is None else p
    )


def numbered(r):
    return [dict(row, seq=i, time_ns=i + 10) for i, row in enumerate(r, 1)]


@pytest.mark.parametrize(
    "kind,values",
    [
        ("OBJECT", [1, 1, 1, 4194305, PROGRAM_SHA]),
        ("EXIT", ["OTHER", 0]),
        ("EXIT", ["EXITED", 256]),
        ("EXIT", ["SIGNALLED", 65]),
        ("ERROR", [""]),
        ("ERROR", [None]),
        ("PAYLOAD", ["ff " * 2]),
    ],
)
def test_invalid_byte_resource_exit_and_error_shapes_reject(kind, values):
    r = rows()
    r[5].update(kind=kind, values=values)
    with pytest.raises(ValueError):
        module("wire").parse_capture(text(r))


@pytest.mark.parametrize("field,value", [("task", 1), ("image", 1)])
def test_observer_scope_cannot_be_a_tracee_image(field, value):
    r = rows()
    r[1][field] = value
    with pytest.raises(ValueError):
        produce(r)


@pytest.mark.parametrize(
    "kind,values", [("OBJECT", [1, 1, 101, 4194305, PROGRAM_SHA]), ("END", [None, 1, 2, 0])]
)
def test_global_record_resource_and_availability_checks_are_not_hidden_by_task_errors(kind, values):
    r = rows()
    r[5].update(kind=kind, task=0, image=0, values=values)
    with pytest.raises(ValueError):
        module("wire").parse_capture(text(r))


def test_generated_material_and_wrong_profile_context_are_not_silent_defaults():
    from compatibility.guest_build_receipt.models import MaterialRole

    p = profile()
    with pytest.raises(ValueError):
        replace(p.materials[0], role=MaterialRole.GENERATED)
    with pytest.raises(ValueError):
        replace(p, identity=None)
    with pytest.raises(ValueError):
        produce(p=replace(p, identity=replace(p.identity, source_digest=None)))
    with pytest.raises(ValueError):
        replace(p, materials=())


def test_image_material_is_not_inferred_from_a_source_object():
    r = rows()
    # Both objects exist before a birth; source bytes still cannot be an image.
    r = [r[0], r[1], r[4], dict(r[2], values=[None, 2]), *r[3:4], *r[5:]]
    with pytest.raises(ValueError):
        produce(numbered(r))


def test_unknown_full_read_and_uint64_extent_overflow_are_not_partial_claims():
    r = rows()
    r[5]["values"] = [2, 0, 17, (b"X" * 17).hex()]
    with pytest.raises(ValueError):
        produce(r)
    r = rows()
    r[9]["values"] = [2, 2**64 - 1, 4096]
    with pytest.raises(ValueError):
        produce(r)


def test_complete_flag_cannot_cover_missing_exits_or_fabricated_counters():
    r = rows()
    r.pop(-2)
    with pytest.raises(ValueError):
        produce(numbered(r))
    r = rows()
    r[-1]["values"][1] = 2
    with pytest.raises(ValueError):
        produce(r)


def test_declared_dropped_count_preserves_zero_unknown_and_positive_distinctions():
    for drops, reason in ((None, "DROP_COUNT_UNAVAILABLE"), (1, "TRACE_RECORDS_DROPPED")):
        r = rows()
        r[-1]["values"][3] = drops
        o = produce(r)
        assert reason in o.profile_reasons and not o.trace_window_complete
        assert (
            o.receipt.completion.dropped_events is drops
            or o.receipt.completion.dropped_events == drops
        )
    assert produce().receipt.completion.dropped_events == 0


def test_incomplete_empty_window_does_not_invent_a_root_task():
    r = [rows()[0], dict(rows()[-1], values=[False, 0, 0, None])]
    o = produce(numbered(r))
    assert "MISSING_TASK_BIRTH" in o.profile_reasons
    assert o.receipt.completion.exit_kind is None and not o.trace_window_complete


def test_object_and_task_bounds_reject_without_silently_dropping_records():
    r = rows()
    objects = [dict(r[1], values=[i, 1, 100 + i, 1, PROGRAM_SHA]) for i in range(1, 66)]
    with pytest.raises(ValueError):
        produce(
            numbered([r[0], *objects, *r[2:4], dict(r[-2]), dict(r[-1], values=[True, 1, 65, 0])])
        )
    births = [dict(r[2], task=i, values=[1, 1]) for i in range(2, 18)]
    with pytest.raises(ValueError):
        produce(numbered([*r[:3], *births, *r[3:]]))


def test_text_and_record_bounds_reject_before_unbounded_capture_construction(monkeypatch):
    w = module("wire")
    raw = text()
    monkeypatch.setattr(w, "MAX_TEXT_BYTES", 10)
    with pytest.raises(ValueError):
        w.parse_capture(raw)
    monkeypatch.undo()
    monkeypatch.setattr(w, "MAX_RECORDS", 2)
    with pytest.raises(ValueError):
        w.parse_capture(raw)
    monkeypatch.undo()
    with pytest.raises(ValueError):
        w.parse_capture("CONSUMPTION " + "[" * 10000)


def test_field_order_does_not_change_content_but_bytes_and_generations_do():
    w = module("wire")
    c = w.parse_capture(text())
    reordered = "\n".join(
        "CONSUMPTION " + json.dumps(dict(reversed(list(r.items())))) for r in rows()
    )
    assert w.capture_digest(w.parse_capture(reordered)) == w.capture_digest(c)
    r = rows()
    r[5]["values"][3] = "58585858"
    assert w.capture_digest(w.parse_capture(text(r))) != w.capture_digest(c)
    r = rows()
    r[5]["image"] = 2
    assert w.capture_digest(w.parse_capture(text(r))) != w.capture_digest(c)


def test_published_diagnostic_cannot_accept_nonboolean_completion_or_reason_coercion():
    o = produce()
    for changes in ({"trace_window_complete": 1}, {"receipt": None}, {"profile_reasons": (False,)}):
        with pytest.raises(ValueError):
            replace(o, **changes)


def test_literal_fixture_checker_catches_missing_stages_or_wrong_bytes():
    check = module("checks").check_case
    o = produce()
    assert check(o, "CP01") == ()
    altered = replace(
        o.receipt,
        uses=tuple(u for u in o.receipt.uses if u.kind not in ("MMAP_BOUND", "METADATA_ONLY")),
    )
    reasons = check(replace(o, receipt=altered), "CP01")
    assert {"MMAP_STAGE_MISMATCH", "METADATA_STAGE_MISMATCH"} <= set(reasons)
    assert "NORMAL_FIXTURE_WINDOW_OR_EXIT_MISMATCH" in check(
        replace(o, trace_window_complete=False), "CP01"
    )
    assert "FIXTURE_ID_MISMATCH" in check(o, "CP02")
    assert "FORK_GENERATION_MISMATCH" in check(o, "CP02")
    assert "REEXEC_GENERATION_MISMATCH" in check(o, "CP03")
    assert "FAILED_READ_NOT_OBSERVED" in check(o, "CP04")
    assert "FORGED_PAYLOAD_NOT_SEPARATELY_OBSERVED" in check(o, "CP07")
    assert "UNSUPPORTED_CAPTURE_NOT_MARKED_INCOMPLETE" in check(o, "CP05")
    assert "ABORT_REAP_NOT_OBSERVED" in check(o, "CP06")
    r = rows()
    r[5]["values"][3] = "58585858"
    assert "RETURNED_BYTES_OR_OFFSETS_MISMATCH" in check(produce(r), "CP01")
    with pytest.raises(ValueError):
        check(o, "CP99")
