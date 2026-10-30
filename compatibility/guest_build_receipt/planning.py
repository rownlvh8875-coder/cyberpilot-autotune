"""Reference-only preparation requirements; no observations or executable plan."""

import re
from dataclasses import dataclass, field

from .models import sha

REGISTRATIONS = ("executor", "producer", "input_seal", "promotion")


@dataclass(frozen=True, slots=True)
class PreparationInputs:
    reference_revision: str
    reference_snapshot_digest: str
    executor_registration: str | None = None
    producer_registration: str | None = None
    input_seal_registration: str | None = None
    promotion_registration: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.reference_revision) is not str
            or re.fullmatch(r"[0-9a-f]{40}", self.reference_revision) is None
        ):
            raise ValueError("invalid reference revision")
        sha(self.reference_snapshot_digest)
        for name in REGISTRATIONS:
            sha(getattr(self, name + "_registration"), optional=True)


@dataclass(frozen=True, slots=True)
class PreparationDecision:
    inputs: PreparationInputs
    missing_registrations: tuple[str, ...] = field(init=False)
    unverified_registrations: tuple[str, ...] = field(init=False)
    evidence_origin: str = field(default="REFERENCE_ONLY", init=False)
    overall_status: str = field(default="BLOCKED", init=False)
    blockers: tuple[str, ...] = field(
        default=(
            "QUALIFIED_EVIDENCE_UNAVAILABLE",
            "BUILD_CONSUMPTION_PRODUCER_NOT_IMPLEMENTED",
            "EXTERNAL_EXECUTOR_UNQUALIFIED",
            "INPUT_SEAL_BACKEND_UNQUALIFIED",
            "OUTPUT_PROMOTION_BACKEND_UNQUALIFIED",
            "APPLICATION_NOT_AUTHORIZED",
        ),
        init=False,
    )
    current_observation: None = field(default=None, init=False)
    prepared_command: None = field(default=None, init=False)
    build_execution_allowed: bool = field(default=False, init=False)
    promotion_authorized: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    device_class_qualified: bool = field(default=False, init=False)
    policy_adopted: bool = field(default=False, init=False)
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    owner_proposal_allowed: bool = field(default=False, init=False)
    successful_prohibited_handles: None = field(default=None, init=False)
    successful_prohibited_effects: None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if type(self.inputs) is not PreparationInputs:
            raise ValueError("invalid preparation context")
        self.inputs.__post_init__()
        for name, unavailable in (
            ("missing_registrations", True),
            ("unverified_registrations", False),
        ):
            object.__setattr__(
                self,
                name,
                tuple(
                    key
                    for key in REGISTRATIONS
                    if (getattr(self.inputs, key + "_registration") is None) is unavailable
                ),
            )


def assess_preparation(inputs: PreparationInputs) -> PreparationDecision:
    return PreparationDecision(inputs)


def current_reference_plan() -> PreparationDecision:
    return assess_preparation(
        PreparationInputs(
            "bbec08f84d0d08b17075663643ddeba6db46d977",
            "6f854b3c1e6bb1f216092c87f983c553a7ff5419897415f56a007d74e06b5eb7",
        )
    )
