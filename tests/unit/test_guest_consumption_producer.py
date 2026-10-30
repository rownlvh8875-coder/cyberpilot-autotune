"""Observed bytes and exact generations map to PR30, never execution authority."""

import hashlib
from dataclasses import asdict, replace

import pytest

from tests.fixtures.guest_consumption import module, profile, rows, text


def produce(values=None, selected_profile=None):
    p = module("producer")
    return p.produce_receipt(
        module("wire").parse_capture(text(values)),
        profile() if selected_profile is None else selected_profile,
    )


def test_observed_bytes_map_to_separate_read_map_exec_metadata_stages():
    o = produce()
    assert o.trace_window_complete and o.profile_reasons == ()
    b = o.receipt
    reads = [u for u in b.uses if u.kind == "READ_BYTES"]
    assert [(u.offset, u.length) for u in reads] == [(0, 4), (4, 4), (8, 3), (100, 0)]
    assert reads[0].range_digest == hashlib.sha256(b"0123").hexdigest()
    assert reads[-1].range_digest == hashlib.sha256(b"").hexdigest()
    maps = [u for u in b.uses if u.kind == "MMAP_BOUND"]
    assert maps[0].length == 4096 and maps[0].range_digest is None
    assert [u.kind for u in b.uses].count("EXEC_BOUND") == 1
    assert [u.kind for u in b.uses].count("METADATA_ONLY") == 1
    assert [(i.task_generation, i.exec_generation) for i in b.images] == [(1, 0), (1, 1)]
    assert b.evidence_kind == "OBSERVED_UNTRUSTED" and b.outputs == ()
    assert b.completion.input_seal_digest is None and b.completion.writer_trace_digest is None
    assert o.overall_status == "BLOCKED"
    for k, v in asdict(o).items():
        if (
            k.endswith("_allowed")
            or k.endswith("_authorized")
            or k
            in ("runtime_qualified", "device_class_qualified", "policy_adopted", "runtime_accepted")
        ):
            assert v is False
    assert o.successful_prohibited_handles is None and o.successful_prohibited_effects is None


@pytest.mark.parametrize(
    "index,change",
    [
        (4, {"values": [3, 1, 102, 17, "a" * 64]}),
        (5, {"image": 0}),
        (5, {"task": 2}),
        (5, {"values": [99, 0, 4, "30313233"]}),
        (5, {"values": [2, 16, 4, "30313233"]}),
        (3, {"image": 2}),
        (2, {"values": [9, 1]}),
    ],
)
def test_unknown_object_image_parent_or_out_of_bounds_bytes_reject(index, change):
    r = rows()
    r[index].update(change)
    with pytest.raises(ValueError):
        produce(r)


def test_changed_bytes_are_observed_not_replaced_with_expected_fixture_bytes():
    r = rows()
    r[5]["values"][-1] = "58585858"
    o = produce(r)
    read = [u for u in o.receipt.uses if u.kind == "READ_BYTES"][0]
    assert read.range_digest == hashlib.sha256(b"XXXX").hexdigest()
    assert read.range_digest != hashlib.sha256(b"0123").hexdigest()


def test_missing_exit_in_incomplete_window_never_fabricates_a_zero_exit_or_finish():
    r = rows()
    r.pop(-2)
    r[-1].update(seq=12, time_ns=22, values=[False, 1, 2, None])
    o = produce(r)
    assert not o.trace_window_complete and "MISSING_TASK_EXIT" in o.profile_reasons
    assert o.receipt.finish_ns is None and o.receipt.completion.exit_kind is None
    assert o.receipt.completion.exit_code is None and o.receipt.completion.dropped_events is None


def test_unknown_profile_case_and_ambiguous_known_content_cannot_pick_latest():
    p = profile()
    with pytest.raises(ValueError):
        produce(selected_profile=replace(p, identity=replace(p.identity, attempt_id="CP02")))
    with pytest.raises(ValueError):
        replace(p, materials=(*p.materials, replace(p.materials[0], material_id="other")))


def test_same_object_range_hash_contradiction_stays_rejected_in_existing_evaluator():
    from compatibility.guest_build_receipt.evaluation import evaluate_receipts

    r = rows()
    r[6]["values"] = [2, 0, 4, "58585858"]
    o = produce(r)
    d = evaluate_receipts(o.receipt, ())
    assert "CONFLICTING_READ_HASHES" in d.reasons
    assert {"MISSING_INPUT_SEAL_WITNESS", "MISSING_WRITER_TRACE_WITNESS", "OUTPUT_MISSING"} <= set(
        d.reasons
    )
    assert d.promotion_authorized is False
