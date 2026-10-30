"""Replay real committed serial bytes; normal pytest never starts a guest."""

import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from tests.fixtures.guest_consumption import module

ROOT = Path(__file__).resolve().parents[2]


def published():
    path = ROOT / "compatibility/guest_consumption/evidence/actual-captures.json.gz"
    assert path.is_file(), "actual seven-case evidence missing"
    return json.loads(gzip.decompress(path.read_bytes()))


@pytest.mark.parametrize("case", ["CP01", "CP02", "CP03", "CP04", "CP05", "CP06", "CP07"])
def test_actual_captures_replay_literal_fixture_checks_without_any_guest(case):
    data = published()
    row = next(r for r in data["captures"] if r["case"] == case)
    raw = base64.b64decode(row["serial_base64"], validate=True)
    assert hashlib.sha256(raw).hexdigest() == row["sha256"] and len(raw) == row["bytes"]
    observation = module("vm_runner").observation_from_log(
        raw.decode(), data["binary"]["sha256"], data["binary"]["bytes"]
    )
    assert module("checks").check_case(observation, case) == ()
    assert observation.overall_status == "BLOCKED"
    assert observation.application_authorized is False and observation.promotion_authorized is False
    assert observation.trace_window_complete is (case not in ("CP05", "CP06"))


def test_published_measurements_are_exact_replays_not_producer_success_flags():
    data = published()
    result = json.loads((ROOT / "docs/evidence/guest_consumption_results.json").read_text())
    assert result["overall_status"] == "BLOCKED"
    assert result["actual_guests"] == 7 and result["fixture_checks_matched"] == 7
    assert result["trace_windows_complete"] == 5 and result["explicitly_incomplete_windows"] == 2
    assert (
        result["successful_prohibited_handles"] is None
        and result["successful_prohibited_effects"] is None
    )
    for case in result["cases"]:
        row = next(r for r in data["captures"] if r["case"] == case["case"])
        obs = module("vm_runner").observation_from_log(
            base64.b64decode(row["serial_base64"]).decode(),
            data["binary"]["sha256"],
            data["binary"]["bytes"],
        )
        assert case["capture_digest"] == module("wire").capture_digest(obs.capture)
        assert case["records"] == len(obs.capture.events)
        assert case["uses"] == len(obs.receipt.uses)
        assert case["profile_reasons"] == list(obs.profile_reasons)
    assert all(value is False for value in result["permissions"].values())


def test_current_source_manifest_and_semantic_ranges_audit_without_prepared_assets():
    assert importlib.util.find_spec("tests.audit.validate_guest_consumption") is not None
    from tests.audit.validate_guest_consumption import validate

    report = validate()
    assert report["local_sources_verified"] is True
    assert report["kernel_source_bytes_verified"] is False
    assert report["runtime_qualified"] is False
