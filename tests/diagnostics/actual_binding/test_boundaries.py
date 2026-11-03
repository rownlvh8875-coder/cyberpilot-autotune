"""Unknown/contradictory nested metadata never acquires an implicit default."""

import copy

import pytest

from cyberpilot_autotune.diagnostics.actual_binding import assess_actual_binding
from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    clock,
    complete_vector,
    document,
)


def assess(v):
    return assess_actual_binding(v.bundle, expected_pre=v.pre, expected_post=v.post)


@pytest.mark.parametrize(
    "value",
    (
        None,
        {},
        clock(context_status="OTHER"),
        clock(context_status="UNAVAILABLE"),
        clock(generation=False),
        clock(cohort_sha256=None),
        clock(context_material_sha256="x" * 64),
    ),
)
def test_bad_clock_shape_does_not_default_cohort(value):
    r = assess(complete_vector(header_changes={"exit": {"host_clock_context": value}}))
    assert r.structural_status == "REJECTED" and "DOCUMENT_SHAPE_INVALID" in r.reasons


@pytest.mark.parametrize("fds", ([False], [-1], [2**31], "0", [0, 0]))
def test_bad_fd_array_does_not_normalize_to_expected(fds):
    profile = copy.deepcopy(
        document(complete_vector(), "baseline")["body"]["declared_case_profile"]
    )
    profile["expected_fds"] = fds
    r = assess(complete_vector(body_changes={"baseline": {"declared_case_profile": profile}}))
    assert r.structural_status == "REJECTED" and "DOCUMENT_SHAPE_INVALID" in r.reasons


@pytest.mark.parametrize(
    "desc",
    (
        None,
        {"availability": "PRESENT", "byte_length": 0},
        {"availability": "UNAVAILABLE", "byte_length": 0, "sha256": None},
        {"availability": "UNAVAILABLE", "byte_length": None, "sha256": "0" * 64},
        {"availability": "PRESENT", "byte_length": False, "sha256": "0" * 64},
        {"availability": "PRESENT", "byte_length": 0, "sha256": None},
        {"availability": "OTHER", "byte_length": None, "sha256": None},
    ),
)
def test_descriptor_shape_preserves_unknown_zero_and_false(desc):
    descriptors = copy.deepcopy(document(complete_vector(), "snapshot")["body"]["raw_descriptors"])
    descriptors["cli_stderr"] = desc
    r = assess(complete_vector(body_changes={"snapshot": {"raw_descriptors": descriptors}}))
    assert r.structural_status == "REJECTED" and "DOCUMENT_SHAPE_INVALID" in r.reasons


def test_entire_raw_descriptor_map_unavailable_is_not_zero_mapping():
    r = assess(complete_vector(body_changes={"snapshot": {"raw_descriptors": None}}))
    assert r.structural_status == "REJECTED" and "DOCUMENT_SHAPE_INVALID" in r.reasons


def test_missing_intent_reference_hash_is_not_derived_from_input():
    r = assess(complete_vector(body_changes={"intent": {"pre_reference_content_sha256": None}}))
    assert r.structural_status == "INCOMPLETE" and "MISSING_CONTEXT" in r.reasons
    assert "HASH_MISMATCH" not in r.reasons


def test_unknown_host_observation_kind_does_not_become_observed():
    r = assess(
        complete_vector(body_changes={"exit": {"host_context_observation_kind": "UNAVAILABLE"}})
    )
    assert r.structural_status == "INCOMPLETE" and "MISSING_CONTEXT" in r.reasons


@pytest.mark.parametrize(
    "field,value",
    (
        ("pid", True),
        ("pid", -1),
        ("pid", 2**31),
        ("process_identity_sha256", "bad"),
        ("returncode", True),
        ("returncode", -(2**31) - 1),
        ("returncode", 2**31),
        ("termination", "OTHER"),
        ("observation_kind", "OTHER"),
    ),
)
def test_process_primitive_boundaries(field, value):
    process = copy.deepcopy(document(complete_vector(), "exit")["body"]["cli_observation"])
    process[field] = value
    r = assess(complete_vector(body_changes={"exit": {"cli_observation": process}}))
    assert r.structural_status == "REJECTED" and "DOCUMENT_SHAPE_INVALID" in r.reasons


@pytest.mark.parametrize("term,number", (("EXITED", 2**31 - 1), ("SIGNALLED", -(2**31))))
def test_signed_reported_boundary_is_not_execution_success(term, number):
    process = copy.deepcopy(document(complete_vector(), "exit")["body"]["cli_observation"])
    process.update(termination=term, returncode=number)
    r = assess(complete_vector(body_changes={"exit": {"cli_observation": process}}))
    assert r.structural_status == "REPORTED_BINDING_CONSISTENT"
    assert r.status == "BLOCKED" and r.content_status == "NOT_EVALUATED"
