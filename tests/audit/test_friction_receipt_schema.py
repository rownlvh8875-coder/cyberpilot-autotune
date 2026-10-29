"""Semantic schema inventory is complete but is never an actual cereal schema."""

import copy
from dataclasses import fields

import pytest

from cyberpilot_autotune.observability import schema


def test_semantic_schema_covers_every_nested_field_without_cereal_tags():
    manifest = schema.semantic_schema()
    expected = {cls.__name__ + "." + f.name for cls in schema.CONTRACT_TYPES for f in fields(cls)}
    assert {f["field"] for f in manifest["fields"]} == expected
    assert not manifest["runtime_producer_implemented"]
    assert manifest["wire_format"] == "PROPOSED_NO_CEREAL_TAG_ASSIGNMENTS"
    assert all(
        set(
            ("type", "unit", "stage", "required", "source", "availability", "qualification_meaning")
        )
        <= set(f)
        for f in manifest["fields"]
    )
    assert all("tag" not in f for f in manifest["fields"])
    byfield = {f["field"]: f for f in manifest["fields"]}
    assert "Float64" in byfield["ScalarObservation.value"]["type"]
    assert byfield["ControllerCallbackSignals.q_observed"]["required"] == "ELIGIBILITY"
    assert (
        byfield["ControllerStageDecomposition.applied_torque"]["stage"]
        == "APPLIED_NORMALIZED_TORQUE"
    )
    assert (
        byfield["InstalledParameters.friction_installed"]["qualification_meaning"]
        == "CONTEXT_ONLY_NOT_TRUTH_OR_TARGET"
    )
    assert byfield["InstalledParameters.offset_installed"]["required"] == "OPTIONAL"
    assert manifest == schema.semantic_schema()
    enums = {e["type"]: e["values"] for e in manifest["enums"]}
    assert "LINEAR_CALLBACK_PRE_PID" in enums["CallbackStage"]
    assert "REJECTED" in enums["EligibilityStatus"]


def test_schema_validator_rejects_semantic_precision_stage_and_permission_changes():
    for change in ("precision", "stage", "required", "missing", "authority"):
        manifest = copy.deepcopy(schema.semantic_schema())
        if change == "precision":
            next(f for f in manifest["fields"] if f["field"] == "ScalarObservation.value")[
                "type"
            ] = "Float32"
        elif change == "stage":
            next(
                f
                for f in manifest["fields"]
                if f["field"] == "ControllerStageDecomposition.applied_torque"
            )["stage"] = "RAW_CALLBACK_PRE_PID_KF"
        elif change == "required":
            next(
                f
                for f in manifest["fields"]
                if f["field"] == "ControllerCallbackSignals.q_observed"
            )["required"] = "OPTIONAL"
        elif change == "missing":
            manifest["fields"].pop()
        else:
            manifest["runtime_producer_implemented"] = True
        with pytest.raises(ValueError, match="SEMANTIC_SCHEMA_MUTATION"):
            schema.validate_semantic_schema(manifest)
