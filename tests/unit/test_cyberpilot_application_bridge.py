"""Current CyberPilot offline results never grant runtime steering authority."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest

from cyberpilot_autotune.application.contracts import ApplicationReason, EvidenceQuality

SOURCE = "02652a441c1c39b4a9c3bfaf1132217f0e57b384"


def inspect(report, source=SOURCE):
    assert importlib.util.find_spec("cyberpilot_autotune.application.cyberpilot") is not None, (
        "neutral CyberPilot compatibility guard is missing"
    )
    module = importlib.import_module("cyberpilot_autotune.application.cyberpilot")
    return module.inspect_research_report(report, source_revision=source)


def profile():
    return dict(
        contracts_ready=True,
        reasons=(),
        profile_sha256="a" * 64,
        runtime_accepted=False,
        offline_evaluable=False,
    )


def torque():
    return dict(
        status="NUMERICAL_DIAGNOSTIC",
        blockers=("PHYSICAL_FRICTION_NOT_IDENTIFIED",),
        input_sha256="b" * 64,
        estimate={"lat_accel_factor": 2.0},
        parameter_identification_qualified=False,
        candidate_generation_allowed=False,
        runtime_accepted=False,
    )


@pytest.mark.parametrize("report", [profile(), torque()])
def test_exact_exported_contracts_stay_research_only(report):
    result = inspect(report)
    assert result.quality is EvidenceQuality.RESEARCH_ONLY
    assert result.reason is ApplicationReason.UNQUALIFIED_EVIDENCE
    assert result.recognized and result.application_authorized is False
    assert result.content_sha256 in {"a" * 64, "b" * 64}
    with pytest.raises(FrozenInstanceError):
        result.application_authorized = True


@pytest.mark.parametrize(
    "field",
    [
        "runtime_accepted",
        "offline_evaluable",
        "parameter_identification_qualified",
        "candidate_generation_allowed",
    ],
)
def test_asserted_true_cannot_promote_an_unqualified_export(field):
    data = torque() if "generation" in field or "identification" in field else profile()
    data[field] = True
    result = inspect(data)
    assert not result.application_authorized and not result.recognized
    assert result.content_sha256 is None


@pytest.mark.parametrize(
    "data,revision",
    [
        (None, SOURCE),
        ({}, SOURCE),
        (profile(), "main"),
        ({**profile(), "profile_sha256": "bad"}, SOURCE),
    ],
)
def test_malformed_or_different_source_is_not_silently_accepted(data, revision):
    result = inspect(data, revision)
    assert not result.recognized and not result.application_authorized
    assert result.content_sha256 is None


def test_estimate_and_raw_diagnostic_are_not_retained_or_reinterpreted():
    data = torque()
    result = inspect(data)
    data["estimate"]["lat_accel_factor"] = 999
    assert not hasattr(result, "estimate") and not hasattr(result, "proposal")
    assert result.content_sha256 == "b" * 64
