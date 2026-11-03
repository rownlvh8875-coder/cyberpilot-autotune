"""Reported clocks/processes never become causal, runtime or safety proof."""

import importlib
import importlib.util
from dataclasses import replace

import pytest

from cyberpilot_autotune.diagnostics.actual_binding._codec import decode_documents
from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    clock,
    complete_vector,
    document,
    replace_document,
    unavailable_clock,
)


def state(v, pre="DEFAULT"):
    assert (
        importlib.util.find_spec("cyberpilot_autotune.diagnostics.actual_binding._state")
        is not None
    ), "state checker missing"
    return importlib.import_module(
        "cyberpilot_autotune.diagnostics.actual_binding._state"
    ).check_state(decode_documents(v.bundle), v.pre if pre == "DEFAULT" else pre)


def proc(term, code, **kw):
    return (
        dict(
            observation_kind="TOOL_REPORTED",
            process_identity_sha256=None,
            pid=None,
            termination=term,
            returncode=code,
        )
        | kw
    )


def test_complete_state():
    assert state(complete_vector()).reasons == ()


@pytest.mark.parametrize("role", ("baseline", "command"))
def test_static_unavailable_clock_does_not_invent_incompleteness(role):
    assert (
        state(
            complete_vector(header_changes={role: {"host_clock_context": unavailable_clock()}})
        ).reasons
        == ()
    )


@pytest.mark.parametrize("role", ("preflight", "intent", "exit", "snapshot"))
def test_required_clock_unavailable(role):
    v = complete_vector(header_changes={role: {"host_clock_context": unavailable_clock()}})
    assert "CLOCK_CONTEXT_UNAVAILABLE" in state(v).reasons


@pytest.mark.parametrize(
    "field,value", (("host_clock_cohort_sha256", "9" * 64), ("host_clock_generation", 1))
)
def test_preflight_intent_expected_clock_mismatch(field, value):
    v = complete_vector()
    assert "CONTEXT_MISMATCH" in state(v, replace(v.pre, **{field: value})).reasons


def test_preflight_intent_material_mismatch():
    v = complete_vector(
        header_changes={"intent": {"host_clock_context": clock(context_material_sha256="f" * 64)}}
    )
    assert "CONTEXT_MISMATCH" in state(v).reasons


@pytest.mark.parametrize("role", ("exit", "snapshot"))
@pytest.mark.parametrize(
    "change",
    ({"cohort_sha256": "9" * 64}, {"generation": 1}, {"context_material_sha256": "a" * 64}),
)
def test_post_intent_clock_change_never_converts(role, change):
    v = complete_vector(header_changes={role: {"host_clock_context": clock(**change)}})
    r = state(v)
    assert "CLOCK_CONTEXT_CHANGED" in r.reasons
    assert "TIME_REVERSED" not in r.reasons


@pytest.mark.parametrize(
    "role,key",
    (
        ("preflight", "mono_ns"),
        ("intent", "mono_ns"),
        ("exit", "launch_before_ns"),
        ("exit", "launch_after_ns"),
        ("exit", "exit_observed_ns"),
        ("exit", "mono_ns"),
        ("snapshot", "mono_ns"),
    ),
)
def test_each_required_time_unavailable(role, key):
    assert (
        "CLOCK_CONTEXT_UNAVAILABLE"
        in state(complete_vector(body_changes={role: {key: None}})).reasons
    )


def test_present_times_compare_across_missing_middle():
    v = complete_vector(body_changes={"preflight": {"mono_ns": 10}, "intent": {"mono_ns": None}})
    assert {"TIME_REVERSED", "CLOCK_CONTEXT_UNAVAILABLE"} <= set(state(v).reasons)


def test_cross_clock_time_not_subtracted_but_same_clock_reversal_remains():
    v = complete_vector(
        header_changes={"exit": {"host_clock_context": clock(generation=1)}},
        body_changes={
            "preflight": {"mono_ns": 10},
            "intent": {"mono_ns": 1},
            "exit": {
                "launch_before_ns": 0,
                "launch_after_ns": 0,
                "exit_observed_ns": 0,
                "mono_ns": 0,
            },
        },
    )
    assert {"TIME_REVERSED", "CLOCK_CONTEXT_CHANGED"} <= set(state(v).reasons)


@pytest.mark.parametrize("number", (0, 2**64 - 1))
def test_zero_equal_uint64_times_allowed(number):
    changes = {r: {"mono_ns": number} for r in ("preflight", "intent", "exit", "snapshot")}
    changes["exit"].update(launch_before_ns=number, launch_after_ns=number, exit_observed_ns=number)
    assert state(complete_vector(body_changes=changes)).reasons == ()


@pytest.mark.parametrize(
    "term,code,expected",
    (
        ("EXITED", 0, None),
        ("EXITED", 2, None),
        ("EXITED", None, "MISSING_CONTEXT"),
        ("EXITED", -1, "PROCESS_STATE_CONFLICT"),
        ("SIGNALLED", -9, None),
        ("SIGNALLED", 0, "PROCESS_STATE_CONFLICT"),
        ("SIGNALLED", None, "MISSING_CONTEXT"),
        ("UNKNOWN", None, "MISSING_CONTEXT"),
        ("UNKNOWN", 0, "PROCESS_STATE_CONFLICT"),
        ("NOT_STARTED", None, "CAPTURE_STATE_CONFLICT"),
        ("NOT_STARTED", 0, "PROCESS_STATE_CONFLICT"),
    ),
)
def test_process_and_capture_coherence(term, code, expected):
    r = state(complete_vector(body_changes={"exit": {"cli_observation": proc(term, code)}}))
    assert r.reasons == () if expected is None else expected in r.reasons


@pytest.mark.parametrize(
    "extra",
    (
        {"pid": 1},
        {"process_identity_sha256": "0" * 64},
        {"observation_kind": "DIRECT_REAP_REPORTED"},
    ),
)
def test_not_started_cannot_have_actual_process_facts(extra):
    r = state(
        complete_vector(
            body_changes={"exit": {"cli_observation": proc("NOT_STARTED", None, **extra)}}
        )
    )
    assert "PROCESS_STATE_CONFLICT" in r.reasons


def test_unavailable_observation_not_actual_exit():
    good = proc("UNKNOWN", None, observation_kind="UNAVAILABLE")
    assert (
        "MISSING_CONTEXT"
        in state(complete_vector(body_changes={"exit": {"qemu_observation": good}})).reasons
    )
    bad = good | {"termination": "EXITED", "returncode": 0}
    assert (
        "PROCESS_STATE_CONFLICT"
        in state(complete_vector(body_changes={"exit": {"qemu_observation": bad}})).reasons
    )


@pytest.mark.parametrize(
    "outcome,stage,reason",
    (
        ("COMPLETE_REPORTED", "LAUNCH", "CAPTURE_STATE_CONFLICT"),
        ("PARTIAL_REPORTED", "NONE", "CAPTURE_STATE_CONFLICT"),
        ("FAILED_REPORTED", "NONE", "CAPTURE_STATE_CONFLICT"),
        ("PARTIAL_REPORTED", "COLLECT", "MISSING_CONTEXT"),
        ("FAILED_REPORTED", "LAUNCH", "MISSING_CONTEXT"),
    ),
)
def test_outcome_failure_stage_rules(outcome, stage, reason):
    r = state(
        complete_vector(body_changes={"exit": {"capture_outcome": outcome, "failure_stage": stage}})
    )
    assert reason in r.reasons


def test_launch_failure_preserves_unavailable_not_fabricated_values():
    v = complete_vector(
        body_changes={
            "exit": dict(
                capture_outcome="FAILED_REPORTED",
                failure_stage="LAUNCH",
                cli_observation=proc("NOT_STARTED", None),
                qemu_observation=proc("NOT_STARTED", None),
                launch_before_ns=None,
                launch_after_ns=None,
                exit_observed_ns=None,
            )
        }
    )
    r = state(v)
    assert {"MISSING_CONTEXT", "CLOCK_CONTEXT_UNAVAILABLE"} <= set(r.reasons)
    assert "CAPTURE_STATE_CONFLICT" not in r.reasons


def test_raw_closure_unavailable_is_incomplete():
    close = dict(document(complete_vector(), "exit")["body"]["raw_close_states"])
    close["console"] = "UNAVAILABLE"
    assert (
        "MISSING_CONTEXT"
        in state(complete_vector(body_changes={"exit": {"raw_close_states": close}})).reasons
    )


def test_unreadable_document_descendants_not_invented():
    v = replace_document(complete_vector(), "exit", b"bad")
    r = state(v)
    assert "process_state" in r.not_evaluated_checks
    assert "PROCESS_STATE_CONFLICT" not in r.reasons
