"""Caller attestations and bounds are explicit; no inferred producer capability."""

import sys
from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.adapter import CachePolicy, CarrotReadOnlyAdapter
from cyberpilot_autotune.integrations.carrot.errors import (
    CarrotDependencyUnavailable,
    CarrotInputError,
)
from cyberpilot_autotune.integrations.carrot.health import SessionToken, TopicHealthEvidence
from tests.fixtures.carrot_adapter import config


def test_actual_construction_without_dependency_is_typed(monkeypatch):
    monkeypatch.setitem(sys.modules, "capnp", None)
    with pytest.raises(CarrotDependencyUnavailable):
        CarrotReadOnlyAdapter(config())


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_revision", "0" * 40),
        ("integration_merge", "0" * 40),
        ("observation_schema_revision", "v1"),
        ("session", None),
    ],
)
def test_unqualified_source_pin_is_rejected(field, value):
    with pytest.raises(CarrotInputError):
        replace(config().attestation, **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("static_context_digest", "0" * 64),
        ("baseline_epoch", 2),
        ("baseline_epoch", True),
        ("permitted_controller_kinds", ("pid",)),
    ],
)
def test_inconsistent_context_epoch_and_kind_are_rejected(field, value):
    cfg = config()
    with pytest.raises(CarrotInputError):
        replace(cfg, attestation=replace(cfg.attestation, **{field: value}))


@pytest.mark.parametrize(
    "generation,token", [(True, "0" * 32), (-1, "0" * 32), (0, "a" * 31), (0, "Z" * 32)]
)
def test_session_is_nonidentifying_software_generation_and_token(generation, token):
    with pytest.raises(CarrotInputError):
        SessionToken(generation, token)


def test_capacities_and_health_cannot_be_boolean_or_unknown_numeric():
    with pytest.raises(CarrotInputError):
        CachePolicy(1, True, 2)
    with pytest.raises(CarrotInputError):
        TopicHealthEvidence(True, True, 1, True, True)


def test_capability_matches_actual_audited_producer_and_context():
    cfg = config()
    capability = cfg.attestation.steering_pressed_capability
    assert capability.supports(cfg.static_context)
    assert not replace(capability, source_revision="0" * 40).supports(cfg.static_context)
    assert not replace(capability, producer_path="unqualified.py").supports(cfg.static_context)
    assert not capability.supports(replace(cfg.static_context, brand="mock"))
    meb = config("mebCurvature")
    assert meb.attestation.steering_pressed_capability.supports(meb.static_context)
    assert not replace(
        meb.attestation.steering_pressed_capability, producer_symbol="dummy"
    ).supports(meb.static_context)


def test_configuration_defensively_copies_baseline_and_capability_list():
    cfg = config()
    mapping = dict(cfg.baseline_parameters)
    kinds = ["torque"]
    copy = replace(
        cfg,
        baseline_parameters=mapping,
        attestation=replace(cfg.attestation, permitted_controller_kinds=kinds),
    )
    mapping.clear()
    kinds.clear()
    assert copy.baseline_parameters == {"synthetic.test_only": 10.0}
    assert copy.attestation.permitted_controller_kinds == ("torque",)
