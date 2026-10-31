"""Strict UTF8 admission over frozen synthetic semantics, without legacy adoption."""

from compatibility.native_containment.contracts import (
    SyntheticContainmentCase,
    canonical_digest,
    parse_synthetic_case,
)
from compatibility.native_containment.validation import (
    SyntheticContainmentDecision,
    SyntheticPolicyContext,
    evaluate_synthetic,
)

VALIDATOR_PROFILE = "containment-scalar-utf8-strict-v1"


def digest_case_strict(case: SyntheticContainmentCase) -> str:
    """Content identity only; normalize only the unencodable Unicode scalar error."""
    try:
        return canonical_digest(case)
    except UnicodeEncodeError:
        raise ValueError("INVALID_UNICODE_SCALAR") from None


def parse_case_strict(raw: str) -> SyntheticContainmentCase:
    """Do not return a synthetic case until canonical UTF8 admission succeeds."""
    case = parse_synthetic_case(raw)
    digest_case_strict(case)
    return case


def evaluate_case_strict(
    case: SyntheticContainmentCase, policy: SyntheticPolicyContext
) -> SyntheticContainmentDecision:
    """Reject invalid scalar content before unchanged diagnostic-only evaluation."""
    digest_case_strict(case)
    return evaluate_synthetic(case, policy)
