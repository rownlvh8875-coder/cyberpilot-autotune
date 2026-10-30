"""A matching current snapshot must never become historical execution authority."""

import importlib
from dataclasses import FrozenInstanceError, asdict, replace

import pytest

from tests.fixtures.guest_closure import image_bytes


def api():
    assert importlib.util.find_spec("compatibility.guest_input_closure.evaluation") is not None
    return (
        importlib.import_module("compatibility.guest_input_closure.contracts"),
        importlib.import_module("compatibility.guest_input_closure.evaluation"),
    )


def test_matching_current_bytes_and_elf_graph_still_leave_full_closure_blocked():
    c, m = api()
    result = m.evaluate_closure(c.InputSnapshot([]), c.InputSnapshot([]), (image_bytes(),))
    assert result.declared_inputs_match and result.guest_elf_dependencies_closed
    assert result.overall_status == "BLOCKED"
    assert result.entry_count == 0 and result.image_count == 1
    assert result.issues == ()
    assert set(result.blockers) >= {
        "HISTORICAL_BUILD_CONSUMPTION_UNPROVEN",
        "HOST_COMPILER_CLOSURE_UNQUALIFIED",
        "HOST_PYTHON_CLOSURE_UNQUALIFIED",
        "QEMU_DYNAMIC_INPUTS_UNQUALIFIED",
        "EXECUTION_INPUT_IMMUTABILITY_UNPROVEN",
        "COLLECTOR_AUTHENTICITY_UNQUALIFIED",
        "DYNAMIC_LOAD_BEHAVIOR_UNQUALIFIED",
        "HISTORICAL_EXECUTED_IMAGE_BINDING_UNPROVEN",
    }
    for key in (
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert asdict(result)[key] is False
    assert result.successful_prohibited_handles is None
    assert result.successful_prohibited_effects is None
    with pytest.raises(FrozenInstanceError):
        result.application_authorized = True
    with pytest.raises(ValueError):
        replace(result, application_authorized=True)


def test_missing_or_malformed_images_are_not_a_closed_graph():
    c, m = api()
    for images in ((), (b"broken",)):
        result = m.evaluate_closure(c.InputSnapshot([]), c.InputSnapshot([]), images)
        assert not result.guest_elf_dependencies_closed and result.issues
        assert result.overall_status == "BLOCKED"


def test_report_does_not_hide_a_real_input_difference_behind_valid_images():
    c, m = api()
    a = c.InputEntry("source", "a", "directory", 0o040755, 0, None, None)
    result = m.evaluate_closure(c.InputSnapshot([a]), c.InputSnapshot([]), (image_bytes(),))
    assert not result.declared_inputs_match
    assert result.issues == ("INPUT_MISSING:source/a",)
