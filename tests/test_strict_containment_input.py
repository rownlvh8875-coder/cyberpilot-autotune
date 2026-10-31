"""Exercise opt-in UTF8 admission, not real containment or legacy caller adoption."""

import json
from dataclasses import replace

import pytest

from compatibility.native_containment.contracts import (
    SyntheticContainmentCase,
    canonical_digest,
    parse_synthetic_case,
)
from compatibility.native_containment.validation import (
    PolicyMode,
    SyntheticPolicyContext,
    evaluate_synthetic,
)
from tests.fixtures.native_containment import synthetic_case
from tests.strict_containment.validation import (
    digest_case_strict,
    evaluate_case_strict,
    parse_case_strict,
)

TEXT_LOCATIONS = ("actor_id", "event_actor", "requested_endpoint", "errno_name", "flag0", "flag1")
PROOFS = (
    "input_closure_complete",
    "enforcement_observed_active",
    "source_loader_immutable",
    "process_stage_bound",
    "resource_resolution_bound",
    "capture_guard_bound",
    "trace_complete",
    "observer_intact",
)
PERMISSIONS = (
    "candidate_generation_allowed",
    "application_authorized",
    "runtime_accepted",
    "owner_proposal_allowed",
)


def policy(mode=PolicyMode.CAPABILITY_CLOSED_DISCOVERY_PROPOSAL):
    return SyntheticPolicyContext(mode, True, "a" * 64)


def put_text(data, location, value):
    if location == "actor_id":
        data["actor_id"] = value
    elif location == "event_actor":
        data["events"][0]["actor_id"] = value
    elif location.startswith("flag"):
        data["events"][0]["flags"][int(location[-1])] = value
    else:
        data["events"][0][location] = value


@pytest.mark.parametrize("codepoint", [0xD800, 0xDFFF])
@pytest.mark.parametrize("location", TEXT_LOCATIONS)
@pytest.mark.parametrize("ascii_escapes", [True, False])
def test_lone_surrogate_rejected_before_parse_result(codepoint, location, ascii_escapes):
    # Catches returning the old parse result without proving canonical UTF8 first.
    data = synthetic_case()
    put_text(data, location, chr(codepoint))
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$") as exc:
        parse_case_strict(json.dumps(data, ensure_ascii=ascii_escapes))
    assert type(exc.value) is ValueError
    assert exc.value.__suppress_context__ is True


@pytest.mark.parametrize("codepoint", [0xD800, 0xDFFF])
@pytest.mark.parametrize("location", TEXT_LOCATIONS)
@pytest.mark.parametrize("construction", ["replace", "forged"])
def test_nested_and_direct_case_surrogates_rejected(codepoint, location, construction):
    # Catches strict digest/evaluation bypass for callers that do not use strict parse.
    case = parse_synthetic_case(json.dumps(synthetic_case()))
    target = case if location == "actor_id" else case.events[0]
    field = "actor_id" if location == "event_actor" else location
    value = chr(codepoint)
    if location.startswith("flag"):
        field = "flags"
        flags = list(target.flags)
        flags[int(location[-1])] = value
        value = tuple(flags)
    if construction == "forged":
        object.__setattr__(target, field, value)
    elif target is case:
        case = replace(case, **{field: value})
    else:
        case = replace(case, events=(replace(target, **{field: value}),))
    for call in (lambda: digest_case_strict(case), lambda: evaluate_case_strict(case, policy())):
        with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$") as exc:
            call()
        assert type(exc.value) is ValueError


@pytest.mark.parametrize("codepoint", [0xD7FF, 0xE000, 0x10FFFF, 0, 10, 0xFFFE, 0xFFFF])
def test_valid_pair_and_scalar_boundaries_keep_legacy_semantics(codepoint):
    data = synthetic_case()
    data["actor_id"] = data["events"][0]["actor_id"] = chr(codepoint)
    raw = json.dumps(data, ensure_ascii=False)
    case = parse_case_strict(raw)
    assert type(case) is SyntheticContainmentCase
    assert case.actor_id == chr(codepoint)
    assert digest_case_strict(case) == canonical_digest(parse_synthetic_case(raw))
    assert evaluate_case_strict(case, policy()) == evaluate_synthetic(case, policy())


def test_json_escaped_pair_succeeds_but_literal_python_surrogates_reject():
    data = synthetic_case()
    data["actor_id"] = data["events"][0]["actor_id"] = chr(0x1F600)
    escaped = json.dumps(data)
    assert r"\ud83d\ude00" in escaped
    case = parse_case_strict(escaped)
    assert case.actor_id == chr(0x1F600)
    assert digest_case_strict(case) == (
        "a538c7fb2078e531d33df0c48524722c337f622ef2731839d369435acea0ccfe"
    )
    data["actor_id"] = chr(0xD83D) + chr(0xDE00)
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$"):
        parse_case_strict(json.dumps(data, ensure_ascii=False))
    direct = replace(case, actor_id=data["actor_id"])
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$"):
        digest_case_strict(direct)
    with pytest.raises(ValueError, match="^INVALID_UNICODE_SCALAR$"):
        evaluate_case_strict(direct, policy())


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("synthetic-child", "07e8c3939efdcd6c5fc4ba2b445b73ba241d7802fae2f195b20b7137348013d1"),
        ("아이", "d2fc2cd4898c2118a6e24e9434a9680d958b173c15c3171e1e630f84ff1ce0e7"),
        (chr(0x1F600), "a538c7fb2078e531d33df0c48524722c337f622ef2731839d369435acea0ccfe"),
        ("\u00e9", "af541ca4f78a8266c0dd9c955289c9aee1ef39c6d7f748ee092c7778ce39292f"),
        ("e\u0301", "82e09ad04694055f536076bdd1c335c8d85bf2f70c052f96bb69f23729b06c20"),
    ],
)
def test_unicode_goldens_and_no_normalization(text, expected):
    # Literal frozen goldens catch ASCII replacement, NFC/NFD or digest-algorithm drift.
    data = synthetic_case()
    data["actor_id"] = data["events"][0]["actor_id"] = text
    for raw in (json.dumps(data), json.dumps(data, sort_keys=True, ensure_ascii=False)):
        case = parse_case_strict(raw)
        assert case.actor_id == text
        assert digest_case_strict(case) == expected
        assert case.schema_version == "synthetic-native-containment-case-v1"


@pytest.mark.parametrize("mode", list(PolicyMode))
@pytest.mark.parametrize(
    "variant",
    ["base", "unknown_counts", "nonzero_counts", "unknown_backend"]
    + [(name, value) for name in PROOFS for value in (False, None)],
)
def test_every_valid_fixture_matches_original_decision(mode, variant):
    data = synthetic_case()
    if isinstance(variant, tuple):
        data["modeled_proofs"][variant[0]] = variant[1]
    elif variant == "unknown_counts":
        data["successful_prohibited_handles"] = data["successful_prohibited_effects"] = None
    elif variant == "nonzero_counts":
        data["successful_prohibited_handles"] = 1
    elif variant == "unknown_backend":
        data["cpu_backend"] = None
    raw = json.dumps(data)
    case = parse_case_strict(raw)
    result = evaluate_case_strict(case, policy(mode))
    assert result == evaluate_synthetic(parse_synthetic_case(raw), policy(mode))
    assert result.evidence_kind == "SYNTHETIC" and result.runtime_qualified is False
    assert all(getattr(result, name) is False for name in PERMISSIONS)
    if variant == "base":
        assert result.reasons == (
            ("DEVICE_ATTEMPT_STRICT",) if mode == PolicyMode.STRICT_NO_DEVICE_ATTEMPT else ()
        )
        assert result.status == (
            "REJECTED"
            if mode == PolicyMode.STRICT_NO_DEVICE_ATTEMPT
            else "DIAGNOSTIC_EXPECTED_DENIAL_ONLY"
        )


@pytest.mark.parametrize(
    "variant",
    [
        "duplicate",
        "unknown_key",
        "nested_key",
        "missing",
        "nan",
        "inf",
        "float",
        "bool",
        "permission",
        "malformed",
        "wrong_raw",
        "wrong_root",
    ],
)
def test_legacy_rejections_propagate_without_repair(variant):
    data = synthetic_case()
    if variant == "unknown_key":
        data["extra"] = 1
    elif variant == "nested_key":
        data["events"][0]["extra"] = 1
    elif variant == "missing":
        del data["events"]
    elif variant in {"nan", "inf", "float", "bool"}:
        data["process_generation"] = {
            "nan": float("nan"),
            "inf": float("inf"),
            "float": 1.0,
            "bool": True,
        }[variant]
    elif variant == "permission":
        data["application_authorized"] = True
    raw = json.dumps(data)
    if variant == "duplicate":
        raw = '{"actor_id":"duplicate",' + raw[1:]
    elif variant == "malformed":
        raw = "{"
    elif variant == "wrong_raw":
        raw = None
    elif variant == "wrong_root":
        raw = "[]"
    with pytest.raises(ValueError) as original:
        parse_synthetic_case(raw)
    with pytest.raises(type(original.value)) as strict:
        parse_case_strict(raw)
    assert type(strict.value) is type(original.value)
    assert str(strict.value) == str(original.value)


@pytest.mark.parametrize("name", PERMISSIONS)
def test_permission_escalation_rejects_at_every_strict_entrypoint(name):
    data = synthetic_case()
    data[name] = True
    with pytest.raises(ValueError, match="real permissions are fixed false"):
        parse_case_strict(json.dumps(data))
    case = parse_synthetic_case(json.dumps(synthetic_case()))
    object.__setattr__(case, name, True)
    for call in (lambda: digest_case_strict(case), lambda: evaluate_case_strict(case, policy())):
        with pytest.raises(ValueError, match="real permissions are fixed false"):
            call()


def test_wrong_case_policy_and_forged_nested_proofs_are_not_repaired():
    with pytest.raises(ValueError, match="expected synthetic case"):
        digest_case_strict({})
    with pytest.raises(ValueError, match="expected synthetic case"):
        evaluate_case_strict({}, policy())
    case = parse_case_strict(json.dumps(synthetic_case()))
    with pytest.raises(ValueError, match="expected synthetic policy context"):
        evaluate_case_strict(case, {})
    object.__setattr__(case.modeled_proofs, "observer_intact", 1)
    for call in (lambda: digest_case_strict(case), lambda: evaluate_case_strict(case, policy())):
        with pytest.raises(ValueError, match="expected bool or null"):
            call()


def test_unknown_counts_do_not_become_observed_zero():
    data = synthetic_case()
    zero = parse_case_strict(json.dumps(data))
    data["successful_prohibited_handles"] = None
    unknown = parse_case_strict(json.dumps(data))
    assert digest_case_strict(zero) != digest_case_strict(unknown)
    assert evaluate_case_strict(zero, policy()).reasons == ()
    assert evaluate_case_strict(unknown, policy()).reasons == ("RESULT_UNKNOWN",)


def test_original_entrypoints_remain_unrepaired_and_unmigrated():
    data = synthetic_case()
    data["actor_id"] = chr(0xD800)
    case = parse_synthetic_case(json.dumps(data))
    assert case.actor_id == chr(0xD800)
    with pytest.raises(UnicodeEncodeError):
        canonical_digest(case)
    with pytest.raises(UnicodeEncodeError):
        evaluate_synthetic(case, policy())
