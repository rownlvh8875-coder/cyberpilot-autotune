"""Wrong source/variant/platform cannot turn a default False into known False."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.adapter import SteeringPressedCapability
from cyberpilot_autotune.integrations.carrot.availability import SOURCE_REVISION
from cyberpilot_autotune.integrations.carrot.errors import CarrotInputError
from tests.fixtures.carrot_adapter import config, hyundai_config


@pytest.mark.parametrize("platform", ["HYUNDAI_SANTA_FE_2022", "HYUNDAI_IONIQ_5"])
def test_hyundai_source_assignment_requires_runtime_platform_and_matching_flags(platform):
    cfg = hyundai_config(platform)
    cap = cfg.attestation.steering_pressed_capability
    assert cap.supports(cfg.static_context, platform_key=platform)
    assert not cap.supports(cfg.static_context)
    assert not cap.supports(
        replace(cfg.static_context, flags=cfg.static_context.flags ^ 8192), platform_key=platform
    )
    assert not cap.supports(replace(cfg.static_context, flags=0), platform_key=platform)
    assert not cap.supports(replace(cfg.static_context, brand="tesla"), platform_key=platform)


@pytest.mark.parametrize("platform", [True, "VIN-like-unqualified-input", "HYUNDAI_SANTA_FE"])
def test_unqualified_platform_metadata_is_typed_rejection(platform):
    with pytest.raises(CarrotInputError, match="UNQUALIFIED_PLATFORM_ATTESTATION"):
        replace(config().attestation, platform_key=platform)


def test_existing_three_field_capability_api_keeps_tesla_and_meb():
    for kind in ("torque", "mebCurvature"):
        cfg = config(kind)
        assert cfg.attestation.steering_pressed_capability.supports(cfg.static_context)
    cfg = hyundai_config("HYUNDAI_SANTA_FE_2022")
    cap = SteeringPressedCapability(
        "opendbc_repo/opendbc/car/hyundai/carstate.py", "CarState.update", SOURCE_REVISION
    )
    assert cap.supports(cfg.static_context, platform_key="HYUNDAI_SANTA_FE_2022")


def test_platform_attestation_cannot_be_attached_to_a_different_brand_context():
    cfg = config()
    with pytest.raises(CarrotInputError, match="INCONSISTENT_CALLER_CONTEXT"):
        replace(cfg, attestation=replace(cfg.attestation, platform_key="HYUNDAI_SANTA_FE_2022"))
