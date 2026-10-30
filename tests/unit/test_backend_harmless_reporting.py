"""Actual primitive assertions must not be promoted to complete-trace PASS."""

import importlib
from dataclasses import asdict

import pytest

from compatibility.containment_backend_harmless.validation import validate_harmless_result


def report(record):
    assert importlib.util.find_spec("compatibility.containment_backend_harmless.reporting")
    module = importlib.import_module("compatibility.containment_backend_harmless.reporting")
    return module.partial_report(record, "a" * 64, "b" * 64, "c" * 64, "d" * 64, "e" * 64)


def test_successful_read_with_unknown_trace_is_unavailable_not_pass():
    result = report(
        {
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
    )
    assert result.outcome == "UNAVAILABLE"
    assert result.actual_observations.trace_complete is None
    assert result.actual_observations.successful_prohibited_handles is None
    assert result.actual_observations.successful_prohibited_effects is None
    assert result.evidence_kind == "UNTRUSTED_FIXTURE_REPORT"


@pytest.mark.parametrize("fixture", ["HF17", "HF23", "HF24"])
def test_unsupported_never_qualifies_devices_or_writes(fixture):
    result = report({"fixture_id": fixture, "measurements": {}})
    assert result.outcome == "REJECTED"  # Failed assertions take precedence even over unsupported.
    assert not result.device_class_qualified
    assert not result.runtime_qualified


def test_empty_capture_is_rejected_not_zero_and_parser_round_trips():
    import json

    result = report({"fixture_id": "HF13", "measurements": {"kernel_events": 0}})
    assert result.outcome == "REJECTED"
    assert result.actual_observations.trace_complete is None
    assert result.actual_observations.successful_prohibited_handles is None
    assert validate_harmless_result(json.dumps(asdict(result))) == result


def test_listener_loss_records_reap_separately_from_complete_lineage():
    result = report(
        {
            "fixture_id": "HF15",
            "measurements": {
                "listener_errno": 38,
                "alive_after_errno": True,
                "tree_exit_observed": True,
            },
        }
    )
    assert result.outcome == "REJECTED"
    assert result.actual_observations.tree_exit_observed is True
    assert result.actual_observations.process_lineage_complete is None
