"""H4 contract evidence consistency; no evidence field becomes authority."""

import copy
import json
from pathlib import Path

import pytest

from cyberpilot_autotune.owner_protocol import OwnerState, ReferenceTorqueParameterOwner
from tests.audit.validate_carrot_writer import REQUIREMENTS

ROOT = Path(__file__).resolve().parents[2]


def evidence():
    return json.loads((ROOT / "docs/evidence/shared_torque_owner_contract.json").read_text())


def validate(record):
    h3 = json.loads((ROOT / "docs/evidence/carrot_writer_ownership_sources.json").read_text())
    pins = h3["pins"] | {"integration": h3["integration"]}
    if record["source_pins"] != {k: pins[k] for k in ("runtime", "integration", "current", "hoya")}:
        raise ValueError("source pin drift")
    if (
        record["application_authorized"] is not False
        or record["real_writer_implemented"] is not False
        or record["native_watchdog_execution_accepted"] is not False
        or record["application_bounds"] is not None
        or record["application_rates"] is not None
        or record["encoded_controller_representation"] is not None
    ):
        raise ValueError("unapproved native authority or representation")
    if len(record["states"]) != 7 or set(record["states"]) != {state.value for state in OwnerState}:
        raise ValueError("state inventory")
    if record["transition_ids"] != [f"T{i:02d}" for i in range(1, 26)]:
        raise ValueError("transition inventory")
    if len(record["operations"]) != 10 or set(record["operations"]) != {
        "initialize",
        "snapshot",
        "commit",
        "rollback",
        "watchdog",
        "transition_mode",
        "disarm",
        "stop",
        "fault",
        "restart",
    }:
        raise ValueError("operation inventory")
    if any(
        not callable(getattr(ReferenceTorqueParameterOwner, operation, None))
        for operation in record["operations"]
    ):
        raise ValueError("operation inventory")
    rows = record["pr9_mapping"]
    if len(rows) != 16 or {r["requirement"] for r in rows} != REQUIREMENTS:
        raise ValueError("PR9 mapping")
    if any(
        r["logical_status"] != "PROTOCOL_DEFINED"
        or r["native_status"]
        != (
            "STILL_BLOCKED"
            if r["requirement"] in {"scope", "watchdog"}
            else "SOURCE_CHANGE_REQUIRED"
        )
        for r in rows
    ):
        raise ValueError("native mapping promotion")
    if record["status"] != [
        "SHARED_TORQUE_OWNER_PROTOCOL_READY",
        "OWNER_STATE_MACHINE_READY",
        "WATCHDOG_EXECUTION_MODEL_UNRESOLVED",
        "PR9_TARGET_MAPPING_READY",
        "CARROT_SOURCE_CHANGE_DESIGN_READY",
    ]:
        raise ValueError("status promotion")
    if record["scientific_conversion"] or record["proposal_ranking"]:
        raise ValueError("scientific authority")
    if record["failure_priority"] != [
        "OWNER_CORRUPTION_OR_CLOSED_DOMAIN",
        "LEASE_EXPIRED",
        "ACTUAL_CONTEXT_SOURCE_OWNER_LOST",
        "UNSUPPORTED_MODE_OR_MODE_HANDOFF",
        "RECOVERY_REQUIRED",
        "CAS_CONFLICT",
        "PROPOSAL_INVALID",
        "NO_CHANGE",
    ]:
        raise ValueError("fault masking")
    if record["no_change"]["revision_increment"] != 0:
        raise ValueError("no-change revision")
    if record["commit_ack_is_readback"] or record["no_change"]["lease_renewal"]:
        raise ValueError("readback or no-change contract")
    required = {
        "FACTOR_UNIT_EQUIVALENCE_UNRESOLVED",
        "FRICTION_UNIT_EQUIVALENCE_UNRESOLVED",
        "APPLICATION_NOT_AUTHORIZED",
        "RUNTIME_FINGERPRINT_UNCONFIRMED",
        "VEHICLE_APPLICATION_BOUNDS_UNRESOLVED",
        "PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED",
    }
    if not required <= set(record["retained_blockers"]):
        raise ValueError("qualification cannot be promoted")
    return {"states": 7, "transitions": 25, "pr9_requirements": 16}


def test_contract_index_preserves_the_reference_and_h3_boundaries():
    assert validate(evidence()) == {"states": 7, "transitions": 25, "pr9_requirements": 16}


@pytest.mark.parametrize(
    "mutation",
    [
        "authority",
        "bounds",
        "encoding",
        "watchdog",
        "states",
        "transition",
        "requirements",
        "ack",
        "renewal",
        "units",
    ],
)
def test_contract_index_rejects_missing_transitions_or_false_native_approval(mutation):
    record = copy.deepcopy(evidence())
    if mutation == "authority":
        record["application_authorized"] = True
    elif mutation == "bounds":
        record["application_bounds"] = [0, 1]
    elif mutation == "encoding":
        record["encoded_controller_representation"] = "BINARY32_EXACT"
    elif mutation == "watchdog":
        record["native_watchdog_execution_accepted"] = True
    elif mutation == "states":
        record["states"].pop()
    elif mutation == "transition":
        record["transition_ids"].pop()
    elif mutation == "requirements":
        record["pr9_mapping"].pop()
    elif mutation == "ack":
        record["commit_ack_is_readback"] = True
    elif mutation == "renewal":
        record["no_change"]["lease_renewal"] = True
    else:
        record["retained_blockers"].remove("FRICTION_UNIT_EQUIVALENCE_UNRESOLVED")
    with pytest.raises(ValueError):
        validate(record)


@pytest.mark.parametrize(
    "mutation",
    ["logical", "native", "status", "science", "priority", "no_change_revision", "source_pin"],
)
def test_contract_index_rejects_contradictory_protocol_and_qualification_metadata(mutation):
    record = evidence()
    if mutation == "logical":
        record["pr9_mapping"][0]["logical_status"] = "NATIVE_APPROVED"
    elif mutation == "native":
        record["pr9_mapping"][-1]["native_status"] = "PROVEN"
    elif mutation == "status":
        record["status"].append("APPLICATION_AUTHORIZED")
    elif mutation == "science":
        record["scientific_conversion"] = True
    elif mutation == "priority":
        record["failure_priority"].reverse()
    elif mutation == "no_change_revision":
        record["no_change"]["revision_increment"] = 1
    else:
        record["source_pins"]["runtime"] = "main"
    with pytest.raises(ValueError):
        validate(record)
