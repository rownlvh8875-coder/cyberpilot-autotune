"""Frozen source/build bytes are not execution, lifetime or authority evidence."""

import copy
import json
import subprocess
import sys

import pytest

from tests.guest_epoch_u64.audit import (
    BUILD,
    SOURCES,
    load_catalog,
    validate,
    validate_build,
    validate_sources,
)


def test_portable_audit_keeps_all_runtime_and_actual_capture_claims_blocked():
    result = validate()
    assert result["status"] == "BLOCKED"
    assert result["source_bytes_verified"] is result["build_assets_bytes_verified"] is False
    assert result["runtime_qualified"] is result["build_input_closure_qualified"] is False
    assert result["actual_epoch_loss"] is result["actual_global_drops"] is None
    assert result["actual_v2_capture_available"] is False
    assert result["actual_guest_executions_this_task"] == 0
    assert all(value is False for value in result["permissions"].values())


@pytest.mark.parametrize("field", ["base_revision", "schema", "kernel_files", "patch_chain"])
def test_source_catalog_changes_reject_before_path_derived_reads(field):
    data = copy.deepcopy(load_catalog(SOURCES))
    data[field] = "tampered"
    with pytest.raises(ValueError, match="SOURCE_CATALOG_DRIFT"):
        validate_sources(data)


@pytest.mark.parametrize("field", ["source_catalog_digest", "assets", "runtime_qualified"])
def test_build_catalog_changes_cannot_promote_or_rebind_a_build(field):
    data = copy.deepcopy(load_catalog(BUILD))
    data[field] = True
    with pytest.raises(ValueError, match="BUILD_CATALOG_DRIFT"):
        validate_build(data)


def test_wrong_external_roots_reject_instead_of_claiming_verified_bytes(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        validate(source_root=tmp_path)
    with pytest.raises((ValueError, FileNotFoundError)):
        validate(assets_root=tmp_path)


def test_cli_default_does_not_assert_external_bytes_or_execution():
    result = subprocess.run(
        [sys.executable, "-m", "tests.guest_epoch_u64.audit"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["status"] == "BLOCKED" and report["actual_v2_capture_available"] is False
