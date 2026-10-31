"""Design catalogs are frozen synthetic premises,not upgradeable actual evidence."""

import importlib
import importlib.util

import pytest


def api():
    assert importlib.util.find_spec("tests.inherited_ofd_design.audit") is not None, "missing audit"
    return importlib.import_module("tests.inherited_ofd_design.audit")


def test_catalog_source_schema_and_no_runtime_authority_are_audited_offline():
    result = api().validate()
    assert result["synthetic_cases"] >= 40 and result["consistent_cases"] >= 4
    assert result["source_bytes_verified"] is False
    assert result["evidence_class"] == "SYNTHETIC_ONLY" and result["status"] == "BLOCKED"
    assert not result["runtime_producer_implemented"] and not result["allocation_history_complete"]
    assert result["actual_global_drops"] is None
    assert all(v is False for v in result["permissions"].values())


@pytest.mark.parametrize("which", ["schema", "sources", "cases"])
def test_manifest_drift_is_rejected_without_external_source_or_execution(which):
    audit = api()
    path = {"schema": audit.SCHEMA, "sources": audit.SOURCES, "cases": audit.CASES}[which]
    data = audit.load(path)
    data["evidence_class"] = "OBSERVED_UNTRUSTED"
    with pytest.raises(ValueError):
        {
            "schema": audit.validate_schema,
            "sources": audit.validate_sources,
            "cases": audit.validate_cases,
        }[which](data)


def test_catalog_expected_outcome_cannot_be_changed_into_observed_or_birth_qualification():
    audit = api()
    data = audit.load(audit.CASES)
    data["cases"][0]["expected_consistent"] = False
    with pytest.raises(ValueError):
        audit.validate_cases(data)


def test_source_range_or_path_drift_rejected_even_without_prepared_checkout():
    audit = api()
    data = audit.load(audit.SOURCES)
    data["kernel_files"][0]["ranges"][0]["start"] += 1
    with pytest.raises(ValueError):
        audit.validate_sources(data)
