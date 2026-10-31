"""Opt-in exact-limit admission; no actual FD/runtime evidence or caller adoption."""

import copy
import json
from collections import UserDict

import pytest

from tests.audit import validate_guest_input_handoff_design as legacy
from tests.strict_handoff.validation import validate_schema_strict

LIMITS = {"members": 16, "bytes_per_member": 4096, "events": 1024, "json_bytes": 2097152}


class IntSubclass(int):
    pass


class DictSubclass(dict):
    pass


class EqualitySpoof:
    def __eq__(self, other):
        return True


class ForbiddenEqualityKey:
    def __hash__(self):
        return hash("members")

    def __eq__(self, other):
        raise AssertionError("non-string key comparison must never be used for admission")


class StringSubclass(str):
    __hash__ = str.__hash__

    def __eq__(self, other):
        raise AssertionError("str-subclass key comparison must never be used for admission")


@pytest.mark.parametrize("field", list(LIMITS))
def test_float_equal_limit_metadata_rejected(field):
    # Catches preserving old numeric equality instead of requiring exact int.
    data = legacy.load("schema")
    data["limits"][field] = float(LIMITS[field])
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)


@pytest.mark.parametrize("field", list(LIMITS))
@pytest.mark.parametrize("spelling", ["decimal", "exponent"])
def test_equal_json_floats_reject_after_decode(field, spelling):
    data = legacy.load("schema")
    value = str(LIMITS[field]) + (".0" if spelling == "decimal" else "e0")
    data["limits"][field] = json.loads(value)
    assert type(data["limits"][field]) is float
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)


@pytest.mark.parametrize("field", list(LIMITS))
@pytest.mark.parametrize(
    "kind",
    [
        "none",
        "false",
        "true",
        "string",
        "float",
        "subclass",
        "spoof",
        "zero",
        "negative",
        "off_by_one",
        "nan",
        "infinity",
    ],
)
def test_nonexact_integer_types_and_values_reject(field, kind):
    expected = LIMITS[field]
    value = {
        "none": None,
        "false": False,
        "true": True,
        "string": str(expected),
        "float": float(expected),
        "subclass": IntSubclass(expected),
        "spoof": EqualitySpoof(),
        "zero": 0,
        "negative": -1,
        "off_by_one": expected + 1,
        "nan": float("nan"),
        "infinity": float("inf"),
    }[kind]
    data = legacy.load("schema")
    data["limits"][field] = value
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)
    assert data["limits"][field] is value


@pytest.mark.parametrize("kind", ["none", "list", "string", "subclass", "userdict", "spoof"])
@pytest.mark.parametrize("where", ["root", "limits"])
def test_nonexact_dict_envelopes_reject_without_coercion(kind, where):
    data = legacy.load("schema")
    original = data if where == "root" else data["limits"]
    value = {
        "none": None,
        "list": list(original.items()),
        "string": json.dumps(original),
        "subclass": DictSubclass(original),
        "userdict": UserDict(original),
        "spoof": EqualitySpoof(),
    }[kind]
    if where == "root":
        data = value
    else:
        data["limits"] = value
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)


@pytest.mark.parametrize("field", list(LIMITS))
@pytest.mark.parametrize("kind", ["missing", "extra", "renamed"])
def test_limit_key_set_is_closed(field, kind):
    data = legacy.load("schema")
    if kind in {"missing", "renamed"}:
        del data["limits"][field]
    if kind in {"extra", "renamed"}:
        data["limits"][field + "_unknown"] = LIMITS[field]
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)


def test_missing_limits_envelope_is_not_filled_in():
    data = legacy.load("schema")
    del data["limits"]
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)
    assert "limits" not in data


@pytest.mark.parametrize("key", [ForbiddenEqualityKey(), StringSubclass("members"), 16])
def test_nonliteral_keys_inside_exact_dict_cannot_spoof_admission(key):
    data = legacy.load("schema")
    del data["limits"]["members"]
    data["limits"][key] = 16
    assert type(data["limits"]) is dict and len(data["limits"]) == 4
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema", "wrong"),
        ("graph_version", "wrong"),
        ("scope", "FULL_BUILD_NAMESPACE"),
        ("clock_domain", "wrong"),
        ("encoding", "RUNTIME_WIRE"),
        ("evidence_kind", "OBSERVED_UNTRUSTED"),
        ("preferred_transport", "SCM_RIGHTS"),
        ("runtime_producer_implemented", True),
        ("runtime_qualified", True),
    ],
)
def test_valid_exact_limits_delegate_all_original_checks(field, value):
    data = legacy.load("schema")
    data[field] = value
    with pytest.raises(ValueError) as original:
        legacy.validate_schema(data)
    with pytest.raises(type(original.value)) as strict:
        validate_schema_strict(data)
    assert type(strict.value) is type(original.value) and str(strict.value) == str(original.value)


@pytest.mark.parametrize("permission", tuple(legacy.load("schema")["permissions"]))
def test_each_permission_escalation_still_rejects(permission):
    data = legacy.load("schema")
    data["permissions"][permission] = True
    with pytest.raises(ValueError, match="^handoff design content/scope mismatch$"):
        validate_schema_strict(data)


@pytest.mark.parametrize("variant", ["type", "unit", "stage", "unknown_root", "proof", "event"])
def test_schema_structure_and_units_are_not_bypassed(variant):
    data = legacy.load("schema")
    if variant in {"type", "unit", "stage"}:
        data["context_fields"][0][variant] = "wrong"
    elif variant == "unknown_root":
        data["extra"] = 1
    elif variant == "proof":
        data["proof_obligations"][0]["runtime_status"] = "QUALIFIED"
    else:
        del data["event_fields"]["BIND"]
    with pytest.raises(ValueError) as original:
        legacy.validate_schema(data)
    with pytest.raises(type(original.value)) as strict:
        validate_schema_strict(data)
    assert str(strict.value) == str(original.value)


@pytest.mark.parametrize("variant", ["valid", "none", "false", "zero", "float", "legacy_error"])
def test_success_and_failure_do_not_mutate_input(variant):
    data = legacy.load("schema")
    if variant in {"none", "false", "zero", "float"}:
        data["limits"]["members"] = {"none": None, "false": False, "zero": 0, "float": 16.0}[
            variant
        ]
    elif variant == "legacy_error":
        data["scope"] = "wrong"
    before = copy.deepcopy(data)
    representation = repr(data)
    limits = data["limits"]
    if variant == "valid":
        assert validate_schema_strict(data) is None
    else:
        with pytest.raises(ValueError):
            validate_schema_strict(data)
    assert data == before and repr(data) == representation
    assert data["limits"] is limits
    assert data["runtime_producer_implemented"] is False and data["runtime_qualified"] is False
    assert all(v is False for v in data["permissions"].values())


@pytest.mark.parametrize("variant", ["duplicate", "nan", "over_limit", "at_limit"])
def test_legacy_load_policy_is_not_replaced(tmp_path, monkeypatch, variant):
    # Real frozen loader, pointed only at exclusively owned synthetic pytest files.
    target = tmp_path / "docs/evidence/guest_input_handoff_design_schema.json"
    target.parent.mkdir(parents=True)
    raw = {
        "duplicate": b'{"limits":{},"limits":{}}',
        "nan": b'{"value":NaN}',
        "over_limit": b" " * 2097153,
        "at_limit": b"{}" + b" " * 2097150,
    }[variant]
    target.write_bytes(raw)
    monkeypatch.setattr(legacy, "ROOT", tmp_path)
    if variant == "at_limit":
        assert legacy.load("schema") == {}
    else:
        with pytest.raises(ValueError):
            legacy.load("schema")


def test_object_api_cannot_recover_duplicate_keys_lost_by_permissive_decoder():
    data = legacy.load("schema")
    raw = '{"limits":{"members":0},' + json.dumps(data)[1:]
    decoded = json.loads(raw)
    assert decoded["limits"] == LIMITS
    assert validate_schema_strict(decoded) is None  # no raw-parser/authenticity claim


@pytest.mark.parametrize("field", list(LIMITS))
def test_original_validator_still_accepts_float_equal_metadata(field):
    data = legacy.load("schema")
    data["limits"][field] = float(LIMITS[field])
    assert legacy.validate_schema(data) is None
    with pytest.raises(ValueError, match="^EXACT_INTEGER_LIMITS_REQUIRED$"):
        validate_schema_strict(data)
