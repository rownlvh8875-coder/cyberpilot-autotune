"""Immutable scalar research records and canonical identity, with no IO."""

import hashlib
import json
import math
import re
from dataclasses import dataclass

RUNTIME = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
RESEARCH = "02652a441c1c39b4a9c3bfaf1132217f0e57b384"
SIGNAL = (
    "torqued-v1:negative-applied-normalized-torque:calibrated-roll-corrected-mps2:lag-aligned-once"
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)  # type: ignore[arg-type]


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
