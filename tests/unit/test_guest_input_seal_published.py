"""Catch fabricated/partial capture sets and mismatched source cohorts."""

import copy
import gzip
import json
from pathlib import Path

import pytest

from tests.audit.validate_guest_input_seal import validate, validate_evidence


def test_eight_committed_guest_diagnostics():
    report = validate()
    assert report["actual_capture_replays"] == 8
    assert report["scoped_object_seal_observations"] == 4
    assert report["runtime_qualified"] is False
    assert report["kernel_source_bytes_verified"] is False


def test_incomplete_capture_bundle_rejected():
    with pytest.raises(ValueError):
        validate_evidence({"captures": []}, {}, b"")


@pytest.mark.parametrize(
    "change",
    [
        "qualified",
        "binary",
        "source_manifest",
        "duplicate",
        "bytes",
        "digest",
        "wrong_case",
        "shape",
    ],
)
def test_complete_capture_bundle_tampering_rejected(change):
    root = Path(__file__).resolve().parents[2] / "compatibility/guest_input_seal"
    raw = (root / "guest/build_manifest.json").read_bytes()
    manifest = json.loads(raw)
    evidence = copy.deepcopy(
        json.loads(gzip.decompress((root / "evidence/actual-captures.json.gz").read_bytes()))
    )
    if change == "qualified":
        evidence["runtime_qualified"] = True
    elif change == "binary":
        evidence["binary"]["sha256"] = "0" * 64
    elif change == "source_manifest":
        evidence["capture_source_manifest_sha256"] = "0" * 64
    elif change == "duplicate":
        evidence["captures"][-1] = copy.deepcopy(evidence["captures"][0])
    elif change == "bytes":
        evidence["captures"][0]["bytes"] += 1
    elif change == "digest":
        evidence["captures"][0]["sha256"] = "0" * 64
    elif change == "wrong_case":
        evidence["captures"][0]["case"] = "IS02"
    else:
        evidence["captures"][0]["unknown"] = True
    with pytest.raises(ValueError):
        validate_evidence(evidence, manifest, raw)
