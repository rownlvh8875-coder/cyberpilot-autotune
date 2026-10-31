"""Frozen actual-byte/source audit mutations, not synthetic qualification."""

import copy
import importlib
import json

import pytest


def api():
    try:
        return importlib.import_module("tests.guest_tag_snapshot.audit")
    except ModuleNotFoundError:
        pytest.fail("MISSING_TAG_SNAPSHOT_AUDIT")


def test_frozen_seven_actual_captures_replay_without_runtime_authority():
    result = api().validate()
    assert result["actual_cases"] == 7 and result["raw_events"] == 2862
    assert result["snapshot_counts"] == [18, 18, 7, 18, 8, 17, 18]
    assert result["complete_source_joins"] == [18, 18, 7, 18, 8, 17, 17]
    assert result["raw_zero_counts"] == [0, 0, 0, 2, 0, 0, 0]
    assert result["local_failures"] == [0, 1, 362, 0, 0, 1, 1]
    assert result["evidence_class"] == "OBSERVED_UNTRUSTED" and result["status"] == "BLOCKED"
    assert not result["runtime_qualified"] and not result["source_bytes_verified"]
    assert not result["assets_verified"] and not result["tag_publication_qualified"]
    assert not result["target_lifetime_proven"] and not result["source_happens_before_proven"]
    assert result["actual_global_drops"] is result["actual_prohibited_operations"] is None
    assert all(v is False for v in result["permissions"].values())


@pytest.mark.parametrize(
    "mutation",
    [
        "schema",
        "evidence_class",
        "runtime_qualified",
        "build_manifest_sha256",
        "baseline",
        "case",
        "serial",
        "image",
        "missing_capture",
        "reordered_captures",
    ],
)
def test_actual_manifest_drift_rejected(mutation):
    audit = api()
    data = json.loads(audit.ACTUAL.read_bytes())
    if mutation in ("schema", "evidence_class", "runtime_qualified", "build_manifest_sha256"):
        data[mutation] = True
    elif mutation == "baseline":
        data["baseline"]["serial_base64"] = "AA=="
    elif mutation == "case":
        data["captures"][0]["case"] = "UNKNOWN"
    elif mutation == "serial":
        data["captures"][0]["serial_base64"] = "AA=="
    elif mutation == "image":
        data["captures"][0]["image"]["sha256"] = "0" * 64
    elif mutation == "missing_capture":
        data["captures"].pop()
    else:
        data["captures"].reverse()
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


@pytest.mark.parametrize("key", ["kernel", "init", "sources", "patch_chain", "runtime_qualified"])
def test_build_drift_rejected_before_consuming_paths(key):
    audit = api()
    data = json.loads(audit.BUILD.read_bytes())
    data[key] = None
    with pytest.raises(ValueError):
        audit.validate_build(data)


def test_missing_or_wrong_explicit_source_root_rejected(tmp_path):
    audit = api()
    data = json.loads(audit.SOURCES.read_bytes())
    assert audit.validate_sources(data) is False
    with pytest.raises((ValueError, OSError)):
        audit.validate_sources(data, tmp_path)
    bad = copy.deepcopy(data)
    bad["files"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        audit.validate_sources(bad)


def test_repository_input_tampering_rejected(tmp_path, monkeypatch):
    audit = api()
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    with pytest.raises((ValueError, OSError)):
        audit.validate_build(json.loads(audit.BUILD.read_bytes()))
