"""Immutable dual-stream evidence; content identity never grants authority."""

from dataclasses import dataclass

from tests.deny_fd_v2.contracts import PERMISSIONS as PERMISSIONS
from tests.deny_fd_v2_harness.contracts import canonical, case_label, digest, identity, need

LIMIT = 1048576


def error_text(value: str | None) -> None:
    need(
        value is None or (type(value) is str and 0 < len(value) <= 4000 and "\0" not in value),
        "invalid error",
    )


@dataclass(frozen=True, slots=True)
class StreamEvidence:
    raw: bytes
    complete: bool
    error: str | None

    def __post_init__(self) -> None:
        need(
            type(self.raw) is bytes and len(self.raw) <= LIMIT,
            "bounded immutable stream bytes required",
        )
        need(type(self.complete) is bool, "explicit completeness required")
        error_text(self.error)
        need(not self.complete or self.error is None, "errored stream cannot be complete")


@dataclass(frozen=True, slots=True)
class TransportProcessResult:
    telemetry: StreamEvidence
    console: StreamEvidence
    exit_code: int | None
    termination: str
    error: str | None

    def __post_init__(self) -> None:
        need(
            type(self.telemetry) is StreamEvidence and type(self.console) is StreamEvidence,
            "explicit stream roles required",
        )
        need(len(self.telemetry.raw) + len(self.console.raw) <= LIMIT, "aggregate stream limit")
        need(
            self.exit_code is None
            or (type(self.exit_code) is int and -(2**31) <= self.exit_code < 2**31),
            "unknown exit is not zero",
        )
        need(
            type(self.termination) is str
            and self.termination
            in {"EXITED", "NONZERO_EXIT", "TIMEOUT", "OUTPUT_LIMIT", "IO_ERROR", "CLEANUP_ERROR"},
            "invalid termination",
        )
        error_text(self.error)

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS


@dataclass(frozen=True, slots=True)
class TransportAcquisitionRecord:
    case: str
    attempt_id: str
    source_revision: str
    source_manifest_digest: str
    probe_sha256: str
    vm_cohort_digest: str
    kernel_sha256: str
    kernel_config_sha256: str
    transport_profile_digest: str
    init_sha256: str
    image_sha256: str
    argv: tuple[str, ...]
    result: TransportProcessResult
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
            self.kernel_config_sha256,
            self.transport_profile_digest,
            self.init_sha256,
            self.image_sha256,
        ):
            identity(value, 64)
        need(
            type(self.argv) in (list, tuple) and 1 <= len(self.argv) <= 128, "bounded argv required"
        )
        need(
            all(type(v) is str and 0 < len(v) <= 4096 and "\0" not in v for v in self.argv),
            "invalid argv",
        )
        object.__setattr__(self, "argv", tuple(self.argv))
        need(type(self.result) is TransportProcessResult, "dual stream result required")
        self.result.__post_init__()
        for clock_value in (self.host_start_ns, self.host_end_ns):
            need(
                type(clock_value) is int and 0 <= clock_value < 2**64,
                "UInt64 host monotonic clock required",
            )
        need(self.host_end_ns >= self.host_start_ns, "host time order invalid")

    def metadata(self) -> dict[str, object]:
        def stream(value: StreamEvidence) -> dict[str, object]:
            return {
                "raw_sha256": digest(value.raw),
                "raw_size": len(value.raw),
                "complete": value.complete,
                "error": value.error,
            }

        return {
            "schema": "deny-fd-v2-dual-acquisition-v1",
            "case": self.case,
            "attempt_id": self.attempt_id,
            "source_revision": self.source_revision,
            "source_manifest_digest": self.source_manifest_digest,
            "probe_sha256": self.probe_sha256,
            "vm_cohort_digest": self.vm_cohort_digest,
            "kernel_sha256": self.kernel_sha256,
            "kernel_config_sha256": self.kernel_config_sha256,
            "transport_profile_digest": self.transport_profile_digest,
            "init_sha256": self.init_sha256,
            "image_sha256": self.image_sha256,
            "argv": self.argv,
            "host_start_ns": self.host_start_ns,
            "host_end_ns": self.host_end_ns,
            "clock_domain": "HOST_MONOTONIC_NS",
            "status": "BLOCKED",
            "permissions": dict(PERMISSIONS),
            "digest_meaning": "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY",
            "telemetry": stream(self.result.telemetry),
            "console": stream(self.result.console),
            "exit_code": self.result.exit_code,
            "termination": self.result.termination,
            "collector_error": self.result.error,
        }

    @property
    def content_digest(self) -> str:
        return digest(canonical(self.metadata()))
