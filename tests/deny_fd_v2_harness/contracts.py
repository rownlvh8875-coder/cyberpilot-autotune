"""Immutable content context; not acquisition authenticity or operational grants."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass

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


@dataclass(frozen=True, slots=True)
class AcquisitionRecord:
    case: str
    attempt_id: str
    source_revision: str
    source_manifest_digest: str
    probe_sha256: str
    vm_cohort_digest: str
    kernel_sha256: str
    init_sha256: str
    image_sha256: str
    argv: tuple[str, ...]
    raw: bytes
    exit_code: int | None
    termination: str
    raw_complete: bool
    host_start_ns: int
    host_end_ns: int

    def __post_init__(self) -> None:
        case_label(self.case)
        identity(self.attempt_id, 32)
        identity(self.source_revision, 40)
        for value in (
            self.source_manifest_digest,
            self.probe_sha256,
            self.vm_cohort_digest,
            self.kernel_sha256,
            self.init_sha256,
            self.image_sha256,
        ):
            identity(value, 64)
        need(
            type(self.argv) in (tuple, list) and 1 <= len(self.argv) <= 128,
            "bounded immutable argv required",
        )
        need(
            all(type(v) is str and 0 < len(v) <= 4096 and "\0" not in v for v in self.argv),
            "invalid argv value",
        )
        object.__setattr__(self, "argv", tuple(self.argv))
        need(type(self.raw) is bytes and len(self.raw) <= 1024 * 1024, "bounded raw bytes required")
        need(
            self.exit_code is None
            or (type(self.exit_code) is int and -(2**31) <= self.exit_code < 2**31),
            "unknown exit is not zero",
        )
        need(type(self.raw_complete) is bool, "explicit completeness required")
        for clock in (self.host_start_ns, self.host_end_ns):
            need(type(clock) is int and 0 <= clock < 2**64, "host UInt64 monotonic time required")
        need(self.host_end_ns >= self.host_start_ns, "host time order invalid")
        need(
            type(self.termination) is str
            and self.termination
            in (
                "EXITED",
                "NONZERO_EXIT",
                "TIMEOUT",
                "OUTPUT_LIMIT",
                "IO_ERROR",
                "CLEANUP_ERROR",
            ),
            "unknown termination",
        )
        if self.termination in ("EXITED", "NONZERO_EXIT"):
            need(
                self.exit_code is not None
                and self.raw_complete
                and ((self.exit_code == 0) == (self.termination == "EXITED")),
                "inconsistent completed exit",
            )
        else:
            need(not self.raw_complete, "failed attempt is not complete capture")

    @property
    def raw_size(self) -> int:
        return len(self.raw)

    @property
    def raw_sha256(self) -> str:
        return digest(self.raw)

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def clock_domain(self) -> str:
        return "HOST_MONOTONIC_NS"

    def metadata(self) -> dict[str, object]:
        data = asdict(self)
        del data["raw"]
        return {
            **data,
            "schema": "deny-fd-v2-acquisition-v1",
            "raw_size": self.raw_size,
            "raw_sha256": self.raw_sha256,
            "clock_domain": self.clock_domain,
            "status": self.status,
            "permissions": dict(self.permissions),
            "digest_meaning": "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY",
        }

    @property
    def content_digest(self) -> str:
        return digest(canonical(self.metadata()))
