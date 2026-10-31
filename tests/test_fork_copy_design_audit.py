"""Finite synthetic/source manifest checks, never a kernel capture or inventory."""

import importlib
import importlib.util

import pytest


def api():
    assert importlib.util.find_spec("tests.fork_copy_design.audit") is not None, (
        "missing design audit"
    )
    return importlib.import_module("tests.fork_copy_design.audit")


def test_offline_design_audit_keeps_synthetic_counts_and_producer_absence_explicit():
    report = api().validate()
    assert report["synthetic_cases"] == 18
    assert report["synthetic_consistent_cases"] == 3
    assert report["synthetic_copy_orders"] == 6 and report["synthetic_copies_without_cut"] == 1
    assert report["proposed_records_per_copy"] == 196 and report["existing_buffer_capacity"] == 128
    assert report["kernel_bytes_verified"] is False
    assert report["runtime_producer_implemented"] is False and report["atomic_cut_proven"] is False
    assert report["actual_copy_records"] is None and report["actual_global_drops"] is None
    assert report["status"] == "BLOCKED" and all(v is False for v in report["permissions"].values())


@pytest.mark.parametrize(
    ("file", "field", "value"),
    [
        ("SCHEMA", "evidence_class", "OBSERVED_UNTRUSTED"),
        ("SCHEMA", "proposed_records_per_copy", 128),
        ("SCHEMA", "atomic_cut_proven", True),
        ("SCHEMA", "runtime_producer_implemented", True),
        ("SOURCES", "base_revision", "0" * 40),
        ("SOURCES", "source_archive_sha256", "0" * 64),
        ("CASES", "evidence_class", "OBSERVED_UNTRUSTED"),
        ("CASES", "runtime_producer_implemented", True),
    ],
)
def test_cohort_metadata_and_authority_cannot_be_promoted(file, field, value):
    audit = api()
    data = audit.load(getattr(audit, file))
    data[field] = value
    validator = {
        "SCHEMA": audit.validate_schema,
        "SOURCES": audit.validate_sources,
        "CASES": audit.validate_cases,
    }[file]
    with pytest.raises(ValueError):
        validator(data)


def test_source_range_and_path_substitution_rejected_before_optional_file_read():
    audit = api()
    data = audit.load(audit.SOURCES)
    data["patched_files"][0]["ranges"][0]["start"] += 1
    with pytest.raises(ValueError):
        audit.validate_sources(data)
    data = audit.load(audit.SOURCES)
    data["repository_files"][0]["path"] = "../../outside"
    with pytest.raises(ValueError):
        audit.validate_sources(data)


def test_schema_cannot_erase_cloexec_or_pairing_stage_meanings():
    audit = api()
    data = audit.load(audit.SCHEMA)
    data["stages"].pop()
    with pytest.raises(ValueError):
        audit.validate_schema(data)


def test_case_outcome_or_payload_cannot_be_silently_reclassified():
    audit = api()
    data = audit.load(audit.CASES)
    data["cases"][0]["expected_consistent"] = False
    with pytest.raises(ValueError):
        audit.validate_cases(data)
    data = audit.load(audit.CASES)
    data["cases"][0]["payload"]["events"][19]["ofd"] = 99
    with pytest.raises(ValueError):
        audit.validate_cases(data)


def test_checked_source_bytes_cannot_be_substituted_by_an_empty_checkout(tmp_path):
    audit = api()
    with pytest.raises(FileNotFoundError):
        audit.validate(tmp_path)
