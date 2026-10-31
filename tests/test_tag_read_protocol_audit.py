"""Frozen design replay cannot turn assumed premises into actual evidence."""

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def api():
    assert (ROOT / "tests/tag_read_protocol/audit.py").is_file(), "MISSING_TAG_READ_AUDIT"
    return importlib.import_module("tests.tag_read_protocol.audit")


def data(name):
    return json.loads((ROOT / f"docs/evidence/tag_read_protocol_{name}.json").read_bytes())


def test_default_replay_checks_sixty_synthetic_stories_without_runtime_or_actual_record_adapter(
    tmp_path, monkeypatch
):
    module = api()
    monkeypatch.chdir(tmp_path)
    result = module.validate()
    assert (
        result["synthetic_cases"],
        result["consistent_cases"],
        result["inconsistent_cases"],
    ) == (60, 7, 53)
    assert result["source_claims"] == 10 and result["retained_source_obligations"] == 13
    assert result["source_reference_evidence_class"] == "STATIC_SOURCE_AUDIT_ONLY"
    assert result["evidence_class"] == "SYNTHETIC_ONLY" and result["status"] == "BLOCKED"
    assert result["external_source_bytes_verified"] is False
    assert result["actual_records_passed_to_model"] is False
    assert result["actual_capture_adapter_implemented"] is False
    assert result["source_happens_before_proven"] is False
    assert result["target_lifetime_proven"] is result["tag_publication_qualified"] is False
    assert result["runtime_producer_implemented"] is result["runtime_qualified"] is False
    assert result["actual_global_drops"] is result["actual_prohibited_operations"] is None
    assert all(v is False for v in result["permissions"].values())


def test_schema_matches_model_sections_and_is_order_independent():
    raw = data("schema")
    assert api().validate_schema(dict(reversed(list(raw.items())))) is None


@pytest.mark.parametrize("change", ["version", "field", "stage", "qualification", "permission"])
def test_changed_semantics_or_injected_authority_cannot_use_the_frozen_schema(change):
    raw = data("schema")
    if change == "version":
        raw["model_version"] = "CPBv1"
    elif change == "field":
        raw["sections"]["reader"].pop()
    elif change == "stage":
        raw["sections"]["graph"][0]["stage"] = "ACTUAL_EFFECT_ORDER"
    elif change == "qualification":
        raw["qualifications"]["source_happens_before_proven"] = True
    else:
        raw["permissions"]["application_authorized"] = True
    with pytest.raises(ValueError, match="SEMANTIC_SCHEMA_DRIFT"):
        api().validate_schema(raw)


@pytest.mark.parametrize("change", ["base", "digest", "path", "claim", "evidence"])
def test_changed_source_cohort_or_provenance_is_rejected_before_source_reads(change):
    raw = data("sources")
    if change == "base":
        raw["base_revision"] = "0" * 40
    elif change == "digest":
        raw["source_catalog_digest"] = "0" * 64
    elif change == "path":
        raw["repository_files"][0]["path"] = "../outside"
    elif change == "claim":
        raw["claims"][0] = "NONEXISTENT_WITNESS"
    else:
        raw["source_evidence_class"] = "QUALIFIED_RUNTIME"
    with pytest.raises(ValueError, match="SOURCE_REFERENCES_DRIFT"):
        api().validate_sources(raw)


def test_repository_byte_change_is_not_hidden_by_unchanged_reference_metadata(
    tmp_path, monkeypatch
):
    module = api()
    raw = data("sources")
    for row in raw["repository_files"]:
        target = tmp_path / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / row["path"]).read_bytes())
    changed = tmp_path / raw["repository_files"][0]["path"]
    changed.write_bytes(changed.read_bytes() + b"\n")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="SOURCE_REFERENCE_BYTES_CHANGED"):
        module.validate_sources(raw)


@pytest.mark.parametrize(
    "change", ["expected", "actual_class", "read_before_ref", "missing", "authority"]
)
def test_rehashed_case_edits_cannot_replace_independent_literal_expected_stories(change):
    raw = data("cases")
    if change == "expected":
        raw["cases"][0]["expected_consistent"] = False
    elif change == "actual_class":
        raw["cases"][0]["payload"]["evidence_class"] = "OBSERVED_UNTRUSTED"
    elif change == "read_before_ref":
        raw["cases"][3]["payload"]["graph"]["edges"].remove(["ref_begin", "read_begin"])
    elif change == "missing":
        raw["cases"].pop()
    else:
        raw["permissions"]["candidate_generation_allowed"] = True
    with pytest.raises(ValueError, match="SYNTHETIC_CATALOG_DRIFT"):
        api().validate_cases(raw)


@pytest.mark.parametrize("raw", [b'{"x":NaN}', b'{"x":1,"x":2}'])
def test_default_pipeline_rejects_nonfinite_or_duplicate_case_manifest(raw, tmp_path, monkeypatch):
    module = api()
    path = tmp_path / "cases.json"
    path.write_bytes(raw)
    monkeypatch.setattr(module, "CASES", path)
    with pytest.raises(ValueError):
        module.validate()


def test_cli_outputs_only_design_and_source_reference_results(monkeypatch, capsys):
    module = api()
    monkeypatch.setattr(sys, "argv", ["tag-read-protocol"])
    assert module.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["synthetic_cases"] == 60
    assert result["evidence_class"] == "SYNTHETIC_ONLY" and result["runtime_qualified"] is False
