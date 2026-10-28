"""Explicit trusted owner capabilities. No concrete production writer/authority."""

from collections.abc import Mapping
from typing import Protocol

from .contracts import AuthorizationGrant, SteeringPolicy, SteeringRequest, TargetSnapshot


class SteeringTarget(Protocol):
    """Single owner-thread CAS: atomic full tuple, exact revision +1, no hidden retry.

    snapshot returns a fresh immutable selected steering tuple. commit either
    rejects the expected revision or commits the complete tuple; readback is
    mandatory even after an acknowledgement. External implementations must prove
    this contract and exclude other writers. No physical actuation is asserted.
    """

    def snapshot(self) -> TargetSnapshot: ...
    def commit(self, expected_revision: int, values: Mapping[str, float]) -> int: ...


class ApplicationAuthority(Protocol):
    """Independent trusted review/evidence authorization, not untrusted metadata.

    The caller owns authentication, actual evidence qualification and one-shot
    authorization. There is deliberately no production allow-all implementation.
    A scope flag, digest, confidence or eligible SHADOW decision is insufficient.
    """

    def authorize(
        self, request: SteeringRequest, policy: SteeringPolicy, now_s: float
    ) -> AuthorizationGrant | None: ...
