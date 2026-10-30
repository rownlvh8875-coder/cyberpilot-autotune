"""Hand-derived lifecycle and FD ledgers must reconcile, not trust producer flags."""

import importlib
import json

import pytest

from tests.fixtures.guest_collector import simple_events, wire


def evaluate(raw):
    assert importlib.util.find_spec("compatibility.containment_guest_collector") is not None
    validation = importlib.import_module("compatibility.containment_guest_collector.validation")
    module = importlib.import_module("compatibility.containment_guest_collector.evaluation")
    return module.evaluate_capture(validation.parse_capture(raw))


def test_hand_checked_open_close_exit_has_two_returns_and_one_terminal_abort():
    result = evaluate(wire())
    assert result.capture_complete and result.fd_profile_complete
    assert (result.task_count, result.call_pairs, result.aborted_calls, result.exec_count) == (
        1,
        2,
        1,
        0,
    )
    assert result.fd_transitions == 2
    assert result.reasons == ()
    assert not result.application_authorized and not result.runtime_qualified


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda e: e[:2] + e[3:], "CALL_WITHOUT_ENTRY"),
        (lambda e: e[:3] + [e[2]] + e[3:], "CALL_ALREADY_PENDING"),
        (lambda e: e[:-1], "TASK_NOT_REAPED"),
        (lambda e: e[:10] + e[11:], "PENDING_CALL_AT_EXIT"),
        (
            lambda e: (
                e[:4]
                + [
                    (
                        "FDS",
                        1,
                        101,
                        0,
                        [1, 2, 0, 0, 1, 10, 0o010600, 7, 4, 0x80000, 1, 20, 0o100444, 7],
                    )
                ]
                + e[5:]
            ),
            "FD_RETURN_MISMATCH",
        ),
        (
            lambda e: e[:4] + [("FDS", 1, 101, 0, [1, 1, 0, 0, 1, 10, 0o010600, 7])] + e[5:],
            "FD_RETURN_MISMATCH",
        ),
        (lambda e: e[:3] + [("RETURN", 1, 101, 0, [99, 3])] + e[4:], "CALL_ID_MISMATCH"),
        (lambda e: [("BIRTH", 1, 101, 0, [0, 0x400])] + e[1:], "FD_SHARED_TABLE_UNSUPPORTED"),
        (
            lambda e: (
                e[:2] + [("ENTER", 1, 101, 0, [1, 0x40000003, 257, 0, 0, 0, 0, 0, 0])] + e[3:]
            ),
            "WRONG_SYSCALL_ABI",
        ),
        (lambda e: e[:9] + [("EXEC", 1, 101, 3, [101])] + e[9:], "EXEC_GENERATION_MISMATCH"),
    ],
)
def test_specific_missing_or_wrong_evidence_fails_closed(mutation, reason):
    result = evaluate(wire(mutation(simple_events())))
    assert reason in result.reasons
    assert not result.fd_profile_complete


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("seq", 1, "SEQUENCE_MISMATCH"),
        ("mono_ns", 0, "CLOCK_ORDER_INVALID"),
        ("tid", 102, "TASK_IDENTITY_MISMATCH"),
        ("image", 2, "EXEC_GENERATION_MISMATCH"),
    ],
)
def test_duplicate_clock_tid_or_exec_generation_not_repaired(field, value, reason):
    lines = wire().splitlines()
    data = json.loads(lines[3].removeprefix("TRACE_EVENT "))
    data[field] = value
    lines[3] = "TRACE_EVENT " + json.dumps(data)
    result = evaluate("\n".join(lines))
    assert reason in result.reasons
    assert not result.capture_complete


@pytest.mark.parametrize(
    "field,value", [("events", 0), ("tasks", 2), ("live", 1), ("root_status", 9)]
)
def test_forged_end_counts_are_not_authority(field, value):
    lines = wire().splitlines()
    end = json.loads(lines[-1].removeprefix("TRACE_END "))
    end[field] = value
    lines[-1] = "TRACE_END " + json.dumps(end)
    assert not evaluate("\n".join(lines)).capture_complete


def test_fd_zero_is_installed_and_closed_with_a_real_generation():
    events = simple_events()
    events[1] = ("FDS", 1, 101, 0, [0, 0])
    events[3] = ("RETURN", 1, 101, 0, [1, 0])
    events[4] = ("FDS", 1, 101, 0, [1, 1, 0, 0x80000, 1, 20, 0o100444, 7])
    events[5] = ("ENTER", 1, 101, 0, [2, 0xC000003E, 3, 0, 0, 0, 0, 0, 0])
    events[7] = ("FDS", 1, 101, 0, [2, 0])
    result = evaluate(wire(events))
    assert result.fd_profile_complete and result.fd_transitions == 2


def test_killed_blocked_call_is_not_a_successful_return():
    events = simple_events()[:3] + [
        ("PRE_EXIT", 1, 101, 0, [9]),
        ("ABORT", 1, 101, 0, [1, 9]),
        ("EXIT", 1, 101, 0, [9]),
    ]
    result = evaluate(wire(events, root_status=9))
    assert result.call_pairs == 0 and result.aborted_calls == 1
    assert not result.capture_complete
