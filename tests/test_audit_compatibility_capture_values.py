"""GC062–064:exact immutable inputs and content-only diagnostic outputs."""

from dataclasses import FrozenInstanceError

import pytest

from tests.fixtures.audit_compatibility_capture import api


@pytest.mark.parametrize("value", (True, None, 0, -1, 1.0, "1"))
def test_budgets_do_not_default_or_accept_bool(value):
    c = api("contracts")
    with pytest.raises(ValueError):
        c.CaptureBudget(value, 100, 100, 100)


def test_immutable_reports_have_no_authority_switches():
    c = api("contracts")
    result = c.CaptureConsistencyDecision((), ())
    assert result.decision == "OBSERVED_STABLE"
    assert result.status == "BLOCKED" and result.integrated_admission is False
    assert result.atomicity == "NOT_ESTABLISHED"
    assert all(v is False for _, v in result.permissions)
    assert result.content_identity_only is True
    with pytest.raises(FrozenInstanceError):
        result.errors = ("changed",)
    with pytest.raises(TypeError):
        c.CaptureConsistencyDecision((), (), atomicity=True)


@pytest.mark.parametrize("paths", (("relative", "/x", "/x"), ("/a/../b", "/x", "/x")))
def test_layout_is_explicit_not_resolved_from_cwd(paths):
    with pytest.raises(ValueError):
        api("contracts").RepoLayout(*paths, ())


def test_diagnostic_errors_beat_unavailable_and_none_is_not_empty():
    c = api("contracts")
    assert c.CaptureConsistencyDecision(("KNOWN_INVALID",), ("MISSING",)).decision == "REJECTED"
    assert c.CaptureConsistencyDecision((), ("MISSING",)).decision == "UNAVAILABLE"
    for value in (None, [], (False,), ("z", "a"), ("a", "a")):
        with pytest.raises(ValueError):
            c.CaptureConsistencyDecision(value, ())
