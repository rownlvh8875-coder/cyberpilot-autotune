"""H3 integrity checks only; no application or reference runtime is imported."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def evidence():
    return tuple(
        json.loads((ROOT / "docs/evidence" / name).read_text(encoding="utf8"))
        for name in (
            "carrot_writer_ownership_sources.json",
            "carrot_writer_unit_matrix.json",
        )
    )


def test_writer_audit_manifest_is_complete_without_authority():
    from tests.audit.validate_carrot_writer import validate

    assert validate(*evidence()) == {"files": 55, "claims": 95, "parameters": 3, "requirements": 16}


@pytest.mark.parametrize(
    "mutation",
    [
        "sha",
        "blob",
        "range",
        "confidence",
        "source_role",
        "duplicate",
        "conflicts",
        "requirements",
        "offset_tunable",
        "bounds",
        "rates",
        "cas",
        "readback",
        "factor_proof",
        "friction_proof",
        "watchdog",
        "writer",
        "hoya",
        "fingerprint",
        "overall_status",
        "factor_gate",
        "cas_gate",
        "readback_gate",
        "duplicate_gate",
        "missing_gate",
        "unknown_gate",
        "parameter_verdict",
        "offset_verdict",
        "requirement_status",
        "score_axis",
    ],
)
def test_incomplete_or_promoted_evidence_fails_closed(mutation):
    from tests.audit.validate_carrot_writer import validate

    s, m = copy.deepcopy(evidence())
    if mutation == "sha":
        s["pins"]["runtime"] = "carrot-wip"
    elif mutation == "blob":
        s["files"][0]["git_blob_sha"] = "invalid"
    elif mutation == "range":
        s["claims"][0]["range_end"] = 10**9
    elif mutation == "confidence":
        s["claims"][0]["confidence"] = "SAFE"
    elif mutation == "source_role":
        s["files"][0]["exact_revision"] = s["pins"]["runtime"]
    elif mutation == "duplicate":
        s["claims"].append(s["claims"][0])
    elif mutation == "conflicts":
        m["writer_conflicts"].pop()
    elif mutation == "requirements":
        m["pr9_requirements"].pop()
    elif mutation == "offset_tunable":
        m["parameters"][2]["tunable"] = True
    elif mutation in {"bounds", "rates"}:
        m["application_" + mutation] = [0, 1]
    elif mutation == "cas":
        m["existing"]["cas"] = "EXISTING_CAS_AVAILABLE"
    elif mutation == "readback":
        m["readback_candidates"][0]["existing_verified"] = True
    elif mutation in {"factor_proof", "friction_proof"}:
        m["parameters"][0 if mutation == "factor_proof" else 1]["global_status"] = (
            "UNIT_EQUIVALENCE_PROVEN"
        )
    elif mutation == "watchdog":
        m["watchdog_owner_approved"] = True
    elif mutation == "writer":
        m["writer_implemented"] = True
    elif mutation == "hoya":
        m["hoya_apply"] = "ADOPT"
    elif mutation == "fingerprint":
        m["verdicts"].remove("RUNTIME_FINGERPRINT_UNCONFIRMED")
    elif mutation == "overall_status":
        m["status"] = "CARROT_WRITER_ARCHITECTURE_APPROVED"
    elif mutation in {"factor_gate", "cas_gate", "readback_gate"}:
        name = {
            "factor_gate": "factor_equivalence",
            "cas_gate": "cas_design_approved",
            "readback_gate": "readback_design_approved",
        }[mutation]
        next(g for g in m["implementation_gates"] if g["gate"] == name)["status"] = "PROVEN"
    elif mutation == "duplicate_gate":
        m["implementation_gates"][0] = copy.deepcopy(m["implementation_gates"][1])
    elif mutation == "missing_gate":
        m["implementation_gates"].pop()
    elif mutation == "parameter_verdict":
        m["parameters"][0]["verdict"] = "UNIT_EQUIVALENCE_PROVEN"
    elif mutation == "offset_verdict":
        m["parameters"][2]["global_status"] = "VEHICLE_OFFSET_APPROVED"
    elif mutation == "requirement_status":
        m["pr9_requirements"][-1]["status"] = "PROVEN"
    elif mutation == "score_axis":
        scores = m["options"][0]["scores"]
        scores["unknown_axis"] = scores.pop("watchdog")
    else:
        m["implementation_gates"][0]["gate"] = "unknown_gate"
    with pytest.raises(ValueError):
        validate(s, m)


def test_source_and_range_bytes_are_independently_verified():
    from tests.audit.validate_carrot_writer import verify_blob

    raw = b"independent synthetic line\nsecond synthetic line\n"
    f = dict(
        sha256=hashlib.sha256(raw).hexdigest(),
        git_blob_sha=hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        line_count=2,
    )
    spans = [
        dict(
            range_start=1,
            range_end=1,
            source_range_sha256=hashlib.sha256(raw.splitlines(keepends=True)[0]).hexdigest(),
        )
    ]
    verify_blob(f, spans, raw)
    for changed_file, changed_spans, changed_raw in (
        (f | {"git_blob_sha": "0" * 40}, spans, raw),
        (f, [spans[0] | {"source_range_sha256": "0" * 64}], raw),
        (f, spans, raw + b"mutated\n"),
    ):
        with pytest.raises(ValueError):
            verify_blob(changed_file, changed_spans, changed_raw)


def test_structural_unit_witness_distinguishes_factor_friction_and_wrong_scale():
    from tests.audit.validate_carrot_writer import coefficient_scales

    # Independently written tiny syntax fixtures, never executed.
    data = b"""raise RuntimeError("do not execute")
state.latAccelFactor = settings.get_float("LateralTorqueAccelFactor") * 0.001
state.friction = settings.get_float("LateralTorqueFriction") * 0.001
"""
    assert coefficient_scales(data) == {
        "LateralTorqueAccelFactor": 0.001,
        "LateralTorqueFriction": 0.001,
    }
    with pytest.raises(ValueError):
        coefficient_scales(data.replace(b"0.001", b"0.01", 1))


def test_production_and_replay_are_frozen_to_the_merge_basis():
    sources, _ = evidence()
    for path, expected in sources["preserved_files"].items():
        # Tracked Python/JSON text only; tolerate checkout CRLF, unlike raw upstream hashes.
        raw = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == expected, path
    actual = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and ".egg-info" not in str(p)
    }
    expected = {p for p in sources["preserved_files"] if p.startswith("src/")}
    # H4/H5 add separately isolated reference/research namespaces. Existing source
    # and replay bytes remain protected by the original hashes above.
    actual = {
        p
        for p in actual
        if not p.startswith(
            (
                "src/cyberpilot_autotune/owner_protocol/",
                "src/cyberpilot_autotune/research/",
                "src/cyberpilot_autotune/observability/",
            )
        )
    }
    assert actual == expected


def test_h2_is_only_a_read_only_proof_index():
    from cyberpilot_autotune.knowledge.steering import get_registry

    registry = get_registry(evidence()[0]["pins"]["runtime"])
    assert registry.get_proven("LateralTorqueAccelFactor") is None
    assert registry.get_proven("LateralTorqueFriction") is None
    offset = registry.get_any("liveTorqueParameters.latAccelOffset")
    assert offset.storage_key is None and offset.canonical_unit is None
    assert not list((ROOT / "src/cyberpilot_autotune/application").glob("*.py"))


def test_h3_only_adds_docs_and_audit_files():
    sources, _ = evidence()
    assert sources["preserved_prs"] == {
        "8": "e4361678ed176cbd7c0bb6f838d3daa7174caf22",
        "9": "6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5",
    }
    assert sources["copied_source_bodies"] is sources["reference_execution"] is False


def test_nn_mode_witness_requires_good_model_bypass_and_callback_fallback():
    from tests.audit.validate_carrot_writer import nn_modes

    data = b"""if mode.use_nnff and model_good:
    result = mode.torque_from_nn([])
    if mode.nn_friction_override:
        result += mode.torque_from_lateral_accel()
else:
    result = mode.torque_from_lateral_accel()
if mode.use_nnff_lite:
    shape()
"""
    nn_modes(data)
    for wrong in (
        data.replace(b"model_good", b"other"),
        data.replace(b"else:", b"elif other:"),
        data.replace(b"use_nnff_lite", b"different_mode"),
    ):
        with pytest.raises(ValueError):
            nn_modes(wrong)


def test_rotation_magnitude_witness_does_not_assume_negative_slope_orthogonality():
    import math

    from tests.audit.validate_carrot_writer import rotation_magnitude

    data = b"""def slope2rot(slope):
    sin = math.sqrt(slope ** 2 / (slope ** 2 + 1))
    return sin
"""
    rotation_magnitude(data)
    with pytest.raises(ValueError):
        rotation_magnitude(data.replace(b"slope ** 2 /", b"slope /"))
    # Algebraic counterexample only; not a fitted or approved vehicle parameter.
    a, x = -2.0, 1.0
    y = a * x
    rotated_coordinate = (y - abs(a) * x) / math.sqrt(a * a + 1)
    assert rotated_coordinate != 0.0
