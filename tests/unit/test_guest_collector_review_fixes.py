"""Independent-review false-complete counterexamples: each must fail closed."""

import gzip
from dataclasses import replace
from pathlib import Path

import pytest

from compatibility.containment_guest_collector.batch import assess_batch
from compatibility.containment_guest_collector.evaluation import evaluate_capture
from compatibility.containment_guest_collector.validation import parse_capture
from tests.fixtures.guest_collector import donation_events, simple_events, wire


def evaluate(events, tasks=1):
    return evaluate_capture(parse_capture(wire(events, tasks=tasks)))


def end(call, image=0):
    return [
        ("ENTER", 1, 101, image, [call, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, image, [0]),
        ("ABORT", 1, 101, image, [call, 0]),
        ("EXIT", 1, 101, image, [0]),
    ]


def test_nonreturning_exit_cannot_have_a_successful_return():
    events = simple_events()
    events[10] = ("RETURN", 1, 101, 0, [3, 0])
    assert not evaluate(events).capture_complete


def test_signal_abort_must_match_actual_terminal_wait_status():
    events = simple_events()[:2] + [
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 0, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [1, 9]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    assert "ABORT_TERMINAL_STATUS_MISMATCH" in evaluate(events).reasons


def test_normal_exit_status_must_match_the_nonreturning_exit_argument():
    events = simple_events()
    values = list(events[8][4])
    values[3] = 7
    events[8] = (*events[8][:4], values)
    assert "EXIT_ARGUMENT_STATUS_MISMATCH" in evaluate(events).reasons


def test_execution_cannot_resume_after_terminal_stop():
    events = simple_events()
    events[11:11] = [
        ("ENTER", 1, 101, 0, [4, 0xC000003E, 39, 0, 0, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [4, 101]),
    ]
    assert "EVENT_AFTER_TERMINAL_STOP" in evaluate(events).reasons


def test_normal_exit_requires_an_observed_exit_call_not_just_matching_counters():
    events = simple_events()[:8] + [("PRE_EXIT", 1, 101, 0, [0]), ("EXIT", 1, 101, 0, [0])]
    assert not evaluate(events).capture_complete


def test_failed_exit_attempt_can_return_without_being_a_terminal_call():
    events = (
        simple_events()[:8]
        + [
            ("ENTER", 1, 101, 0, [3, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
            ("RETURN", 1, 101, 0, [3, -1]),
        ]
        + end(4)
    )
    assert evaluate(events).fd_profile_complete


def test_successful_exec_requires_a_generation_event():
    events = (
        simple_events()[:8]
        + [
            ("ENTER", 1, 101, 0, [3, 0xC000003E, 59, 0x9000, 0, 0, 0, 0, 0]),
            ("RETURN", 1, 101, 0, [3, 0]),
        ]
        + end(4)
    )
    assert "EXEC_EVENT_MISSING" in evaluate(events).reasons


@pytest.mark.parametrize("checkpoint", [None, 2])
def test_exec_fd_checkpoint_is_required_and_bound_to_that_exec_call(checkpoint):
    events = simple_events()[:8] + [
        ("ENTER", 1, 101, 0, [3, 0xC000003E, 59, 0x9000, 0, 0, 0, 0, 0]),
        ("EXEC", 1, 101, 1, [101]),
    ]
    if checkpoint is not None:
        events.append(("FDS", 1, 101, 1, [checkpoint, 1, 0, 0, 1, 10, 0o010600, 7]))
    events += [("RETURN", 1, 101, 1, [3, 0])] + end(4, 1)
    result = evaluate(events)
    assert not result.fd_profile_complete


@pytest.mark.parametrize("flags", [0x411, 0x800011])
def test_birth_flags_cannot_override_unsupported_flags_in_parent_clone(flags):
    events = donation_events()
    values = list(events[2][4])
    values[3] = flags
    events[2] = (*events[2][:4], values)
    assert "CLONE_FLAGS_MISMATCH" in evaluate(events, 2).reasons


def test_clone3_pointer_is_not_a_substitute_for_separately_observed_flags():
    events = donation_events()
    values = list(events[2][4])
    values[2] = 435
    values[3] = 0xF000
    events[2] = (*events[2][:4], values)
    assert "FD_CLONE3_FLAGS_UNAVAILABLE" in evaluate(events, 2).reasons


@pytest.mark.parametrize("result", [0, 1, 101])
def test_successful_x32_execution_is_not_a_native_fd_profile(result):
    events = (
        simple_events()[:8]
        + [
            ("ENTER", 1, 101, 0, [3, 0xC000003E, 0x40000000, 0, 0, 0, 0, 0, 0]),
            ("RETURN", 1, 101, 0, [3, result]),
        ]
        + end(4)
    )
    assert "UNSUPPORTED_X32_SUCCESS" in evaluate(events).reasons


def test_rejected_x32_attempt_remains_observable_without_native_execution():
    events = (
        simple_events()[:8]
        + [
            ("ENTER", 1, 101, 0, [3, 0xC000003E, 0x40000027, 0, 0, 0, 0, 0, 0]),
            ("RETURN", 1, 101, 0, [3, -1]),
        ]
        + end(4)
    )
    assert evaluate(events).fd_profile_complete


def test_scalar_acquisition_cannot_change_an_unrelated_existing_fd():
    events = simple_events()
    for index in (4, 7):
        values = list(events[index][4])
        values[5] = 999
        events[index] = (*events[index][:4], values)
    assert "FD_UNEXPLAINED_MUTATION" in evaluate(events).reasons


def test_dup2_result_must_be_the_requested_destination():
    events = simple_events()
    events[2] = ("ENTER", 1, 101, 0, [1, 0xC000003E, 33, 0, 4, 0, 0, 0, 0])
    assert "FD_DUP_DESTINATION_MISMATCH" in evaluate(events).reasons


def test_duplication_target_must_match_source_object_and_flags():
    events = simple_events()
    events[2] = ("ENTER", 1, 101, 0, [1, 0xC000003E, 32, 0, 0, 0, 0, 0, 0])
    assert "FD_DUP_SOURCE_MISMATCH" in evaluate(events).reasons


@pytest.mark.parametrize("nr,args", [(317, [1, 0, 0, 0, 0, 0]), (321, [15, 0, 0, 0, 0, 0])])
def test_status_only_seccomp_or_bpf_call_does_not_acquire_a_scalar_fd(nr, args):
    events = simple_events()
    events[2] = ("ENTER", 1, 101, 0, [1, 0xC000003E, nr, *args])
    assert not evaluate(events).fd_profile_complete


@pytest.mark.parametrize("field,value", [(5, 0), (5, 0x80001), (4, 7)])
def test_addfd_flag_dependent_fields_must_match_the_observed_target(field, value):
    events = donation_events()
    values = list(events[15][4])
    values[field] = value
    events[15] = (*events[15][:4], values)
    assert "FD_ADDFD_FLAGS_MISMATCH" in evaluate(events, 2).reasons


def test_addfd_without_cloexec_is_valid_only_with_a_matching_target():
    events = donation_events()
    values = list(events[15][4])
    values[5] = 0
    events[15] = (*events[15][:4], values)
    values = list(events[17][4])
    values[9] = 0
    events[17] = (*events[17][:4], values)
    assert evaluate(events, 2).fd_profile_complete


@pytest.mark.parametrize("kind", ["exit-return", "addfd-flags"])
def test_actual_hf01_cannot_be_made_complete_with_contradictory_receipts(kind):
    root = Path(__file__).resolve().parents[2]
    raw = gzip.decompress(
        (
            root / "compatibility/containment_guest_collector/evidence/actual-captures.txt.gz"
        ).read_bytes()
    ).decode()
    case = assess_batch(raw, tuple(f"HF{i:02d}" for i in range(1, 25)))[0]
    events = list(case.capture.events)
    for index, event in enumerate(events):
        if kind == "exit-return" and event.kind == "ABORT" and event.values[1] == 0:
            events[index] = replace(event, kind="RETURN", values=(event.values[0], 0))
            break
        if kind == "addfd-flags" and event.kind == "ADDFD" and event.values[6] >= 0:
            values = list(event.values)
            values[5] = 0
            events[index] = replace(event, values=tuple(values))
            break
    else:
        pytest.fail("actual case must contain the reviewed event")
    result = evaluate_capture(replace(case.capture, events=tuple(events)))
    assert not result.fd_profile_complete


@pytest.mark.parametrize("pending", [False, True])
def test_legitimate_signal_death_with_or_without_a_pending_call(pending):
    events = donation_events()[:6]
    if pending:
        events.append(("ENTER", 2, 102, 0, [2, 0xC000003E, 0, 0, 0, 0, 0, 0, 0]))
    events.append(("PRE_EXIT", 2, 102, 0, [9]))
    if pending:
        events.append(("ABORT", 2, 102, 0, [2, 9]))
    events += [("EXIT", 2, 102, 0, [9])] + end(3)
    assert evaluate(events, 2).fd_profile_complete


@pytest.mark.parametrize("status", [128, 127, 0x109, 0xFFFF, 0x10000])
def test_nonterminal_or_malformed_wait_status_cannot_close_a_lifetime(status):
    events = simple_events()
    events[9] = ("PRE_EXIT", 1, 101, 0, [status])
    events[11] = ("EXIT", 1, 101, 0, [status])
    assert "INVALID_TERMINAL_WAIT_STATUS" in evaluate(events).reasons


@pytest.mark.parametrize("result", [-2, 1])
def test_exec_event_cannot_accompany_a_failed_or_nonzero_exec_return(result):
    events = simple_events()[:8] + [
        ("ENTER", 1, 101, 0, [3, 0xC000003E, 59, 0x9000, 0, 0, 0, 0, 0]),
        ("EXEC", 1, 101, 1, [101]),
        ("FDS", 1, 101, 1, [3, 1, 0, 0, 1, 10, 0o010600, 7]),
        ("RETURN", 1, 101, 1, [3, result]),
    ]
    assert "EXEC_RESULT_MISMATCH" in evaluate(events + end(4, 1)).reasons


@pytest.mark.parametrize(
    "nr,args,flags",
    [
        (32, [0, 0, 0, 0, 0, 0], 0),
        (33, [0, 3, 0, 0, 0, 0], 0),
        (292, [0, 3, 0x80000, 0, 0, 0], 0x80000),
        (72, [0, 0, 3, 0, 0, 0], 0),
        (72, [0, 1030, 3, 0, 0, 0], 0x80000),
    ],
)
def test_valid_dup_variants_copy_the_object_with_exact_per_fd_flags(nr, args, flags):
    events = simple_events()
    events[2] = ("ENTER", 1, 101, 0, [1, 0xC000003E, nr, *args])
    values = list(events[4][4])
    values[9:14] = [flags, 1, 10, 0o010600, 7]
    events[4] = (*events[4][:4], values)
    assert evaluate(events).fd_profile_complete
    values[9] ^= 0x80000
    assert "FD_DUP_SOURCE_MISMATCH" in evaluate(events).reasons


def test_later_snapshot_cannot_replace_the_receipt_for_an_earlier_call():
    events = simple_events()
    events.insert(8, ("FDS", 1, 101, 0, list(events[7][4][:1]) + list(events[7][4][1:])))
    assert "FD_CHECKPOINT_CALL_MISMATCH" in evaluate(events).reasons
