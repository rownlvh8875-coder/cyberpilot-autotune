"""Public API precedence and fixed negative qualification boundary."""

import importlib
import importlib.util
from dataclasses import replace

import pytest

from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    clock,
    complete_vector,
    mutate_document,
    replace_document,
)


def subject():
    assert (
        importlib.util.find_spec("cyberpilot_autotune.diagnostics.actual_binding.assessment")
        is not None
    ), "public assessor missing"
    return importlib.import_module(
        "cyberpilot_autotune.diagnostics.actual_binding.assessment"
    ).assess_actual_binding


def assess(v):
    return subject()(v.bundle, expected_pre=v.pre, expected_post=v.post)


def blocked(r):
    assert r.status == "BLOCKED" and r.content_status == "NOT_EVALUATED"
    assert r.provenance == "BLOCKED_NO_INDEPENDENT_VERIFICATION" and r.history == "UNAVAILABLE"
    assert r.integrated_admission is False
    assert len(r.permissions) == 9 and all(value is False for _, value in r.permissions)


def test_full_reported_consistency_is_still_blocked():
    r = assess(complete_vector())
    assert r.structural_status == "REPORTED_BINDING_CONSISTENT"
    assert r.reasons == r.not_evaluated_checks == ()
    blocked(r)


def test_reject_beats_incomplete_and_clock_change():
    v = complete_vector(
        header_changes={"exit": {"host_clock_context": clock(generation=1)}},
        raw_changes={"cli_stderr": None},
    )
    v = mutate_document(
        v,
        "snapshot",
        lambda d: d["header"]["permissions"].__setitem__("application_authorized", True),
    )
    r = assess(v)
    assert r.structural_status == "REJECTED"
    assert {"PERMISSION_ESCALATION", "MISSING_RAW", "CLOCK_CONTEXT_CHANGED"} <= set(r.reasons)
    blocked(r)


def test_independent_conflict_survives_bad_root():
    v = replace_document(complete_vector(), "baseline", b"bad")
    v = mutate_document(
        v,
        "snapshot",
        lambda d: d["header"]["permissions"].__setitem__("application_authorized", True),
    )
    r = assess(v)
    assert {"PARSE_INVALID", "PERMISSION_ESCALATION"} <= set(r.reasons)
    assert {"document:baseline", "assets"} <= set(r.not_evaluated_checks)
    assert r.structural_status == "REJECTED"
    blocked(r)


def test_explicit_none_reference_and_document_incomplete():
    v = complete_vector()
    r = subject()(v.bundle, expected_pre=None, expected_post=None)
    assert r.structural_status == "INCOMPLETE"
    assert {"MISSING_PRE_REFERENCE", "MISSING_POST_REFERENCE"} <= set(r.reasons)
    blocked(r)
    r = assess(replace_document(v, "exit", None))
    assert r.structural_status == "INCOMPLETE" and "MISSING_DOCUMENT" in r.reasons
    assert "process_state" in r.not_evaluated_checks


def test_all_reported_statuses_have_fixed_facets():
    vectors = (
        complete_vector(),
        complete_vector(raw_changes={"cli_stderr": None}),
        complete_vector(header_changes={"snapshot": {"host_clock_context": clock(generation=1)}}),
        replace_document(complete_vector(), "baseline", b"bad"),
    )
    assert [assess(v).structural_status for v in vectors] == [
        "REPORTED_BINDING_CONSISTENT",
        "INCOMPLETE",
        "REPORTED_TIME_ORDER_UNCOMPARABLE",
        "REJECTED",
    ]
    for v in vectors:
        blocked(assess(v))


def test_public_arguments_and_result_invariants():
    fn = subject()
    v = complete_vector()
    with pytest.raises(TypeError):
        fn(v.bundle)
    with pytest.raises(TypeError):
        fn(v.bundle, v.pre, v.post)
    with pytest.raises(TypeError):
        fn(v.bundle, expected_pre=v.pre, expected_post=v.post, reference_factory=lambda: v.pre)
    for bad in (False, {}, [], object()):
        with pytest.raises(ValueError):
            fn(bad, expected_pre=v.pre, expected_post=v.post)
        with pytest.raises(ValueError):
            fn(v.bundle, expected_pre=bad, expected_post=v.post)
        with pytest.raises(ValueError):
            fn(v.bundle, expected_pre=v.pre, expected_post=bad)


def test_foreign_reference_before_any_attribute_hooks():
    touched = []

    class SevenInputReference:
        def __getattribute__(self, name):
            touched.append(name)
            raise AssertionError("foreign accessor")

    v = complete_vector()
    with pytest.raises(ValueError):
        subject()(v.bundle, expected_pre=SevenInputReference(), expected_post=v.post)
    assert touched == []


def test_public_named_order_does_not_change_result():
    v = complete_vector()
    other = replace(
        v, bundle=replace(v.bundle, documents=v.bundle.documents[::-1], raw=v.bundle.raw[::-1])
    )
    assert assess(v) == assess(other)


def test_invalid_role_sets_never_consistent():
    v = complete_vector()
    v = replace(v, bundle=replace(v.bundle, raw=v.bundle.raw[:-1]))
    r = assess(v)
    assert r.structural_status == "REJECTED" and "ROLE_SET_INVALID" in r.reasons
    blocked(r)


def test_incomplete_does_not_hide_source_time_reversal():
    v = complete_vector(body_changes={"preflight": {"mono_ns": 100}, "intent": {"mono_ns": None}})
    r = assess(v)
    assert r.structural_status == "REJECTED"
    assert {"TIME_REVERSED", "CLOCK_CONTEXT_UNAVAILABLE"} <= set(r.reasons)


def test_coherent_malformed_raw_is_not_content_qualified():
    v = complete_vector(
        raw_changes={"record_json": b"\xff", "cli_stdout": b"{bad", "exit_receipt": b"bad"}
    )
    r = assess(v)
    assert r.structural_status == "REPORTED_BINDING_CONSISTENT"
    blocked(r)
