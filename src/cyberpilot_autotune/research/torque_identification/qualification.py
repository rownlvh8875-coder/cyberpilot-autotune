"""Separate scientific verdicts with permanently absent application authority."""

import json
from dataclasses import dataclass, field

from .cluster_stats import ClusterStatistics, analyze_clusters
from .contracts import (
    POLICY_SHA256,
    PREREGISTRATION_COMMIT,
    RESEARCH,
    RUNTIME,
    FrozenDevelopment,
    digest,
    require,
)
from .experiments import SyntheticCaseResult, run_synthetic_suite

RETAINED_GATES = (
    "VEHICLE_APPLICATION_BOUNDS_UNRESOLVED",
    "RUNTIME_FINGERPRINT_UNCONFIRMED",
    "REPRESENTATION_ENCODING_UNRESOLVED",
    "APPLICATION_NOT_AUTHORIZED",
    "WATCHDOG_EXECUTION_MODEL_UNRESOLVED",
    "EXTERNAL_INHIBITION_EXECUTOR_ACCEPTANCE_UNRESOLVED",
    "PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED",
)


@dataclass(frozen=True, slots=True)
class ScientificQualificationReport:
    source_revisions: tuple[tuple[str, str], ...]
    estimand_version: str
    statistical_policy_digest: str
    preregistration_commit: str
    development_evidence_digest: str | None
    cluster_count: int | None
    epoch_count: int | None
    point_count: int | None
    status: str
    factor_verdict: str
    friction_verdict: str
    joint_identifiability: str
    synthetic_recovery_summary: tuple[SyntheticCaseResult, ...]
    cluster_statistics: ClusterStatistics | None
    evidence_gaps: tuple[str, ...]
    blockers: tuple[str, ...]
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    parameter_identification_qualified: bool = field(default=False, init=False)


def qualify(data: FrozenDevelopment | None, policy_json: str) -> ScientificQualificationReport:
    policy = json.loads(policy_json)
    require(digest(policy) == POLICY_SHA256, "POLICY_MUTATION")
    synthetic = run_synthetic_suite()
    require(
        not any(r.verdict == "ANALYTIC_SYNTHETIC_MISMATCH" for r in synthetic),
        "ANALYTIC_SYNTHETIC_MISMATCH",
    )
    require(data is None or type(data) is FrozenDevelopment, "FROZEN_DEVELOPMENT_REQUIRED")
    statistics = analyze_clusters(data) if data is not None else None
    gaps = (
        ("FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE", "SCIENTIFIC_CLUSTER_STRUCTURE_UNAVAILABLE")
        if data is None
        else ("SOURCE_SELECTION_AUTHENTICATION_UNAVAILABLE",)
    )
    blockers = (
        gaps
        + (statistics.blockers if statistics else ("THRESHOLD_NOT_JUSTIFIED",))
        + ("FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION",)
        + RETAINED_GATES
    )
    reason = (
        "FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE" if data is None else "SCIENTIFIC_GATES_UNRESOLVED"
    )
    return ScientificQualificationReport(
        (
            ("runtime", RUNTIME),
            ("integration", policy["source_pins"]["integration"]),
            ("current", policy["source_pins"]["current"]),
            ("research", RESEARCH),
        ),
        policy["estimand_version"],
        POLICY_SHA256,
        PREREGISTRATION_COMMIT,
        data.digest if data is not None else None,
        statistics.cluster_count if statistics else None,
        statistics.epoch_count if statistics else None,
        statistics.point_count if statistics else None,
        "TORQUE_IDENTIFICATION_BLOCKED_" + reason,
        "FACTOR_IDENTIFICATION_UNQUALIFIED_" + reason,
        "FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION",
        "NONIDENTIFIABLE",
        synthetic,
        statistics,
        gaps,
        blockers,
    )
