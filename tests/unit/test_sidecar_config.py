"""Pins/platform/context must fail before any dependency or receive resource exists."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cyberpilot_autotune.integrations.carrot.sidecar.config import SidecarError
from tests.fixtures.sidecar import sidecar_config


@pytest.mark.parametrize(
    "field,value,reason,exit_code",
    [
        ("source_revision", "0" * 40, "SOURCE_REVISION_MISMATCH", 4),
        ("integration_revision", "0" * 40, "INTEGRATION_REVISION_MISMATCH", 4),
        ("contract_basis", "0" * 40, "CONTRACT_BASIS_MISMATCH", 4),
        ("schema_revision", "v1", "SCHEMA_REVISION_MISMATCH", 4),
        ("runtime_platform", None, "RUNTIME_PLATFORM_UNCONFIRMED", 4),
        ("expected_platform", None, "RUNTIME_PLATFORM_UNCONFIRMED", 4),
        ("runtime_platform", "HYUNDAI_IONIQ_5", "RUNTIME_PLATFORM_MISMATCH", 4),
        ("maximum_updates", True, "INVALID_CONFIG", 2),
        ("maximum_updates", 0, "INVALID_CONFIG", 2),
        ("poll_timeout_ms", 0, "INVALID_CONFIG", 2),
        ("poll_timeout_ms", 2**31, "INVALID_CONFIG", 2),
    ],
)
def test_config_rejects_unqualified_pin_platform_or_budget(field, value, reason, exit_code):
    with pytest.raises(SidecarError) as error:
        replace(sidecar_config(), **{field: value})
    assert error.value.reason.code == reason and error.value.reason.exit_code == exit_code


def test_matching_but_unsupported_platform_does_not_become_vehicle_evidence():
    with pytest.raises(SidecarError, match="UNSUPPORTED_PLATFORM"):
        replace(sidecar_config(), expected_platform="other", runtime_platform="other")


def test_config_is_frozen_and_revalidates_existing_context_and_baseline():
    cfg = sidecar_config()
    with pytest.raises(FrozenInstanceError):
        cfg.runtime_platform = "other"
    assert cfg.adapter.baseline_parameters == {"synthetic.test_only": 10.0}
    for field, value, reason in (
        ("static_context_digest", "0" * 64, "STATIC_CONTEXT_MISMATCH"),
        ("baseline_epoch", 2, "BASELINE_EPOCH_MISMATCH"),
        ("session", None, "SESSION_TOKEN_MISSING"),
    ):
        # Simulate a corrupted frozen input at the boundary; revalidation is required.
        broken = replace(cfg.adapter)
        object.__setattr__(broken.attestation, field, value)
        with pytest.raises(SidecarError, match=reason):
            replace(cfg, adapter=broken)


def test_missing_capability_or_wrong_platform_attestation_cannot_subscribe():
    cfg = sidecar_config()
    for value in (None, "HYUNDAI_IONIQ_5"):
        adapter = replace(
            cfg.adapter, attestation=replace(cfg.adapter.attestation, platform_key=value)
        )
        with pytest.raises(SidecarError, match="RUNTIME_PLATFORM_MISMATCH"):
            replace(cfg, adapter=adapter)
    adapter = replace(
        cfg.adapter, attestation=replace(cfg.adapter.attestation, steering_pressed_capability=None)
    )
    with pytest.raises(SidecarError, match="CAPABILITY_UNAVAILABLE"):
        replace(cfg, adapter=adapter)
