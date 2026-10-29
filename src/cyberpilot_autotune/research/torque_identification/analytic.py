"""Conditional source-equation predictions, not physical identification."""

from math import sqrt

from .contracts import number, require


def friction_shape(error: float, deadzone: float, threshold: float) -> float:
    require(all(number(v) for v in (error, deadzone, threshold)), "FINITE_MODEL_REQUIRED")
    require(deadzone >= 0 and threshold > 0, "FRICTION_DOMAIN")
    if -deadzone < error < deadzone:
        return 0.0
    return max(-1.0, min(1.0, error / threshold))


def projected_coefficient(
    factor: float, controller_friction: float, q_variance: float, noise_variance: float
) -> float:
    """Projection at true F, independent q/noise; not fitted-TLS recovery."""
    require(
        all(number(v) for v in (factor, controller_friction, q_variance, noise_variance)),
        "FINITE_MODEL_REQUIRED",
    )
    require(
        factor > 0 and min(controller_friction, q_variance, noise_variance) >= 0, "FRICTION_DOMAIN"
    )
    return (
        1.5
        * sqrt(factor**2 * controller_friction**2 * q_variance + noise_variance)
        / sqrt(1 + factor**2)
    )


def symmetric_tls_prediction(
    factor: float, controller_friction: float, command_variance: float, q_variance: float
) -> tuple[float, float]:
    """Zero means, b=0, Cov(u,q)=0, no measurement noise, line eigenvalue < 1.

    Only in this specified symmetric submodel does [x,1,y] SVD reduce to the
    two-dimensional moment eigensystem. Not a general centered-TLS substitute.
    """
    require(
        all(number(v) for v in (factor, controller_friction, command_variance, q_variance)),
        "FINITE_MODEL_REQUIRED",
    )
    require(
        factor > 0 and command_variance > 0 and min(controller_friction, q_variance) >= 0,
        "MOMENT_DOMAIN",
    )
    vx = command_variance
    covariance = factor * vx
    vy = factor**2 * (vx + controller_friction**2 * q_variance)
    discriminant = sqrt((vy - vx) ** 2 + 4 * covariance**2)
    smallest = max(0.0, (vx + vy - discriminant) / 2)
    require(smallest < 1.0, "TLS_INTERCEPT_MODE")
    slope = (vy - vx + discriminant) / (2 * covariance)
    # Evaluate residual variance directly; subtraction in the small eigenvalue
    # is less accurate near an exactly affine line.
    variance = (factor - slope) ** 2 * vx + factor**2 * controller_friction**2 * q_variance
    return slope, 1.5 * sqrt(variance / (1 + slope**2))
