"""Only reported structure is assessed; all operational permissions stay false."""

from ._codec import decode_documents
from ._linkage import check_links
from ._state import check_state
from .constants import (
    CHECK_GROUP_ORDER,
    DOCUMENT_ROLES,
    INCOMPLETE_REASONS,
    REASON_ORDER,
    REJECT_REASONS,
)
from .values import (
    ActualBindingAssessment,
    ActualDiagnosticBundle,
    CaptureFreezeExpectedReference,
    PrelaunchExpectedReference,
    require,
)


def assess_actual_binding(
    bundle: ActualDiagnosticBundle,
    *,
    expected_pre: PrelaunchExpectedReference | None,
    expected_post: CaptureFreezeExpectedReference | None,
) -> ActualBindingAssessment:
    require(type(bundle) is ActualDiagnosticBundle)
    ActualDiagnosticBundle.__post_init__(bundle)
    if expected_pre is not None:
        require(type(expected_pre) is PrelaunchExpectedReference)
        PrelaunchExpectedReference.__post_init__(expected_pre)
    if expected_post is not None:
        require(type(expected_post) is CaptureFreezeExpectedReference)
        CaptureFreezeExpectedReference.__post_init__(expected_post)
    decoded = decode_documents(bundle)
    linkage = check_links(decoded, bundle, expected_pre, expected_post)
    state = check_state(decoded, expected_pre)
    issues = (*decoded.reasons, *linkage.reasons, *state.reasons)
    skipped = [*linkage.not_evaluated_checks, *state.not_evaluated_checks]
    if not decoded.container_valid:
        skipped.append("container_bounds")
    for role in DOCUMENT_ROLES:
        if role not in decoded.documents:
            skipped.append("document:" + role)
    reasons = tuple(r for r in REASON_ORDER if r in issues)
    if any(r in REJECT_REASONS for r in reasons):
        status = "REJECTED"
    elif any(r in INCOMPLETE_REASONS for r in reasons):
        status = "INCOMPLETE"
        skipped.append("completeness")
    elif reasons:
        status = "REPORTED_TIME_ORDER_UNCOMPARABLE"
    else:
        status = "REPORTED_BINDING_CONSISTENT"
    return ActualBindingAssessment(
        status, reasons, tuple(g for g in CHECK_GROUP_ORDER if g in skipped)
    )
