"""Descriptive route-cluster inference, never point-IID or calibrated confidence."""

from dataclasses import dataclass, field
from math import fsum, sqrt

from .contracts import FrozenDevelopment, Point, RawFit, require
from .estimator import fit_raw

BOUNDS = (
    (-0.5, -0.3),
    (-0.3, -0.2),
    (-0.2, -0.1),
    (-0.1, 0.0),
    (0.0, 0.1),
    (0.1, 0.2),
    (0.2, 0.3),
    (0.3, 0.5),
)
MINIMUM = (100, 300, 500, 500, 500, 500, 300, 100)


def bucket_counts(points: tuple[Point, ...]) -> tuple[int, ...]:
    return tuple(sum(low <= p.normalized_command < high for p in points) for low, high in BOUNDS)


@dataclass(frozen=True, slots=True)
class FitDiagnostic:
    fit: RawFit | None
    reason: str | None


def diagnostic(points: tuple[Point, ...]) -> FitDiagnostic:
    try:
        return FitDiagnostic(fit_raw(points), None)
    except (ValueError, ArithmeticError) as error:
        return FitDiagnostic(None, str(error))


@dataclass(frozen=True, slots=True)
class EpochDiagnostic:
    route_sha256: str
    epoch_sha256: str
    boundary_reason: str
    point_count: int
    bucket_counts: tuple[int, ...]
    status: str
    numerical: FitDiagnostic


@dataclass(frozen=True, slots=True)
class RouteDiagnostic:
    route_sha256: str
    epoch_count: int
    point_count: int
    bucket_counts: tuple[int, ...]
    numerical: FitDiagnostic


@dataclass(frozen=True, slots=True)
class Omission:
    cluster_sha256: str
    retained_point_count: int
    numerical: FitDiagnostic
    factor_delta: float | None
    factor_relative_delta: float | None
    offset_delta: float | None
    native_spread_delta: float | None


@dataclass(frozen=True, slots=True)
class ResidualDiagnostic:
    variance: float
    skew: float | None
    command_covariance: float
    left_mean: float | None
    right_mean: float | None
    left_fit: FitDiagnostic
    right_fit: FitDiagnostic
    ols_slope_diagnostic: float | None


@dataclass(frozen=True, slots=True)
class ClusterStatistics:
    cluster_count: int
    epoch_count: int
    point_count: int
    full: FitDiagnostic
    routes: tuple[RouteDiagnostic, ...]
    epochs: tuple[EpochDiagnostic, ...]
    leave_one_route_out: tuple[Omission, ...]
    leave_one_epoch_out: tuple[Omission, ...]
    factor_jackknife_se: float | None
    offset_jackknife_se: float | None
    native_spread_jackknife_se: float | None
    maximum_route_factor_relative_delta: float | None
    residuals: ResidualDiagnostic | None
    blockers: tuple[str, ...]
    confidence_interval: None = field(default=None, init=False)
    stability_qualified: bool = field(default=False, init=False)


def _omission(identity: str, points: tuple[Point, ...], full: RawFit | None) -> Omission:
    observed = diagnostic(points)
    new = observed.fit
    if new is None or full is None:
        return Omission(identity, len(points), observed, None, None, None, None)
    return Omission(
        identity,
        len(points),
        observed,
        new.linear_mode_tls_lat_accel_slope - full.linear_mode_tls_lat_accel_slope,
        (new.linear_mode_tls_lat_accel_slope - full.linear_mode_tls_lat_accel_slope)
        / full.linear_mode_tls_lat_accel_slope,
        new.lat_accel_offset_mps2 - full.lat_accel_offset_mps2,
        new.native_residual_spread_coefficient - full.native_residual_spread_coefficient,
    )


def _jackknife(values: tuple[float, ...]) -> float:
    mean = fsum(values) / len(values)
    return sqrt((len(values) - 1) / len(values) * fsum((x - mean) ** 2 for x in values))


def _residuals(points: tuple[Point, ...], fit: RawFit) -> ResidualDiagnostic:
    residual = tuple(
        p.lateral_accel_mps2
        - fit.linear_mode_tls_lat_accel_slope * p.normalized_command
        - fit.lat_accel_offset_mps2
        for p in points
    )
    mean = fsum(residual) / len(points)
    x_mean = fsum(p.normalized_command for p in points) / len(points)
    variance = fsum((e - mean) ** 2 for e in residual) / len(points)
    skew = (
        fsum((e - mean) ** 3 for e in residual) / len(points) / variance**1.5 if variance else None
    )
    covariance = fsum(
        (p.normalized_command - x_mean) * (e - mean) for p, e in zip(points, residual, strict=True)
    ) / len(points)
    sides = tuple(
        tuple(p for p in points if (p.normalized_command < 0) == negative)
        for negative in (True, False)
    )
    means = tuple(
        fsum(
            p.lateral_accel_mps2
            - fit.linear_mode_tls_lat_accel_slope * p.normalized_command
            - fit.lat_accel_offset_mps2
            for p in side
        )
        / len(side)
        if side
        else None
        for side in sides
    )
    x_variance = fsum((p.normalized_command - x_mean) ** 2 for p in points) / len(points)
    ols = fit.linear_mode_tls_lat_accel_slope + covariance / x_variance if x_variance else None
    return ResidualDiagnostic(
        variance,
        skew,
        covariance,
        means[0],
        means[1],
        diagnostic(sides[0]),
        diagnostic(sides[1]),
        ols,
    )


def analyze_clusters(data: FrozenDevelopment) -> ClusterStatistics:
    require(type(data) is FrozenDevelopment, "FROZEN_DEVELOPMENT_REQUIRED")
    points = tuple(p for r in data.routes for e in r.epochs for p in e.points)
    full = diagnostic(points)
    routes = []
    epochs = []
    route_omissions = []
    epoch_omissions = []
    nonempty_omissions = []
    for route in data.routes:
        route_points = tuple(p for e in route.epochs for p in e.points)
        routes.append(
            RouteDiagnostic(
                route.route_sha256,
                len(route.epochs),
                len(route_points),
                bucket_counts(route_points),
                diagnostic(route_points),
            )
        )
        retained = tuple(
            p for r in data.routes if r is not route for e in r.epochs for p in e.points
        )
        omitted = _omission(route.route_sha256, retained, full.fit)
        route_omissions.append(omitted)
        if route_points:
            nonempty_omissions.append(omitted)
        for epoch in route.epochs:
            counts = bucket_counts(epoch.points)
            domain = all(
                -0.5 <= p.normalized_command < 0.5
                and abs(p.normalized_command) > 0.02
                and abs(p.lateral_accel_mps2) <= 1.0
                for p in epoch.points
            )
            status = (
                "INVALID_SOURCE_CONTRACT"
                if not domain or max(counts) > 1500
                else "VALID"
                if len(epoch.points) >= 4000
                and all(n >= m for n, m in zip(counts, MINIMUM, strict=True))
                else "INSUFFICIENT_COVERAGE"
            )
            epochs.append(
                EpochDiagnostic(
                    route.route_sha256,
                    epoch.epoch_sha256,
                    epoch.boundary_reason,
                    len(epoch.points),
                    counts,
                    status,
                    diagnostic(epoch.points),
                )
            )
            kept = tuple(
                p for r in data.routes for e in r.epochs if e is not epoch for p in e.points
            )
            epoch_omissions.append(_omission(epoch.epoch_sha256, kept, full.fit))
    fits = tuple(o.numerical.fit for o in nonempty_omissions)
    usable = tuple(f for f in fits if f is not None)
    jackknife_ok = len(nonempty_omissions) >= 3 and len(usable) == len(fits)
    errors: tuple[str, ...] = (
        "THRESHOLD_NOT_JUSTIFIED",
        "INDEPENDENT_ROUTE_SAMPLING_AND_CALIBRATION_UNPROVEN",
    )
    if len(nonempty_omissions) < 3:
        errors += ("INSUFFICIENT_CLUSTER_COUNT",)
    if len(usable) != len(fits):
        errors += ("LEAVE_ONE_ROUTE_FIT_UNAVAILABLE",)
    if any(e.status != "VALID" for e in epochs):
        errors += ("NATIVE_EPOCH_VALIDITY_NOT_ESTABLISHED",)
    deltas = tuple(
        abs(o.factor_relative_delta) for o in route_omissions if o.factor_relative_delta is not None
    )
    return ClusterStatistics(
        len(nonempty_omissions),
        len(epochs),
        len(points),
        full,
        tuple(routes),
        tuple(epochs),
        tuple(route_omissions),
        tuple(epoch_omissions),
        _jackknife(tuple(f.linear_mode_tls_lat_accel_slope for f in usable))
        if jackknife_ok
        else None,
        _jackknife(tuple(f.lat_accel_offset_mps2 for f in usable)) if jackknife_ok else None,
        _jackknife(tuple(f.native_residual_spread_coefficient for f in usable))
        if jackknife_ok
        else None,
        max(deltas) if deltas else None,
        _residuals(points, full.fit) if full.fit else None,
        errors,
    )
