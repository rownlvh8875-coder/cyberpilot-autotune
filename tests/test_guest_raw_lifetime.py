"""Literal synthetic unit frames; actual guest artifacts are audited separately."""

import tracemalloc
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.guest_raw_lifetime.image import build_image
from tests.guest_raw_lifetime.model import assess, parse_serial


def frame(case="NORMAL", failed=0, capacity=128):
    return (
        "boot noise\nCPL_DRIVER ok=1 child=0\n"
        f"CPL_META version=1 case={case} release=6.12.113-cplife-v1 cpus=1 capacity={capacity}\n"
        f"CPL_COUNT attempted={2 + failed} reserved=2 committed=2 failed={failed} "
        "discarded=0 pending=0\n"
        "CPL_EVENT seq=1 kind=FILE_NEW table=0 ofd=1 old=0 fd=-1 flags=0 mono=10\n"
        f"CPL_EVENT seq={2 + failed} kind=FILE_FREE table=0 ofd=1 old=0 fd=-1 flags=0 mono=11\n"
        "CPL_END\n"
    ).encode()


def test_partial_actual_format_preserves_unknown_context_and_denies_authority():
    capture = parse_serial(frame())
    assert capture.events[0].table_id is None
    assert capture.events[0].file_id == 1
    assert capture.events[0].fd is None
    assert capture.events[0].flags == 0
    result = assess(capture)
    assert result.local_accounting_balanced is True
    assert result.local_loss_observed is False
    assert result.reasons == ()
    assert result.status == "BLOCKED"
    assert result.actual_global_drops is None
    assert all(value is False for _, value in result.permissions)
    with pytest.raises(FrozenInstanceError):
        result.status = "QUALIFIED"


def test_real_format_failure_is_visible_not_patched_into_a_lossless_stream():
    result = assess(parse_serial(frame("FORCED_LOSS", failed=1)))
    assert result.local_accounting_balanced is True
    assert result.local_loss_observed is True
    assert "LOCAL_RESERVATION_LOSS" in result.reasons
    assert "SOURCE_SEQUENCE_GAP" in result.reasons
    assert result.actual_global_drops is None


@pytest.mark.parametrize(
    "old,new",
    [
        (b"attempted=2", b"attempted=3"),
        (b"reserved=2", b"reserved=3"),
        (b"committed=2", b"committed=3"),
        (b"discarded=0", b"discarded=1"),
        (b"pending=0", b"pending=1"),
    ],
)
def test_counter_or_transport_contradiction_cannot_be_considered_balanced(old, new):
    result = assess(parse_serial(frame().replace(old, new)))
    assert result.local_accounting_balanced is False
    assert result.reasons


@pytest.mark.parametrize(
    "old,new",
    [
        (b"seq=2", b"seq=1"),
        (b"kind=FILE_NEW", b"kind=APPLIED_TORQUE"),
        (b"table=0", b"table=-1"),
        (b"ofd=1", b"ofd=True"),
        (b"flags=0", b"flags=0.0"),
        (b"flags=0", b"flags=4294967296"),
        (b"fd=-1", b"fd=2147483648"),
        (b"mono=10", b"mono=18446744073709551616"),
        (b"cpus=1", b"cpus=2"),
        (b"version=1", b"version=2"),
        (b"case=NORMAL", b"case=ARBITRARY"),
        (b"release=6.12.113-cplife-v1", b"release=host-kernel"),
        (b"capacity=128", b"capacity=99999"),
        (b"ok=1", b"ok=0"),
        (b"CPL_END\n", b""),
        (b"CPL_END\n", b"CPL_END\nCPL_END\n"),
        (b"reserved=2 committed", b"reserved=2 reserved=2 committed"),
        (b"CPL_COUNT", b"CPL_UNKNOWN"),
    ],
)
def test_unknown_malformed_or_wrong_cohort_frame_is_rejected(old, new):
    with pytest.raises(ValueError):
        parse_serial(frame().replace(old, new))


def test_scope_control_cases_are_fixed_and_image_is_deterministic():
    binary = b"\x7fELF\x02\x01" + b"fixed synthetic image bytes"
    image = build_image(binary, "NORMAL")
    assert image == build_image(binary, "NORMAL")
    assert image != build_image(binary, "FORCED_LOSS")
    with pytest.raises(ValueError):
        build_image(binary, "RUN_HOST_COMMAND")
    with pytest.raises(ValueError):
        build_image(b"#!/bin/sh\n", "NORMAL")


def test_truncated_non_utf8_or_oversized_serial_is_rejected():
    for raw in (b"", b"\xff", b"x" * (1024 * 1024 + 1)):
        with pytest.raises(ValueError):
            parse_serial(raw)


def test_fabricated_large_attempt_counter_does_not_expand_a_sequence_vector():
    capture = replace(parse_serial(frame()), attempted=100000)
    tracemalloc.start()
    try:
        result = assess(capture)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert result.local_accounting_balanced is False
    assert peak < 100000  # memory resource regression, not an empirical admission threshold
