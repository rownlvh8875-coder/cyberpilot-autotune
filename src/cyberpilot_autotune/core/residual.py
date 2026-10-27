"""Deterministic proposal-only residual research; no vehicle policy or defaults."""

import math
from dataclasses import dataclass, replace
from fractions import Fraction

from cyberpilot_autotune.contracts import (
    ObservationSnapshot,
    ParameterSpec,
    TuningProposal,
    ValidationError,
)
from cyberpilot_autotune.contracts.validation import count, finite, nonnegative


@dataclass(frozen=True, slots=True)
class ResidualStatisticsConfig:
    """All scales, ages and conversion coefficients are explicitly caller supplied."""

    alpha: float
    minimum_samples: int
    maximum_samples: int
    maximum_source_age_s: float
    maximum_sample_gap_s: float
    maximum_state_age_s: float
    maximum_absolute_residual_inv_m: float
    consistency_scale_inv_m: float
    mean_deadband_inv_m: float
    parameter_delta_per_inv_m: float

    def __post_init__(self) -> None:
        if not 0 < finite(self.alpha, "alpha") <= 1:
            raise ValidationError("alpha must be in (0, 1]")
        count(self.minimum_samples, "minimum_samples")
        count(self.maximum_samples, "maximum_samples")
        if self.minimum_samples < 2 or self.maximum_samples < self.minimum_samples:
            raise ValidationError("require 2 <= minimum_samples <= maximum_samples")
        nonnegative(self.maximum_source_age_s, "maximum_source_age_s")
        for name in (
            "maximum_sample_gap_s",
            "maximum_state_age_s",
            "maximum_absolute_residual_inv_m",
            "consistency_scale_inv_m",
        ):
            if nonnegative(getattr(self, name), name) == 0:
                raise ValidationError(f"{name} must be positive")
        if self.maximum_state_age_s < self.maximum_sample_gap_s:
            raise ValidationError("maximum_state_age_s must cover maximum_sample_gap_s")
        nonnegative(self.mean_deadband_inv_m, "mean_deadband_inv_m")
        if self.mean_deadband_inv_m >= self.maximum_absolute_residual_inv_m:
            raise ValidationError("deadband must be below the residual exclusion threshold")
        if finite(self.parameter_delta_per_inv_m, "parameter_delta_per_inv_m") == 0:
            raise ValidationError("a nonzero explicit parameter conversion is required")


@dataclass(frozen=True, slots=True)
class ResidualStatistics:
    """Heuristic support/consistency, not a physical confidence probability."""

    sample_count: int
    mean_residual_inv_m: float
    mean_absolute_innovation_inv_m: float
    confidence: float

    def __post_init__(self) -> None:
        count(self.sample_count, "sample_count")
        if self.sample_count == 0:
            raise ValidationError("statistics require at least one sample")
        finite(self.mean_residual_inv_m, "mean_residual_inv_m")
        nonnegative(self.mean_absolute_innovation_inv_m, "mean_absolute_innovation_inv_m")
        if not 0 <= finite(self.confidence, "confidence") <= 1:
            raise ValidationError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class _Window:
    context_key: str
    baseline: float
    started_s: float
    statistics: ResidualStatistics


def _finite_float(value: Fraction) -> float | None:
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


class ResidualStatisticsLearner:
    """One stream and one bounded window. Never applies or clips a proposal."""

    def __init__(self, parameter: ParameterSpec, config: ResidualStatisticsConfig) -> None:
        if type(parameter) is not ParameterSpec or type(config) is not ResidualStatisticsConfig:
            raise ValidationError(
                "explicit ParameterSpec and ResidualStatisticsConfig are required"
            )
        self._parameter = replace(parameter)
        self._config = replace(config)
        self._window: _Window | None = None
        self._last_sequence: int | None = None
        self._last_timestamp_s: float | None = None

    @property
    def statistics(self) -> ResidualStatistics | None:
        return self._window.statistics if self._window is not None else None

    def reset(self) -> None:
        """Discard evidence but preserve sequence/time high-water ordering."""
        self._window = None

    def observe(self, snapshot: ObservationSnapshot) -> tuple[TuningProposal, ...]:
        if type(snapshot) is not ObservationSnapshot:
            self.reset()
            raise ValidationError("expected ObservationSnapshot")
        try:
            snapshot = replace(snapshot)
        except ValidationError:
            self.reset()
            raise
        except (AttributeError, TypeError) as exc:
            self.reset()
            raise ValidationError("malformed ObservationSnapshot") from exc

        previous_time = self._last_timestamp_s
        if (self._last_sequence is not None and snapshot.sequence <= self._last_sequence) or (
            previous_time is not None and snapshot.timestamp_s <= previous_time
        ):
            self.reset()
            return ()
        self._last_sequence, self._last_timestamp_s = snapshot.sequence, snapshot.timestamp_s
        desired = snapshot.desired_curvature_inv_m
        measured = snapshot.measured_curvature_inv_m
        if (
            not snapshot.source_valid
            or snapshot.speed_mps is None
            or desired is None
            or measured is None
            or snapshot.driver_override is not False
            or snapshot.controller_saturated is not False
            or snapshot.source_age_s > self._config.maximum_source_age_s
            or self._parameter.parameter_id not in snapshot.baseline_parameters
        ):
            self.reset()
            return ()

        residual = Fraction(desired) - Fraction(measured)
        if abs(residual) > Fraction(self._config.maximum_absolute_residual_inv_m):
            self.reset()
            return ()
        baseline = snapshot.baseline_parameters[self._parameter.parameter_id]
        window = self._window
        if window is not None and (
            snapshot.context_key != window.context_key
            or baseline != window.baseline
            or (
                previous_time is not None
                and Fraction(snapshot.timestamp_s) - Fraction(previous_time)
                > Fraction(self._config.maximum_sample_gap_s)
            )
            or Fraction(snapshot.timestamp_s) - Fraction(window.started_s)
            > Fraction(self._config.maximum_state_age_s)
        ):
            window = None
        if window is None:
            mean, innovation, sample_count, started = residual, Fraction(0), 1, snapshot.timestamp_s
        else:
            previous = window.statistics
            alpha = Fraction(self._config.alpha)
            mean = (1 - alpha) * Fraction(previous.mean_residual_inv_m) + alpha * residual
            innovation = (1 - alpha) * Fraction(
                previous.mean_absolute_innovation_inv_m
            ) + alpha * abs(residual - Fraction(previous.mean_residual_inv_m))
            sample_count = min(previous.sample_count + 1, self._config.maximum_samples)
            started = window.started_s
        mean_float, innovation_float = _finite_float(mean), _finite_float(innovation)
        if mean_float is None or innovation_float is None:
            self.reset()
            return ()
        support = min(Fraction(1), Fraction(sample_count, self._config.minimum_samples))
        consistency = max(
            Fraction(0),
            1 - Fraction(innovation_float) / Fraction(self._config.consistency_scale_inv_m),
        )
        statistics = ResidualStatistics(
            sample_count, mean_float, innovation_float, float(support * consistency)
        )
        self._window = _Window(snapshot.context_key, baseline, started, statistics)
        if (
            sample_count < self._config.minimum_samples
            or abs(mean_float) <= self._config.mean_deadband_inv_m
        ):
            return ()
        delta = Fraction(self._config.parameter_delta_per_inv_m) * Fraction(mean_float)
        candidate = _finite_float(Fraction(baseline) + delta)
        if candidate is None:
            self.reset()
            return ()
        # Float resolution must not turn the requested sign into an opposite/zero change.
        observed_delta = Fraction(candidate) - Fraction(baseline)
        if observed_delta * delta <= 0:
            return ()
        return (
            TuningProposal(
                parameter_id=self._parameter.parameter_id,
                baseline_value=baseline,
                proposed_value=candidate,
                confidence=statistics.confidence,
                sample_count=sample_count,
                context_key=snapshot.context_key,
                learner_version="residual-ewma-v1",
                timestamp_s=snapshot.timestamp_s,
                evidence_summary=(
                    "RESIDUAL_STATISTICS_ONLY",
                    "desired_minus_measured_curvature_inv_m",
                    "confidence_is_heuristic_support_times_consistency",
                ),
            ),
        )
