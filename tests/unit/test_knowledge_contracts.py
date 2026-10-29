"""Descriptive metadata cannot acquire current values or application authority."""

from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.knowledge import REVISION, claim, parameter


def test_ui_unit_claim_is_separate_from_consumer_unit_and_transform():
    p = parameter(ui_unit_description="UI label scale differs from the consumer.")
    assert p.ui_unit_description != p.consumer_unit
    assert replace(p, ui_unit_description="Different descriptive label").digest != p.digest


def test_frozen_contracts_defensively_copy_nested_values():
    conditions, owners = ["synthetic torque mode"], []
    p = parameter(mode_conditions=conditions, evidence_gaps=owners)
    c = claim(conditions=conditions)
    conditions.append("later mutation")
    owners.append("later gap")
    assert p.mode_conditions == c.conditions == ("synthetic torque mode",)
    assert p.evidence_gaps == ()
    for value in (p, c):
        with pytest.raises(FrozenInstanceError):
            value.schema_version = 2


@pytest.mark.parametrize(
    "field", ["ui_default", "ui_catalog_min", "ui_catalog_max", "storage_scale"]
)
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), True, "1"])
def test_nonfinite_or_wrong_numeric_metadata_rejects(field, value):
    with pytest.raises(ValueError):
        parameter(**{field: value})


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": 2},
        {"domain": "longitudinal"},
        {"classification": "TUNING_CANDIDATE"},
        {"evidence_status": "PROVEN"},
        {"ui_catalog_min": 30},
        {"storage_scale": 0},
        {"canonical_unit": None},
        {"storage_scale": None},
        {"mode_conditions": None},
        {"consumer_claim_ids": []},
        {"descriptive_owner": ["EXCLUSIVE_OWNER_PROVEN"]},
    ],
)
def test_invalid_or_unproved_proven_metadata_rejects(changes):
    with pytest.raises(ValueError):
        parameter(**changes)


def test_unavailable_scale_unit_and_mode_do_not_become_one_or_unconditional():
    from cyberpilot_autotune.knowledge.contracts import Confidence

    p = parameter(
        storage_scale=None,
        canonical_unit=None,
        mode_conditions=None,
        evidence_status=Confidence.UNRESOLVED,
        evidence_gaps=["UNRESOLVED_INPUT"],
    )
    assert p.storage_scale is p.canonical_unit is p.mode_conditions is None
    assert p.digest != parameter(ui_default=0).digest
    assert replace(p, ui_default=0).ui_default == 0
    assert replace(p, ui_default=None).ui_default is None


@pytest.mark.parametrize(
    "changes",
    [
        {"exact_revision": "carrot-wip"},
        {"git_blob_sha": "abc"},
        {"source_range_sha256": "X" * 64},
        {"range_start": 0},
        {"range_end": 9},
        {"confidence": "PROVEN"},
        {"path": "../escape.py"},
        {"schema_version": True},
        {"conditions": []},
        {"supersedes_claim_id": "synthetic:kp"},
    ],
)
def test_source_claim_requires_exact_valid_identity_and_conditions(changes):
    with pytest.raises(ValueError):
        claim(**changes)


def test_source_matching_is_exact_and_hashes_are_not_attestation():
    c = claim()
    values = dict(exact_revision=REVISION, git_blob_sha="1" * 40, source_range_sha256="2" * 64)
    assert c.matches_source(**values)
    for name, wrong in (
        ("exact_revision", "3" * 40),
        ("git_blob_sha", "4" * 40),
        ("source_range_sha256", "5" * 64),
    ):
        assert not c.matches_source(**(values | {name: wrong}))
    assert not c.matches_source(**(values | {"exact_revision": "carrot-wip"}))


def test_descriptors_have_no_current_baseline_policy_or_grant_fields():
    from dataclasses import fields

    p = parameter()
    forbidden = {
        "current_value",
        "baseline",
        "default",
        "approved_hard_min",
        "approved_hard_max",
        "approved_step",
        "approved_rate",
        "authorization",
        "safe_to_apply",
        "vehicle_approved",
        "application_grant",
    }
    assert forbidden.isdisjoint(f.name for f in fields(p))
    for name in forbidden:
        with pytest.raises(TypeError):
            parameter(**{name: 1})
    from cyberpilot_autotune.contracts import ParameterSpec

    assert not isinstance(p, ParameterSpec)
    assert type(p.digest) is str  # an identity, not any application capability


def test_canonical_identity_ignores_mapping_order_but_preserves_numeric_representation():
    from cyberpilot_autotune.knowledge.canonical import canonical_digest

    assert canonical_digest({"a": 1, "b": [2, None]}) == canonical_digest({"b": (2, None), "a": 1})
    assert canonical_digest({"a": 1}) != canonical_digest({"a": 1.0})
    for value in (object(), {1: "bad"}, {"a": float("nan")}):
        with pytest.raises(ValueError):
            canonical_digest(value)
    p = parameter()
    for name, value in (
        ("ui_default", 11),
        ("canonical_unit", "changed software unit"),
        ("source_revision", "6" * 40),
    ):
        assert replace(p, **{name: value}).digest != p.digest
    assert len(p.digest) == 64 and p.digest == p.digest.lower()


def test_registry_rejects_duplicates_aliases_dangling_and_cross_revision_claims():
    from cyberpilot_autotune.knowledge.contracts import KnowledgeRegistry

    p, c = parameter(), claim()
    r = KnowledgeRegistry(REVISION, [p], [c])
    assert r.get_proven(p.parameter_id) == r.get_any(p.parameter_id) == p
    assert r.get_any("not-present") is r.get_proven("not-present") is None
    for ps, cs in (
        ([p, p], [c]),
        ([p], [c, c]),
        ([p], []),
        ([p], [replace(c, exact_revision="9" * 40)]),
        ([replace(p, consumer_claim_ids=["missing"])], [c]),
    ):
        with pytest.raises(ValueError):
            KnowledgeRegistry(REVISION, ps, cs)
    for name in ("CarSelected3", "CruiseMaxVals1"):
        with pytest.raises(ValueError):
            KnowledgeRegistry(REVISION, [replace(p, parameter_id=name, storage_key=name)], [c])


def test_registry_does_not_promote_unresolved_units_or_change_classification():
    from cyberpilot_autotune.knowledge.contracts import Confidence, KnowledgeRegistry

    p = parameter(
        canonical_unit=None,
        evidence_status=Confidence.UNRESOLVED,
        evidence_gaps=["UNRESOLVED_UNIT_EQUIVALENCE"],
    )
    r = KnowledgeRegistry(REVISION, [p], [claim()])
    assert r.get_any(p.parameter_id) == p
    assert r.get_proven(p.parameter_id) is None


def test_explicit_supersession_and_required_descriptive_metadata():
    from cyberpilot_autotune.knowledge.contracts import Confidence

    assert claim(supersedes_claim_id="prior:claim").supersedes_claim_id == "prior:claim"
    for changes in (
        {"mode_conditions": []},
        {"descriptive_owner": []},
        {"evidence_status": Confidence.UNRESOLVED},
    ):
        with pytest.raises(ValueError):
            parameter(**changes)


def test_registry_rejects_aliases_misclassified_modes_and_unproved_claims():
    from cyberpilot_autotune.knowledge.contracts import (
        Classification,
        Confidence,
        KnowledgeRegistry,
    )

    p, c = parameter(), claim()
    variants = [
        ([p, replace(p, parameter_id="LateralTorqueKiV")], [c]),
        ([replace(p, storage_key="alias")], [c]),
        ([replace(p, parameter_id="LateralTorqueCustom", storage_key="LateralTorqueCustom")], [c]),
        ([p], [replace(c, confidence=Confidence.CONDITIONAL)]),
        ([p], [replace(c, parameter_ids=["LateralTorqueKiV"])]),
        ([replace(p, source_revision="8" * 40)], [c]),
    ]
    for changes in (
        {"storage_key": "liveTorqueParameters.latAccelOffset"},
        {"storage_key": None, "classification": Classification.TUNING_CANDIDATE},
    ):
        variants.append(
            ([replace(p, parameter_id="liveTorqueParameters.latAccelOffset", **changes)], [c])
        )
    for ps, cs in variants:
        with pytest.raises(ValueError):
            KnowledgeRegistry(REVISION, ps, cs)
