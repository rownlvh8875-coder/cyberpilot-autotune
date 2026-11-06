"""Known contradictions survive every unrelated missing policy or claim."""

import copy
import importlib
import json
from dataclasses import replace

import pytest

from tests.audit_preparation_profile import decode_policy, decode_profile
from tests.fixtures.preparation_profile import complete, registration


def assessor():
    api = importlib.import_module("tests.audit_preparation_profile")
    check = getattr(api, "assess_profile", None)
    assert callable(check), "pure profile comparator missing"
    return check


@pytest.mark.parametrize("case", registration()["conformance"]["cases"], ids=lambda c: c["id"])
def test_frozen_synthetic_conformance_expectation(case):
    vector = registration()["conformance"]
    bodies = {
        "record": copy.deepcopy(vector["baseline_record"]),
        "policy": copy.deepcopy(vector["baseline_policy"]),
    }
    for mutation in case["mutations"]:
        target = bodies
        for key in mutation[:-2]:
            target = target[key]
        target[mutation[-2]] = mutation[-1]

    def evaluate():
        record = decode_profile(
            json.dumps(
                {
                    "schema": "preparation-profile-claims-v1",
                    "kind": "RECORD",
                    "body": bodies["record"],
                }
            ).encode()
        )
        policy = (
            None
            if case["policy"] == "NONE"
            else decode_policy(
                json.dumps(
                    {
                        "schema": "preparation-profile-claims-v1",
                        "kind": "POLICY",
                        "body": bodies["policy"],
                    }
                ).encode()
            )
        )
        return assessor()(record, policy)

    if case["expected_ValueError"]:
        with pytest.raises(ValueError):
            evaluate()
    else:
        decision = evaluate()
        assert decision.consistency == case["expected_consistency"]
        assert set(case["required_error_codes"]) <= {r.code for r in decision.errors}
        assert set(case["required_unavailable_codes"]) <= {r.code for r in decision.unavailable}
        assert decision.status == "BLOCKED" and not decision.integrated_admission
        assert not decision.H_executed and all(not flag for _, flag in decision.permissions)


@pytest.mark.parametrize("side", ["record", "policy"])
@pytest.mark.parametrize(
    "field",
    ["run_id", "artifacts", "cohorts", "batch_boundary", "batch_limits", "commands", "controls"],
)
def test_missing_root_is_reported_without_inventing_children(side, field):
    record, policy = complete()
    if side == "record":
        record = replace(record, **{field: None})
    else:
        policy = replace(policy, **{field: None})
    decision = assessor()(record, policy)
    reasons = {(r.code, r.subject) for r in decision.unavailable}
    code = (
        "TABLE_UNAVAILABLE"
        if field in ("artifacts", "cohorts", "batch_limits", "commands", "controls")
        else "VALUE_UNAVAILABLE"
    )
    assert (code, side + "." + field) in reasons
    assert not any(r.subject.startswith(side + "." + field + ".") for r in decision.unavailable)


@pytest.mark.parametrize("side", ["record", "policy"])
@pytest.mark.parametrize("field", ["artifacts", "cohorts", "batch_limits", "commands", "controls"])
def test_nonnull_incomplete_inventory_rejects_instead_of_becoming_unknown(side, field):
    record, policy = complete()
    if side == "record":
        record = replace(record, **{field: ()})
    else:
        policy = replace(policy, **{field: ()})
    decision = assessor()(record, policy)
    assert ("TABLE_INVENTORY_MISMATCH", side + "." + field) in {
        (r.code, r.subject) for r in decision.errors
    }


@pytest.mark.parametrize("side", ["record", "policy"])
@pytest.mark.parametrize("field", ["boundary", "limits", "timing"])
def test_missing_command_context_is_not_borrowed_from_other_side(side, field):
    record, policy = complete()
    target = record if side == "record" else policy
    commands = (replace(target.commands[0], **{field: None}),) + target.commands[1:]
    if side == "record":
        record = replace(record, commands=commands)
    else:
        policy = replace(policy, commands=commands)
    decision = assessor()(record, policy)
    root = side + ".commands.O-PYTEST." + field
    assert any(r.subject == root for r in decision.unavailable)
    assert not any(r.subject.startswith(root + ".") for r in decision.unavailable)


def test_all_independent_errors_and_missing_reasons_are_preserved_and_sorted():
    record, _ = complete()
    record = replace(
        record,
        run_id=None,
        policy_digest=None,
        controls=(replace(record.controls[0], value=False),),
        batch_limits=(replace(record.batch_limits[0], value=0),),
        producer_errors=("PRODUCER_REPORTED_FAILURE",),
        producer_unavailable=("PRODUCER_REPORTED_UNAVAILABLE",),
    )
    decision = assessor()(record)
    assert {
        "CONTROL_CLAIM_FALSE",
        "LIMIT_NONPOSITIVE",
        "TABLE_INVENTORY_MISMATCH",
        "PRODUCER_FAILURE",
    } <= {r.code for r in decision.errors}
    assert {"POLICY_UNAVAILABLE", "VALUE_UNAVAILABLE", "PRODUCER_UNAVAILABLE"} <= {
        r.code for r in decision.unavailable
    }
    for reasons in (decision.errors, decision.unavailable):
        assert [(r.code, r.subject) for r in reasons] == sorted(
            {(r.code, r.subject) for r in reasons}
        )
    assert decision.consistency == "REJECTED"
