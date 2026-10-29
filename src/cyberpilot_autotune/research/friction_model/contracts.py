"""Immutable controller-domain observations and installed-context identity."""

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass

RUNTIME = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
CURRENT = "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3"
BASE = "43ca6761749e71ec575906f099b02386bc76d994"
PREREGISTRATION = "de42ce3ad6d7b8aa90133898a04685432972ec1a"
POLICY_SHA256 = "503c1f9d07c4dda45edf55693ad4b25fde89f8f751998cef9cff8b84565cdc8c"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def finite(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)  # type: ignore[arg-type]
    except OverflowError:
        return False


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SteeringGeometryContext:
    source_revision: str
    vehicle_context_digest: str | None = None
    wheelbase: float | None = None
    center_to_front: float | None = None
    center_to_front_ratio: float | None = None
    steer_ratio_effective: float | None = None
    stiffness_factor: float | None = None
    controller_mode: str | None = None
    geometry_generation: int | None = None
    snapshot_time_ns: int | None = None
    cohort: str | None = None
    geometry_source: str | None = None
    steer_ratio_rate: float | None = None
    custom_sr: float | None = None
    delay_source: str | None = None
    effective_delay_s: float | None = None
    custom_torque_mode: int | None = None
    factor_installed: float | None = None
    friction_installed: float | None = None

    def __post_init__(self) -> None:
        require(self.source_revision in {RUNTIME, CURRENT}, "SOURCE_REVISION")
        if self.vehicle_context_digest is not None:
            require(
                type(self.vehicle_context_digest) is str
                and re.fullmatch("[0-9a-f]{64}", self.vehicle_context_digest) is not None,
                "VEHICLE_CONTEXT_DIGEST",
            )
        for name in (
            "wheelbase",
            "center_to_front",
            "steer_ratio_effective",
            "stiffness_factor",
            "factor_installed",
        ):
            value = getattr(self, name)
            require(value is None or (finite(value) and value > 0), "POSITIVE_CONTEXT")
        for name in ("steer_ratio_rate", "custom_sr", "effective_delay_s", "friction_installed"):
            value = getattr(self, name)
            require(value is None or (finite(value) and value >= 0), "NONNEGATIVE_CONTEXT")
        ratio = self.center_to_front_ratio
        require(ratio is None or (finite(ratio) and 0 < ratio < 1), "PHYSICAL_RATIO")
        if self.center_to_front is not None and self.wheelbase is not None:
            require(self.center_to_front < self.wheelbase, "AXLE_GEOMETRY")
            if ratio is not None:
                require(
                    math.isclose(self.center_to_front / self.wheelbase, ratio, rel_tol=1e-12),
                    "INCOHERENT_GEOMETRY",
                )
        for value in (self.geometry_generation, self.snapshot_time_ns, self.custom_torque_mode):
            require(
                value is None or (type(value) is int and 0 <= value < 2**63), "CONTEXT_GENERATION"
            )
        require(
            self.controller_mode in {None, "LINEAR_TORQUE", "NN_LITE", "NN", "GM", "CUSTOM"},
            "CONTROLLER_MODE",
        )
        require(self.delay_source in {None, "LIVE_DELAY", "MANUAL", "STATIC_CP"}, "DELAY_SOURCE")
        expected = "STATIC_CP" if self.source_revision == RUNTIME else "APPLIED_VM"
        require(self.geometry_source in {None, expected}, "SOURCE_GEOMETRY")
        require(
            self.cohort is None or (type(self.cohort) is str and 0 < len(self.cohort) <= 128),
            "COHORT",
        )

    @property
    def complete(self) -> bool:
        return all(v is not None for v in asdict(self).values())

    @property
    def digest(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True, slots=True)
class Sample:
    acceleration: float
    callback_output: float
    q: float
    explicit_term: float
    pid: float
    total: float
    context: SteeringGeometryContext
    time_ns: int
    saturated: bool = False
    override: bool = False

    def __post_init__(self) -> None:
        require(
            all(
                finite(v)
                for v in (
                    self.acceleration,
                    self.callback_output,
                    self.q,
                    self.explicit_term,
                    self.pid,
                    self.total,
                )
            ),
            "NONFINITE_SAMPLE",
        )
        require(-1 <= self.q <= 1, "NORMALIZED_Q")
        require(type(self.context) is SteeringGeometryContext, "SAMPLE_CONTEXT")
        require(type(self.time_ns) is int and 0 <= self.time_ns < 2**63, "SAMPLE_TIME")
        require(type(self.saturated) is bool and type(self.override) is bool, "SAMPLE_HEALTH")
