"""Raw guest measurements must satisfy independent fixture-specific assertions."""

import importlib
import json

import pytest


def api():
    assert (
        importlib.util.find_spec("compatibility.containment_backend_harmless.host_cases")
        is not None
    )
    return importlib.import_module("compatibility.containment_backend_harmless.host_cases")


def test_actual_read_measurements_not_a_caller_pass_flag():
    validator = api().check_case
    data = {
        "fixture_id": "HF01",
        "passed": True,
        "measurements": {
            "fd_received": 7,
            "read_matches": True,
            "object_matches": True,
            "read_only": True,
            "broker_lookup_calls": 1,
            "continue_calls": 0,
        },
    }
    assert validator(data) == ()
    data["measurements"]["read_matches"] = False
    assert "READ_OR_OBJECT_MISMATCH" in validator(data)


def test_empty_capture_does_not_prove_zero():
    assert "MISSING_KERNEL_EVENT" in api().check_case(
        {
            "fixture_id": "HF13",
            "measurements": {
                "kernel_events": 0,
                "duplicate_detected": True,
                "drop_detected": True,
                "reorder_detected": True,
            },
        }
    )


def test_listener_loss_is_not_tree_exit():
    data = {
        "fixture_id": "HF15",
        "measurements": {
            "listener_errno": 38,
            "alive_after_errno": True,
            "tree_exit_observed": False,
        },
    }
    assert "TREE_EXIT_NOT_OBSERVED" in api().check_case(data)
    data["measurements"]["tree_exit_observed"] = True
    assert api().check_case(data) == ()


def test_descriptor_zero_is_a_real_successful_descriptor():
    assert (
        api().check_case(
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
        == ()
    )


@pytest.mark.parametrize("fixture", ["HF00", "HF25", "bad"])
def test_unknown_or_incomplete_case_rejected(fixture):
    with pytest.raises(ValueError):
        api().check_case({"fixture_id": fixture, "measurements": {}})


def test_raw_log_requires_unique_complete_actual_records():
    line = "RAW_FIXTURE " + json.dumps({"fixture_id": "HF01", "measurements": {}})
    with pytest.raises(ValueError):
        api().parse_guest_log(line + "\n" + line, ("HF01",))
    with pytest.raises(ValueError):
        api().parse_guest_log("GUEST_HARNESS_DONE", ("HF01",))


@pytest.mark.parametrize("status", [None, "1", "-9", "0\nHARNESS_EXIT HF01 0"])
def test_missing_failed_or_duplicate_exit_is_not_a_complete_run(status):
    raw = 'RAW_FIXTURE {"fixture_id":"HF01","measurements":{}}\n'
    if status is not None:
        raw += f"HARNESS_EXIT HF01 {status}\n"
    with pytest.raises(ValueError):
        api().parse_guest_log(raw + "GUEST_HARNESS_DONE", ("HF01",))


@pytest.mark.parametrize(
    "value",
    [
        '{"fixture_id":"HF01","fixture_id":"HF01","measurements":{}}',
        '{"fixture_id":"HF01","measurements":{"x":NaN}}',
        '{"fixture_id":"HF01","measurements":{"x":1e999}}',
    ],
)
def test_ambiguous_or_nonfinite_raw_json_rejects(value):
    with pytest.raises(ValueError):
        api().parse_guest_log(
            "RAW_FIXTURE " + value + "\nHARNESS_EXIT HF01 0\nGUEST_HARNESS_DONE", ("HF01",)
        )
