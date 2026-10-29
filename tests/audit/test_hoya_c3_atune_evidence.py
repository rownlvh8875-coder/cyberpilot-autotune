"""Integrity and scope tests for a source-only architecture audit, without network."""

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def evidence():
    directory = ROOT / "docs/evidence"
    return tuple(
        json.loads((directory / name).read_text(encoding="utf-8"))
        for name in ("hoya_c3_atune_sources.json", "hoya_c3_atune_features.json")
    )


def test_hoya_audit_evidence_is_complete_and_consistent():
    from tests.audit.validate_hoya_c3_atune import validate

    sources, features = evidence()
    result = validate(sources, features)
    assert result["episodes"] == 8
    assert result["providers"] == 6
    assert result["application_authority"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "pin",
        "range",
        "duplicate_id",
        "claim",
        "threshold",
        "apply",
        "parameter",
        "score",
        "advisory",
        "network",
        "fingerprint",
        "unsafe_adoption",
        "catalog",
        "cause",
    ],
)
def test_invalid_or_unsafe_audit_evidence_rejects(mutation):
    from tests.audit.validate_hoya_c3_atune import validate

    sources, features = copy.deepcopy(evidence())
    if mutation == "pin":
        sources["pins"]["pr9_head"] = "0" * 40
    elif mutation == "range":
        sources["files"][0]["ranges"][0]["end"] = 10**9
    elif mutation == "duplicate_id":
        sources["files"].append(copy.deepcopy(sources["files"][0]))
    elif mutation == "claim":
        features["adoption"][0]["evidence"] = ["missing-evidence"]
    elif mutation == "threshold":
        features["episodes"][0]["threshold_role"] = "VEHICLE_SAFETY_BOUND"
    elif mutation == "apply":
        features["application_architecture"] = "ADOPT"
    elif mutation == "parameter":
        features["parameters"].pop()
    elif mutation == "score":
        features["scores"][0]["risk"] = 6
    elif mutation == "advisory":
        features["advisory_authority"] = "AUTHORIZED"
    elif mutation == "network":
        features["external_ai"] = "AUTHORIZED"
    elif mutation == "fingerprint":
        features["runtime_fingerprint"] = "CONFIRMED"
    elif mutation == "unsafe_adoption":
        next(x for x in features["adoption"] if x["concept"] == "Apply endpoint")["decision"] = (
            "ADOPT"
        )
    elif mutation == "catalog":
        features["additional_catalog_parameters"].pop()
    else:
        next(x for x in features["episodes"] if x["name"] == "driver_steer_override")[
            "observed_fact"
        ] = "DRIVER_DISSATISFACTION"
    with pytest.raises(ValueError):
        validate(sources, features)


def test_reference_hash_verification_detects_source_or_range_mutation():
    import hashlib

    from tests.audit.validate_hoya_c3_atune import verify_blob

    data = b"synthetic audit line\nsecond line\n"
    item = {
        "blob_sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "line_count": 2,
        "ranges": [{"start": 2, "end": 2, "sha256": hashlib.sha256(b"second line\n").hexdigest()}],
    }
    verify_blob(item, data)
    with pytest.raises(ValueError):
        verify_blob(item, data + b"changed\n")
    changed = copy.deepcopy(item)
    changed["ranges"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        verify_blob(changed, data)


def test_inventory_distinguishes_unavailable_defaults_and_never_executes_sources():
    from tests.audit.validate_hoya_c3_atune import source_inventory

    synthetic = b"""raise RuntimeError('must never run')
getattr(sample, 'zero', 0.0)
getattr(sample, 'false', False)
getattr(sample, 'unknown', None)
try:
    observe()
except Exception:
    pass
"""
    defaults, handlers = source_inventory("synthetic", synthetic)
    assert [(x["field"], x["default_kind"]) for x in defaults] == [
        ("zero", "ZERO"),
        ("false", "FALSE"),
    ]
    assert [(x["line"], x["end"]) for x in handlers] == [(7, 8)]


def test_car_selection_is_excluded_and_catalog_is_not_a_tuning_allowlist():
    _, features = evidence()
    params = {p["name"]: p for p in features["parameters"]}
    assert params["CarSelected3"]["classification"] == "NOT_SUITABLE"
    assert params["RadarReactionFactor"]["classification"] == "UNRESOLVED"
    assert all(p["application_authorized"] is False for p in features["parameters"])


def test_catalog_metadata_is_verified_against_source_not_a_second_ui_claim():
    from tests.audit.validate_hoya_c3_atune import verify_catalog

    raw = b'{"params":[{"name":"synthetic","min":0,"max":2,"default":1}]}'
    row = {
        "name": "synthetic",
        "catalog_present": True,
        "ui_min": 0,
        "ui_max": 2,
        "ui_default": 1,
    }
    verify_catalog([row], raw)
    changed = dict(row, ui_max=3)
    with pytest.raises(ValueError):
        verify_catalog([changed], raw)
    with pytest.raises(ValueError):
        verify_catalog([dict(row, catalog_present=False)], raw)


def test_named_catalog_facts_have_individual_hashed_source_ranges():
    sources, features = evidence()
    catalog = next(x for x in sources["files"] if x["id"] == "catalog")
    entries = {x["id"]: x for x in catalog["ranges"]}
    for parameter in features["parameters"]:
        if parameter["catalog_present"]:
            key = "K:parameter:" + parameter["name"]
            assert key in parameter["evidence"]
            assert entries[key]["start"] < entries[key]["end"]


def test_adoption_table_decisions_and_score_axes_match_structured_evidence():
    from collections import Counter

    _, features = evidence()
    text = (ROOT / "docs/hoya_c3_atune_adoption_matrix.md").read_text(encoding="utf-8")
    decisions = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) == 6 and cells[4] in {
            "ADOPT",
            "ADOPT_WITH_STRONGER_CONTRACT",
            "REFERENCE_ONLY",
            "REJECT",
            "DEFER",
        }:
            decisions.append(cells[4])
    assert Counter(decisions) == Counter(x["decision"] for x in features["adoption"])
    for score in features["scores"]:
        row = next(
            line
            for line in text.splitlines()
            if line.startswith("| " + score["subsystem"] + " |") and len(line.split("|")) == 10
        )
        cells = [cell.strip() for cell in row.split("|")[1:-1]]
        assert [int(x) for x in cells[1:7]] == [
            score[k]
            for k in (
                "architectural_value",
                "evidence_quality",
                "safety_compatibility",
                "reuse_value",
                "implementation_coupling",
                "risk",
            )
        ]


def test_audit_keeps_the_entire_existing_source_and_replay_goldens_unchanged():
    import hashlib

    sources, _ = evidence()
    for path, expected in sources["preserved_files"].items():
        data = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == expected, path
    assert {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src/cyberpilot_autotune").rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and "knowledge" not in p.parts
        and "owner_protocol" not in p.parts
    } == {p for p in sources["preserved_files"] if p.startswith("src/")}
