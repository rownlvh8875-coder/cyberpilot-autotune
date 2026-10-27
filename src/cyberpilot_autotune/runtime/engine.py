"""Outer fail-closed processing boundary. No controller capability exists."""

from collections.abc import Mapping
from dataclasses import replace

from cyberpilot_autotune.contracts import (
    EngineResult,
    GateDecision,
    ObservationSnapshot,
    TuningProposal,
    ValidationError,
)
from cyberpilot_autotune.contracts.validation import count, nonnegative, parameters
from cyberpilot_autotune.core.learner import Learner, LearningRequirements, ResettableLearner
from cyberpilot_autotune.safety.gate import SafetyGate
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from cyberpilot_autotune.safety.sanitizer import proposal_error
from cyberpilot_autotune.telemetry.events import DiagnosticEvent

from .clock import Clock
from .mode import RuntimeMode


class AutoTuneEngine:
    """Single-owner synchronous stream processor with a trusted fixed baseline."""

    def __init__(
        self,
        *,
        mode: RuntimeMode,
        baseline_parameters: Mapping[str, float],
        learner: Learner,
        gate: SafetyGate,
        clock: Clock,
        maximum_proposals: int = 64,
    ) -> None:
        if not isinstance(mode, RuntimeMode):
            raise ValidationError("only typed OFF and SHADOW modes are supported")
        count(maximum_proposals, "maximum_proposals")
        if maximum_proposals == 0:
            raise ValidationError("maximum_proposals must be positive")
        if isinstance(learner, LearningRequirements):
            required_speed = learner.minimum_speed_mps
            nonnegative(required_speed, "learner minimum_speed_mps")
            if gate.minimum_speed_mps < required_speed:
                raise ValidationError("gate minimum speed must cover the learner requirement")
        self._mode = mode
        self._baseline = parameters(baseline_parameters)
        self._learner = learner
        self._gate = gate
        self._clock = clock
        self._maximum_proposals = maximum_proposals
        self._previous_sequence: int | None = None
        self._previous_timestamp_s: float | None = None
        self._last_clock_s: float | None = None
        self._faulted = False

    def _result(
        self,
        sequence: int | None,
        *,
        proposals: tuple[TuningProposal, ...] = (),
        decisions: tuple[GateDecision, ...] = (),
        events: tuple[DiagnosticEvent, ...] = (),
    ) -> EngineResult:
        return EngineResult(
            self._mode, sequence, proposals, decisions, self._baseline, self._baseline, events
        )

    def step(self, observation: object) -> EngineResult:
        sequence = None
        try:
            # Include metadata extraction in the outer boundary, even for forged dataclasses.
            if type(observation) is ObservationSnapshot:
                raw_sequence = observation.sequence
                if type(raw_sequence) is int and raw_sequence >= 0:
                    sequence = raw_sequence
            if self._mode is RuntimeMode.OFF:
                return self._result(
                    sequence, events=(DiagnosticEvent(R.MODE_OFF, "Learner skipped"),)
                )
            if self._faulted:
                return self._result(
                    sequence,
                    events=(
                        DiagnosticEvent(
                            R.UNHEALTHY, "Engine fault latched; construct a new engine to reset"
                        ),
                    ),
                )
            now = nonnegative(self._clock.now_s(), "clock")
            if self._last_clock_s is not None and now < self._last_clock_s:
                self._faulted = True
                return self._reject(sequence, R.UNHEALTHY, "Monotonic clock regressed")
            self._last_clock_s = now
            previous_sequence = self._previous_sequence
            previous_timestamp_s = self._previous_timestamp_s
            reason = self._gate.validate_learning_sample(
                observation,
                now_s=now,
                baseline_parameters=self._baseline,
                previous_sequence=previous_sequence,
                previous_timestamp_s=previous_timestamp_s,
            )
            # Consume rejected sequences too; future timestamps cannot advance time high-water.
            self._record_order(observation, now_s=now)
            if reason is not None:
                return self._reject(sequence, reason, "Observation rejected")
            assert isinstance(observation, ObservationSnapshot)
            snapshot = replace(observation)
            output = self._learner.observe(snapshot)
            finished = nonnegative(self._clock.now_s(), "clock")
            if finished < now:
                self._faulted = True
                return self._reject(
                    sequence, R.UNHEALTHY, "Monotonic clock regressed during learner work"
                )
            self._last_clock_s = finished
            reason = self._gate.validate_learning_sample(
                snapshot,
                now_s=finished,
                baseline_parameters=self._baseline,
                previous_sequence=previous_sequence,
                previous_timestamp_s=previous_timestamp_s,
            )
            if reason is not None:
                return self._reject(sequence, reason, "Post-work validation")
            # Do not consume iterators/generators: they can be unbounded or execute code.
            if type(output) not in (tuple, list) or len(output) > self._maximum_proposals:
                return self._reject(
                    sequence, R.INVALID_PROPOSAL, "Expected a bounded proposal collection"
                )
            proposals: list[TuningProposal] = []
            identifiers: set[str] = set()
            for item in output:
                reason = proposal_error(item)
                if reason is not None:
                    return self._reject(sequence, reason, "Malformed proposal")
                if item.parameter_id in identifiers:
                    return self._reject(
                        sequence, R.INVALID_PROPOSAL, "Duplicate parameter proposal"
                    )
                identifiers.add(item.parameter_id)
                proposals.append(replace(item))
            decisions = tuple(
                self._gate.evaluate(
                    snapshot,
                    candidate,
                    now_s=finished,
                    baseline_parameters=self._baseline,
                    engine_healthy=True,
                    previous_sequence=previous_sequence,
                    previous_timestamp_s=previous_timestamp_s,
                )
                for candidate in proposals
            )
            return self._result(sequence, proposals=tuple(proposals), decisions=decisions)
        except Exception as exc:
            if self._mode is RuntimeMode.SHADOW:
                self._faulted = True
            return self._result(
                sequence,
                events=(
                    DiagnosticEvent(R.INTERNAL_ERROR, f"Processing failed: {type(exc).__name__}"),
                ),
            )

    def _record_order(self, observation: object, *, now_s: float) -> None:
        if type(observation) is not ObservationSnapshot:
            return
        sequence = observation.sequence
        if type(sequence) is int and sequence >= 0:
            if self._previous_sequence is None or sequence > self._previous_sequence:
                self._previous_sequence = sequence
        timestamp = observation.timestamp_s
        try:
            nonnegative(timestamp, "timestamp_s")
        except ValidationError:
            return
        if timestamp <= now_s and (
            self._previous_timestamp_s is None or timestamp > self._previous_timestamp_s
        ):
            self._previous_timestamp_s = timestamp

    def _reject(self, sequence: int | None, reason: R, detail: str) -> EngineResult:
        # Only called inside SHADOW's outer boundary; reset failure is an internal fault.
        if isinstance(self._learner, ResettableLearner):
            self._learner.reset()
        return self._result(sequence, events=(DiagnosticEvent(reason, detail),))
