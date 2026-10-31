"""Run the byte/citation auditor against controlled data,not implementation text."""

import base64
import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ROOT / "docs/evidence"


def api():
    assert (ROOT / "tests/bootstrap_tag_audit/audit.py").is_file(), "MISSING_SOURCE_BYTE_AUDIT"
    return importlib.import_module("tests.bootstrap_tag_audit.audit")


def data(name):
    return json.loads((PREFIX / f"bootstrap_tag_initialization_{name}.json").read_bytes())


def excerpt(raw=b"x\n", start=1):
    return dict(
        claim="UNIT_SOURCE",
        start=start,
        end=start + len(raw.splitlines()) - 1,
        sha256=hashlib.sha256(raw).hexdigest(),
        source_base64=base64.b64encode(raw).decode(),
    )


def source(raw=b"x\n"):
    return dict(
        path="unit.c",
        bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        git_blob_sha1=hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        ranges=[excerpt(raw)],
    )


def test_default_offline_audit_distinguishes_embedded_integrity_from_external_and_runtime_proof(
    tmp_path, monkeypatch
):
    module = api()
    monkeypatch.chdir(tmp_path)
    result = module.validate()
    assert result["subjects"] == 5 and result["open_obligations"] == 13
    assert result["source_files"] == {"pristine": 9, "patched": 11}
    assert result["embedded_source_ranges"] == 33
    assert result["embedded_range_hashes_verified"] is True
    assert result["external_source_bytes_verified"] is False
    assert result["source_interpretations_machine_proven"] is False
    assert result["actual_runtime_executions_this_task"] == 0
    assert result["prior_observations_reclassified"] is False
    assert result["evidence_class"] == "STATIC_SOURCE_AUDIT_ONLY" and result["status"] == "BLOCKED"
    assert result["actual_global_drops"] is result["actual_prohibited_operations"] is None
    assert all(v is False for v in result["permissions"].values())
    assert all(result[k] is False for k in data("result")["qualification"])


def test_canonical_field_order_does_not_change_source_catalog_identity():
    raw = data("sources")
    assert len(api().validate_sources(dict(reversed(list(raw.items()))))) == 33


@pytest.mark.parametrize("change", ["base", "path", "blob", "range", "remove", "duplicate"])
def test_rehashed_or_well_formed_source_manifest_changes_cannot_switch_the_frozen_cohort(change):
    rows = data("sources")
    if change == "base":
        rows["base_revision"] = "0" * 40
    elif change == "path":
        rows["patched_files"][0]["path"] = "../outside.c"
    elif change == "blob":
        rows["patched_files"][0]["git_blob_sha1"] = "0" * 40
    elif change == "range":
        span = rows["patched_files"][0]["ranges"][0]
        altered = base64.b64decode(span["source_base64"]).replace(b"src", b"bad")
        span["source_base64"] = base64.b64encode(altered).decode()
        span["sha256"] = hashlib.sha256(altered).hexdigest()
    elif change == "remove":
        rows["patched_files"].pop()
    else:
        rows["patched_files"].append(copy.deepcopy(rows["patched_files"][0]))
    with pytest.raises(ValueError, match="SOURCE_CATALOG_DRIFT"):
        api().validate_sources(rows)


@pytest.mark.parametrize(
    "field", ["permissions", "qualification", "source_catalog_digest", "status"]
)
def test_changed_result_cannot_authorize_or_claim_unbound_source_proof(field):
    payload = data("result")
    if field in ("permissions", "qualification"):
        payload[field]["runtime_qualified"] = True
    else:
        payload[field] = "QUALIFIED"
    with pytest.raises(ValueError, match="RESULT_CATALOG_DRIFT"):
        api().validate_result(payload, frozenset())


@pytest.mark.parametrize("side", ["pristine", "patched"])
def test_one_external_source_root_does_not_silently_become_full_source_verification(side, tmp_path):
    roots = (tmp_path, None) if side == "pristine" else (None, tmp_path)
    with pytest.raises(ValueError, match="BOTH_SOURCE_ROOTS_REQUIRED"):
        api().validate_sources(data("sources"), *roots)


def test_external_byte_checker_verifies_blob_and_excerpt_against_real_file_bytes(tmp_path):
    module = api()
    (tmp_path / "unit.c").write_bytes(b"x\n")
    assert module.verify_source_file(tmp_path, source()) is None
    pristine = source()
    del pristine["ranges"]
    assert module.verify_source_file(tmp_path, pristine) is None


@pytest.mark.parametrize("change", ["file", "size", "bool_size", "blob", "range", "empty_ranges"])
def test_external_source_or_metadata_drift_never_counts_as_verified(change, tmp_path):
    module = api()
    (tmp_path / "unit.c").write_bytes(b"x\n")
    row = source()
    if change == "file":
        (tmp_path / "unit.c").write_bytes(b"z\n")
    elif change == "size":
        row["bytes"] = 2.0
    elif change == "bool_size":
        row["bytes"] = True
    elif change == "blob":
        row["git_blob_sha1"] = "0" * 40
    elif change == "range":
        row["ranges"] = [excerpt(b"z\n")]
    else:
        row["ranges"] = []
    with pytest.raises(ValueError):
        module.verify_source_file(tmp_path, row)


@pytest.mark.parametrize("path", ["../outside.c", "/outside.c", "C:outside.c", "a\\b.c", "./x.c"])
def test_standalone_source_checker_rejects_escaping_or_noncanonical_paths_before_open(
    path, tmp_path
):
    row = source()
    row["path"] = path
    with pytest.raises(ValueError, match="RELATIVE_SOURCE_PATH_REQUIRED"):
        api().verify_source_file(tmp_path, row)


@pytest.mark.parametrize(
    "change", ["encoding", "hash", "start", "bool", "end", "line_count", "extra"]
)
def test_embedded_excerpt_integrity_and_exact_line_coordinates_are_required(change):
    module = api()
    span = excerpt()
    if change == "encoding":
        span["source_base64"] = "!invalid!"
    elif change == "hash":
        span["sha256"] = "0" * 64
    elif change == "start":
        span["start"] = 0
    elif change == "bool":
        span["start"] = True
    elif change == "end":
        span["end"] = 1.0
    elif change == "line_count":
        span["end"] = 2
    else:
        span["runtime_qualified"] = True
    with pytest.raises(ValueError):
        module.verify_excerpt(span)


@pytest.mark.parametrize("raw", [b'{"x":NaN}', b'{"x":1,"x":2}'])
def test_default_pipeline_rejects_nonfinite_or_duplicate_manifest_input(raw, tmp_path, monkeypatch):
    module = api()
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    monkeypatch.setattr(module, "SOURCES", path)
    with pytest.raises(ValueError):
        module.validate()


def test_cli_reports_static_scope_only(monkeypatch, capsys):
    module = api()
    monkeypatch.setattr(sys, "argv", ["bootstrap-tag-audit"])
    assert module.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["embedded_source_ranges"] == 33 and result["runtime_qualified"] is False
