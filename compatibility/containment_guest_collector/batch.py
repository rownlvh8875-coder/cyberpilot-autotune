"""Pure per-case demultiplexing; ignore producer success summaries entirely."""

from dataclasses import dataclass

from compatibility.containment_backend_harmless.host_cases import (
    FIXTURES,
    check_case,
    parse_guest_log,
)

from .contracts import Capture, CaptureAssessment
from .evaluation import evaluate_capture
from .validation import parse_capture


@dataclass(frozen=True, slots=True)
class CapturedCase:
    capture: Capture
    assessment: CaptureAssessment
    harmless_assertion_failures: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.capture) is not Capture or type(self.assessment) is not CaptureAssessment:
            raise ValueError("expected frozen capture and assessment")
        self.capture.__post_init__()
        self.assessment.__post_init__()
        if type(self.harmless_assertion_failures) not in (list, tuple) or any(
            type(reason) is not str or not reason for reason in self.harmless_assertion_failures
        ):
            raise ValueError("expected reason array")
        object.__setattr__(
            self, "harmless_assertion_failures", tuple(self.harmless_assertion_failures)
        )


def assess_batch(raw: str, selected: tuple[str, ...]) -> tuple[CapturedCase, ...]:
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(x not in FIXTURES for x in selected)
    ):
        raise ValueError("invalid case selection")
    found: dict[str, CapturedCase] = {}
    current = None
    body: list[str] = []
    for line in raw.replace("\r\n", "\n").splitlines():
        if line.startswith("GUEST_CASE_BEGIN "):
            case = line.removeprefix("GUEST_CASE_BEGIN ")
            if current is not None or case not in selected or case in found:
                raise ValueError("unknown/duplicate/overlapping case")
            current = case
            body = []
        elif line.startswith("GUEST_CASE_END "):
            if current is None or line.removeprefix("GUEST_CASE_END ") != current:
                raise ValueError("wrong case end")
            text = "\n".join(body)
            capture = parse_capture(text)
            if capture.fixture_id != current:
                raise ValueError("capture/selection identity mismatch")
            records = parse_guest_log(text, (current,))
            failures = tuple(reason for record in records for reason in check_case(record))
            found[current] = CapturedCase(capture, evaluate_capture(capture), failures)
            current = None
        elif current is not None:
            body.append(line)
    if current is not None or set(found) != set(selected):
        raise ValueError("incomplete selected batch")
    return tuple(found[case] for case in selected)
