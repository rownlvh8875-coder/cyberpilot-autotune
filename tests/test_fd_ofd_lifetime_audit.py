"""Strict metadata, published counterexamples, and exact source bytes, not runtime proof."""

import hashlib

import pytest

from tests.audit import validate_fd_ofd_lifetime_design as audit
from tests.audit.fd_ofd_lifetime_examples import catalog
from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, evaluate


def bundle():
    return {
        "schema": "fd-ofd-lifetime-cases-v1",
        "evidence_class": "SYNTHETIC_ONLY",
        "cases": catalog(),
        "permissions": dict(PERMISSIONS),
        "runtime_qualified": False,
    }


def test_published_schema_defines_complete_timing_and_binding_envelope():
    schema = audit.schema_template()
    assert audit.validate_schema(schema) is None
    assert {r["field"] for r in schema["envelope"]} == {
        "seq",
        "time_ns",
        "cpu",
        "cpu_seq",
        "context_digest",
        "kind",
        "data",
    }
    assert next(r for r in schema["envelope"] if r["field"] == "time_ns")["unit"] == "ns"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["resource_limits"].__setitem__("fd_slots", 64.0),
        lambda d: d.__setitem__("runtime_qualified", 0),
        lambda d: d["permissions"].__setitem__("application_authorized", True),
        lambda d: d["events"]["INSTALL"][0].__setitem__("type", "UInt64"),
        lambda d: d["envelope"].pop(),
        lambda d: d["binding_entry"][0].__setitem__("availability", "DEFAULT_ZERO"),
    ],
)
def test_semantic_metadata_drift_not_silently_equivalent(mutate):
    schema = audit.schema_template()
    mutate(schema)
    with pytest.raises(ValueError):
        audit.validate_schema(schema)


def test_catalog_is_simulated_consistency_only():
    assert audit.validate_catalog(bundle()) == (51, 16)
    assert all(evaluate(c["graph"]).status == "BLOCKED" for c in catalog())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["cases"].pop(),
        lambda d: d["cases"][1].__setitem__("case_id", "L001"),
        lambda d: d["cases"][0].__setitem__("expected_consistent", 1),
        lambda d: d["cases"][0]["graph"].__setitem__("evidence_class", "OBSERVED"),
        lambda d: d.__setitem__("runtime_qualified", True),
    ],
)
def test_catalog_cannot_drop_or_relabel_counterexamples(mutate):
    data = bundle()
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_catalog(data)


def test_full_blob_and_exact_range_are_both_bound():
    raw = b"first\nsecond\nthird\n"
    row = {
        "path": "fs/file.c",
        "bytes": 19,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "git_blob_sha1": hashlib.sha1(b"blob 19\0" + raw).hexdigest(),
        "ranges": [
            {
                "claim": "copy",
                "start": 2,
                "end": 2,
                "sha256": hashlib.sha256(b"second\n").hexdigest(),
            }
        ],
    }
    audit.validate_source_record(row, raw)
    with pytest.raises(ValueError):
        audit.validate_source_record(row, raw.replace(b"third", b"THIRD"))
    row["ranges"][0]["start"] = 2.0
    with pytest.raises(ValueError):
        audit.validate_source_record(row, raw)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["authenticated_package"].__setitem__("sha256", "f" * 64),
        lambda d: d["git_files"].__setitem__(0, None),
        lambda d: d["kernel_files"][0].__setitem__("path", ["fs/file.c"]),
    ],
)
def test_source_profile_rejects_tampered_package_and_malformed_rows(monkeypatch, mutate):
    original = audit.json_file
    data = original(audit.PREFIX + "sources.json")
    mutate(data)
    monkeypatch.setattr(
        audit, "json_file", lambda p: data if p == audit.PREFIX + "sources.json" else original(p)
    )
    with pytest.raises(ValueError):
        audit.validate()


def test_published_catalogs_replay_without_runtime_assets():
    report = audit.validate()
    assert report == {
        "synthetic_cases": 51,
        "consistent_models": 16,
        "git_files": 4,
        "kernel_files": 9,
        "kernel_bytes_verified": False,
        "ranges": 28,
        "status": "BLOCKED",
        "runtime_qualified": False,
    }
