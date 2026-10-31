"""Direct original APIs: stricter admission without authority or digest changes."""

import copy
import json
from dataclasses import replace

import pytest

from compatibility.native_containment.contracts import canonical_digest, parse_synthetic_case
from compatibility.native_containment.validation import evaluate_synthetic
from tests.audit import validate_guest_input_handoff_design as handoff
from tests.fixtures.native_containment import synthetic_case
from tests.test_strict_containment_input import policy, put_text

LIMITS = {"members": 16, "bytes_per_member": 4096, "events": 1024, "json_bytes": 2097152}


@pytest.mark.parametrize(
    "location", ("actor_id", "event_actor", "requested_endpoint", "errno_name", "flag0", "flag1")
)
@pytest.mark.parametrize("text", (chr(0xD800), chr(0xDFFF), "x" + chr(0xD800) + "y"))
def test_original_parse_rejects_surrogates_before_return(location, text):
    # Removing parse's canonical UTF8 admission must admit these malformed scalars.
    data = synthetic_case()
    put_text(data, location, text)
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$") as raised:
        parse_synthetic_case(json.dumps(data))
    assert type(raised.value) is ValueError
    assert raised.value.__cause__ is None and raised.value.__suppress_context__


def test_original_parse_checks_nested_event_clock_domain():
    data = synthetic_case()
    data["events"][0]["clock_domain"] = chr(0xD800)
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$"):
        parse_synthetic_case(json.dumps(data))


@pytest.mark.parametrize("text", ("ascii", "한글", "\U0001f600", "é", "e\u0301", "x\0y"))
def test_original_parse_preserves_valid_values_and_decisions(text):
    data = synthetic_case()
    put_text(data, "requested_endpoint", text)
    case = parse_synthetic_case(json.dumps(data))
    assert case.events[0].requested_endpoint == text
    assert evaluate_synthetic(case, policy()).case_digest == canonical_digest(case)
    assert case.candidate_generation_allowed is False
    assert case.application_authorized is False
    assert case.runtime_accepted is False
    assert case.owner_proposal_allowed is False


def test_direct_constructor_and_digest_remain_the_same_lower_level_contract():
    case = parse_synthetic_case(json.dumps(synthetic_case()))
    case = replace(case, actor_id=chr(0xD800))
    with pytest.raises(UnicodeEncodeError):
        canonical_digest(case)


@pytest.mark.parametrize("field", tuple(LIMITS))
@pytest.mark.parametrize("representation", ("float", "bool", "none", "str", "wrong_int"))
def test_original_handoff_rejects_non_exact_limit_values(field, representation):
    # Numeric dict equality wrongly accepts each equal float; exact int is required.
    data = handoff.load("schema")
    data["limits"][field] = {
        "float": float(LIMITS[field]),
        "bool": True,
        "none": None,
        "str": str(LIMITS[field]),
        "wrong_int": LIMITS[field] + 1,
    }[representation]
    with pytest.raises(ValueError, match="^handoff design content/scope mismatch$"):
        handoff.validate_schema(data)


class EqualInt(int):
    pass


class DictSubclass(dict):
    pass


class HostileKey:
    def __hash__(self):
        return hash("members")

    def __eq__(self, other):
        raise AssertionError("must reject non-exact string before comparison")


@pytest.mark.parametrize("variant", ("dict_subclass", "int_subclass", "hostile_key"))
def test_original_handoff_rejects_subclasses_and_keys_before_equality(variant):
    data = handoff.load("schema")
    if variant == "dict_subclass":
        data["limits"] = DictSubclass(LIMITS)
    elif variant == "int_subclass":
        data["limits"]["members"] = EqualInt(16)
    else:
        del data["limits"]["members"]
        data["limits"][HostileKey()] = 16
    with pytest.raises(ValueError, match="^handoff design content/scope mismatch$"):
        handoff.validate_schema(data)


def test_original_handoff_keeps_input_identity_and_exact_representations():
    data = handoff.load("schema")
    before = copy.deepcopy(data)
    limits = data["limits"]
    assert handoff.validate_schema(data) is None
    assert data == before and data["limits"] is limits
    assert all(type(value) is int for value in limits.values())
