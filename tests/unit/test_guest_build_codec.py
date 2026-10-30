"""Canonical content identity cannot become proof, authority or silent defaults."""

import hashlib
import importlib
import json
from dataclasses import replace

import pytest

from tests.fixtures.guest_build_receipt import build, identity, models, promotion


def codec():
    models()
    return importlib.import_module("compatibility.guest_build_receipt.codec")


def test_round_trip_preserves_exact_immutable_fields_for_both_receipt_stages():
    c = codec()
    assert c.parse_build(c.encode_receipt(build())) == build()
    assert c.parse_promotion(c.encode_receipt(promotion())) == promotion()


def test_identity_digest_has_an_independently_encoded_semantic_domain():
    c = codec()
    raw = {
        "schema": "guest-build-identity-v1",
        "payload": {
            "session_id": "session-1",
            "attempt_id": "attempt-1",
            "source_digest": "1" * 64,
            "toolchain_digest": "2" * 64,
            "recipe_digest": "3" * 64,
            "environment_digest": "4" * 64,
            "observer_digest": "5" * 64,
            "clock_domain": "GUEST_TRACER_OBSERVATION_MONOTONIC_NS",
        },
    }
    expected = hashlib.sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert c.receipt_digest(identity()) == expected
    assert c.receipt_digest(identity()) != c.receipt_digest(build())


def test_field_order_is_irrelevant_but_stream_order_none_and_generation_are_not():
    c = codec()
    b = build()
    raw = json.loads(c.encode_receipt(b))
    reordered = json.dumps(dict(reversed(list(raw.items()))))
    assert c.receipt_digest(c.parse_build(reordered)) == c.receipt_digest(b)
    assert c.receipt_digest(replace(b, uses=tuple(reversed(b.uses)))) != c.receipt_digest(b)
    assert c.receipt_digest(replace(b, start_ns=None)) != c.receipt_digest(replace(b, start_ns=0))
    assert c.receipt_digest(
        replace(b, outputs=(replace(b.outputs[0], generation=1),))
    ) != c.receipt_digest(b)


@pytest.mark.parametrize("change", ["schema", "unknown", "duplicate", "nan", "enum", "missing"])
def test_unknown_duplicate_nonfinite_or_future_wire_values_fail_closed(change):
    c = codec()
    raw = c.encode_receipt(build())
    if change == "schema":
        raw = raw.replace("guest-build-consumption-v1", "future")
    elif change == "unknown":
        raw = raw.replace('"payload":{', '"payload":{"authority":true,')
    elif change == "duplicate":
        raw = raw.replace('"start_ns":10', '"start_ns":10,"start_ns":10')
    elif change == "nan":
        raw = raw.replace('"start_ns":10', '"start_ns":NaN')
    elif change == "enum":
        raw = raw.replace('"READ_BYTES"', '"OTHER"')
    else:
        raw = raw.replace('"exit_code":0,', "")
    with pytest.raises(ValueError):
        c.parse_build(raw)


def test_wrong_stage_cannot_be_parsed_as_a_build_receipt():
    c = codec()
    with pytest.raises(ValueError):
        c.parse_build(c.encode_receipt(promotion()))
    with pytest.raises(ValueError):
        c.parse_promotion(c.encode_receipt(build()))
