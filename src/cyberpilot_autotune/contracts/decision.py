"""A gate decision is never an application receipt."""

from dataclasses import dataclass

from cyberpilot_autotune.safety.reasons import ReasonCode

from .validation import ValidationError, boolean, finite, nonnegative, strings, text


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """In-memory diagnostic value without an external sink."""

    reason: ReasonCode
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.reason, ReasonCode):
            raise ValidationError("invalid event reason")
        text(self.detail, "detail")


@dataclass(frozen=True, slots=True)
class GateDecision:
    eligible: bool
    parameter_id: str | None
    evaluated_candidate: float | None
    reason: ReasonCode
    diagnostic_details: tuple[str, ...]
    evaluation_timestamp_s: float | None

    def __post_init__(self) -> None:
        boolean(self.eligible, "eligible")
        if not isinstance(self.reason, ReasonCode):
            raise ValidationError("invalid reason code")
        if self.eligible != (self.reason is ReasonCode.ACCEPTED_FOR_SHADOW):
            raise ValidationError("eligibility and reason disagree")
        if self.parameter_id is not None:
            text(self.parameter_id, "parameter_id")
        if self.evaluated_candidate is not None:
            finite(self.evaluated_candidate, "evaluated_candidate")
        if self.eligible and (self.parameter_id is None or self.evaluated_candidate is None):
            raise ValidationError("eligible decision requires an identified candidate")
        if self.evaluation_timestamp_s is not None:
            nonnegative(self.evaluation_timestamp_s, "evaluation_timestamp_s")
        object.__setattr__(self, "diagnostic_details", strings(self.diagnostic_details))
