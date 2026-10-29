"""Design audit rejects unsafe proposals; it never builds a native producer."""

import copy
import importlib
import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest

from cyberpilot_autotune.observability.validation import ObservationPolicy, evaluate
from tests.fixtures.friction_receipt import complete

ROOT = Path(__file__).resolve().parents[2]
MODULE = "tests.audit.validate_carrot_friction_patch_design"


def auditor():
    assert importlib.util.find_spec(MODULE) is not None, "DESIGN_AUDITOR_NOT_IMPLEMENTED"
    return importlib.import_module(MODULE)


def artifact(name):
    path = ROOT / f"docs/evidence/carrot_friction_patch_{name}.json"
    assert path.is_file(), "DESIGN_ARTIFACT_NOT_IMPLEMENTED"
    return json.loads(path.read_text())


def test_wire_design_preserves_all_semantics_and_never_serializes_local_authority():
    wire = artifact("wire")
    auditor().validate_wire(wire)
    assert len(wire["fields"]) == 144
    on_wire = [f for f in wire["fields"] if not f["local_only"]]
    assert len(on_wire) == 134
    assert not any(
        f["semantic_field"].startswith("ObservationEligibilityDecision.") for f in on_wire
    )
    assert wire["q_observed_policy"] == "UNAVAILABLE_ALWAYS_PASSIVE"
    assert wire["candidate_revision"] is None
    assert wire["slot"]["event_ordinal"] == 110
    assert wire["slot"]["type_id"] == "0xda96579883444c35"
    assert wire["optional_wrappers"]["OptionalBool"]["unavailable_ordinal"] == 0


def test_wire_mapping_uses_record_types_not_primitive_substrings_in_class_names():
    fields = {f["semantic_field"]: f for f in auditor().build_wire()["fields"]}
    assert fields["ControllerStageDecomposition.downstream_identities"]["wire_type"] == (
        "List(DownstreamStageIdentity)"
    )
    assert (
        fields["ControllerCallbackSignals.desired_lateral_accel"]["wire_type"]
        == "ScalarObservation"
    )
    assert fields["CycleIdentity.controller_cycle_id"]["wire_type"] == "OptionalUInt64"


@pytest.mark.parametrize("change", ["slot", "q", "authority", "absence", "field", "revision"])
def test_wire_validator_rejects_reuse_laundering_default_and_old_revision_proposals(change):
    wire = copy.deepcopy(artifact("wire"))
    if change == "slot":
        wire["slot"]["event_ordinal"] = 107
    elif change == "q":
        wire["q_observed_policy"] = "RECONSTRUCTED_IN_HELPER_IS_OBSERVED"
    elif change == "authority":
        next(f for f in wire["fields"] if f["semantic_field"].endswith("application_authorized"))[
            "local_only"
        ] = False
    elif change == "absence":
        wire["optional_wrappers"]["OptionalBool"]["unavailable_ordinal"] = 1
    elif change == "field":
        wire["fields"].pop()
    else:
        wire["candidate_revision"] = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
    with pytest.raises(ValueError):
        auditor().validate_wire(wire)


def test_passive_receipt_remains_rejected_not_promoted_to_empirical_or_application_evidence():
    full = complete()
    passive = replace(full, signals=replace(full.signals, q_observed=None))
    decision = evaluate(passive, ObservationPolicy())
    assert decision.status.value == "REJECTED"
    assert "MISSING_Q" in {r.value for r in decision.reasons}
    assert not decision.candidate_generation_allowed
    assert not decision.application_authorized
    assert not decision.runtime_accepted
    assert not decision.owner_proposal_allowed


def test_numeric_counterexample_is_nonzero_and_signed_zero_is_reported_separately():
    proof = artifact("math")
    auditor().validate_math(proof)
    for profile in proof["profiles"]:
        assert len(profile["cases"]) == 40
        assert profile["bit_differences"] > profile["numeric_differences"] > 0
        witness = next(
            c
            for c in profile["cases"]
            if c["error_hex"] == "0x1.eb851eb851eb8p-5" and c["C_hex"] == "0x1.0000000000000p-3"
        )
        assert witness["legacy_hex"] == "0x1.9999999999998p-6"
        assert witness["cq_hex"] == "0x1.999999999999ap-6"
        assert not witness["numeric_equal"]


@pytest.mark.parametrize("change", ["output", "qualification", "q_origin"])
def test_math_validator_rejects_forged_parity_or_observed_q_claim(change):
    proof = copy.deepcopy(artifact("math"))
    if change == "output":
        proof["profiles"][0]["cases"][0]["legacy_hex"] = "0x0.0p+0"
    elif change == "qualification":
        proof["empirical_qualified"] = True
    else:
        proof["q_origin"] = "HELPER_OBSERVED"
    with pytest.raises(ValueError):
        auditor().validate_math(proof)


def test_source_and_history_audit_preserve_h7_and_identify_all_native_files_as_read_only():
    audit = auditor()
    source = artifact("sources")
    audit.validate_sources(source)
    result = audit.verify_history()
    assert result["all_h7_source_unchanged"]
    assert not source["native_patch_implemented"]
    assert source["candidate_revision"] is None


@pytest.mark.parametrize("change", ["revision", "range", "implemented", "missing"])
def test_source_validator_rejects_moving_pin_or_unimplemented_runtime_claim(change):
    source = copy.deepcopy(artifact("sources"))
    if change == "revision":
        source["files"][0]["revision"] = "carrot-wip"
    elif change == "range":
        source["files"][0]["ranges"][0]["sha256"] = "0" * 64
    elif change == "implemented":
        source["native_patch_implemented"] = True
    else:
        source["files"].pop()
    with pytest.raises(ValueError):
        auditor().validate_sources(source)


def test_additive_ci_exception_never_allows_removed_old_gates_or_arbitrary_edits():
    audit = auditor()
    original = audit.git_bytes(ROOT, audit.BASE, ".github/workflows/ci.yml").decode()
    assert audit.compatible_ci(original, original)
    assert audit.compatible_ci(original, audit.extend_ci(original))
    assert not audit.compatible_ci(original, original.replace("--verify-history", ""))
    assert not audit.compatible_ci(original, audit.extend_ci(original) + "# unrelated\n")
