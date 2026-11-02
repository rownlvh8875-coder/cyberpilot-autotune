"""HR001–012/017/019/020/022/023:known errors must beat missing witnesses."""

from dataclasses import replace

import pytest

from tests.fixtures.audit_compatibility_history import api, complete


def changed(record, index=0, **fields):
    rows = list(record.commands)
    rows[index] = replace(rows[index], **fields)
    return replace(record, commands=tuple(rows))


def decide(record, policy):
    return api("validation").assess_record(record, policy)


def test_complete_supplied_record_is_structural_only():
    record, policy = complete()
    decision = decide(record, policy)
    assert decision.consistency == "STRUCTURAL_RECORD_MATCH", decision
    assert decision.status == "BLOCKED" and not decision.integrated_admission
    assert "HISTORICAL_REPLAY" in decision.remaining_blockers


@pytest.mark.parametrize(
    "kind",
    (
        "policy",
        "command",
        "case_inventory",
        "origin_inventory",
        "coverage_inventory",
        "executor",
        "toolchain",
        "case_digest",
        "control",
        "budget",
        "policy_digest",
        "exit",
        "protocol",
    ),
)
def test_missing_prerequisite_stays_unavailable(kind):
    record, policy = complete()
    if kind == "policy":
        policy = None
    elif kind == "command":
        record = replace(record, commands=record.commands[:-1])
    elif kind in ("case_inventory", "origin_inventory", "coverage_inventory"):
        field = {
            "case_inventory": "expected_nodeids",
            "origin_inventory": "origins",
            "coverage_inventory": "coverage_groups",
        }[kind]
        policy = replace(
            policy, commands=(replace(policy.commands[0], **{field: None}), *policy.commands[1:])
        )
        record = replace(record, policy_digest=policy.content_digest)
    elif kind in ("executor", "toolchain", "case_digest", "control", "budget"):
        field = {
            "executor": "executor_revision",
            "toolchain": "toolchain_digest",
            "case_digest": "case_inventory_digest",
            "control": "control_profile_digest",
            "budget": "budget_profile_digest",
        }[kind]
        policy = replace(policy, **{field: None})
        record = replace(record, policy_digest=policy.content_digest)
    elif kind == "policy_digest":
        record = replace(record, policy_digest=None)
    elif kind == "exit":
        record = changed(record, exit_code=None)
    else:
        record = changed(record, origins=None, coverage=None, outcomes=None, collected_nodeids=None)
    assert decide(record, policy).consistency == "UNAVAILABLE"


@pytest.mark.parametrize(
    "kind",
    (
        "source",
        "revision",
        "tree",
        "profile",
        "policy_profile",
        "entrypoint",
        "argv",
        "command_id",
        "cohort",
        "duplicate_command",
        "unknown_command",
        "policy_digest",
        "origin",
        "producer",
        "artifact",
        "run",
        "policy_cohort",
    ),
)
def test_available_binding_mismatch_is_rejected(kind):
    record, policy = complete()
    item = record.commands[0]
    if kind in ("source", "revision", "tree"):
        subject = (
            record.commands[3].subject
            if kind == "source"
            else replace(item.subject, **{kind: "9" * 40})
        )
        record = changed(record, subject=subject)
    elif kind == "profile":
        record = replace(record, profile_id="STACK_ADOPTION_V1")
    elif kind == "policy_profile":
        policy = replace(policy, profile_id="STACK_ADOPTION_V1")
        record = replace(record, policy_digest=policy.content_digest)
    elif kind == "duplicate_command":
        record = replace(record, commands=(*record.commands, item))
    elif kind == "unknown_command":
        record = changed(record, command_id="O-UNREGISTERED")
    elif kind == "policy_digest":
        record = replace(record, policy_digest="9" * 64)
    elif kind == "origin":
        record = changed(record, origins=(replace(item.origins[0], sha256="9" * 64),))
    elif kind == "producer":
        record = changed(record, coverage_producer_command_id="D-PYTEST")
    elif kind == "artifact":
        record = changed(record, index=1, coverage_artifact_sha256="c" * 64)
    elif kind == "run":
        record = changed(record, run_id="9" * 32)
    elif kind == "policy_cohort":
        policy = replace(policy, cohorts=(("O", record.commands[3].subject), policy.cohorts[1]))
        record = replace(record, policy_digest=policy.content_digest)
    else:
        field, value = {
            "entrypoint": ("entrypoint", "evil.main"),
            "argv": ("argv", ("other",)),
            "command_id": ("command_id", "D-PYTEST"),
            "cohort": ("cohort_id", "D"),
        }[kind]
        record = changed(record, **{field: value})
    assert decide(record, policy).consistency == "REJECTED"


@pytest.mark.parametrize(
    "damage", ("missing", "substituted", "duplicate", "AR56", "outcome_missing", "outcome_extra")
)
def test_original_476_and_all_499_nodes_cannot_be_replaced_by_count(damage):
    record, policy = complete()
    item = record.commands[3]
    assert len(item.collected_nodeids) == 499
    if damage == "missing":
        record = changed(record, 3, collected_nodeids=item.collected_nodeids[1:])
    elif damage == "substituted":
        record = changed(
            record, 3, collected_nodeids=("tests/other.py::fake", *item.collected_nodeids[1:])
        )
    elif damage == "duplicate":
        record = changed(
            record, 3, collected_nodeids=(item.collected_nodeids[1], *item.collected_nodeids[1:])
        )
    elif damage == "AR56":
        record = changed(record, 3, collected_nodeids=tuple(f"AR-{i:02d}" for i in range(1, 57)))
    elif damage == "outcome_missing":
        record = changed(record, 3, outcomes=item.outcomes[1:])
    else:
        record = changed(
            record,
            3,
            outcomes=(*item.outcomes, replace(item.outcomes[0], nodeid="tests/extra.py::fake")),
        )
    assert decide(record, policy).consistency == "REJECTED"


@pytest.mark.parametrize("phase", ("setup", "call", "teardown"))
@pytest.mark.parametrize(
    "outcome", ("FAILED", "SKIPPED", "XFAIL", "XPASS", "NOT_RUN", "UNAVAILABLE")
)
def test_every_case_phase_is_required(phase, outcome):
    record, policy = complete()
    item = record.commands[0]
    record = changed(record, outcomes=(replace(item.outcomes[0], **{phase: outcome}),))
    expected = "UNAVAILABLE" if outcome == "UNAVAILABLE" else "REJECTED"
    assert decide(record, policy).consistency == expected


@pytest.mark.parametrize("statement,branch", ((97, 100), (100, 94), (0, 0), (98, 95)))
def test_coverage_floors_are_per_group_not_pooled(statement, branch):
    record, policy = complete()
    counts = record.commands[0].coverage
    counts = (
        replace(counts[0], covered=statement, covered_branches=branch),
        replace(counts[1], covered=100, covered_branches=100),
    )
    record = replace(
        record,
        commands=tuple(
            replace(r, coverage=counts) if r.cohort_id == "O" else r for r in record.commands
        ),
    )
    assert decide(record, policy).consistency == (
        "STRUCTURAL_RECORD_MATCH" if (statement, branch) == (98, 95) else "REJECTED"
    )


@pytest.mark.parametrize("damage", ("missing", "extra", "duplicate", "zero", "peer_different"))
def test_coverage_inventory_is_complete_and_same_artifact_same_counts(damage):
    record, policy = complete()
    counts = record.commands[0].coverage
    if damage == "missing":
        counts = counts[:1]
    elif damage == "extra":
        counts = (*counts, replace(counts[0], path="src/unknown.py"))
    elif damage == "duplicate":
        counts = (*counts, counts[0])
    elif damage == "zero":
        counts = tuple(
            replace(r, statements=0, covered=0, branches=0, covered_branches=0) for r in counts
        )
    else:
        counts = (replace(counts[0], covered=100), counts[1])
    record = changed(record, coverage=counts)
    assert decide(record, policy).consistency == "REJECTED"
