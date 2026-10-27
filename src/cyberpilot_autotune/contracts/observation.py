"""Canonical units; None denotes unavailable, never an inferred numeric zero."""

from collections.abc import Mapping
from dataclasses import dataclass

from .validation import boolean, count, finite, nonnegative, parameters, text


@dataclass(frozen=True, slots=True)
class ObservationSnapshot:
    timestamp_s: float
    sequence: int
    source_age_s: float
    context_key: str
    source_valid: bool
    speed_mps: float | None
    desired_curvature_inv_m: float | None
    measured_curvature_inv_m: float | None
    lateral_acceleration_mps2: float | None
    controller_saturated: bool | None
    driver_override: bool | None
    baseline_parameters: Mapping[str, float]

    def __post_init__(self) -> None:
        nonnegative(self.timestamp_s, "timestamp_s")
        nonnegative(self.source_age_s, "source_age_s")
        count(self.sequence, "sequence")
        text(self.context_key, "context_key")
        boolean(self.source_valid, "source_valid")
        boolean(self.controller_saturated, "controller_saturated", optional=True)
        boolean(self.driver_override, "driver_override", optional=True)
        if self.speed_mps is not None:
            nonnegative(self.speed_mps, "speed_mps")
        for value in (
            self.desired_curvature_inv_m,
            self.measured_curvature_inv_m,
            self.lateral_acceleration_mps2,
        ):
            if value is not None:
                finite(value, "observation signal")
        object.__setattr__(self, "baseline_parameters", parameters(self.baseline_parameters))
