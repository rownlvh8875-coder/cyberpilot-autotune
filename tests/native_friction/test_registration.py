"""Offline content registration must never become runtime source approval."""

import copy
import importlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from cyberpilot_autotune.observability.validation import (
    ObservationPolicy,
    ObservationReason,
    evaluate,
)
from tests.fixtures.friction_receipt import complete


def registration():
    path = Path(__file__).resolve().parents[2] / "compatibility/friction_native/registration.py"
    assert path.is_file(), "OFFLINE_REGISTRATION_MISSING"
    return importlib.import_module("compatibility.friction_native.registration")


def test_canonical_identity_is_order_independent_and_unknown_is_not_zero_or_false():
    module = registration()
    assert module.canonical({"z": None, "a": "관측"}) == '{"a":"관측","z":null}'.encode()
    assert module.canonical({"a": 1, "b": 2}) == module.canonical({"b": 2, "a": 1})
    assert len({module.canonical(v) for v in (None, False, 0)}) == 3
    for value in (float("nan"), float("inf"), -float("inf")):
        with pytest.raises(ValueError):
            module.canonical({"raw": value})


@pytest.mark.parametrize("change", ["revision", "closure", "authority", "unknown", "type"])
def test_record_comparison_does_not_trust_caller_digest_or_truthy_permissions(change):
    module = registration()
    expected = {"revision": "a" * 40, "closure": "b" * 64, "runtime_accepted": False}
    actual = copy.deepcopy(expected)
    module.check_record(actual, expected)
    if change == "unknown":
        actual["approved"] = True
    elif change == "type":
        actual["runtime_accepted"] = 0
    elif change == "authority":
        actual["runtime_accepted"] = True
    else:
        actual[change] = "0" * len(actual[change])
    with pytest.raises(ValueError, match="REGISTRATION_CONTENT_MISMATCH"):
        module.check_record(actual, expected)


def test_new_content_revision_is_not_accepted_by_the_unchanged_h7_policy():
    registration()
    candidate = "ab" * 20
    with pytest.raises(ValueError, match="POLICY_SOURCE"):
        ObservationPolicy(source_revisions=(candidate,))
    receipt = complete()
    updated = replace(receipt, cycle=replace(receipt.cycle, source_revision=candidate))
    reasons = evaluate(updated, ObservationPolicy()).reasons
    assert ObservationReason.UNSUPPORTED_SOURCE_REVISION in reasons
    assert ObservationReason.SOURCE_SCHEMA_MISMATCH in reasons


def test_cli_requires_explicit_source_and_never_infers_a_runtime_checkout(tmp_path):
    registration()
    command = [sys.executable, "-m", "compatibility.friction_native.registration"]
    result = subprocess.run(command + ["--help"], capture_output=True, text=True)
    assert result.returncode == 0 and "--reference-checkout" in result.stdout
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2
    result = subprocess.run(
        command + ["--reference-checkout", str(tmp_path / "missing")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "OFFLINE_REGISTRATION_REJECTED" in result.stderr


def test_committed_record_has_no_runtime_or_candidate_permissions():
    module = registration()
    record = json.loads(module.RECORD.read_text())
    assert record["registration_scope"] == "OFFLINE_CONTENT_ONLY"
    for field in (
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
        "runtime_qualified",
        "empirical_qualified",
        "deployment_performed",
        "native_revision_published",
        "h7_source_allowlist_updated",
    ):
        assert record[field] is False
    assert record["q_observed"] is None


def test_duplicate_record_keys_are_not_silently_resolved_by_json_parser(tmp_path):
    module = registration()
    path = tmp_path / "record.json"
    path.write_text('{"runtime_accepted":true,"runtime_accepted":false}')
    with pytest.raises(ValueError, match="DUPLICATE_REGISTRATION_KEY"):
        module.read_record(path)
    path.write_text('{"runtime_accepted":false,"q_observed":null}')
    assert module.read_record(path) == {"runtime_accepted": False, "q_observed": None}


@pytest.mark.parametrize("case", ["executable", "missing_directory", "file_and_directory"])
def test_tree_rewrite_rejects_unexpected_native_layout_without_replacing_it(tmp_path, case):
    module = registration()
    subprocess.run(["git", "init", "--bare", "--quiet", str(tmp_path)], check=True)

    def git(*args, data=None):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], input=data)

    oid = git("hash-object", "-w", "--stdin", data=b"old\n").decode().strip()
    new = git("hash-object", "-w", "--stdin", data=b"new\n").decode().strip()
    mode = "100755" if case == "executable" else "100644"
    tree = git("mktree", data=f"{mode} blob {oid}\tx\n".encode()).decode().strip()
    changes = {(b"x",): new}
    if case == "missing_directory":
        changes = {(b"absent", b"child"): new}
    elif case == "file_and_directory":
        changes[(b"x", b"child")] = new
    with pytest.raises(ValueError, match="UNEXPECTED_TARGET_MODE_OR_TREE|MISSING_BASE_DIRECTORY"):
        module._rewrite_tree(git, tree, changes)
    assert git("show", tree + ":x") == b"old\n"
