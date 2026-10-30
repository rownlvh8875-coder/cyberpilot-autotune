"""Synthetic source counterexamples, not observed kernel or transport evidence."""

from dataclasses import FrozenInstanceError, replace

import pytest

from tests.audit.kernel_lifetime_witness import CpuLedger, analyze_copy, assess_loss, copy_orders


@pytest.mark.parametrize(
    "order,copied,has_cut",
    [
        (("R0", "R1", "W0", "W1"), (False, False), True),
        (("R0", "W0", "R1", "W1"), (False, False), True),
        (("R0", "W0", "W1", "R1"), (False, True), False),
        (("W0", "R0", "R1", "W1"), (True, False), True),
        (("W0", "R0", "W1", "R1"), (True, True), True),
        (("W0", "W1", "R0", "R1"), (True, True), True),
    ],
)
def test_copy_of_two_reserved_slots_need_not_have_an_atomic_cut(order, copied, has_cut):
    result = analyze_copy(order)
    assert result.copied == copied
    assert result.source_states == ((False, False), (True, False), (True, True))
    assert result.has_cut is has_cut
    with pytest.raises(FrozenInstanceError):
        result.has_cut = True


def test_copy_enumeration_covers_exactly_six_program_order_interleavings():
    orders = copy_orders()
    assert len(orders) == len(set(orders)) == 6
    assert [order for order in orders if not analyze_copy(order).has_cut] == [
        ("R0", "W0", "W1", "R1")
    ]


@pytest.mark.parametrize(
    "order",
    [
        (),
        ("R0", "R1", "W0"),
        ("R1", "R0", "W0", "W1"),
        ("R0", "R1", "W1", "W0"),
        ("R0", "R0", "W0", "W1"),
        ("R0", "R1", "W0", "X"),
        ["R0", "R1", "W0", "W1"],
    ],
)
def test_copy_witness_rejects_invalid_or_out_of_profile_schedule(order):
    with pytest.raises(ValueError):
        analyze_copy(order)


def complete(cpu=0):
    return CpuLedger(
        cpu,
        attempted=2,
        reserve_failed=0,
        reserved=2,
        committed=2,
        discarded=0,
        pending=0,
        received=2,
        armed=True,
        drained=True,
    )


def test_consistent_simulated_loss_ledger_is_not_an_observer_qualification():
    assert assess_loss((complete(), complete(260)), (0, 260)) == ()
    # A coherent fabricated/wholly omitted history is intentionally undetectable.
    empty = replace(complete(), attempted=0, reserved=0, committed=0, received=0)
    assert assess_loss((empty,), (0,)) == ()


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"attempted": None}, "UNKNOWN_COUNTER"),
        ({"attempted": True}, "INVALID_COUNTER"),
        ({"attempted": 2.0}, "INVALID_COUNTER"),
        ({"received": -1}, "INVALID_COUNTER"),
        ({"pending": 2**64}, "INVALID_COUNTER"),
        ({"attempted": 3}, "ATTEMPT_ACCOUNTING_MISMATCH"),
        ({"reserved": 3, "attempted": 3}, "RESERVATION_ACCOUNTING_MISMATCH"),
        ({"attempted": 3, "reserve_failed": 1}, "RESERVE_FAILURE"),
        ({"discarded": 1, "committed": 1, "received": 1}, "DISCARDED_EVENT"),
        ({"pending": 1, "committed": 1, "received": 1}, "PENDING_RESERVATION"),
        ({"received": 1}, "DELIVERY_MISMATCH"),
        ({"armed": None}, "UNPROVEN_ARM_DRAIN"),
        ({"drained": False}, "UNPROVEN_ARM_DRAIN"),
        ({"armed": 1}, "UNPROVEN_ARM_DRAIN"),
    ],
)
def test_loss_ledger_rejects_unknowns_failures_and_unclosed_accounting(changes, reason):
    assert reason in assess_loss((replace(complete(), **changes),), (0,))


@pytest.mark.parametrize(
    "rows,cpus,reason",
    [
        ((complete(),), (0, 1), "CPU_COHORT_MISMATCH"),
        ((complete(), complete()), (0,), "CPU_COHORT_MISMATCH"),
        ((complete(),), (0, 0), "CPU_COHORT_INVALID"),
        ((complete(),), (False,), "CPU_COHORT_INVALID"),
        ((complete(),), (), "CPU_COHORT_INVALID"),
        ((complete(-1),), (0,), "CPU_COHORT_MISMATCH"),
        ((complete(True),), (0,), "CPU_COHORT_MISMATCH"),
        ((complete(),), (2**32,), "CPU_COHORT_INVALID"),
        ([complete()], (0,), "INVALID_LEDGER"),
        ((None,), (0,), "INVALID_LEDGER"),
    ],
)
def test_loss_ledger_requires_unique_complete_cpu_cohort(rows, cpus, reason):
    assert reason in assess_loss(rows, cpus)
