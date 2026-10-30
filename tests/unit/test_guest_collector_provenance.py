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


def test_successful_untraced_fork_without_birth_must_not_be_complete():
    events = simple_events()
    events = events[:2] + [
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 56, 0x800011, 0, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [1, 999]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [2, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    result = evaluate(events)
    assert not result.capture_complete
    assert "FORK_WITHOUT_BIRTH" in result.reasons


def test_enosys_with_live_listener_is_not_proof_of_listener_loss():
    events = donation_events()[:10] + [
        ("RETURN", 2, 102, 0, [2, -38]),
        ("ENTER", 2, 102, 0, [6, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 2, 102, 0, [0]),
        ("ABORT", 2, 102, 0, [6, 0]),
        ("EXIT", 2, 102, 0, [0]),
        ("ENTER", 1, 101, 0, [7, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [7, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    result = evaluate(events, tasks=2)
    assert not result.fd_profile_complete
    assert "FD_LISTENER_LOSS_UNPROVEN" in result.reasons


def test_pidfd_does_not_retarget_a_new_task_that_reuses_the_numeric_pid():
    base = [0, 0, 1, 10, 0o010600, 7, 4, 0x80000, 2, 30, 0o100600, 7]
    with_pidfd = base + [6, 0x80002, 2, 99, 0o100600, 7]
    events = [
        ("BIRTH", 1, 101, 0, [0, 0]),
        ("FDS", 1, 101, 0, [0, 2, *base]),
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 56, 17, 0, 0, 0, 0, 0]),
        ("BIRTH", 2, 102, 0, [1, 17]),
        ("FDS", 2, 102, 0, [0, 2, *base]),
        ("RETURN", 1, 101, 0, [1, 102]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 434, 102, 0, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [2, 6]),
        ("FDS", 1, 101, 0, [2, 3, *with_pidfd]),
        ("ENTER", 2, 102, 0, [3, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 2, 102, 0, [0]),
        ("ABORT", 2, 102, 0, [3, 0]),
        ("EXIT", 2, 102, 0, [0]),
        ("ENTER", 1, 101, 0, [4, 0xC000003E, 56, 17, 0, 0, 0, 0, 0]),
        ("BIRTH", 3, 102, 0, [1, 17]),
        ("FDS", 3, 102, 0, [0, 3, *with_pidfd]),
        ("RETURN", 1, 101, 0, [4, 102]),
        ("ENTER", 3, 102, 0, [5, 0xC000003E, 3, 4, 0, 0, 0, 0, 0]),
        ("RETURN", 3, 102, 0, [5, 0]),
        ("FDS", 3, 102, 0, [5, 2, *base[:6], *with_pidfd[12:]]),
        ("ENTER", 3, 102, 0, [6, 0xC000003E, 257, 2**64 - 100, 0x9000, 0x80000, 0, 0, 0]),
        ("RETURN", 3, 102, 0, [6, 4]),
        ("FDS", 3, 102, 0, [6, 3, *base[:6], 4, 0x80000, 1, 20, 0o100444, 7, *with_pidfd[12:]]),
        ("ENTER", 1, 101, 0, [7, 0xC000003E, 438, 6, 4, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [7, 7]),
        ("FDS", 1, 101, 0, [7, 4, *with_pidfd, 7, 0x80000, 1, 20, 0o100444, 7]),
        ("ENTER", 3, 102, 0, [8, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 3, 102, 0, [0]),
        ("ABORT", 3, 102, 0, [8, 0]),
        ("EXIT", 3, 102, 0, [0]),
        ("ENTER", 1, 101, 0, [9, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [9, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    result = evaluate(events, tasks=3)
    assert not result.fd_profile_complete
    assert "FD_PIDFD_TARGET_GENERATION_GONE" in result.reasons


@pytest.mark.parametrize("nr", [46, 47, 299, 307, 425, 426, 427])
def test_rights_passing_or_async_fd_mutation_is_not_qualified_by_no_snapshot_delta(nr):
    events = simple_events()[:2] + [
        ("ENTER", 1, 101, 0, [1, 0xC000003E, nr, 0, 0, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [1, -14]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [2, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    result = evaluate(events)
    assert result.capture_complete
    assert not result.fd_profile_complete
    assert "FD_ASYNC_OR_RIGHTS_PROFILE_UNSUPPORTED" in result.reasons


def test_unknown_ioctl_cannot_hide_partial_fd_effects_behind_an_error():
    events = simple_events()[:2] + [
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 16, 0, 0xDEADBEEF, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [1, -14]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [2, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    result = evaluate(events)
    assert result.capture_complete and not result.fd_profile_complete
    assert "FD_IOCTL_PROFILE_UNSUPPORTED" in result.reasons


@pytest.mark.parametrize("change_cloexec", [False, True])
def test_dup2_rebinds_same_inode_listener_even_when_snapshot_metadata_is_unchanged(change_cloexec):
    original = donation_events()
    # Initial fd4 is a different listener with identical anon-inode metadata.
    initial = [0, 0, 1, 10, 0o010600, 7, 4, 0, 2, 30, 0o100600, 7]
    both = [0, 0, 1, 10, 0o010600, 7, 3, 0x80000, 2, 30, 0o100600, 7, 4, 0, 2, 30, 0o100600, 7]
    prefix = [
        original[0],
        ("FDS", 1, 101, 0, [0, 2, *initial]),
        ("ENTER", 1, 101, 0, [8, 0xC000003E, 317, 1, 8, 0xD000, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [8, 3]),
        ("FDS", 1, 101, 0, [8, 3, *both]),
        ("ENTER", 1, 101, 0, [9, 0xC000003E, 33, 3, 4, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [9, 4]),
        ("FDS", 1, 101, 0, [9, 3, *both]),
    ]
    if change_cloexec:
        no_cloexec = list(both)
        no_cloexec[7] = 0
        prefix += [
            ("ENTER", 1, 101, 0, [10, 0xC000003E, 72, 3, 2, 0, 0, 0, 0]),
            ("RETURN", 1, 101, 0, [10, 0]),
            ("FDS", 1, 101, 0, [10, 3, *no_cloexec]),
        ]
    events = prefix
    for kind, task, tid, image, raw in original[2:]:
        values = list(raw)
        if kind == "FDS":
            call_id, count, *table = values
            records = {table[i]: table[i : i + 6] for i in range(0, 6 * count, 6)}
            records[4][1] = 0
            records[3] = [3, 0 if change_cloexec else 0x80000, 2, 30, 0o100600, 7]
            values = [
                call_id,
                count + 1,
                *[value for fd in sorted(records) for value in records[fd]],
            ]
        if kind == "ENTER" and values[0] == 5:
            values[3] = 3  # ADDFD uses alias3 while RECV used the rebound alias4.
        events.append((kind, task, tid, image, values))
    result = evaluate(events, tasks=2)
    assert result.capture_complete and result.fd_profile_complete
    assert result.donations == 1


def test_ofd_flag_mutation_is_not_silently_inside_the_fd_profile():
    events = simple_events()[:2] + [
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 72, 0, 4, 0x800, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [1, 0]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [2, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    assert "FD_FCNTL_PROFILE_UNSUPPORTED" in evaluate(events).reasons


def test_successful_setfd_requires_the_observed_cloexec_bit_to_match():
    events = simple_events()[:2] + [
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 72, 0, 2, 1, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [1, 0]),
        ("FDS", 1, 101, 0, [1, 1, 0, 0, 1, 10, 0o010600, 7]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [2, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
    assert "FD_FLAG_UPDATE_MISMATCH" in evaluate(events).reasons
