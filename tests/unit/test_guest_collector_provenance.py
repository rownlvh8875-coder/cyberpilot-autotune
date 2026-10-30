"""Exact request/task/FD lineage, rather than similar inode or caller flags."""

import importlib

import pytest

from tests.fixtures.guest_collector import donation_events, simple_events, wire


def evaluate(events, tasks=1):
    assert importlib.util.find_spec("compatibility.containment_guest_collector")
    parser = importlib.import_module("compatibility.containment_guest_collector.validation")
    evaluator = importlib.import_module("compatibility.containment_guest_collector.evaluation")
    return evaluator.evaluate_capture(parser.parse_capture(wire(events, tasks=tasks)))


def test_actual_receipt_shape_binds_source_fd_to_notified_target_call():
    result = evaluate(donation_events(), tasks=2)
    assert result.capture_complete and result.fd_profile_complete
    assert (result.notifications, result.donations, result.task_count) == (1, 1, 2)


def test_an_older_identical_open_is_not_the_consumed_notification_call():
    events = []
    for kind, task, tid, image, raw in donation_events():
        values = list(raw)
        if (
            kind in {"ENTER", "RETURN", "ABORT", "FDS", "NOTIFY_RECV", "ADDFD", "NOTIFY_SEND"}
            and values[0] >= 2
        ):
            values[0] += 1
        events.append((kind, task, tid, image, values))
    events[6:6] = [
        ("ENTER", 2, 102, 0, [2, 0xC000003E, 257, 2**64 - 100, 0x8000, 0, 0, 0, 0]),
        ("RETURN", 2, 102, 0, [2, -2]),
    ]
    result = evaluate(events, tasks=2)
    assert result.capture_complete and result.fd_profile_complete


@pytest.mark.parametrize(
    "index,value,reason",
    [
        (1, 88, "FD_NOTIFICATION_ID_UNKNOWN"),
        (2, 0, "FD_ADDFD_NOT_ATOMIC_SEND"),
        (3, 7, "FD_ADDFD_SOURCE_UNKNOWN"),
        (6, 2, "FD_ADDFD_RESULT_MISMATCH"),
    ],
)
def test_similar_object_cannot_replace_exact_donation_provenance(index, value, reason):
    events = donation_events()
    values = list(events[15][4])
    values[index] = value
    events[15] = (*events[15][:4], values)
    result = evaluate(events, tasks=2)
    assert reason in result.reasons and not result.fd_profile_complete


@pytest.mark.parametrize(
    "index,value,reason",
    [
        (2, 999, "FD_NOTIFICATION_TARGET_UNKNOWN"),
        (4, 2, "FD_NOTIFICATION_CALL_MISMATCH"),
        (8, 0xDEAD, "FD_NOTIFICATION_CALL_MISMATCH"),
    ],
)
def test_consumed_notification_matches_pending_kernel_call_not_latest_pid(index, value, reason):
    events = donation_events()
    values = list(events[9][4])
    values[index] = value
    events[9] = (*events[9][:4], values)
    result = evaluate(events, tasks=2)
    assert reason in result.reasons and not result.fd_profile_complete


def test_matching_inode_without_addfd_receipt_does_not_prove_fd_delivery():
    events = donation_events()
    del events[15]
    result = evaluate(events, tasks=2)
    assert "FD_NOTIFICATION_RECEIPT_MISSING" in result.reasons
    assert not result.fd_profile_complete


def test_fork_child_seed_must_match_exact_inherited_fd_context():
    events = donation_events()
    events[4] = ("FDS", 2, 102, 0, [0, 1, 0, 0, 1, 999, 0o010600, 7])
    result = evaluate(events, tasks=2)
    assert "FD_INHERITANCE_MISMATCH" in result.reasons


def test_canceled_target_cannot_receive_successful_addfd():
    events = donation_events()
    killed = [("PRE_EXIT", 2, 102, 0, [9]), ("ABORT", 2, 102, 0, [2, 9]), ("EXIT", 2, 102, 0, [9])]
    events = events[:10] + killed + events[10:16] + events[22:]
    result = evaluate(events, tasks=2)
    assert "FD_ADDFD_TARGET_GONE" in result.reasons
    assert not result.fd_profile_complete


def test_fork_child_and_close_on_exec_have_separate_generations():
    events = simple_events()
    # fd3 has O_CLOEXEC and disappears at the actual exec event, not a fake close.
    events = events[:5] + [
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 59, 0x9000, 0, 0, 0, 0, 0]),
        ("EXEC", 1, 101, 1, [101]),
        ("FDS", 1, 101, 1, [2, 1, 0, 0, 1, 10, 0o010600, 7]),
        ("RETURN", 1, 101, 1, [2, 0]),
        ("ENTER", 1, 101, 1, [3, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 1, [0]),
        ("ABORT", 1, 101, 1, [3, 0]),
        ("EXIT", 1, 101, 1, [0]),
    ]
    result = evaluate(events)
    assert result.capture_complete and result.fd_profile_complete
    assert result.exec_count == 1


def test_close_on_exec_fd_cannot_silently_survive_exec():
    events = simple_events()
    events = events[:5] + [
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 59, 0x9000, 0, 0, 0, 0, 0]),
        ("EXEC", 1, 101, 1, [101]),
        ("FDS", 1, 101, 1, list(events[4][4][:1]) + list(events[4][4][1:])),
        ("RETURN", 1, 101, 1, [2, 0]),
        ("ENTER", 1, 101, 1, [3, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 1, [0]),
        ("ABORT", 1, 101, 1, [3, 0]),
        ("EXIT", 1, 101, 1, [0]),
    ]
    assert "FD_EXEC_TABLE_MISMATCH" in evaluate(events).reasons
