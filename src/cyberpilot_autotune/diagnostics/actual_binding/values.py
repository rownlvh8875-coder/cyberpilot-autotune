"""Exact immutable supported value boundary. No authority or reference generation."""

import re
from dataclasses import dataclass

from .constants import (
    CASES,
    CHECK_GROUP_ORDER,
    INCOMPLETE_REASONS,
    PERMISSIONS,
    POST_VERSION,
    PRE_VERSION,
    REASON_ORDER,
    REJECT_REASONS,
    STATUSES,
)


def require(condition: bool) -> None:
    if not condition:
        raise ValueError("invalid neutral value")


def hex_value(value: object, width: int) -> bool:
    return type(value) is str and re.fullmatch("[0-9a-f]{" + str(width) + "}", value) is not None


def uint(value: object, bits: int = 64) -> bool:
    return type(value) is int and 0 <= value < 2**bits


def optional_hex(value: object) -> bool:
    return value is None or hex_value(value, 64)


def _identity(run: str, attempt: str, case: str) -> None:
    require(hex_value(run, 32) and hex_value(attempt, 32))
    require(type(case) is str and case in CASES)


def _pairs(pairs: tuple[tuple[str, bytes | None], ...]) -> None:
    require(type(pairs) is tuple)
    for pair in pairs:
        require(type(pair) is tuple and len(pair) == 2)
        require(type(pair[0]) is str and (pair[1] is None or type(pair[1]) is bytes))


@dataclass(frozen=True, slots=True)
class ActualDiagnosticBundle:
    documents: tuple[tuple[str, bytes | None], ...]
    raw: tuple[tuple[str, bytes | None], ...]

    def __post_init__(self) -> None:
        _pairs(self.documents)
        _pairs(self.raw)


@dataclass(frozen=True, slots=True)
class PrelaunchExpectedReference:
    contract_version: str
    workflow_run_id: str
    workflow_attempt_id: str
    case: str
    host_clock_cohort_sha256: str | None
    host_clock_generation: int | None
    baseline_sha256: str | None
    command_sha256: str | None
    preflight_sha256: str | None

    def __post_init__(self) -> None:
        require(type(self.contract_version) is str and self.contract_version == PRE_VERSION)
        _identity(self.workflow_run_id, self.workflow_attempt_id, self.case)
        for value in (
            self.host_clock_cohort_sha256,
            self.baseline_sha256,
            self.command_sha256,
            self.preflight_sha256,
        ):
            require(optional_hex(value))
        require(self.host_clock_generation is None or uint(self.host_clock_generation))


@dataclass(frozen=True, slots=True)
class CaptureFreezeExpectedReference:
    contract_version: str
    workflow_run_id: str
    workflow_attempt_id: str
    case: str
    pre_reference_content_sha256: str | None
    intent_sha256: str | None
    exit_sha256: str | None
    snapshot_sha256: str | None

    def __post_init__(self) -> None:
        require(type(self.contract_version) is str and self.contract_version == POST_VERSION)
        _identity(self.workflow_run_id, self.workflow_attempt_id, self.case)
        for value in (
            self.pre_reference_content_sha256,
            self.intent_sha256,
            self.exit_sha256,
            self.snapshot_sha256,
        ):
            require(optional_hex(value))


def _ordered(values: tuple[str, ...], order: tuple[str, ...]) -> None:
    require(type(values) is tuple and all(type(v) is str for v in values))
    require(all(v in order for v in values))
    require(values == tuple(v for v in order if v in values))


@dataclass(frozen=True, slots=True)
class ActualBindingAssessment:
    structural_status: str
    reasons: tuple[str, ...]
    not_evaluated_checks: tuple[str, ...]

    def __post_init__(self) -> None:
        require(type(self.structural_status) is str and self.structural_status in STATUSES)
        _ordered(self.reasons, REASON_ORDER)
        _ordered(self.not_evaluated_checks, CHECK_GROUP_ORDER)
        if any(r in REJECT_REASONS for r in self.reasons):
            expected = "REJECTED"
        elif any(r in INCOMPLETE_REASONS for r in self.reasons):
            expected = "INCOMPLETE"
        elif self.reasons:
            expected = "REPORTED_TIME_ORDER_UNCOMPARABLE"
        else:
            expected = "REPORTED_BINDING_CONSISTENT"
        require(self.structural_status == expected)
        require(expected != "REPORTED_BINDING_CONSISTENT" or not self.not_evaluated_checks)

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def content_status(self) -> str:
        return "NOT_EVALUATED"

    @property
    def provenance(self) -> str:
        return "BLOCKED_NO_INDEPENDENT_VERIFICATION"

    @property
    def history(self) -> str:
        return "UNAVAILABLE"

    @property
    def integrated_admission(self) -> bool:
        return False

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS
