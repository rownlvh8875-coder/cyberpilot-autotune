"""Wire claims are exact values, never capability-bearing instructions."""

import importlib
import importlib.util
import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

REGISTRATION = (
    Path(__file__).resolve().parents[1]
    / "docs/evidence/audit_compatibility/preparation-profile-v1/registration.json"
)


def wire():
    assert importlib.util.find_spec("tests.audit_preparation_profile") is not None, "missing wire"
    return importlib.import_module("tests.audit_preparation_profile.wire")


def vectors():
    return json.loads(REGISTRATION.read_text())["conformance"]


@pytest.mark.parametrize("kind", ["policy", "record"])
def test_roundtrip_matches_independently_frozen_canonical_bytes(kind):
    w = wire()
    raw = vectors()[f"canonical_{kind}_utf8"].encode()
    decode = w.decode_policy if kind == "policy" else w.decode_profile
    encode = w.canonical_policy if kind == "policy" else w.canonical_profile
    value = decode(raw)
    assert encode(value) == raw
    assert sha256(raw).hexdigest() == vectors()[f"canonical_{kind}_sha256"]
    envelope = json.loads(raw)
    envelope["body"] = dict(reversed(list(envelope["body"].items())))
    for key in ("artifacts", "cohorts", "batch_limits", "commands", "controls"):
        envelope["body"][key].reverse()
    assert encode(decode(json.dumps(envelope, indent=2).encode())) == raw


@pytest.mark.parametrize("value", [None, 0, 2**53 + 1, 2**64 - 1, "UNBOUNDED"])
def test_wire_preserves_exact_integers_and_null(value):
    w = wire()
    p = w.decode_policy(vectors()["canonical_policy_utf8"].encode())
    limits = (replace(p.batch_limits[0], value=value),) + p.batch_limits[1:]
    assert (
        w.decode_policy(w.canonical_policy(replace(p, batch_limits=limits))).batch_limits[0].value
        == value
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "kind",
        "version",
        "nested-extra",
        "float",
        "bool",
        "unit",
        "duplicate-id",
        "authority",
    ],
)
def test_wire_rejects_malformed_or_authority_bearing_fields(mutation):
    w = wire()
    doc = json.loads(vectors()["canonical_record_utf8"])
    if mutation == "missing":
        del doc["body"]["run_id"]
    elif mutation == "extra":
        doc["extra"] = None
    elif mutation == "kind":
        doc["kind"] = "POLICY"
    elif mutation == "version":
        doc["schema"] = "v2"
    elif mutation == "nested-extra":
        doc["body"]["batch_boundary"]["extra"] = 0
    elif mutation in ("float", "bool"):
        doc["body"]["batch_limits"][0]["value"] = 1.0 if mutation == "float" else True
    elif mutation == "unit":
        doc["body"]["batch_limits"][0]["unit"] = "second"
    elif mutation == "duplicate-id":
        doc["body"]["commands"].append(doc["body"]["commands"][0])
    else:
        doc["body"]["application_authorized"] = True
    with pytest.raises(ValueError):
        w.decode_profile(json.dumps(doc).encode())


@pytest.mark.parametrize(
    "bad",
    [
        b"",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b"{} {}",
        b"NaN",
        b"Infinity",
        b"[]",
        b"null",
        b"1.0",
        b"[" * 1500 + b"]" * 1500,
        b" " * (1048576 + 1),
        "{}",
        bytearray(b"{}"),
    ],
)
def test_wire_rejects_invalid_encoding_shape_and_capacity(bad):
    with pytest.raises(ValueError):
        wire().decode_profile(bad)


def test_duplicate_json_keys_are_rejected_even_with_identical_values():
    w = wire()
    raw = vectors()["canonical_record_utf8"].encode()
    duplicate = b'{"schema":"preparation-profile-claims-v1",' + raw[1:]
    with pytest.raises(ValueError):
        w.decode_profile(duplicate)


def test_serialization_revalidates_forged_nested_graph_and_top_level_kind():
    w = wire()
    p = w.decode_policy(vectors()["canonical_policy_utf8"].encode())
    with pytest.raises(ValueError):
        w.canonical_profile(p)
    object.__setattr__(p.batch_limits[0], "value", True)
    with pytest.raises(ValueError):
        w.canonical_policy(p)
    broken = object.__new__(type(p))
    with pytest.raises(ValueError):
        w.canonical_policy(broken)
