"""Published partial records are tied to the checked actual guest log, never PASS."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from compatibility.containment_backend_harmless.host_cases import (
    FIXTURES,
    check_case,
    parse_guest_log,
)
from compatibility.containment_backend_harmless.validation import (
    result_digest,
    validate_harmless_result,
)

ROOT = Path(__file__).resolve().parents[2]


def evidence():
    return json.loads(
        (ROOT / "docs/evidence/containment_backend_harmless_results.json").read_text()
    )


def test_published_results_have_real_measurements_but_no_complete_trace_claim():
    import hashlib

    data = evidence()
    raw = (ROOT / data["actual_log"]["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == data["actual_log"]["sha256"]
    records = parse_guest_log(raw.decode(), FIXTURES)
    assert all(not check_case(record) for record in records)
    assert list(FIXTURES) == [record["fixture_id"] for record in data["fixtures"]]
    for raw_record, record in zip(records, data["fixtures"], strict=True):
        result = validate_harmless_result(json.dumps(record["result"]))
        assert record["result_digest"] == result_digest(result)
        assert record["actual_measurements"] == raw_record["measurements"]
        assert record["assertion_failures"] == []
        assert result.outcome != "PASS_NAMED_HARMLESS_FIXTURE"
        assert result.actual_observations.trace_complete is None
        assert result.actual_observations.successful_prohibited_handles is None
        assert result.actual_observations.successful_prohibited_effects is None
        assert asdict(result)["runtime_qualified"] is False


@pytest.mark.parametrize("index", range(24))
def test_every_named_case_rejects_missing_measurements(index):
    record = evidence()["fixtures"][index]
    assert check_case({"fixture_id": record["fixture_id"], "measurements": {}})


def test_published_source_ranges_and_manifest_identity():
    import hashlib

    data = evidence()
    for key in ("build_manifest", "source_manifest"):
        assert (
            hashlib.sha256((ROOT / data[key]["path"]).read_bytes()).hexdigest()
            == data[key]["sha256"]
        )
    manifest = json.loads((ROOT / data["source_manifest"]["path"]).read_text())
    assert manifest["package_version"] == "6.12.113-1"
    assert len(manifest["files"]) >= 7
    assert manifest["runtime_qualified"] is False
