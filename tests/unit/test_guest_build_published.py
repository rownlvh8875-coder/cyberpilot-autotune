"""Published evidence cannot imply that a pure contract is an actual producer."""

import json
from pathlib import Path

from compatibility.guest_build_receipt.planning import current_reference_plan

ROOT = Path(__file__).resolve().parents[2]


def test_published_contract_keeps_reference_and_execution_unavailability_explicit():
    data = json.loads((ROOT / "docs/evidence/guest_build_promotion_contract.json").read_text())
    plan = current_reference_plan()
    assert data["base_revision"] == plan.inputs.reference_revision
    assert data["reference_snapshot_digest"] == plan.inputs.reference_snapshot_digest
    assert data["overall_status"] == "BLOCKED" and data["preparation_origin"] == "REFERENCE_ONLY"
    assert data["generated_input_dag"] == "UNSUPPORTED_IN_V1"
    assert all(value is None for value in data["registrations"].values())
    assert (
        data["successful_prohibited_handles"] is None
        and data["successful_prohibited_effects"] is None
    )
    for name in (
        "actual_producer_implemented",
        "actual_input_seal_implemented",
        "actual_output_promotion_implemented",
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert data[name] is False
    for name in (
        "guest_hermetic_build_receipt_contract",
        "guest_hermetic_build_capture_design",
        "guest_build_promotion_result",
    ):
        assert (ROOT / "docs" / (name + ".md")).is_file()
