"""Immutable UNTRUSTED fixture reports. No authority or actual device qualification."""

import re
from dataclasses import dataclass, fields
from enum import StrEnum

DIGEST_FIELDS = (
    "kernel_build_digest",
    "kernel_config_digest",
    "btf_digest",
    "source_loader_digest",
    "object_receipt_digest",
    "fd_lineage_digest",
)
BOOL_FIELDS = (
    "guard_active",
    "collector_bound",
    "process_lineage_complete",
    "trace_complete",
    "tree_exit_observed",
    "broker_effects_observed",
)
PERMISSIONS = (
    "runtime_qualified",
    "device_class_qualified",
    "policy_adopted",
    "candidate_generation_allowed",
    "application_authorized",
    "runtime_accepted",
    "owner_proposal_allowed",
)


def text(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("expected nonempty immutable string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("text is not canonical UTF-8") from error


def digest(value: object) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("expected lowercase SHA-256")


class FixtureOutcome(StrEnum):
    PASS_NAMED_HARMLESS_FIXTURE = "PASS_NAMED_HARMLESS_FIXTURE"
    REJECTED = "REJECTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class HarmlessObservations:
    kernel_build_digest: str | None
    kernel_config_digest: str | None
    btf_digest: str | None
    source_loader_digest: str | None
    object_receipt_digest: str | None
    fd_lineage_digest: str | None
    guard_active: bool | None
    collector_bound: bool | None
    process_lineage_complete: bool | None
    trace_complete: bool | None
    tree_exit_observed: bool | None
    broker_effects_observed: bool | None
    clock_domain: str | None
    successful_prohibited_handles: int | None
    successful_prohibited_effects: int | None

    def __post_init__(self) -> None:
        for name in DIGEST_FIELDS:
            value = getattr(self, name)
            if value is not None:
                digest(value)
        for name in BOOL_FIELDS:
            value = getattr(self, name)
            if value is not None and type(value) is not bool:
                raise ValueError("expected bool or null")
        if self.clock_domain is not None:
            text(self.clock_domain)
        for number in (self.successful_prohibited_handles, self.successful_prohibited_effects):
            if number is not None and (type(number) is not int or not 0 <= number < 2**64):
                raise ValueError("expected UInt64 or null, not bool")

    def complete_named_evidence(self) -> bool:
        return (
            all(getattr(self, name) is not None for name in DIGEST_FIELDS)
            and self.clock_domain is not None
            and all(getattr(self, name) is True for name in BOOL_FIELDS[:-1])
            and self.broker_effects_observed is False
            and self.successful_prohibited_handles == 0
            and self.successful_prohibited_effects == 0
        )


@dataclass(frozen=True, slots=True)
class HarmlessFixtureResult:
    fixture_id: str
    evidence_cohort_digest: str
    outcome: FixtureOutcome
    actual_observations: HarmlessObservations
    reasons: tuple[str, ...]
    schema_version: str = "harmless-backend-fixture-v1"
    evidence_kind: str = "UNTRUSTED_FIXTURE_REPORT"
    runtime_qualified: bool = False
    device_class_qualified: bool = False
    policy_adopted: bool = False
    candidate_generation_allowed: bool = False
    application_authorized: bool = False
    runtime_accepted: bool = False
    owner_proposal_allowed: bool = False

    def __post_init__(self) -> None:
        text(self.schema_version)
        text(self.evidence_kind)
        text(self.fixture_id)
        if self.schema_version != "harmless-backend-fixture-v1":
            raise ValueError("unsupported fixture schema")
        if self.evidence_kind != "UNTRUSTED_FIXTURE_REPORT":
            raise ValueError("no observed/authenticity promotion exists")
        if re.fullmatch(r"HF(0[1-9]|1[0-9]|2[0-4])", self.fixture_id) is None:
            raise ValueError("unknown fixture")
        digest(self.evidence_cohort_digest)
        if not isinstance(self.outcome, str):
            raise ValueError("expected fixture outcome")
        object.__setattr__(self, "outcome", FixtureOutcome(self.outcome))
        if type(self.actual_observations) is not HarmlessObservations:
            raise ValueError("expected immutable observations")
        self.actual_observations.__post_init__()
        if type(self.reasons) not in (list, tuple):
            raise ValueError("expected reason array")
        for reason in self.reasons:
            text(reason)
        if len(set(self.reasons)) != len(self.reasons):
            raise ValueError("duplicate reasons")
        object.__setattr__(self, "reasons", tuple(self.reasons))
        passed = self.outcome == FixtureOutcome.PASS_NAMED_HARMLESS_FIXTURE
        if passed and (self.reasons or not self.actual_observations.complete_named_evidence()):
            raise ValueError("PASS requires all named evidence, no rejection reasons")
        if not passed and not self.reasons:
            raise ValueError("nonpass requires reasons")
        for name in PERMISSIONS:
            if getattr(self, name) is not False:
                raise ValueError("all real qualification/permission fields are fixed false")


def field_names(cls: type[HarmlessFixtureResult] | type[HarmlessObservations]) -> set[str]:
    return {field.name for field in fields(cls)}
