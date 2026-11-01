"""Immutable dual-stream evidence; content identity never grants authority."""

from dataclasses import dataclass

from tests.deny_fd_v2.contracts import PERMISSIONS as PERMISSIONS
from tests.deny_fd_v2_harness.contracts import need

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
