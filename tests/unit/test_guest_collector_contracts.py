"""Malformed trace or caller metadata never becomes evidence authority."""

import importlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.guest_collector import wire


def api():
    assert importlib.util.find_spec("compatibility.containment_guest_collector") is not None
    return importlib.import_module("compatibility.containment_guest_collector.validation")


def test_real_event_shape_is_immutable_and_content_identity_only():
    module = api()
    capture = module.parse_capture(wire())
    assert capture.fixture_id == "HF01"
    assert len(capture.events) == 12
    assert capture.events[0].values == (0, 0)
    assert capture.evidence_kind == "UNTRUSTED_CAPTURE_REPORT"
    assert capture.successful_prohibited_handles is None
    assert capture.successful_prohibited_effects is None
    for name in (
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert getattr(capture, name) is False
        with pytest.raises(ValueError):
            replace(capture, **{name: True})
    with pytest.raises(FrozenInstanceError):
        capture.events[0].tid = 5
    values = [0, 0]
    copied = replace(capture.events[0], values=values)
    values.clear()
    assert copied.values == (0, 0)
    assert module.capture_digest(capture) == module.capture_digest(module.parse_capture(wire()))
    changed = replace(
        capture, events=(replace(capture.events[0], mono_ns=999),) + capture.events[1:]
    )
    assert module.capture_digest(capture) != module.capture_digest(changed)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x.replace('"version":"guest-syscall-fd-v1"', '"version":"other"'),
        lambda x: x.replace('"fixture_id":"HF01"', '"fixture_id":"HF25"'),
        lambda x: x.replace(
            '"clock_domain":"GUEST_TRACER_OBSERVATION_MONOTONIC_NS"', '"clock_domain":"wall-clock"'
        ),
        lambda x: x.replace('"task": 1', '"task": true', 1),
        lambda x: x.replace('"tid": 101', '"tid": -1', 1),
        lambda x: x.replace('"seq": 1', '"seq": 1.0', 1),
        lambda x: x.replace('"values": [0, 0]', '"values": [null, 0]', 1),
        lambda x: x.replace('"values": [0, 0]', '"values": [0, Infinity]', 1),
        lambda x: x.replace('"values": [0, 0]', '"values": [0, 1e999]', 1),
        lambda x: x.replace('"kind": "BIRTH"', '"kind": "UNKNOWN"', 1),
        lambda x: x.replace('"seq": 1', '"seq": 1, "seq": 1', 1),
        lambda x: x.replace('"seq": 1', '"seq": 1, "approved": true', 1),
        lambda x: x.replace('"values": [0, 0]', '"values": [0]', 1),
        lambda x: x.rsplit("\n", 1)[0],
        lambda x: x + "\n" + x,
        lambda x: x + "\nTRACE_EVENT {}",
    ],
)
def test_ambiguous_unavailable_or_untyped_capture_rejected(mutation):
    with pytest.raises(ValueError):
        api().parse_capture(mutation(wire()))


def test_default_hf_log_without_kernel_capture_is_not_a_trace():
    with pytest.raises(ValueError):
        api().parse_capture('RAW_FIXTURE {"fixture_id":"HF01","measurements":{}}')


def test_order_of_json_keys_does_not_change_content_digest():
    module = api()
    raw = wire()
    lines = []
    for line in raw.splitlines():
        prefix, value = line.split(" ", 1)
        data = json.loads(value)
        lines.append(prefix + " " + json.dumps(dict(reversed(list(data.items())))))
    assert module.capture_digest(module.parse_capture(raw)) == module.capture_digest(
        module.parse_capture("\n".join(lines))
    )
