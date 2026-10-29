"""Immutable scalar research records and canonical identity, with no IO."""

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass

RUNTIME = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
RESEARCH = "02652a441c1c39b4a9c3bfaf1132217f0e57b384"
SIGNAL = (
    "torqued-v1:negative-applied-normalized-torque:calibrated-roll-corrected-mps2:lag-aligned-once"
)
PREREGISTRATION_COMMIT = "da2f9a082018285dd706e49aad61d3783233a29d"
POLICY_SHA256 = "5ee040a5ad7af8bcf8c56422da3ae8ed7794c5b77f52ddd380e5aa24df95b94b"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def number(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)  # type: ignore[arg-type]
    except OverflowError:
        return False


def sha(value: object, length: int = 64) -> bool:
    return type(value) is str and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Point:
    sample_sha256: str
    time_ns: int
    normalized_command: float
    lateral_accel_mps2: float

    def __post_init__(self) -> None:
        require(sha(self.sample_sha256), "SAMPLE_ID")
        require(type(self.time_ns) is int and 0 <= self.time_ns < 2**63, "SAMPLE_TIME")
        require(
            number(self.normalized_command) and number(self.lateral_accel_mps2), "NONFINITE_POINT"
        )


@dataclass(frozen=True, slots=True)
class RawFit:
    linear_mode_tls_lat_accel_slope: float
    lat_accel_offset_mps2: float
    native_residual_spread_coefficient: float
    residual_rmse_mps2: float
    point_count: int


@dataclass(frozen=True, slots=True)
class Epoch:
    epoch_sha256: str
    source_revision: str
    start_segment: int
    end_segment: int
    boundary_reason: str
    points: tuple[Point, ...]

    def __post_init__(self) -> None:
        require(sha(self.epoch_sha256), "EPOCH_ID")
        require(self.source_revision == RUNTIME, "SOURCE_REVISION")
        require(
            type(self.start_segment) is int
            and type(self.end_segment) is int
            and 0 <= self.start_segment <= self.end_segment,
            "SEGMENT",
        )
        require(
            self.boundary_reason in {"START", "CLOCK_RESET", "MANIFEST_GAP", "MALFORMED_PREVIOUS"},
            "BOUNDARY",
        )
        require(
            type(self.points) is tuple
            and len(self.points) <= 12000
            and all(type(p) is Point for p in self.points),
            "EPOCH_POINTS",
        )
        require(len({p.sample_sha256 for p in self.points}) == len(self.points), "DUPLICATE_SAMPLE")
        require(
            all(
                a.time_ns < b.time_ns
                for a, b in zip(self.points[:-1], self.points[1:], strict=True)
            ),
            "NONINCREASING_TIME",
        )


@dataclass(frozen=True, slots=True)
class Route:
    route_sha256: str
    epochs: tuple[Epoch, ...]

    def __post_init__(self) -> None:
        require(sha(self.route_sha256), "ROUTE_ID")
        require(
            type(self.epochs) is tuple
            and 1 <= len(self.epochs) <= 128
            and all(type(e) is Epoch for e in self.epochs),
            "ROUTE_EPOCHS",
        )
        require(len({e.epoch_sha256 for e in self.epochs}) == len(self.epochs), "DUPLICATE_EPOCH")
        ordered = tuple(sorted(self.epochs, key=lambda e: (e.start_segment, e.epoch_sha256)))
        for prior, current in zip(ordered[:-1], ordered[1:], strict=True):
            gap = current.start_segment - prior.end_segment
            require(
                gap > 0
                and (
                    (gap == 1 and current.boundary_reason == "CLOCK_RESET")
                    or (
                        gap > 1
                        and current.boundary_reason in {"MANIFEST_GAP", "MALFORMED_PREVIOUS"}
                    )
                ),
                "ROUTE_BOUNDARY",
            )
        object.__setattr__(self, "epochs", ordered)


@dataclass(frozen=True, slots=True)
class FrozenDevelopment:
    role: str
    signal_contract: str
    runtime_revision: str
    research_revision: str
    x_stage: str
    y_unit: str
    delay_applications: int
    controller_mode: str
    provenance_sha256: str
    selection_binding_sha256: str
    routes: tuple[Route, ...]

    def __post_init__(self) -> None:
        require(self.role == "development_fit", "ROLE")
        require(self.signal_contract == SIGNAL, "SIGNAL_CONTRACT")
        require(
            self.runtime_revision == RUNTIME and self.research_revision == RESEARCH,
            "SOURCE_REVISION",
        )
        require(self.x_stage == "negative_applied_normalized_torque", "APPLIED_STAGE")
        require(self.y_unit == "m/s^2", "UNIT")
        require(type(self.delay_applications) is int and self.delay_applications == 1, "DELAY")
        require(self.controller_mode == "LINEAR_TORQUE", "MODE")
        require(sha(self.provenance_sha256) and sha(self.selection_binding_sha256), "PROVENANCE")
        require(
            type(self.routes) is tuple
            and 1 <= len(self.routes) <= 128
            and all(type(r) is Route for r in self.routes),
            "ROUTES",
        )
        require(len({r.route_sha256 for r in self.routes}) == len(self.routes), "DUPLICATE_ROUTE")
        epochs = tuple(e for r in self.routes for e in r.epochs)
        require(
            len(epochs) <= 128 and len({e.epoch_sha256 for e in epochs}) == len(epochs),
            "DUPLICATE_OR_EXCESS_EPOCH",
        )
        samples = tuple(p.sample_sha256 for e in epochs for p in e.points)
        require(len(set(samples)) == len(samples), "DUPLICATE_SAMPLE")
        object.__setattr__(self, "routes", tuple(sorted(self.routes, key=lambda r: r.route_sha256)))

    @property
    def digest(self) -> str:
        return digest(asdict(self))
