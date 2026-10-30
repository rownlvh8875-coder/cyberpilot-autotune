"""Malformed or caller-authored reports cannot manufacture execution authority."""

import importlib
import json
from collections import UserString
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.backend_harmless import fixture_report


def api():
    assert importlib.util.find_spec("compatibility.containment_backend_harmless") is not None
    return importlib.import_module("compatibility.containment_backend_harmless.validation")


def parse(raw=None):
    return api().validate_harmless_result(json.dumps(fixture_report() if raw is None else raw))


def test_fabricated_scope_is_not_authority():
    value = parse()
    assert value.evidence_kind == "UNTRUSTED_FIXTURE_REPORT"
    for field in (
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert getattr(value, field) is False
        raw = fixture_report()
        raw[field] = True
        with pytest.raises(ValueError):
            parse(raw)


def test_standin_is_not_device_qualification():
    raw = fixture_report()
    raw["fixture_id"] = "HF23"
    assert parse(raw).device_class_qualified is False
    raw["evidence_kind"] = "OBSERVED"
    with pytest.raises(ValueError):
        parse(raw)


@pytest.mark.parametrize(
    "field",
    [
        "guard_active",
        "collector_bound",
        "trace_complete",
        "process_lineage_complete",
        "tree_exit_observed",
        "broker_effects_observed",
        "clock_domain",
        "successful_prohibited_handles",
        "successful_prohibited_effects",
        "kernel_build_digest",
        "kernel_config_digest",
        "btf_digest",
        "source_loader_digest",
        "object_receipt_digest",
        "fd_lineage_digest",
    ],
)
def test_null_is_not_zero_and_cannot_support_pass(field):
    raw = fixture_report()
    raw["actual_observations"][field] = None
    with pytest.raises(ValueError):
        parse(raw)
    raw["outcome"] = "UNAVAILABLE"
    raw["reasons"] = ["MISSING_NAMED_OBSERVATION"]
    assert getattr(parse(raw).actual_observations, field) is None


@pytest.mark.parametrize("location", ["root", "observations"])
@pytest.mark.parametrize("mutation", ["unknown", "missing", "duplicate"])
def test_unknown_keys_and_missing_or_duplicate_keys_reject(location, mutation):
    raw = fixture_report()
    part = raw if location == "root" else raw["actual_observations"]
    key = next(iter(part))
    if mutation == "unknown":
        part["fake_approval"] = True
    elif mutation == "missing":
        del part[key]
    text = json.dumps(raw)
    if mutation == "duplicate":
        pair = json.dumps(key) + ": " + json.dumps(part[key])
        text = text.replace(pair, pair + ", " + pair, 1)
    with pytest.raises(ValueError):
        api().validate_harmless_result(text)


@pytest.mark.parametrize("value", ["\ud800", "\udfff", ""])
def test_non_utf8_and_empty_clock_reject(value):
    raw = fixture_report()
    raw["actual_observations"]["clock_domain"] = value
    with pytest.raises(ValueError):
        parse(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("fixture_id", "HF00"),
        ("fixture_id", "HF25"),
        ("fixture_id", "HF1"),
        ("schema_version", "other"),
        ("evidence_cohort_digest", "A" * 64),
        ("outcome", "ACCEPTED"),
        ("reasons", [0]),
        ("reasons", ["x", "x"]),
        ("reasons", "reason"),
        ("runtime_qualified", 0),
    ],
)
def test_wrong_root_scalar_rejects(field, value):
    raw = fixture_report()
    raw[field] = value
    with pytest.raises(ValueError):
        parse(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("guard_active", 1),
        ("trace_complete", 0),
        ("broker_effects_observed", True),
        ("successful_prohibited_handles", True),
        ("successful_prohibited_effects", -1),
        ("successful_prohibited_handles", 2**64),
        ("successful_prohibited_effects", 1.0),
        ("successful_prohibited_handles", 1),
        ("clock_domain", 1),
        ("btf_digest", "bad"),
    ],
)
def test_wrong_observation_scalar_or_inconsistent_pass_rejects(field, value):
    raw = fixture_report()
    raw["actual_observations"][field] = value
    with pytest.raises(ValueError):
        parse(raw)


@pytest.mark.parametrize("outcome", ["REJECTED", "NOT_SUPPORTED", "UNAVAILABLE"])
def test_nonpass_requires_reason_and_preserves_unknowns(outcome):
    raw = fixture_report()
    raw["outcome"] = outcome
    with pytest.raises(ValueError):
        parse(raw)
    raw["reasons"] = ["INCOMPLETE_CAPTURE"]
    raw["actual_observations"]["trace_complete"] = None
    assert parse(raw).outcome == outcome


def test_immutable_defensive_constructors_and_literal_types():
    value = parse()
    reasons = ["INCOMPLETE_CAPTURE"]
    copied = replace(value, outcome="REJECTED", reasons=reasons)
    reasons.clear()
    assert copied.reasons == ("INCOMPLETE_CAPTURE",)
    with pytest.raises(FrozenInstanceError):
        value.actual_observations.guard_active = False
    for key in ("schema_version", "evidence_kind", "fixture_id", "evidence_cohort_digest"):
        with pytest.raises(ValueError):
            replace(value, **{key: UserString(getattr(value, key))})
    with pytest.raises(ValueError):
        replace(value, actual_observations={})
    with pytest.raises(ValueError):
        replace(value.actual_observations, guard_active=1)


@pytest.mark.parametrize("raw", ["null", "[]", "{", "NaN", "Infinity", "-Infinity"])
def test_malformed_or_nonfinite_report_rejects(raw):
    with pytest.raises(ValueError):
        api().validate_harmless_result(raw)


def test_canonical_identity_preserves_unknowns_and_order_independence():
    validation = api()
    raw = fixture_report()
    raw["outcome"] = "UNAVAILABLE"
    raw["reasons"] = ["INCOMPLETE_CAPTURE"]
    digest = validation.result_digest(parse(raw))
    assert digest == validation.result_digest(parse(dict(reversed(list(raw.items())))))
    raw["actual_observations"]["trace_complete"] = None
    assert digest != validation.result_digest(parse(raw))
    assert parse(raw).runtime_accepted is False
