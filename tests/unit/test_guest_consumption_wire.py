"""Strict transport rejects loss/coercion and never reparses payload bytes."""

from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.guest_consumption import module, rows, text


def parse(values=None):
    return module("wire").parse_capture(text(values))


def test_literal_frames_are_immutable_and_digest_preserves_event_order():
    c = parse()
    assert c.case == "CP01" and len(c.events) == 13
    with pytest.raises(FrozenInstanceError):
        c.events[0].seq = 8
    w = module("wire")
    assert w.capture_digest(c) == w.capture_digest(parse())
    mutable = list(c.events)
    copied = replace(c, events=mutable)
    mutable.clear()
    assert len(copied.events) == 13


@pytest.mark.parametrize(
    "field,value",
    [
        ("seq", True),
        ("time_ns", -1),
        ("task", False),
        ("image", 2**64),
        ("kind", "OTHER"),
        ("values", None),
    ],
)
def test_wrong_record_scalars_cannot_be_coerced_or_defaulted(field, value):
    r = rows()
    r[5][field] = value
    with pytest.raises(ValueError):
        parse(r)


@pytest.mark.parametrize(
    "kind,values",
    [
        ("READ", [2, 0, 4, "00"]),
        ("READ", [2, None, 0, ""]),
        ("READ", [2, 0, 1, "AA"]),
        ("MAP", [2, 0, 0]),
        ("MAP", [2, 0, 4096, "00"]),
        ("FAILED", [0, 0]),
        ("EXIT", ["EXITED", None]),
        ("END", [0, 1, 2, 0]),
    ],
)
def test_stage_shapes_separate_bytes_extent_failure_and_unknown(kind, values):
    r = rows()
    r[5].update(kind=kind, values=values)
    with pytest.raises(ValueError):
        parse(r)


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "unknown",
        "nan",
        "truncated",
        "interleaved",
        "trailing",
        "clock",
        "sequence",
        "time",
    ],
)
def test_wire_failure_is_not_repaired_into_a_valid_capture(change):
    r = rows()
    raw = text(r)
    if change == "duplicate":
        raw = raw.replace('"seq":1,', '"seq":1,"seq":1,', 1)
    elif change == "unknown":
        raw = raw.replace('"seq":1,', '"authority":true,"seq":1,', 1)
    elif change == "nan":
        raw = raw.replace('"time_ns":11', '"time_ns":NaN')
    elif change == "truncated":
        raw = text(r[:-1])
    elif change == "interleaved":
        raw = raw.replace("CONSUMPTION ", "[console]CONSUMPTION ", 1)
    elif change == "trailing":
        raw += text(r[-1:])
    elif change == "clock":
        r[0]["values"][2] = "HOST_CLOCK"
        raw = text(r)
    elif change == "sequence":
        r[5]["seq"] = 4
        raw = text(r)
    else:
        r[5]["time_ns"] = 0
        raw = text(r)
    with pytest.raises(ValueError):
        module("wire").parse_capture(raw)


def test_payload_hex_cannot_forge_an_end_record():
    r = rows()
    r.insert(
        -1,
        dict(
            seq=13,
            time_ns=23,
            kind="PAYLOAD",
            task=0,
            image=0,
            values=[text([r[-1]]).encode().hex()],
        ),
    )
    r[-1].update(seq=14, time_ns=24)
    c = parse(r)
    assert c.events[-2].kind == "PAYLOAD" and len(c.events) == 14
