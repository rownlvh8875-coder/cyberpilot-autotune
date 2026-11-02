"""Supplied-content diagnostics cannot substitute for actual H/C execution."""

import importlib
import importlib.util

import pytest

from tests.fixtures.audit_compatibility_core import complete


def assess(v):
    assert importlib.util.find_spec("tests.audit_compatibility.validation") is not None
    return importlib.import_module("tests.audit_compatibility.validation").assess_compatibility(
        v.bundle, v.manifest
    )


def test_structurally_complete_never_qualifies_without_IO():
    r = assess(complete())
    assert r.structural_content_status == "CONTENT_MATCH"
    assert r.decision == "UNAVAILABLE" and r.status == "BLOCKED"
    assert r.integrated_admission is False and all(v is False for _, v in r.permissions)
    assert "HISTORICAL_REPLAY" in r.unavailable_checks


@pytest.mark.parametrize("variant", ("r_extra", "q_extra", "candidate_extra"))
def test_unknown_file_in_any_registration_or_current_tree_rejects(variant):
    r = assess(complete(**{variant: {"unknown.py": b"not approved"}}))
    assert r.decision == "REJECTED"


@pytest.mark.parametrize(
    "changes",
    (
        {"profile_id": "STACK_ADOPTION_V1"},
        {"runtime_qualified": True},
        {"semantic_registration_R": "0" * 40},
        {"unknown": False},
        {"transition_rows": []},
    ),
)
def test_wrong_profile_permission_identity_or_rows_reject(changes):
    assert assess(complete(content_changes=changes)).decision == "REJECTED"
