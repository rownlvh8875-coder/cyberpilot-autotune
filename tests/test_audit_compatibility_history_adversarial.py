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
