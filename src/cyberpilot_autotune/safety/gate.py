"""Ordered, stateless eligibility evaluation. Runtime owns exception recovery."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType

from cyberpilot_autotune.contracts import (
    GateDecision,
    ObservationSnapshot,
    ParameterSpec,
    TuningProposal,
)
from cyberpilot_autotune.contracts.validation import (
    NonFiniteError,
    ValidationError,
    count,
    finite,
    nonnegative,
    parameters,
)

from .bounds import within_bounds, within_step
from .rate_limiter import within_rate
from .reasons import ReasonCode as R
from .sanitizer import observation_error, proposal_error


@dataclass(frozen=True, slots=True)
class GateConfig:
    """Caller-approved screening policy, with no vehicle defaults."""

    maximum_observation_age_s: float
    minimum_samples: int
    minimum_confidence: float
    minimum_speed_mps: float = field(kw_only=True)

    def __post_init__(self) -> None:
        nonnegative(self.maximum_observation_age_s, "maximum_observation_age_s")
        nonnegative(self.minimum_speed_mps, "minimum_speed_mps")
        count(self.minimum_samples, "minimum_samples")
        if not 0 <= finite(self.minimum_confidence, "minimum_confidence") <= 1:
            raise ValidationError("minimum_confidence must be in [0, 1]")


class SafetyGate:
    """One immutable registry; evaluation has no IO and changes no state."""

    def __init__(self, registry: Mapping[str, ParameterSpec], config: GateConfig) -> None:
        if type(config) is not GateConfig or not isinstance(registry, Mapping):
            raise ValidationError("invalid gate configuration")
        self._config = replace(config)
        copied = {}
        for key, spec in registry.items():
            if type(spec) is not ParameterSpec or key != spec.parameter_id:
                raise ValidationError("registry key must match its parameter specification")
            copied[key] = replace(spec)
        self._registry = MappingProxyType(copied)

    def validate_observation(
        self,
        observation: object,
        *,
        now_s: float,
        previous_sequence: int | None = None,
        previous_timestamp_s: float | None = None,
    ) -> R | None:
        # 1. Existence/type. 2. Monotonic timestamp domain and future rejection.
        if type(observation) is not ObservationSnapshot:
            return R.INVALID_OBSERVATION
        try:
            nonnegative(now_s, "now_s")
            nonnegative(observation.timestamp_s, "timestamp_s")
        except NonFiniteError:
            return R.NON_FINITE
        except ValidationError:
            return R.INVALID_OBSERVATION
        if observation.timestamp_s > now_s:
            return R.FUTURE_TIMESTAMP
        # 3. Freshness: source age at capture plus elapsed time since capture.
        try:
            nonnegative(observation.source_age_s, "source_age_s")
        except NonFiniteError:
            return R.NON_FINITE
        except ValidationError:
            return R.INVALID_OBSERVATION
        age = observation.source_age_s + (now_s - observation.timestamp_s)
        if age > self._config.maximum_observation_age_s:
            return R.STALE_OBSERVATION
        # 4. Sequence and strict timestamp progress. History is trusted engine state.
        try:
            count(observation.sequence, "sequence")
        except ValidationError:
            return R.INVALID_OBSERVATION
        if (previous_sequence is not None and observation.sequence <= previous_sequence) or (
            previous_timestamp_s is not None and observation.timestamp_s <= previous_timestamp_s
        ):
            return R.OUT_OF_ORDER
        # 5. All remaining numbers, types, source validity and required signals.
        return observation_error(observation)

    def evaluate(
        self,
        observation: object,
        proposal: object,
        *,
        now_s: float,
        baseline_parameters: Mapping[str, float],
        previous_sequence: int | None = None,
        previous_timestamp_s: float | None = None,
        engine_healthy: bool = True,
    ) -> GateDecision:
        reason = self.validate_observation(
            observation,
            now_s=now_s,
            previous_sequence=previous_sequence,
            previous_timestamp_s=previous_timestamp_s,
        )
        # A corrupt proposal is never echoed into a validated decision.
        parameter_id = None
        candidate = None

        def decision(code: R) -> GateDecision:
            timestamp = None
            try:
                timestamp = nonnegative(now_s, "now_s")
            except ValidationError:
                pass
            return GateDecision(
                code is R.ACCEPTED_FOR_SHADOW, parameter_id, candidate, code, (), timestamp
            )

        if reason is not None:
            return decision(reason)
        assert isinstance(observation, ObservationSnapshot)
        reason = proposal_error(proposal)
        if reason is not None:
            return decision(reason)
        assert isinstance(proposal, TuningProposal)
        parameter_id, candidate = proposal.parameter_id, proposal.proposed_value
        try:
            baseline = parameters(baseline_parameters)
        except NonFiniteError:
            return decision(R.NON_FINITE)
        except ValidationError:
            return decision(R.BASELINE_MISMATCH)
        if proposal.timestamp_s > now_s:
            return decision(R.FUTURE_TIMESTAMP)
        if proposal.timestamp_s != observation.timestamp_s:
            return decision(R.INVALID_PROPOSAL)
        # 6. Registry. 7. Baseline identity. 8. Context binding.
        spec = self._registry.get(parameter_id)
        if spec is None:
            return decision(R.UNKNOWN_PARAMETER)
        if (
            parameter_id not in baseline
            or observation.baseline_parameters != baseline
            or proposal.baseline_value != baseline[parameter_id]
        ):
            return decision(R.BASELINE_MISMATCH)
        if proposal.context_key != observation.context_key:
            return decision(R.CONTEXT_MISMATCH)
        # 9/10. Evidence thresholds. 11/12. Driver/saturation vetoes.
        if proposal.sample_count < self._config.minimum_samples:
            return decision(R.INSUFFICIENT_SAMPLES)
        if proposal.confidence < self._config.minimum_confidence:
            return decision(R.LOW_CONFIDENCE)
        if observation.driver_override:
            return decision(R.DRIVER_OVERRIDE)
        if observation.controller_saturated:
            return decision(R.CONTROLLER_SATURATED)
        # 13/14/15. Hard bounds, step, then elapsed rate budget. Never clip.
        if not within_bounds(candidate, spec) or not within_bounds(baseline[parameter_id], spec):
            return decision(R.OUT_OF_BOUNDS)
        if not within_step(candidate, baseline[parameter_id], spec.maximum_step):
            return decision(R.STEP_LIMIT_EXCEEDED)
        if not within_rate(
            candidate,
            baseline[parameter_id],
            spec.maximum_rate_per_second,
            observation.timestamp_s,
            previous_timestamp_s,
        ):
            return decision(R.RATE_LIMIT_EXCEEDED)
        # 16. Watchdog/health, explicitly true only. 17. Shadow eligibility.
        if engine_healthy is not True:
            return decision(R.UNHEALTHY)
        return decision(R.ACCEPTED_FOR_SHADOW)
