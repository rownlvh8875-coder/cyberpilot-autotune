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


@pytest.mark.parametrize(
    "damage",
    (
        "joint_absence",
        "wrong_policy_hash",
        "wrong_policy_path",
        "wrong_policy_archive",
        "missing_observed_H6",
    ),
)
def test_review_known_H6_identity_is_not_conditional_on_matching_policy(damage):
    record, policy = complete()
    c = api()
    if damage == "joint_absence":
        other = (c.OriginPin("unrelated", "tests/unrelated.py", "f" * 64, None),)
        policy = replace(policy, commands=tuple(replace(p, origins=other) for p in policy.commands))
        record = replace(record, commands=tuple(replace(r, origins=other) for r in record.commands))
    elif damage == "missing_observed_H6":
        record = replace(
            record,
            commands=(
                *record.commands[:1],
                replace(
                    record.commands[1],
                    origins=(c.OriginPin("unrelated", "tests/unrelated.py", "f" * 64, None),),
                ),
                *record.commands[2:],
            ),
        )
        policy = None
    else:
        p = policy.commands[0]
        origin = replace(
            p.origins[0],
            **{
                "wrong_policy_hash": {"sha256": "f" * 64},
                "wrong_policy_path": {"path": "tests/wrong.py"},
                "wrong_policy_archive": {"archive_member": "helper.py"},
            }[damage],
        )
        policy = replace(policy, commands=(replace(p, origins=(origin,)), *policy.commands[1:]))
        record = replace(
            record, commands=(replace(record.commands[0], origins=None), *record.commands[1:])
        )
    if policy is not None:
        record = replace(record, policy_digest=policy.content_digest)
    assert api("validation").assess_record(record, policy).consistency == "REJECTED"


@pytest.mark.parametrize("policy_damage", ("absent", "command_absent", "expected_absent"))
@pytest.mark.parametrize("record_damage", ("collected_missing", "completed_outcome_missing"))
def test_review_D499_is_known_even_when_expected_inventory_unavailable(
    policy_damage, record_damage
):
    record, policy = complete()
    item = record.commands[3]
    item = replace(
        item,
        **(
            {"collected_nodeids": item.collected_nodeids[1:]}
            if record_damage == "collected_missing"
            else {"outcomes": item.outcomes[1:]}
        ),
    )
    record = replace(record, commands=(*record.commands[:3], item, *record.commands[4:]))
    if policy_damage == "absent":
        policy = None
    else:
        commands = (
            (*policy.commands[:3], *policy.commands[4:])
            if policy_damage == "command_absent"
            else (
                *policy.commands[:3],
                replace(policy.commands[3], expected_nodeids=None),
                *policy.commands[4:],
            )
        )
        policy = replace(policy, commands=commands)
        record = replace(record, policy_digest=policy.content_digest)
    assert api("validation").assess_record(record, policy).consistency == "REJECTED"


@pytest.mark.parametrize("dimension", ("statements", "branches", "both", "zero_totals", "empty"))
def test_review_impossible_coverage_is_known_without_policy(dimension):
    record, _ = complete()
    rows = []
    for item in record.commands:
        if dimension in ("zero_totals", "empty"):
            counts = (
                tuple(
                    replace(c, statements=0, covered=0, branches=0, covered_branches=0)
                    for c in item.coverage
                )
                if dimension == "zero_totals"
                else ()
            )
            rows.append(replace(item, coverage=counts))
            continue
        counts = tuple(
            replace(
                c,
                covered=0 if dimension in ("statements", "both") else c.covered,
                covered_branches=0 if dimension in ("branches", "both") else c.covered_branches,
            )
            for c in item.coverage
        )
        rows.append(replace(item, coverage=counts))
    record = replace(record, commands=tuple(rows))
    assert api("validation").assess_record(record, None).consistency == "REJECTED"


def test_review_low_individual_module_can_be_compensated_within_a_group():
    record, _ = complete()
    rows = []
    for item in record.commands:
        first, second = item.coverage
        rows.append(
            replace(
                item,
                coverage=(
                    replace(first, covered=96, covered_branches=90),
                    replace(second, covered=100, covered_branches=100),
                ),
            )
        )
    assert (
        api("validation").assess_record(replace(record, commands=tuple(rows)), None).consistency
        == "UNAVAILABLE"
    )
