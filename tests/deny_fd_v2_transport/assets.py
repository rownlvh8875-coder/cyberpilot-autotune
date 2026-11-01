"""Read-only pinned old assets plus an exact separate transport profile."""

import json
from dataclasses import dataclass

from compatibility.guest_input_closure.filesystem import read_regular
from tests.deny_fd_v2_harness import assets as source
from tests.deny_fd_v2_harness.contracts import AssetBundle, digest, need

from .contracts import PERMISSIONS

MANIFEST = "docs/evidence/deny_fd_v2_transport_assets_v1.json"
CONFIG = "boot/config-6.12.113+deb13-cloud-amd64"
CONFIG_SHA256 = "3540f9dc8a7e48ef1d2e7b945a87976cf292f736d297cfebe3ac5cdf8571ee1e"
PROFILE = {
    "schema": "deny-fd-v2-dual-transport-profile-v1",
    "kernel_config_sha256": CONFIG_SHA256,
    "console": "isa-serial-index0-ttyS0-stdio",
    "telemetry": "isa-serial-index1-ttyS1-pipe",
    "aggregate_limit": 1048576,
    "timeout_seconds": 180,
    "termination_grace_seconds": 2,
    "runtime_qualified": False,
    "permissions": dict(PERMISSIONS),
}


@dataclass(frozen=True, slots=True)
class TransportAssets:
    base: AssetBundle

    def __post_init__(self) -> None:
        need(type(self.base) is AssetBundle, "bound base context required")
        source.validate_bundle(self.base)

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS


def preflight() -> TransportAssets:
    # Retain old strict JSON duplicate/nonfinite rejection and full asset checks.
    profile = source._json(read_regular(source.ROOT, MANIFEST, 65536))
    need(
        profile == PROFILE
        and json.dumps(profile, sort_keys=True) == json.dumps(PROFILE, sort_keys=True),
        "transport profile changed",
    )
    config = read_regular(source.VM, CONFIG, 4 * 1024 * 1024)
    need(digest(config) == CONFIG_SHA256, "kernel config changed")
    return TransportAssets(source.preflight())
