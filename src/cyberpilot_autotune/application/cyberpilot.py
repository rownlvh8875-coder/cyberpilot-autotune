"""Neutral guard for current offline exports; no import, fit or authority minting."""

from dataclasses import dataclass, field

from cyberpilot_autotune.contracts.validation import ValidationError

from .contracts import ApplicationReason, EvidenceQuality, identity

INSPECTED_SOURCE_REVISION = "02652a441c1c39b4a9c3bfaf1132217f0e57b384"


@dataclass(frozen=True, slots=True)
class ResearchAssessment:
    recognized: bool
    content_sha256: str | None
    quality: EvidenceQuality = field(default=EvidenceQuality.RESEARCH_ONLY, init=False)
    reason: ApplicationReason = field(default=ApplicationReason.UNQUALIFIED_EVIDENCE, init=False)
    application_authorized: bool = field(default=False, init=False)


def inspect_research_report(report: object, *, source_revision: str) -> ResearchAssessment:
    """Inspect a caller-exported dict (e.g. asdict), never an imported producer.

    Recognized means compatible offline structure only. Numeric estimates, raw
    diagnostics and asserted permission are not retained, converted or applied.
    The two pinned report contracts deliberately forbid runtime authorization.
    """
    if source_revision != INSPECTED_SOURCE_REVISION or type(report) is not dict:
        return ResearchAssessment(False, None)
    flags: tuple[str, ...]
    if {
        "contracts_ready",
        "reasons",
        "profile_sha256",
        "runtime_accepted",
        "offline_evaluable",
    } <= report.keys():
        flags = ("runtime_accepted", "offline_evaluable")
        hash_key = "profile_sha256"
    elif {
        "status",
        "blockers",
        "input_sha256",
        "parameter_identification_qualified",
        "candidate_generation_allowed",
        "runtime_accepted",
    } <= report.keys():
        flags = (
            "parameter_identification_qualified",
            "candidate_generation_allowed",
            "runtime_accepted",
        )
        hash_key = "input_sha256"
    else:
        return ResearchAssessment(False, None)
    if any(report[name] is not False for name in flags):
        return ResearchAssessment(False, None)
    content = report[hash_key]
    try:
        identity(content, 64)
    except ValidationError:
        return ResearchAssessment(False, None)
    return ResearchAssessment(True, content)
