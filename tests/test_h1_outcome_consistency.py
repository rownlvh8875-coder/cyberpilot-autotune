"""Available record contradictions never depend on an optional policy witness."""

import ast
import importlib
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from tests.fixtures.audit_compatibility_history import api, complete

ROOT = Path(__file__).resolve().parents[1]
BASE = "a8b2bf1e6f27a4157212298928a50c8e970babf5"
ADDITIONS = {
    "docs/superpowers/specs/2026-11-03-h1-outcome-consistency-design.md",
    "docs/superpowers/plans/2026-11-03-h1-outcome-consistency.md",
    "tests/test_h1_outcome_consistency.py",
    "docs/evidence/audit_compatibility/h1-outcome-consistency-v1/registration.json",
}
MODIFICATIONS = {
    "tests/audit_compatibility_history/validation.py",
    "tests/test_audit_compatibility_history_architecture.py",
    "tests/test_audit_compatibility_capture_portability.py",
    "tests/test_actions_preflight_registration.py",
}
POLICIES = ("complete", "absent", "command_absent", "expected_absent")


def vector(index, witness):
    record, policy = complete()
    if index == 3:
        # Keep all D499 diagnostic nodes;the extra audit node is also observed.
        node = "tests/audit/test_ADDITIONAL.py::test_supplied"
        command = record.commands[index]
        command = replace(
            command,
            collected_nodeids=(*command.collected_nodeids, node),
            outcomes=(*command.outcomes, api().CaseOutcome(node, "PASSED", "PASSED", "PASSED")),
        )
        record = replace(
            record, commands=(*record.commands[:index], command, *record.commands[index + 1 :])
        )
        expected = replace(policy.commands[index], expected_nodeids=command.collected_nodeids)
        policy = replace(
            policy, commands=(*policy.commands[:index], expected, *policy.commands[index + 1 :])
        )
    if witness == "absent":
        policy = None
    elif witness == "command_absent":
        policy = replace(policy, commands=(*policy.commands[:index], *policy.commands[index + 1 :]))
    elif witness == "expected_absent":
        expected = replace(policy.commands[index], expected_nodeids=None)
        policy = replace(
            policy, commands=(*policy.commands[:index], expected, *policy.commands[index + 1 :])
        )
    if policy is not None:
        record = replace(record, policy_digest=policy.content_digest)
    return record, policy


def assess_changed(record, policy, index, **changes):
    item = replace(record.commands[index], **changes)
    record = replace(
        record, commands=(*record.commands[:index], item, *record.commands[index + 1 :])
    )
    decision = api("validation").assess_record(record, policy)
    assert decision.status == "BLOCKED" and not decision.integrated_admission
    assert len(decision.permissions) == 9 and all(v is False for _, v in decision.permissions)
    return decision


@pytest.mark.parametrize("index", (0, 3))
@pytest.mark.parametrize("witness", POLICIES)
@pytest.mark.parametrize("damage", ("missing", "foreign"))
def test_completed_record_contradictions_reject_without_policy(index, witness, damage):
    record, policy = vector(index, witness)
    original = record.commands[index].outcomes
    outcomes = (
        original[:-1]
        if damage == "missing"
        else (
            *original,
            api().CaseOutcome("tests/FOREIGN.py::test_extra", "PASSED", "PASSED", "PASSED"),
        )
    )
    decision = assess_changed(record, policy, index, outcomes=outcomes)
    assert decision.consistency == "REJECTED"
    assert "OUTCOME_COLLECTION_MISMATCH" in decision.errors


@pytest.mark.parametrize("index", (0, 3))
@pytest.mark.parametrize("witness", POLICIES)
def test_foreign_outcome_rejects_even_when_exit_unavailable(index, witness):
    record, policy = vector(index, witness)
    outcomes = (
        *record.commands[index].outcomes,
        api().CaseOutcome("tests/FOREIGN.py::test_extra", "PASSED", "PASSED", "PASSED"),
    )
    decision = assess_changed(record, policy, index, outcomes=outcomes, exit_code=None)
    assert decision.consistency == "REJECTED"
    assert "OUTCOME_COLLECTION_MISMATCH" in decision.errors
    assert "EXIT_UNAVAILABLE" in decision.unavailable


@pytest.mark.parametrize("index", (0, 3))
@pytest.mark.parametrize("witness", POLICIES)
@pytest.mark.parametrize("missing", ("collection", "outcomes", "partial"))
def test_missing_or_incomplete_observations_are_not_fabricated_errors(index, witness, missing):
    record, policy = vector(index, witness)
    changes = (
        {"collected_nodeids": None}
        if missing == "collection"
        else {"outcomes": None}
        if missing == "outcomes"
        else {"outcomes": record.commands[index].outcomes[:-1], "exit_code": None}
    )
    decision = assess_changed(record, policy, index, **changes)
    assert decision.consistency == "UNAVAILABLE" and decision.errors == ()


@pytest.mark.parametrize("index", (0, 3))
@pytest.mark.parametrize("witness", POLICIES)
def test_equal_reordered_inventory_is_not_a_contradiction(index, witness):
    record, policy = vector(index, witness)
    decision = assess_changed(record, policy, index, outcomes=record.commands[index].outcomes[::-1])
    assert decision.errors == ()
    assert decision.consistency == (
        "STRUCTURAL_RECORD_MATCH" if witness == "complete" else "UNAVAILABLE"
    )


def test_observed_empty_sets_are_not_missing_values():
    record, _ = vector(0, "absent")
    decision = assess_changed(record, None, 0, collected_nodeids=(), outcomes=())
    assert decision.errors == ()
    assert decision.unavailable == ("POLICY_UNAVAILABLE",)
    unknown = assess_changed(record, None, 0, collected_nodeids=None, outcomes=None)
    assert "COMMAND_OBSERVATION_MISSING" in unknown.unavailable


def source_git(*args):
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"},
    )


def successor():
    module = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    check = getattr(module, "_h1_outcome_changes", None)
    assert callable(check), "bounded H1 successor not implemented"
    return module, check


def test_scope_is_exact_and_registration_does_not_authorize_it():
    # Freeze this completed repair; the current successor consumer below still
    # checks every tracked and untracked change after this literal checkpoint.
    rows = (
        source_git(
            "diff",
            "--no-renames",
            "--name-status",
            BASE,
            "209edaa83b398e6204af1097fda4b651807cc815",
        )
        .decode()
        .splitlines()
    )
    assert sorted(rows) == sorted(
        ["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS]
    )
    module, check = successor()
    check(rows)
    module.test_all_earlier_files_and_guard_bytes_are_preserved()
    path = "docs/evidence/audit_compatibility/h1-outcome-consistency-v1/registration.json"
    value = json.loads((ROOT / path).read_text())
    old = json.loads(
        source_git(
            "show", BASE + ":docs/evidence/audit_compatibility/ci-portability-v1/registration.json"
        )
    )
    assert value["base"] == BASE and value["status"] == "BLOCKED"
    assert set(value["new_paths"]) == ADDITIONS and set(value["modified_paths"]) == MODIFICATIONS
    assert value["permissions"] == old["permissions"] and not value["manifest_is_authority"]
    assert set(old["retained_blockers"]) <= set(value["retained_blockers"])


@pytest.mark.parametrize(
    "rows",
    [
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\ttests/audit_compatibility_capture/worktree_reader.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\ttools/actions_runner_preflight.py"],
        ["A\tdocs/unknown.md"],
        ["D\ttests/audit_compatibility_history/validation.py"],
        ["R100\ta.py\ttests/audit_compatibility_history/validation.py"],
        ["M\ttests/audit_compatibility_history/validation.py"] * 2,
        ["A\t../tests/test_h1_outcome_consistency.py"],
        ["M tests/audit_compatibility_history/validation.py"],
    ],
)
def test_scope_rejects_unknown_alias_or_status_changes(rows):
    _, check = successor()
    with pytest.raises(AssertionError):
        check(rows)


@pytest.mark.parametrize("tamper", ("frozen", "untracked"))
def test_scope_consumer_rejects_frozen_history_and_untracked_paths(monkeypatch, tamper):
    module, _ = successor()
    real = module.subprocess.check_output

    def damaged(args, **kwargs):
        if tamper == "frozen" and args[1:] == [
            "diff",
            "--no-renames",
            "--name-status",
            "ce138c503ff320a2a6956ceff3d8735418b72bcc",
            BASE,
        ]:
            return b"M\tsrc/cyberpilot_autotune/__init__.py\n"
        raw = real(args, **kwargs)
        if tamper == "untracked" and args[1:] == ["ls-files", "--others", "--exclude-standard"]:
            raw += b"UNREGISTERED.py\n"
        return raw

    monkeypatch.setattr(module.subprocess, "check_output", damaged)
    with pytest.raises(AssertionError):
        module.test_all_earlier_files_and_guard_bytes_are_preserved()


def test_scope_preserves_every_prior_nonconsumer_function():
    allowed = {
        "tests/audit_compatibility_history/validation.py": {"_observed"},
        "tests/test_audit_compatibility_history_architecture.py": {
            "test_all_earlier_files_and_guard_bytes_are_preserved",
        },
        "tests/test_audit_compatibility_capture_portability.py": {
            "test_repair_inventory_is_exact_and_not_manifest_authority",
            "test_frozen_ranges_and_runtime_bytes_are_not_changed",
            "test_normalization_followup_has_only_registered_modifications",
        },
        "tests/test_actions_preflight_registration.py": {
            "test_real_consumer_checks_all_legacy_ranges_and_literal_checkpoint",
        },
    }
    for path, exceptions in allowed.items():
        old = ast.parse(source_git("show", BASE + ":" + path).decode())
        new = ast.parse((ROOT / path).read_text())
        current = {n.name: ast.dump(n) for n in new.body if isinstance(n, ast.FunctionDef)}
        for node in old.body:
            if isinstance(node, ast.FunctionDef) and node.name not in exceptions:
                assert current[node.name] == ast.dump(node), (path, node.name)
