"""I1: one immutable byte range cannot return contradictory observed hashes."""

from dataclasses import replace
from hashlib import sha256

import pytest

from compatibility.guest_build_receipt.evaluation import evaluate_receipts
from tests.fixtures.guest_build_receipt import SHA_A, SHA_B, build, promotion


def repeated_partial_read(*, other_task, second_hash, offset=0):
    b = build()
    source = replace(b.materials[1], size=2, sha256=sha256(b"ab").hexdigest())
    first = b.uses[1]
    second = replace(first, sequence=3, time_ns=22, range_digest=second_hash, offset=offset)
    images = b.images
    if other_task:
        images = (
            *images,
            replace(images[0], task_generation=2, parent_generation=1, start_ns=21, finish_ns=90),
        )
        second = replace(second, task_generation=2)
    return replace(
        b, materials=(b.materials[0], source), images=images, uses=(b.uses[0], first, second)
    )


@pytest.mark.parametrize("other_task", [False, True])
def test_same_immutable_range_rejects_conflicting_hashes_even_across_tasks(other_task):
    b = repeated_partial_read(other_task=other_task, second_hash=SHA_B)
    d = evaluate_receipts(b, (promotion(b),))
    assert d.status == "REJECTED" and "CONFLICTING_READ_HASHES" in d.reasons
    assert d.build_execution_allowed is False and d.promotion_authorized is False


@pytest.mark.parametrize("other_task", [False, True])
def test_repeated_equal_range_hashes_remain_consistent_without_inventing_authority(other_task):
    b = repeated_partial_read(other_task=other_task, second_hash=SHA_A)
    d = evaluate_receipts(b, (promotion(b),))
    assert d.status == "DIAGNOSTIC_CHAIN_CONSISTENT" and d.reasons == ()
    assert d.overall_status == "BLOCKED" and d.read_events == 2


def test_different_partial_ranges_can_contain_different_bytes():
    b = repeated_partial_read(other_task=False, second_hash=SHA_B, offset=1)
    assert evaluate_receipts(b, (promotion(b),)).status == "DIAGNOSTIC_CHAIN_CONSISTENT"
