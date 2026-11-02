"""A missing witness must never hide available contradictions or type tampering."""

from dataclasses import replace

import pytest

from tests.fixtures.audit_compatibility_history import api, complete


@pytest.mark.parametrize("policy_missing", (False, True))
@pytest.mark.parametrize("failure", ("exit", "origin", "case", "duplicate", "coverage"))
def test_known_failure_over_missing_peers_without_producer_errors(policy_missing, failure):
    record, policy = complete()
    item = record.commands[0]
    if failure == "exit":
        item = replace(item, exit_code=1)
    elif failure == "origin":
        item = replace(item, origins=(replace(item.origins[0], sha256="f" * 64),))
    elif failure == "case":
        item = replace(item, outcomes=(replace(item.outcomes[0], call="FAILED"),))
    elif failure == "duplicate":
        item = replace(item, collected_nodeids=(*item.collected_nodeids, *item.collected_nodeids))
    else:
        item = replace(item, coverage=(*item.coverage, item.coverage[0]))
    record = replace(record, commands=(item, *record.commands[1:-1]))
    decision = api("validation").assess_record(record, None if policy_missing else policy)
    assert decision.errors and decision.consistency == "REJECTED"
    assert record.errors == item.errors == ()


def test_revalidation_rejects_forged_nested_type_before_assessing():
    record, policy = complete()
    object.__setattr__(record.commands[0].coverage[0], "covered", True)
    with pytest.raises(ValueError):
        api("validation").assess_record(record, policy)


def test_supplied_errors_and_unavailable_are_retained():
    record, policy = complete()
    record = replace(record, errors=("KNOWN",), unavailable=("SOURCE",))
    decision = api("validation").assess_record(record, policy)
    assert "KNOWN" in decision.errors and "SOURCE" in decision.unavailable
    assert decision.consistency == "REJECTED"


@pytest.mark.parametrize("damage", ("one_missing", "AR56", "same_count_other"))
def test_policy_and_record_cannot_jointly_shrink_registered_D_inventory(damage):
    record, policy = complete()
    command = policy.commands[3]
    original = command.expected_nodeids
    nodes = (
        original[1:]
        if damage == "one_missing"
        else tuple(f"AR-{i}" for i in range(56))
        if damage == "AR56"
        else ("tests/other.py::fake", *original[1:])
    )
    policy = replace(
        policy,
        commands=(
            *policy.commands[:3],
            replace(command, expected_nodeids=nodes),
            *policy.commands[4:],
        ),
    )
    item = record.commands[3]
    c = api()
    item = replace(
        item,
        collected_nodeids=nodes,
        outcomes=tuple(c.CaseOutcome(n, "PASSED", "PASSED", "PASSED") for n in nodes),
    )
    record = replace(
        record,
        policy_digest=policy.content_digest,
        commands=(*record.commands[:3], item, *record.commands[4:]),
    )
    assert api("validation").assess_record(record, policy).consistency == "REJECTED"
