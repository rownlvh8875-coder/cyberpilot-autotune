"""Immutable caller gates; no runtime discovery, defaults or IO."""

from dataclasses import dataclass, replace
from enum import Enum

from ..adapter import HYUNDAI_PLATFORM_FLAGS, AdapterConfig
from ..availability import INTEGRATION_MERGE, SCHEMA_REVISION, SOURCE_REVISION
from ..health import SessionToken

CONTRACT_BASIS = "b24ef18e4270af5ab4f731aca31cf95f4f4b0cce"
TOPICS = ("carControl", "carState", "carOutput")


class SidecarReason(Enum):
    INVALID_CONFIG = ("INVALID_CONFIG", 2)
    SOURCE_REVISION_MISMATCH = ("SOURCE_REVISION_MISMATCH", 4)
    INTEGRATION_REVISION_MISMATCH = ("INTEGRATION_REVISION_MISMATCH", 4)
    CONTRACT_BASIS_MISMATCH = ("CONTRACT_BASIS_MISMATCH", 4)
    SCHEMA_REVISION_MISMATCH = ("SCHEMA_REVISION_MISMATCH", 4)
    RUNTIME_PLATFORM_UNCONFIRMED = ("RUNTIME_PLATFORM_UNCONFIRMED", 4)
    RUNTIME_PLATFORM_MISMATCH = ("RUNTIME_PLATFORM_MISMATCH", 4)
    UNSUPPORTED_PLATFORM = ("UNSUPPORTED_PLATFORM", 4)
    STATIC_CONTEXT_MISMATCH = ("STATIC_CONTEXT_MISMATCH", 4)
    CONTROLLER_CONTEXT_MISMATCH = ("CONTROLLER_CONTEXT_MISMATCH", 4)
    BASELINE_EPOCH_MISMATCH = ("BASELINE_EPOCH_MISMATCH", 4)
    SESSION_TOKEN_MISSING = ("SESSION_TOKEN_MISSING", 4)
    CAPABILITY_UNAVAILABLE = ("CAPABILITY_UNAVAILABLE", 4)
    SESSION_REQUIRED = ("SESSION_REQUIRED", 4)
    PRODUCER_RESTARTED = ("PRODUCER_RESTARTED", 4)
    MONOTONIC_REGRESSION = ("MONOTONIC_REGRESSION", 4)
    RUNTIME_INVARIANT_FAULT = ("RUNTIME_INVARIANT_FAULT", 5)
    INVALID_SOURCE_METADATA = ("INVALID_SOURCE_METADATA", 5)
    INVALID_TOPIC = ("INVALID_TOPIC", 5)
    SOURCE_CLOSED = ("SOURCE_CLOSED", 5)
    UNSUPPORTED_ENVIRONMENT = ("UNSUPPORTED_ENVIRONMENT", 6)

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def exit_code(self) -> int:
        return self.value[1]


class SidecarError(RuntimeError):
    def __init__(self, reason: SidecarReason, *, topic: str | None = None) -> None:
        self.reason = reason
        self.topic = topic if topic in TOPICS else None
        super().__init__(reason.code)


def require(condition: bool, reason: SidecarReason) -> None:
    if not condition:
        raise SidecarError(reason)


def validate_launch_pins(
    source_revision: str,
    integration_revision: str,
    contract_basis: str,
    schema_revision: str,
    expected_platform: str | None,
    runtime_platform: str | None,
) -> None:
    for value, expected, reason in (
        (source_revision, SOURCE_REVISION, SidecarReason.SOURCE_REVISION_MISMATCH),
        (integration_revision, INTEGRATION_MERGE, SidecarReason.INTEGRATION_REVISION_MISMATCH),
        (contract_basis, CONTRACT_BASIS, SidecarReason.CONTRACT_BASIS_MISMATCH),
        (schema_revision, SCHEMA_REVISION, SidecarReason.SCHEMA_REVISION_MISMATCH),
    ):
        require(type(value) is str and value == expected, reason)
    require(
        bool(expected_platform) and bool(runtime_platform),
        SidecarReason.RUNTIME_PLATFORM_UNCONFIRMED,
    )
    require(expected_platform == runtime_platform, SidecarReason.RUNTIME_PLATFORM_MISMATCH)
    require(
        runtime_platform in tuple(key for key, _ in HYUNDAI_PLATFORM_FLAGS),
        SidecarReason.UNSUPPORTED_PLATFORM,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SidecarConfig:
    adapter: AdapterConfig
    source_revision: str
    integration_revision: str
    contract_basis: str
    schema_revision: str
    expected_platform: str | None
    runtime_platform: str | None
    poll_timeout_ms: int
    maximum_updates: int

    def __post_init__(self) -> None:
        validate_launch_pins(
            self.source_revision,
            self.integration_revision,
            self.contract_basis,
            self.schema_revision,
            self.expected_platform,
            self.runtime_platform,
        )
        require(type(self.adapter) is AdapterConfig, SidecarReason.INVALID_CONFIG)
        a = self.adapter.attestation
        require(type(a.session) is SessionToken, SidecarReason.SESSION_TOKEN_MISSING)
        require(a.platform_key == self.runtime_platform, SidecarReason.RUNTIME_PLATFORM_MISMATCH)
        require(a.source_revision == self.source_revision, SidecarReason.SOURCE_REVISION_MISMATCH)
        require(
            a.integration_merge == self.integration_revision,
            SidecarReason.INTEGRATION_REVISION_MISMATCH,
        )
        require(
            a.observation_schema_revision == self.schema_revision,
            SidecarReason.SCHEMA_REVISION_MISMATCH,
        )
        require(
            a.baseline_epoch == self.adapter.snapshot_policy.baseline_epoch,
            SidecarReason.BASELINE_EPOCH_MISMATCH,
        )
        require(
            a.static_context_digest == self.adapter.static_context.digest,
            SidecarReason.STATIC_CONTEXT_MISMATCH,
        )
        capability = a.steering_pressed_capability
        require(
            capability is not None
            and capability.supports(
                self.adapter.static_context, platform_key=self.runtime_platform
            ),
            SidecarReason.CAPABILITY_UNAVAILABLE,
        )
        for value in (self.maximum_updates, self.poll_timeout_ms):
            require(type(value) is int and value > 0, SidecarReason.INVALID_CONFIG)
        # Pinned msgq Poller.poll converts timeout to a signed C int (ipc_pyx.pyx:148).
        require(self.poll_timeout_ms < 2**31, SidecarReason.INVALID_CONFIG)
        try:
            object.__setattr__(self, "adapter", replace(self.adapter))
        except Exception:
            raise SidecarError(SidecarReason.INVALID_CONFIG) from None
