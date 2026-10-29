"""Applied-geometry epoch policy and generic coherent source-based VM diagnostic."""

from dataclasses import dataclass

from .contracts import SteeringGeometryContext, finite, require


def resolve_intent(
    raw_percent: int, cp_front: float | None, wheelbase: float | None
) -> tuple[float | None, str]:
    require(type(raw_percent) is int, "RAW_PERCENT")
    if 31 <= raw_percent <= 69:
        return raw_percent * 0.01, "MANUAL_OVERRIDE"
    if cp_front is None or wheelbase is None:
        return None, "VEHICLE_DEFAULT"
    require(finite(cp_front) and finite(wheelbase) and 0 < cp_front < wheelbase, "CP_GEOMETRY")
    return cp_front / wheelbase, "VEHICLE_DEFAULT"


def epoch_boundary(before: SteeringGeometryContext, after: SteeringGeometryContext) -> str:
    if not before.complete or not after.complete:
        return "CONTEXT_UNAVAILABLE"
    geometry_fields = (
        "wheelbase",
        "center_to_front",
        "center_to_front_ratio",
        "stiffness_factor",
        "geometry_generation",
        "geometry_source",
        "vehicle_context_digest",
    )
    if any(getattr(before, k) != getattr(after, k) for k in geometry_fields):
        return "GEOMETRY_CONTEXT_CHANGED"
    return "SAME_CONTEXT" if before.digest == after.digest else "CONTEXT_CHANGED"


@dataclass(frozen=True, slots=True)
class VehicleDiagnostic:
    ratio: float
    center_to_front: float
    front_stiffness: float
    rear_stiffness: float
    slip_factor: float
    curvature: float
    roll_compensation: float
    yaw_rate: float
    lateral_velocity: float
    acceleration_series: tuple[float, ...]


def vehicle_diagnostic(ratio: float) -> VehicleDiagnostic:
    """Fixed preregistered mathematical fixture; NOT vehicle-safe parameter bounds."""
    require(finite(ratio) and 0 < ratio < 1, "TOY_RATIO")
    mass, inertia, length, r0, sr, speed = 1234.0, 2300.0, 2.73, 0.43, 14.7, 18.0
    steer, roll, k = 0.035, 0.02, 0.95
    af, ar = length * ratio, length * (1 - ratio)
    cf = k * 70000.0 * (1 - ratio) / (1 - r0)
    cr = k * 90000.0 * ratio / r0
    sf = mass * (cf * af - cr * ar) / (length * length * cf * cr)
    factor = 1.0 / (1 - sf * speed * speed) / length
    rc = 0.0 if abs(sf) < 1e-6 else 9.81 * roll / (1 / sf - speed * speed)
    curvature = factor * steer / sr + rc
    # Exact continuous bicycle matrices at rear-steer-ratio=0; explicit Euler is diagnostic.
    a00 = -(cf + cr) / (mass * speed)
    a01 = -(cf * af - cr * ar) / (mass * speed) - speed
    a10 = -(cf * af - cr * ar) / (inertia * speed)
    a11 = -(cf * af * af + cr * ar * ar) / (inertia * speed)
    b0, b1 = cf / mass / sr, cf * af / inertia / sr
    vy, yaw = 0.0, 0.0
    series = []
    for _ in range(200):
        dv = a00 * vy + a01 * yaw + b0 * steer - 9.81 * roll
        dr = a10 * vy + a11 * yaw + b1 * steer
        series.append(dv + speed * yaw)
        vy += 0.001 * dv
        yaw += 0.001 * dr
    return VehicleDiagnostic(ratio, af, cf, cr, sf, curvature, rc, yaw, vy, tuple(series))
