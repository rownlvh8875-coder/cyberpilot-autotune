"""Boundary and incomplete diagnostics, including valid non-executing alternatives."""

import json
from dataclasses import replace

import pytest

from compatibility.guest_build_receipt import codec, evaluation, models
from tests.fixtures.guest_build_receipt import EMPTY_SHA, SHA_A, build


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"materials": ()}, "MATERIALS_MISSING"),
        ({"images": ()}, "TASK_IMAGES_MISSING"),
        ({"uses": ()}, "CONSUMPTION_STREAM_MISSING"),
        ({"outputs": ()}, "OUTPUT_MISSING"),
        ({"start_ns": None}, "MISSING_BUILD_INTERVAL"),
        ({"finish_ns": 9}, "BUILD_TIME_ORDER_INVALID"),
    ],
)
def test_partial_builds_keep_missingness_explicit(change, reason):
    assert reason in evaluation.evaluate_receipts(replace(build(), **change), ()).reasons


def test_conflicting_generations_origins_and_empty_hashes_are_not_silently_pooled():
    b = build()
    bad_materials = (
        *b.materials,
        replace(b.materials[1], generation=1, origin_digest="a" * 64, size=0),
    )
    d = evaluation.evaluate_receipts(replace(b, materials=bad_materials), ())
    assert {
        "MATERIAL_ID_REUSED",
        "UNEXPECTED_MATERIAL_ORIGIN",
        "EMPTY_MATERIAL_HASH_MISMATCH",
    } <= set(d.reasons)
    outputs = (*b.outputs, replace(b.outputs[0], generation=1, size=0, last_write_ns=None))
    d = evaluation.evaluate_receipts(replace(b, outputs=outputs), ())
    assert {"OUTPUT_ID_REUSED", "EMPTY_OUTPUT_HASH_MISMATCH", "MISSING_OUTPUT_WRITE_TIME"} <= set(
        d.reasons
    )
    d = evaluation.evaluate_receipts(
        replace(b, outputs=(replace(b.outputs[0], writer_task_generation=9),)), ()
    )
    assert "OUTPUT_WRITER_UNKNOWN" in d.reasons


def test_parent_identity_cannot_change_across_execs_and_exec_is_not_a_path_request():
    b = build()
    second = replace(b.images[0], exec_generation=1, start_ns=99, parent_generation=9)
    assert (
        "TASK_PARENT_CHANGED"
        in evaluation.evaluate_receipts(replace(b, images=(*b.images, second)), ()).reasons
    )
    uses = list(b.uses)
    uses[0] = replace(uses[0], material_id="source", length=1)
    d = evaluation.evaluate_receipts(replace(b, uses=uses), ())
    assert {"EXEC_OBJECT_MISMATCH", "EXEC_HAS_BYTE_CLAIM"} <= set(d.reasons)
    uses[-1] = replace(uses[-1], length=None)
    assert "MISSING_MAP_EXTENT" in evaluation.evaluate_receipts(replace(b, uses=uses), ()).reasons
    uses[-1] = replace(uses[-1], offset=2**64 - 1, length=1)
    assert "RANGE_OVERFLOW" in evaluation.evaluate_receipts(replace(b, uses=uses), ()).reasons


def test_signal_is_a_failed_build_and_unknown_signal_stays_missing():
    b = build()
    for signal, reason in ((9, "BUILD_NOT_SUCCESSFUL"), (None, "MISSING_EXIT_STATUS")):
        c = replace(
            b.completion, exit_kind=models.ExitKind.SIGNALLED, exit_code=None, term_signal=signal
        )
        assert reason in evaluation.evaluate_receipts(replace(b, completion=c), ()).reasons
    unknown = replace(b.completion, exit_kind=None, exit_code=None)
    assert (
        "MISSING_EXIT_STATUS"
        in evaluation.evaluate_receipts(replace(b, completion=unknown), ()).reasons
    )


@pytest.mark.parametrize(
    "change",
    [
        {"status": "REJECTED"},
        {"reasons": (False,)},
        {"status": evaluation.ReceiptStatus.CONSISTENT, "reasons": ("bad",)},
        {"read_events": False},
    ],
)
def test_decisions_cannot_coerce_status_missingness_or_counts(change):
    with pytest.raises(ValueError):
        replace(evaluation.evaluate_receipts(build(), ()), **change)


@pytest.mark.parametrize("value", [None, "", "a" * 4097, "bad\ud800"])
def test_path_scalar_and_utf8_bounds(value):
    with pytest.raises(ValueError):
        replace(build().materials[0], logical_path=value)


@pytest.mark.parametrize(
    "change",
    [
        {"identity": None},
        {"completion": None},
        {"evidence_kind": "SYNTHETIC"},
        {"uses": None},
        {"uses": (None,)},
    ],
)
def test_wrong_structural_record_kinds_reject_without_default_objects(change):
    with pytest.raises(ValueError):
        replace(build(), **change)


@pytest.mark.parametrize(
    "change",
    [
        {"exit_kind": "EXITED"},
        {"exit_code": 256},
        {"exit_kind": models.ExitKind.SIGNALLED, "term_signal": 9},
        {"exit_kind": models.ExitKind.SIGNALLED, "exit_code": None, "term_signal": 65},
    ],
)
def test_exit_scalar_domain_is_not_a_generic_positive_integer(change):
    with pytest.raises(ValueError):
        replace(build().completion, **change)


def test_bounded_collections_stop_before_materializing_an_unbounded_iterator(monkeypatch):
    sample = build().uses[0]
    calls = []
    monkeypatch.setattr(models, "MAX_ITEMS", 2)

    def stream():
        while True:
            calls.append(1)
            yield sample

    with pytest.raises(ValueError):
        models.records(stream(), models.InputUse)
    assert len(calls) == 3


def test_codec_rejects_nonobjects_nonstring_enums_and_nonarrays():
    with pytest.raises(ValueError):
        codec.encode_receipt(build().identity.session_id)
    for raw in (False, "[]", "[" * 10000):
        with pytest.raises(ValueError):
            codec.parse_build(raw)
    for field, value in (("images", {}), ("evidence_kind", False)):
        data = json.loads(codec.encode_receipt(build()))
        data["payload"][field] = value
        with pytest.raises(ValueError):
            codec.parse_build(json.dumps(data))
    b = build()
    unknown = replace(b, completion=replace(b.completion, exit_kind=None, exit_code=None))
    assert codec.parse_build(codec.encode_receipt(unknown)).completion.exit_kind is None


def test_codec_resource_bound_covers_both_encode_and_parse(monkeypatch):
    monkeypatch.setattr(codec, "MAX_JSON_BYTES", 10)
    with pytest.raises(ValueError):
        codec.encode_receipt(build())
    with pytest.raises(ValueError):
        codec.parse_build(" " * 11)


def test_zero_byte_material_and_partial_reads_preserve_distinct_content_claims():
    b = build()
    source = replace(b.materials[1], size=0, sha256=EMPTY_SHA)
    use = replace(b.uses[1], length=0, range_digest=EMPTY_SHA)
    d = evaluation.evaluate_receipts(
        replace(b, materials=(b.materials[0], source), uses=(b.uses[0], use)), ()
    )
    assert "EMPTY_MATERIAL_HASH_MISMATCH" not in d.reasons
    assert "FULL_READ_HASH_MISMATCH" not in d.reasons
    source = replace(source, size=2, sha256=SHA_A)
    d = evaluation.evaluate_receipts(replace(b, materials=(b.materials[0], source)), ())
    assert "FULL_READ_HASH_MISMATCH" not in d.reasons
