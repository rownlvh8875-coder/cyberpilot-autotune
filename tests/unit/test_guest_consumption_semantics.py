"""Failed targets and malformed provenance are not successful window repairs."""

from dataclasses import replace

import pytest

from tests.fixtures.guest_consumption import module, profile, rows, text


def produce(r, p=None):
    return module("producer").produce_receipt(
        module("wire").parse_capture(text(r)), profile() if p is None else p
    )


def test_observed_nonzero_exit_is_diagnostic_not_a_contradictory_closed_window():
    r = rows()
    r[-2]["values"] = ["EXITED", 1]
    o = produce(r)
    assert o.trace_window_complete and o.receipt.completion.exit_code == 1
    assert o.profile_reasons == ("PAYLOAD_NOT_SUCCESSFUL",)
    assert o.application_authorized is False


def test_profile_clock_cannot_relabel_guest_observation_times():
    p = profile()
    with pytest.raises(ValueError):
        produce(rows(), replace(p, identity=replace(p.identity, clock_domain="HOST_MONOTONIC_NS")))


def test_error_must_bind_the_actual_task_image_or_explicit_observer_scope():
    r = rows()
    r.insert(
        -1,
        dict(
            seq=13,
            time_ns=23,
            kind="ERROR",
            task=99,
            image=1,
            values=["RETURNED_BUFFER_UNAVAILABLE"],
        ),
    )
    r[-1].update(seq=14, time_ns=24, values=[False, 1, 2, 0])
    with pytest.raises(ValueError):
        produce(r)


def test_observation_cannot_replace_the_original_capture_with_an_unavailable_object():
    o = produce(rows())
    with pytest.raises(ValueError):
        replace(o, capture=None)


def test_target_observed_interval_starts_at_root_stop_not_observer_setup():
    o = produce(rows())
    assert o.receipt.start_ns == o.capture.events[2].time_ns
    r = [rows()[0], dict(rows()[-1], seq=2, time_ns=12, values=[False, 0, 0, None])]
    assert produce(r).receipt.start_ns is None
