"""Published actual captures must independently reconcile with pinned source bytes."""

import gzip
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from compatibility.containment_guest_collector.validation import capture_digest

ROOT = Path(__file__).resolve().parents[2]


def test_actual_24_case_artifact_and_every_summary_are_recomputed():
    from compatibility.containment_guest_collector.batch import assess_batch

    data = json.loads((ROOT / "docs/evidence/guest_collector_results.json").read_text())
    raw = (ROOT / data["raw_artifact"]["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == data["raw_artifact"]["sha256"]
    decoded = gzip.decompress(raw)
    assert hashlib.sha256(decoded).hexdigest() == data["raw_artifact"]["uncompressed_sha256"]
    cases = assess_batch(decoded.decode(), tuple(f"HF{i:02d}" for i in range(1, 25)))
    assert len(cases) == 24
    assert data["global_successful_prohibited_handles"] is None
    assert data["global_successful_prohibited_effects"] is None
    assert data["gate_a"] == "BLOCKED"
    for case, entry in zip(cases, data["cases"], strict=True):
        assert entry["fixture_id"] == case.capture.fixture_id
        assert entry["capture_digest"] == capture_digest(case.capture)
        assert entry["assessment"] == json.loads(json.dumps(asdict(case.assessment)))
        assert entry["harmless_assertion_failures"] == list(case.harmless_assertion_failures)
        assert not case.assessment.application_authorized
        assert not case.assessment.runtime_qualified
        assert not case.assessment.device_class_qualified


@pytest.mark.parametrize(
    "path",
    [
        "compatibility/containment_guest_collector/guest/build_manifest.json",
        "docs/evidence/guest_collector_sources.json",
        "docs/evidence/guest_collector_results.json",
        "compatibility/containment_guest_collector/evidence/actual-captures.txt.gz",
    ],
)
def test_hash_bound_collector_artifacts_survive_autocrlf_checkout(path):
    result = subprocess.check_output(["git", "check-attr", "text", "--", path], cwd=ROOT, text=True)
    assert result.strip() == f"{path}: text: unset"


def test_published_manifest_hashes_are_exact_bytes():
    data = json.loads((ROOT / "docs/evidence/guest_collector_results.json").read_text())
    for key in ("build_manifest", "source_manifest"):
        assert (
            hashlib.sha256((ROOT / data[key]["path"]).read_bytes()).hexdigest()
            == data[key]["sha256"]
        )
