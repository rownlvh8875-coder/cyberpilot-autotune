"""Conditional OLS prototypes; numerical rank is not physical qualification."""

from dataclasses import dataclass, field

from .contracts import Sample, finite, require
from .geometry import epoch_boundary


def normalize_state(error: float, deadzone: float, threshold: float, enabled: bool) -> float:
    """Reconstruct q only from exact callback-stage inputs; never from installed C."""
    require(
        all(finite(v) for v in (error, deadzone, threshold))
        and deadzone >= 0
        and threshold > 0
        and type(enabled) is bool,
        "FRICTION_STATE_INPUT",
    )
    if not enabled or -deadzone < error < deadzone:
        return 0.0
    return max(-1.0, min(1.0, error / threshold))


@dataclass(frozen=True, slots=True)
class ControllerFrictionEstimate:
    status: str
    factor: float | None = None
    estimate: float | None = None
    intercept: float | None = None
    rank: int | None = None
    condition_number: float | None = None
    negative_count: int = 0
    zero_count: int = 0
    positive_count: int = 0
    target_claim: str = "CALLBACK_CONDITIONAL_ONLY"
    estimand: str = "CONDITIONAL_CONTROLLER_DOMAIN_C_NOT_OPTIMAL_PHYSICAL_FRICTION"
    scope_mode: str = "LINEAR_TORQUE_SYNTHETIC_ONLY"
    factor_dependency: str = "UNAVAILABLE"
    uncertainty_diagnostic: str = "NUMERICAL_RANK_CONDITION_ONLY_NOT_CI"
    observation_completeness: bool = False
    geometry_context_digest: str | None = None
    model_family: str = "UNSPECIFIED"
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    owner_proposal_allowed: bool = field(default=False, init=False)


def fit(
    samples: tuple[Sample, ...],
    family: str,
    *,
    factor: float | None = None,
    target: str = "callback",
    q_observed: bool = True,
) -> ControllerFrictionEstimate:
    require(family in {"controller", "inverse", "branch", "explicit"}, "MODEL")
    require(target in {"callback", "total", "pid_subtracted"}, "TARGET")
    require(type(samples) is tuple and all(type(s) is Sample for s in samples), "SAMPLES")
    require(type(q_observed) is bool, "Q_OBSERVED_FLAG")
    if factor is not None and (not finite(factor) or factor <= 0):
        return ControllerFrictionEstimate("INVALID_FACTOR_CONTEXT")
    if len(samples) < 3:
        return ControllerFrictionEstimate("INSUFFICIENT_POINTS")
    if not q_observed:
        return ControllerFrictionEstimate("Q_STATE_UNOBSERVED")
    first = samples[0].context
    for sample in samples:
        boundary = epoch_boundary(first, sample.context)
        if boundary != "SAME_CONTEXT":
            return ControllerFrictionEstimate(boundary)
    if first.controller_mode != "LINEAR_TORQUE":
        return ControllerFrictionEstimate("MODE_OUTSIDE_LINEAR_SCOPE")
    if any(s.saturated or s.override for s in samples):
        return ControllerFrictionEstimate("SATURATION_OR_OVERRIDE")
    if any(a.time_ns >= b.time_ns for a, b in zip(samples[:-1], samples[1:], strict=True)):
        return ControllerFrictionEstimate("NONINCREASING_TIME")
    if family == "branch":
        if any(s.q != 0 for s in samples) and not any(abs(s.q) == 1 for s in samples):
            return ControllerFrictionEstimate("BRANCH_REQUIRES_SATURATED_STATES")
        samples = tuple(s for s in samples if abs(s.q) == 1)
    negative = sum(s.q < 0 for s in samples)
    positive = sum(s.q > 0 for s in samples)
    zero = len(samples) - negative - positive
    if not negative and not positive:
        return ControllerFrictionEstimate("FRICTION_UNOBSERVABLE_IN_DEADZONE")
    if not negative or not positive or len(samples) < 3:
        return ControllerFrictionEstimate("FRICTION_EXCITATION_INSUFFICIENT")
    try:
        import numpy as np
    except ImportError as exc:
        raise ValueError("RESEARCH_EXTRA_REQUIRED") from exc
    a = np.array([s.acceleration for s in samples], dtype=float)
    q = np.array([s.q for s in samples], dtype=float)
    u = np.array(
        [
            s.callback_output
            if target == "callback"
            else s.total - (s.pid if target == "pid_subtracted" else 0)
            for s in samples
        ],
        dtype=float,
    )
    one = np.ones(len(samples))
    if family == "explicit":
        design = np.column_stack((q, one))
        y = np.array([s.explicit_term for s in samples])
    elif factor is not None:
        design = np.column_stack((q, one))
        y = u - a / factor if family == "controller" else a - factor * u
    elif family == "controller":
        design, y = np.column_stack((a, q, one)), u
    elif family == "inverse":
        design, y = np.column_stack((u, q, one)), a
    else:
        design, y = np.column_stack((u, q > 0, q < 0)), a
    beta, _, rank, singular = np.linalg.lstsq(design, y, rcond=None)
    if rank < design.shape[1]:
        return ControllerFrictionEstimate("NONIDENTIFIABLE_DESIGN_MATRIX", rank=int(rank))
    condition = float(singular[0] / singular[-1])
    if family == "explicit":
        f, c, intercept = None, float(beta[0]), float(beta[1])
    elif factor is not None:
        f = factor
        c = float(beta[0]) if family == "controller" else -float(beta[0]) / f
        intercept = float(beta[1])
    else:
        if beta[0] <= 0:
            return ControllerFrictionEstimate(
                "NONPOSITIVE_FACTOR", rank=int(rank), condition_number=condition
            )
        f = 1 / float(beta[0]) if family == "controller" else float(beta[0])
        c = (
            float(beta[1])
            if family == "controller"
            else (
                -float(beta[1]) / f if family == "inverse" else float(beta[2] - beta[1]) / (2 * f)
            )
        )
        intercept = float(beta[2]) if family != "branch" else float((beta[1] + beta[2]) / 2)
    status = (
        "IMPLEMENTED_COEFFICIENT_CONSISTENCY_ONLY"
        if family == "explicit"
        else "CONDITIONALLY_IDENTIFIABLE_SYNTHETIC_ONLY"
    )
    claim = {
        "callback": "CALLBACK_CONDITIONAL_ONLY",
        "total": "WRONG_STAGE_DIAGNOSTIC_ONLY",
        "pid_subtracted": "UNCLIPPED_SYNTHETIC_SUBTRACTION_ONLY",
    }[target]
    dependency = (
        "NONE_FOR_CONSTRUCTED_TERM_CONSISTENCY_ONLY"
        if family == "explicit"
        else ("KNOWN_F_SYNTHETIC_ORACLE" if factor is not None else "JOINT_F_C_FULL_RANK")
    )
    return ControllerFrictionEstimate(
        status,
        f,
        c,
        intercept,
        int(rank),
        condition,
        negative,
        zero,
        positive,
        claim,
        factor_dependency=dependency,
        observation_completeness=True,
        geometry_context_digest=first.digest,
        model_family=family,
    )


@dataclass(frozen=True, slots=True)
class Sensitivity:
    status: str
    lower: float | None = None
    upper: float | None = None


def factor_sensitivity(samples: tuple[Sample, ...], interval: tuple[float, float]) -> Sensitivity:
    require(type(interval) is tuple and len(interval) == 2, "INTERVAL")
    low, high = interval
    if not finite(low) or not finite(high) or not 0 < low <= high:
        return Sensitivity("INVALID_FACTOR_INTERVAL")
    endpoints = [fit(samples, "controller", factor=f) for f in interval]
    values = [r.estimate for r in endpoints if r.estimate is not None]
    if len(values) != 2:
        return Sensitivity(endpoints[0].status)
    return Sensitivity("DETERMINISTIC_FACTOR_SENSITIVITY_NOT_CI", min(values), max(values))


def select_model(*, required_signals_complete: bool, independent_response: bool) -> str:
    require(
        type(required_signals_complete) is bool and type(independent_response) is bool,
        "SELECTION_FLAGS",
    )
    if not required_signals_complete or not independent_response:
        return "NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS"
    return "CONTROLLER_DOMAIN_CONDITIONAL_MODEL"
