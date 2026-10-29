"""Offline metadata consistency and independently read source hash checks."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def evidence():
    return tuple(
        json.loads((ROOT / "docs/evidence" / name).read_text(encoding="utf-8"))
        for name in (
            "steering_parameter_knowledge_sources.json",
            "steering_parameter_catalog.json",
        )
    )


def test_catalog_projection_matches_compiled_immutable_descriptors():
    from tests.audit.validate_steering_knowledge import validate

    assert validate(*evidence()) == {"files": 39, "claims": 78, "descriptors": 27}


@pytest.mark.parametrize(
    "mutation",
    [
        "pin",
        "range_hash",
        "source_hash",
        "unit",
        "scale",
        "revision",
        "authority",
        "role",
        "duplicate",
        "compatibility",
    ],
)
def test_altered_knowledge_manifest_rejects(mutation):
    from tests.audit.validate_steering_knowledge import validate

    sources, catalog = copy.deepcopy(evidence())
    if mutation == "pin":
        sources["pins"]["runtime"] = "carrot-wip"
    elif mutation == "range_hash":
        sources["entries"][0]["source_range_sha256"] = "0" * 64
    elif mutation == "source_hash":
        sources["files"][0]["sha256"] = "0" * 64
    elif mutation in {"unit", "scale", "revision"}:
        key = {"unit": "canonical_unit", "scale": "storage_scale", "revision": "source_revision"}[
            mutation
        ]
        catalog["entries"][0]["descriptor"][key] = "changed"
    elif mutation == "authority":
        catalog["application_registry"] = True
    elif mutation == "role":
        sources["entries"][0]["source_role"] = "runtime"
    elif mutation == "duplicate":
        sources["files"].append(sources["files"][0])
    else:
        catalog["entries"][0]["compatibility_verdict"] = "SEMANTICALLY_EQUIVALENT"
    with pytest.raises(ValueError):
        validate(sources, catalog)


def test_hash_check_uses_exact_blob_bytes_and_lf_inclusive_line_ranges():
    from tests.audit.validate_steering_knowledge import verify_blob

    data = b"synthetic first\nsynthetic second\n"
    file = {
        "git_blob_sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "line_count": 2,
    }
    ranges = [
        {
            "range_start": 2,
            "range_end": 2,
            "source_range_sha256": hashlib.sha256(b"synthetic second\n").hexdigest(),
        }
    ]
    verify_blob(file, ranges, data)
    with pytest.raises(ValueError):
        verify_blob(file, ranges, data + b"changed\n")
    with pytest.raises(ValueError):
        verify_blob(file, [ranges[0] | {"source_range_sha256": "0" * 64}], data)
