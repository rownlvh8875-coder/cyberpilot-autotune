"""Read-only manifest boundaries; synthetic consistency must not become authority."""

import copy
import json

import pytest

from tests.audit import validate_kernel_lifetime_feasibility as audit


def test_source_absence_never_reports_kernel_bytes_verified():
    report = audit.validate()
    assert report["kernel_bytes_verified"] is False
    assert report["current_profile"] == "NO_GO_CURRENT_PROFILE"
    assert report["instrumented_design"] == "CONDITIONAL_DESIGN_ONLY"
    assert report["runtime_qualified"] is False
    assert report["actual_dropped_events"] is None
    assert all(v is False for v in report["permissions"].values())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["files"][0].__setitem__("sha256", "0" * 64),
        lambda d: d["files"][0]["ranges"][0].__setitem__("start", 1.0),
        lambda d: d["files"].pop(),
        lambda d: d.__setitem__("source_archive_sha256", "0" * 64),
        lambda d: d.__setitem__("base_revision", "0" * 40),
        lambda d: d["files"][0].__setitem__("path", "../outside"),
    ],
)
def test_source_reference_metadata_cannot_drift_without_a_new_pin(mutate):
    data = audit.load(audit.SOURCES)
    mutate(data)
    with pytest.raises(ValueError, match="SOURCE_MANIFEST_DRIFT"):
        audit.audit_sources(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.__setitem__("runtime_qualified", True),
        lambda d: d.__setitem__("actual_dropped_events", 0),
        lambda d: d["permissions"].__setitem__("application_authorized", 1),
        lambda d: d["permissions"].__setitem__("candidate_generation_allowed", True),
        lambda d: d["rows"][0].__setitem__("current_source", "GO"),
        lambda d: d["rows"][0].__setitem__("instrumented_design", "QUALIFIED"),
        lambda d: d["rows"][0].__setitem__("claims", []),
        lambda d: d["rows"][0].__setitem__("claims", ["NONEXISTENT"]),
        lambda d: d["rows"][0].__setitem__("claims", ["RING_DOC"]),
        lambda d: d["rows"].pop(),
        lambda d: d["rows"].append(copy.deepcopy(d["rows"][0])),
        lambda d: d["rows"][0].__setitem__("blockers", []),
        lambda d: d["rows"][0].__setitem__("blockers", [False]),
    ],
)
def test_matrix_cannot_erase_evidence_gaps_or_promote_design(mutate):
    claims = audit.audit_sources(audit.load(audit.SOURCES))
    data = audit.load(audit.MATRIX)
    mutate(data)
    with pytest.raises(ValueError):
        audit.audit_matrix(data, claims)


def test_json_input_rejects_duplicate_fields_and_nonfinite_values(tmp_path):
    path = tmp_path / "bad.json"
    for raw in ('{"status":"BLOCKED","status":"GO"}', '{"count":NaN}'):
        path.write_text(raw)
        with pytest.raises(ValueError):
            audit.load(path)


def test_source_byte_and_range_change_is_not_hidden_by_valid_metadata(tmp_path):
    data = audit.load(audit.SOURCES)
    first = data["files"][0]
    path = tmp_path / first["path"]
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not the pinned kernel file\n")
    with pytest.raises(ValueError, match="SOURCE_BLOB_DRIFT"):
        audit.audit_sources(data, tmp_path)


def test_published_matrix_is_json_roundtrippable_without_authority():
    data = json.loads(json.dumps(audit.load(audit.MATRIX)))
    claims = audit.audit_sources(audit.load(audit.SOURCES))
    assert audit.audit_matrix(data, claims) == 9
