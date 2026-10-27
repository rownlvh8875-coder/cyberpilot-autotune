"""A proposal is data only and confers no controller authority."""

from dataclasses import dataclass

from .validation import ValidationError, count, finite, nonnegative, strings, text


@dataclass(frozen=True, slots=True)
class TuningProposal:
    parameter_id: str
    baseline_value: float
    proposed_value: float
    confidence: float
    sample_count: int
    context_key: str
    learner_version: str
    timestamp_s: float
    evidence_summary: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("parameter_id", "context_key", "learner_version"):
            text(getattr(self, name), name)
        finite(self.baseline_value, "baseline_value")
        finite(self.proposed_value, "proposed_value")
        if not 0 <= finite(self.confidence, "confidence") <= 1:
            raise ValidationError("confidence must be in [0, 1]")
        count(self.sample_count, "sample_count")
        nonnegative(self.timestamp_s, "timestamp_s")
        object.__setattr__(self, "evidence_summary", strings(self.evidence_summary))
