"""Batch summaries are recomputed from frames, never host-provided success flags."""

import importlib
import json
from dataclasses import replace

import pytest

from tests.fixtures.guest_collector import simple_events, wire


def api():
    assert importlib.util.find_spec("compatibility.containment_guest_collector.batch")
    return importlib.import_module("compatibility.containment_guest_collector.batch")


def batch(events=None):
    measurement = {
        "fixture_id": "HF01",
        "measurements": {
            "fd_received": 0,
            "read_matches": True,
            "object_matches": True,
            "read_only": True,
            "broker_lookup_calls": 1,
            "continue_calls": 0,
        },
    }
    return (
        "GUEST_CASE_BEGIN HF01\n"
        + wire(events)
        + "\nRAW_FIXTURE "
        + json.dumps(measurement)
        + "\nHARNESS_EXIT HF01 0\nGUEST_HARNESS_DONE\nGUEST_CASE_END HF01\n"
        + 'CAPTURE_ASSESSMENT {"fixture_id":"HF01","capture_complete":true}\n'
    )


def test_batch_recomputes_case_and_preserves_unknown_global_counts():
    cases = api().assess_batch(batch(), ("HF01",))
    assert len(cases) == 1
    assert cases[0].capture.fixture_id == "HF01"
    assert cases[0].assessment.capture_complete
    assert cases[0].harmless_assertion_failures == ()
    assert cases[0].assessment.successful_prohibited_handles is None
    assert cases[0].assessment.successful_prohibited_effects is None


def test_producer_success_summary_cannot_replace_missing_syscall_entry():
    events = simple_events()
    del events[2]
    case = api().assess_batch(batch(events), ("HF01",))[0]
    assert not case.assessment.capture_complete
    assert "CALL_WITHOUT_ENTRY" in case.assessment.reasons


def test_case_envelope_defensively_freezes_reasons_and_rejects_mutable_evidence():
    case = api().assess_batch(batch(), ("HF01",))[0]
    reasons = ["MISSING"]
    copied = replace(case, harmless_assertion_failures=reasons)
    reasons.clear()
    assert copied.harmless_assertion_failures == ("MISSING",)
    with pytest.raises(ValueError):
        replace(case, assessment={"capture_complete": True})


@pytest.mark.parametrize(
    "raw,selected",
    [
        ("", ("HF01",)),
        (batch(), ()),
        (batch(), ("HF01", "HF01")),
        (batch(), ("HF02",)),
        (batch() + batch(), ("HF01",)),
        (batch().replace("GUEST_CASE_END HF01", "GUEST_CASE_END HF02"), ("HF01",)),
        (batch().replace("GUEST_CASE_BEGIN HF01", "GUEST_CASE_BEGIN HF25"), ("HF01",)),
        (batch().replace("HARNESS_EXIT HF01 0", "HARNESS_EXIT HF01 1"), ("HF01",)),
    ],
)
def test_incomplete_duplicate_or_unselected_run_is_not_admitted(raw, selected):
    with pytest.raises(ValueError):
        api().assess_batch(raw, selected)
