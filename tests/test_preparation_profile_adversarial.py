"""Adversarial supplied claims must never gain effects or suppress failures."""

import copy
import json
from dataclasses import replace
from hashlib import sha256

import pytest

from tests.audit_preparation_profile import canonical_policy, canonical_profile, decode_profile
from tests.fixtures.preparation_profile import complete
from tests.test_preparation_profile_validation import assessor


@pytest.mark.parametrize(
    "field", ["artifacts", "cohorts", "batch_boundary", "batch_limits", "commands", "controls"]
)
def test_unrelated_missing_table_cannot_hide_false_claim_without_policy(field):
    record, _ = complete()
    record = replace(record, **{field: None}, producer_errors=("PRODUCER_REPORTED_FAILURE",))
    decision = assessor()(record)
    assert decision.consistency == "REJECTED"
    assert any(r.code == "PRODUCER_FAILURE" for r in decision.errors)
    assert any(r.code == "POLICY_UNAVAILABLE" for r in decision.unavailable)


@pytest.mark.parametrize("field", ["identity_digest", "generation", "clock_domain"])
def test_boundary_partial_unknowns_and_generation_zero_are_not_defaults(field):
    record, policy = complete()
    record = replace(record, batch_boundary=replace(record.batch_boundary, **{field: None}))
    decision = assessor()(record, policy)
    assert any(r.subject == "record.batch_boundary." + field for r in decision.unavailable)
    assert decision.consistency == "UNAVAILABLE"


@pytest.mark.parametrize("duration", [None, 0, "UNBOUNDED"])
def test_invalid_or_unknown_duration_is_never_used_for_deadline_arithmetic(duration):
    record, _ = complete()
    cmd = record.commands[0]
    limits = tuple(
        replace(v, value=duration) if v.name == "wall_limit_ns" else v for v in cmd.limits
    )
    cmd = replace(
        cmd, limits=limits, timing=replace(cmd.timing, start_ns=2**64 - 1, deadline_ns=None)
    )
    decision = assessor()(replace(record, commands=(cmd,) + record.commands[1:]))
    assert not {"TIME_OVERFLOW", "DEADLINE_MISMATCH"} & {r.code for r in decision.errors}


def test_batch_boundary_reuse_and_clock_mismatch_are_detected_with_other_nulls():
    record, _ = complete()
    cmd = record.commands[0]
    cmd = replace(
        cmd,
        boundary=replace(
            cmd.boundary, identity_digest=record.batch_boundary.identity_digest, generation=None
        ),
        timing=replace(cmd.timing, start_ns=None, clock_domain="different"),
    )
    decision = assessor()(replace(record, commands=(cmd,) + record.commands[1:]))
    assert {"BOUNDARY_REUSE", "CLOCK_DOMAIN_MISMATCH"} <= {r.code for r in decision.errors}


def test_duplicate_boundary_at_later_registry_command_not_caller_order():
    record, _ = complete()
    commands = (
        record.commands[0],
        replace(record.commands[1], boundary=record.commands[0].boundary),
    ) + record.commands[2:]
    record = replace(record, commands=commands)
    object.__setattr__(record, "commands", tuple(reversed(record.commands)))
    decision = assessor()(record)
    assert [(r.code, r.subject) for r in decision.errors if r.code == "BOUNDARY_REUSE"] == [
        ("BOUNDARY_REUSE", "record.commands.O-H6.boundary.identity_digest")
    ]


def test_forged_nested_and_foreign_policy_fail_before_assessment():
    record, policy = complete()
    with pytest.raises(ValueError):
        assessor()(policy, record)
    with pytest.raises(ValueError):
        assessor()(record, object())
    object.__setattr__(record.commands[0].timing, "start_ns", True)
    with pytest.raises(ValueError):
        assessor()(record, policy)


def _mutable_leaves(node, path=()):
    if isinstance(node, dict):
        for key, value in node.items():
            if key not in (
                "role",
                "name",
                "unit",
                "command_id",
                "producer_errors",
                "producer_unavailable",
                "policy_digest",
            ):
                if key == "cohort_id" and "cohorts" in path:
                    continue
                yield from _mutable_leaves(value, (*path, key))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _mutable_leaves(item, (*path, i))
    else:
        yield path, node


def test_every_available_comparable_scalar_change_is_seen_without_table_position_join():
    record, policy = complete()
    original = json.loads(canonical_profile(record))
    for path, value in _mutable_leaves(original["body"]):
        doc = copy.deepcopy(original)
        parent = doc["body"]
        for part in path[:-1]:
            parent = parent[part]
        if type(value) is bool:
            changed = not value
        elif type(value) is int:
            changed = value + 1
        elif value in ("O", "D"):
            changed = "D" if value == "O" else "O"
        elif len(value) in (32, 40, 64):
            changed = "2" * len(value)
        else:
            changed = "OTHER"
        parent[path[-1]] = changed
        decision = assessor()(decode_profile(json.dumps(doc).encode()), policy)
        assert any(r.code == "POLICY_RECORD_MISMATCH" for r in decision.errors), path


def test_digest_changes_with_generation_and_null_zero_false_stay_distinct():
    record, policy = complete()
    assert record.policy_digest == sha256(canonical_policy(policy)).hexdigest()
    outputs = []
    for generation in (None, 0, 1):
        changed = replace(
            record, batch_boundary=replace(record.batch_boundary, generation=generation)
        )
        outputs.append(sha256(canonical_profile(changed)).hexdigest())
    assert len(set(outputs)) == 3
    for value in (None, False, True):
        changed = replace(
            record, controls=(replace(record.controls[0], value=value),) + record.controls[1:]
        )
        assert assessor()(changed, policy).status == "BLOCKED"
