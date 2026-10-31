"""Exercise frozen fixture and source checks without elevating their evidence."""

import copy
import json
import subprocess
import sys

import pytest

from tests.epoch_encoding_design.audit import CASES, load_catalog, validate, validate_cases


def test_frozen_cases_cover_uint64_and_detect_narrowing_without_qualification():
    result = validate()
    assert result["boundary_cases"] == 12 and result["mismatch_cases"] == 6
    assert result["evidence_class"] == "SYNTHETIC_ONLY" and result["status"] == "BLOCKED"
    assert result["external_source_bytes_verified"] is False
    assert result["future_producer_implemented"] is False
    assert result["source_interpretations_machine_proven"] is False
    assert result["runtime_qualified"] is False and result["type_fidelity_qualified"] is False
    assert result["actual_epoch_loss"] is result["actual_global_drops"] is None
    assert result["future_producer_revision"] is None
    assert all(value is False for value in result["permissions"].values())


@pytest.mark.parametrize("change", ["number", "value", "missing", "extra", "schema"])
def test_altered_case_catalog_is_rejected_before_it_can_be_used(change):
    data = copy.deepcopy(load_catalog(CASES))
    if change == "number":
        data["boundaries"][0] = 0
    elif change == "value":
        data["boundaries"][0] = "1"
    elif change == "missing":
        data["boundaries"].pop()
    elif change == "extra":
        data["runtime_qualified"] = True
    else:
        data["schema"] = "CPRv2"
    with pytest.raises(ValueError, match="CASE_CATALOG_DRIFT"):
        validate_cases(data)


def test_default_cli_only_reports_a_synthetic_blocked_design():
    completed = subprocess.run(
        [sys.executable, "-m", "tests.epoch_encoding_design.audit"],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "BLOCKED" and result["evidence_class"] == "SYNTHETIC_ONLY"
    assert not result["external_source_bytes_verified"]


def test_wrong_source_root_cannot_be_mistaken_for_a_verified_binary(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        validate(tmp_path)
