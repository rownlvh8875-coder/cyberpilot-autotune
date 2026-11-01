"""Immutable content context; not acquisition authenticity or operational grants."""

import hashlib
import json
import re
from dataclasses import dataclass

from tests.deny_fd_v2.contracts import PERMISSIONS

CASES = ("DFD01", "DFD02", "DFD03", "DFD04", "DFD05", "DFD06")


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def identity(value: object, width: int) -> None:
    need(
        type(value) is str and re.fullmatch("[0-9a-f]{" + str(width) + "}", value) is not None,
        "exact content identity required",
    )


def case_label(value: object) -> str:
    need(type(value) is str and value in CASES, "fixed case required")
    assert isinstance(value, str)
    return value


@dataclass(frozen=True, slots=True)
class AssetBundle:
    source_revision: str
    source_manifest_digest: str
    vm_cohort_digest: str
    probe: bytes
    busybox: bytes
    kernel_sha256: str

    def __post_init__(self) -> None:
        identity(self.source_revision, 40)
        for value in (self.source_manifest_digest, self.vm_cohort_digest, self.kernel_sha256):
            identity(value, 64)
        for raw in (self.probe, self.busybox):
            need(
                type(raw) is bytes and 0 < len(raw) <= 4 * 1024 * 1024,
                "immutable bounded asset bytes required",
            )

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS
