"""Malformed claims cannot hide behind Python coercion or mutable graphs."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError, fields

import pytest


def contracts():
    assert importlib.util.find_spec("tests.audit_preparation_profile") is not None, "missing DTOs"
    return importlib.import_module("tests.audit_preparation_profile.contracts")


@pytest.mark.parametrize("value", [None, 0, 1, 2**53 + 1, 2**64 - 1, "UNBOUNDED"])
def test_known_zero_unlimited_and_unknown_are_distinct_values(value):
    c = contracts()
    item = c.LimitValue("memory_max_bytes", "byte", value)
    assert item.value == value and type(item.value) is type(value)
    assert item.status == "BLOCKED" and not item.H_executed
    assert not item.integrated_admission and item.content_identity_only
    assert item.atomicity == "NOT_ESTABLISHED"
    assert len(item.permissions) == 9 and all(flag is False for _, flag in item.permissions)
    assert not hasattr(item, "__dict__")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        item.value = 7


@pytest.mark.parametrize("value", [True, False, -1, 2**64, 1.0, float("nan"), "max", [], {}])
def test_limit_rejects_nonexact_integer_and_unknown_encodings(value):
    c = contracts()
    with pytest.raises(ValueError):
        c.LimitValue("memory_max_bytes", "byte", value)


@pytest.mark.parametrize(
    "name,args",
    [
        ("ArtifactPin", ("UNKNOWN", "1" * 64)),
        ("ArtifactPin", ("executor_content", "A" * 64)),
        ("ArtifactPin", ("executor_content", "1" * 63)),
        ("LimitValue", ("memory_max_bytes", "second", 1)),
        ("LimitValue", ("UNKNOWN", "byte", 1)),
        ("ControlClaim", ("subject_ro_enforced", 0)),
        ("ControlClaim", ("UNKNOWN", True)),
        ("CohortPin", ("X", None, None)),
        ("CohortPin", ("O", "x" * 40, None)),
        ("BoundaryRef", (None, True, None)),
        ("BoundaryRef", (None, None, "wall clock")),
        ("TimingClaim", (-1, None, None)),
        ("TimingClaim", (None, 1.5, None)),
        ("CommandProfile", ("UNKNOWN", "O", None, None, None)),
        ("ProfileReason", ("NOT_A_CODE", "policy")),
        ("ProfileReason", ("VALUE_UNAVAILABLE", "record./arbitrary/path")),
    ],
)
def test_malformed_primitive_context_is_rejected(name, args):
    with pytest.raises(ValueError):
        getattr(contracts(), name)(*args)


def test_tables_own_order_and_reject_duplicates_foreign_types_and_context():
    c = contracts()
    first = c.ArtifactPin("executor_content", None)
    last = c.ArtifactPin("scope_record", "1" * 64)
    supplied = (last, first)
    p = c.PreparationProfilePolicy(c.PROFILE, None, supplied, None, None, None, None, None)
    assert p.artifacts == (first, last) and p.artifacts is not supplied
    assert p.controls is None
    for items in ([first], (first, first), (object(),)):
        with pytest.raises(ValueError):
            c.PreparationProfilePolicy(c.PROFILE, None, items, None, None, None, None, None)
    with pytest.raises(ValueError):
        c.CommandProfile(
            "O-H6", "O", None, (c.LimitValue("batch_pids_max", "process_or_thread_count", 2),), None
        )

    class Foreign(c.ArtifactPin):
        pass

    with pytest.raises(ValueError):
        Foreign("executor_content", None)

    class Text(str):
        pass

    with pytest.raises(ValueError):
        c.ArtifactPin(Text("executor_content"), None)


def test_reason_category_deduplication_and_derived_consistency():
    c = contracts()
    error = c.ProfileReason("CONTROL_CLAIM_FALSE", "record.controls.subject_ro_enforced.value")
    missing = c.ProfileReason("POLICY_UNAVAILABLE", "policy")
    rejected = c.PreparationProfileDecision((error, error), (missing,))
    assert rejected.errors == (error,) and rejected.consistency == "REJECTED"
    assert c.PreparationProfileDecision((), (missing,)).consistency == "UNAVAILABLE"
    assert c.PreparationProfileDecision((), ()).consistency == "STRUCTURAL_PROFILE_MATCH"
    with pytest.raises(ValueError):
        c.PreparationProfileDecision((missing,), ())
    with pytest.raises(ValueError):
        c.PreparationProfileDecision((), (error,))
    assert [f.name for f in fields(c.PreparationProfileDecision)] == ["errors", "unavailable"]


@pytest.mark.parametrize("value", [None, False, True])
def test_control_unknown_is_not_false(value):
    c = contracts()
    assert c.ControlClaim("subject_ro_enforced", value).value is value
    assert c.BoundaryRef(None, 0, None).generation == 0
