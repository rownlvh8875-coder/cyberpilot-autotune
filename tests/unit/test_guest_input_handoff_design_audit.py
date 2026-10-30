"""Catch synthetic design/evidence drift without executing any guest or target."""

import copy
import json
from pathlib import Path

import pytest

from tests.audit.guest_input_handoff_examples import CASES
from tests.audit.validate_guest_input_handoff_design import (
    validate,
    validate_cases,
    validate_schema,
    validate_sources,
)

ROOT = Path(__file__).resolve().parents[2]


def document(kind):
    return json.loads((ROOT / f"docs/evidence/guest_input_handoff_design_{kind}.json").read_text())


def test_published_design_is_not_a_runtime_backend():
    report = validate()
    assert report["synthetic_cases"] == len(CASES)
    assert report["synthetic_consistent"] == 6
    assert report["overall"] == "BLOCKED"
    assert report["runtime_producer_implemented"] is False
    assert report["runtime_qualified"] is False
    assert all(v is False for v in report["permissions"].values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_producer_implemented", True),
        ("runtime_qualified", True),
        ("evidence_kind", "OBSERVED_UNTRUSTED"),
        ("scope", "FULL_BUILD_NAMESPACE"),
    ],
)
def test_semantic_schema_cannot_promote_synthetic_design(field, value):
    data = document("schema")
    data[field] = value
    with pytest.raises(ValueError):
        validate_schema(data)


def test_permission_escalation_rejected_individually_from_valid_schema():
    data = document("schema")
    validate_schema(data)
    for permission in data["permissions"]:
        bad = copy.deepcopy(data)
        bad["permissions"][permission] = True
        with pytest.raises(ValueError):
            validate_schema(bad)


@pytest.mark.parametrize(
    "section,event_kind,field,patch",
    [
        ("event_fields", "BIND", "fd", {"type": "SHA256"}),
        ("context_fields", None, "namespace_generation", {"type": "Bool"}),
        ("event_fields", "PREAD_FULL", "offset", {"unit": "ns"}),
        ("event_fields", "PIN", "dev", {"type": []}),
    ],
)
def test_schema_field_type_and_units_are_exact(section, event_kind, field, patch):
    data = document("schema")
    rows = data[section][event_kind] if event_kind else data[section]
    next(row for row in rows if row["field"] == field).update(patch)
    with pytest.raises(ValueError):
        validate_schema(data)


@pytest.mark.parametrize("change", ["missing", "duplicate", "claim_consistent", "wrong_reason"])
def test_published_counterexamples_cannot_be_relabeled(change):
    data = document("cases")
    if change == "missing":
        data["cases"].pop()
    elif change == "duplicate":
        data["cases"][-1] = copy.deepcopy(data["cases"][0])
    elif change == "claim_consistent":
        data["cases"][5]["expected_status"] = "SYNTHETIC_GRAPH_CONSISTENT"
    else:
        data["cases"][5]["expected_reason"] = "CALLER_APPROVED"
    with pytest.raises(ValueError):
        validate_cases(data)


@pytest.mark.parametrize(
    "change", ["revision", "path", "file_sha", "blob_sha", "range_sha", "range_bounds"]
)
def test_exact_git_source_bindings_reject_tampering(change):
    data = document("sources")
    if change == "revision":
        data["base_revision"] = "e" * 40
    elif change == "path":
        data["files"][0]["path"] = "../../escape"
    elif change == "file_sha":
        data["files"][0]["sha256"] = "0" * 64
    elif change == "blob_sha":
        data["files"][0]["git_blob_sha1"] = "0" * 40
    elif change == "range_sha":
        data["files"][0]["ranges"][0]["sha256"] = "0" * 64
    else:
        data["files"][0]["ranges"][0]["start"] = 0
    with pytest.raises(ValueError):
        validate_sources(data)
