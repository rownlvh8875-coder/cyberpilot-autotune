"""Fresh OFF/SHADOW runs and independent software evidence, never state persistence."""

import hashlib
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import partial
from time import perf_counter_ns
from types import MappingProxyType

from cyberpilot_autotune.contracts import EngineResult, ValidationError
from cyberpilot_autotune.contracts.validation import count, typed_tuple
from cyberpilot_autotune.core.no_op import NoOpLearner
from cyberpilot_autotune.core.residual import ResidualStatisticsLearner
from cyberpilot_autotune.runtime.engine import AutoTuneEngine
from cyberpilot_autotune.runtime.mode import RuntimeMode
from cyberpilot_autotune.safety.gate import SafetyGate
from cyberpilot_autotune.safety.reasons import ReasonCode as R

from .canonical import canonical_bytes
from .schema import ReplayEvent, ReplayScenario


@dataclass(frozen=True, slots=True)
class ReplaySummary:
    event_count: int
    proposal_count: int
    eligible_count: int
    rejection_counts: Mapping[R, int]
    override_exclusion_count: int
    saturation_exclusion_count: int
    maximum_proposed_delta: Fraction
    invariant_violations: int
    internal_error_count: int

    def __post_init__(self) -> None:
        for name in (
            "event_count",
            "proposal_count",
            "eligible_count",
            "override_exclusion_count",
            "saturation_exclusion_count",
            "invariant_violations",
            "internal_error_count",
        ):
            count(getattr(self, name), name)
        if type(self.maximum_proposed_delta) is not Fraction or self.maximum_proposed_delta < 0:
            raise ValidationError("maximum proposed delta must be a nonnegative exact Fraction")
        if not isinstance(self.rejection_counts, Mapping):
            raise ValidationError("invalid rejection counts")
        copied = {}
        for reason, value in self.rejection_counts.items():
            if not isinstance(reason, R):
                raise ValidationError("rejection counts require stable reason codes")
            count(value, "rejection count")
            copied[reason] = value
        object.__setattr__(self, "rejection_counts", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class ReplayLatency:
    """Nondeterministic measurements, explicitly excluded from the evidence digest."""

    off_ns: tuple[int, ...]
    shadow_ns: tuple[int, ...]

    def __post_init__(self) -> None:
        for name in ("off_ns", "shadow_ns"):
            values = typed_tuple(getattr(self, name), int)
            for value in values:
                count(value, "latency_ns")
            object.__setattr__(self, name, values)

    @property
    def off_total_ns(self) -> int:
        return sum(self.off_ns)

    @property
    def shadow_total_ns(self) -> int:
        return sum(self.shadow_ns)


@dataclass(frozen=True, slots=True)
class ReplayReport:
    scenario: ReplayScenario
    off_results: tuple[EngineResult, ...]
    shadow_results: tuple[EngineResult, ...]
    summary: ReplaySummary
    latency: ReplayLatency

    def __post_init__(self) -> None:
        if (
            type(self.scenario) is not ReplayScenario
            or type(self.summary) is not ReplaySummary
            or type(self.latency) is not ReplayLatency
        ):
            raise ValidationError("invalid replay report types")
        scenario = replace(self.scenario)
        off = tuple(replace(item) for item in typed_tuple(self.off_results, EngineResult))
        shadow = tuple(replace(item) for item in typed_tuple(self.shadow_results, EngineResult))
        size = len(scenario.events)
        if (
            len(off) != size
            or len(shadow) != size
            or self.summary.event_count != size
            or len(self.latency.off_ns) != size
            or len(self.latency.shadow_ns) != size
        ):
            raise ValidationError("replay report event counts disagree")
        for name, value in (
            ("scenario", scenario),
            ("off_results", off),
            ("shadow_results", shadow),
            ("summary", replace(self.summary)),
            ("latency", replace(self.latency)),
        ):
            object.__setattr__(self, name, value)

    def deterministic_bytes(self) -> bytes:
        return canonical_bytes(
            {
                "report_schema_version": 1,
                "scenario": self.scenario,
                "off_results": self.off_results,
                "shadow_results": self.shadow_results,
                "summary": self.summary,
            }
        )

    @property
    def digest(self) -> str:
        """Compatibility alias for the historical deterministic report projection."""
        return self.result_sha256

    @property
    def scenario_sha256(self) -> str:
        return hashlib.sha256(canonical_bytes(self.scenario)).hexdigest()

    @property
    def configuration_sha256(self) -> str:
        configuration = {
            name: getattr(self.scenario, name)
            for name in (
                "scope",
                "learner_version",
                "time_domain",
                "baseline_parameters",
                "parameter_spec",
                "gate_config",
                "learner_config",
            )
        }
        return hashlib.sha256(canonical_bytes(configuration)).hexdigest()

    @property
    def result_sha256(self) -> str:
        return hashlib.sha256(self.deterministic_bytes()).hexdigest()

    @property
    def software_checks_passed(self) -> bool:
        return (
            self.summary.invariant_violations == 0
            and self.summary.internal_error_count == 0
            and self.summary.rejection_counts.get(R.UNHEALTHY, 0) == 0
        )


class _ReplayClock:
    def __init__(self) -> None:
        self.event: ReplayEvent | None = None
        self.reads = 0

    def set_event(self, event: ReplayEvent) -> None:
        self.event, self.reads = event, 0

    def now_s(self) -> float:
        if self.event is None or self.reads >= 2:
            raise ValidationError("unexpected replay clock access")
        value = self.event.clock_before_s if self.reads == 0 else self.event.clock_after_s
        self.reads += 1
        return value


def _measure(
    operation: Callable[[], EngineResult], timer: Callable[[], int]
) -> tuple[EngineResult, int]:
    start = timer()
    count(start, "timer start")
    result = operation()
    end = timer()
    count(end, "timer end")
    if end < start:
        raise ValidationError("latency timer regressed")
    return result, end - start


def _violations(
    result: EngineResult,
    event: ReplayEvent,
    scenario: ReplayScenario,
    mode: RuntimeMode,
    previous_capture: float | None,
    previous_sequence: int | None,
) -> int:
    """Independent checks, deliberately not delegated to SafetyGate's own predicates."""
    snapshot, baseline, spec = (
        event.observation,
        scenario.baseline_parameters,
        scenario.parameter_spec,
    )
    violations = int(result.mode is not mode or result.observation_sequence != snapshot.sequence)
    violations += int(
        result.baseline_parameters != baseline or result.effective_parameters != baseline
    )
    if mode is RuntimeMode.OFF:
        return violations + int(
            bool(result.proposals or result.gate_decisions)
            or any(item.reason is not R.MODE_OFF for item in result.events)
        )
    violations += int(len(result.proposals) != len(result.gate_decisions))
    violations += int(
        any(item.reason is R.MODE_OFF for item in result.events)
        or any(item.reason is R.MODE_OFF for item in result.gate_decisions)
    )
    for proposal, decision in zip(result.proposals, result.gate_decisions, strict=False):
        if not decision.eligible:
            continue
        value = proposal.proposed_value
        delta = abs(Fraction(value) - Fraction(baseline[spec.parameter_id]))
        rate_ok = (
            delta == 0
            if previous_capture is None
            else (
                delta
                <= Fraction(spec.maximum_rate_per_second)
                * (Fraction(snapshot.timestamp_s) - Fraction(previous_capture))
            )
        )
        gate = scenario.gate_config
        valid = (
            proposal.parameter_id == decision.parameter_id == spec.parameter_id
            and decision.evaluated_candidate == value
            and proposal.baseline_value == baseline[spec.parameter_id]
            and snapshot.baseline_parameters == baseline
            and proposal.context_key == snapshot.context_key
            and proposal.timestamp_s == snapshot.timestamp_s
            and proposal.learner_version == scenario.learner_version
            and decision.evaluation_timestamp_s == event.clock_after_s
            and snapshot.source_valid
            and snapshot.control_active is True
            and snapshot.driver_override is False
            and snapshot.controller_saturated is False
            and snapshot.speed_mps is not None
            and snapshot.speed_mps >= gate.minimum_speed_mps
            and snapshot.timestamp_s <= event.clock_before_s
            and (previous_sequence is None or snapshot.sequence > previous_sequence)
            and (previous_capture is None or snapshot.timestamp_s > previous_capture)
            and snapshot.source_age_s + (event.clock_after_s - snapshot.timestamp_s)
            <= gate.maximum_observation_age_s
            and proposal.sample_count >= gate.minimum_samples
            and proposal.confidence >= gate.minimum_confidence
            and spec.lower_bound <= value <= spec.upper_bound
            and delta <= Fraction(spec.maximum_step)
            and rate_ok
        )
        violations += int(not valid)
    return violations


def run_replay(
    scenario: ReplayScenario, *, timer_ns: Callable[[], int] = perf_counter_ns
) -> ReplayReport:
    """Run only validated synthetic scenarios, with fresh in-memory engines on every call."""
    return characterize_replay(scenario, timer_ns=timer_ns)[0]


def characterize_replay(
    scenario: ReplayScenario, *, timer_ns: Callable[[], int] = perf_counter_ns
) -> tuple[ReplayReport, tuple[int | None, ...]]:
    """Return the report and same-run post-event learner sample counts, without IO.

    None denotes an empty evidence window. The sidecar is outside the historical
    report v1 hash projection and is separately checked by focused expectations.
    """
    if type(scenario) is not ReplayScenario:
        raise ValidationError("run_replay requires ReplayScenario")
    scenario = replace(scenario)  # Revalidate before construction or execution of either engine.
    registry = {scenario.parameter_spec.parameter_id: scenario.parameter_spec}
    off_clock, shadow_clock = _ReplayClock(), _ReplayClock()
    off = AutoTuneEngine(
        mode=RuntimeMode.OFF,
        baseline_parameters=scenario.baseline_parameters,
        learner=NoOpLearner(),
        gate=SafetyGate(registry, scenario.gate_config),
        clock=off_clock,
    )
    learner = ResidualStatisticsLearner(scenario.parameter_spec, scenario.learner_config)
    shadow = AutoTuneEngine(
        mode=RuntimeMode.SHADOW,
        baseline_parameters=scenario.baseline_parameters,
        learner=learner,
        gate=SafetyGate(registry, scenario.gate_config),
        clock=shadow_clock,
    )
    off_results, shadow_results = [], []
    off_ns, shadow_ns = [], []
    sample_counts: list[int | None] = []
    rejections: Counter[R] = Counter()
    proposal_count = eligible_count = violations = internal_errors = 0
    maximum_delta = Fraction(0)
    previous_capture = None
    previous_sequence: int | None = None
    for event in scenario.events:
        off_clock.set_event(event)
        shadow_clock.set_event(event)
        off_result, elapsed = _measure(partial(off.step, event.observation), timer_ns)
        off_results.append(off_result)
        off_ns.append(elapsed)
        shadow_result, elapsed = _measure(partial(shadow.step, event.observation), timer_ns)
        shadow_results.append(shadow_result)
        statistics = learner.statistics
        sample_counts.append(None if statistics is None else statistics.sample_count)
        shadow_ns.append(elapsed)
        violations += _violations(
            off_result, event, scenario, RuntimeMode.OFF, previous_capture, previous_sequence
        )
        violations += int(off_clock.reads != 0)
        violations += _violations(
            shadow_result, event, scenario, RuntimeMode.SHADOW, previous_capture, previous_sequence
        )
        for result_event in shadow_result.events:
            if result_event.reason not in (R.ACCEPTED_FOR_SHADOW, R.MODE_OFF):
                rejections[result_event.reason] += 1
        for decision in shadow_result.gate_decisions:
            if decision.eligible:
                eligible_count += 1
            else:
                rejections[decision.reason] += 1
        internal_errors += sum(item.reason is R.INTERNAL_ERROR for item in off_result.events)
        for proposal in shadow_result.proposals:
            proposal_count += 1
            maximum_delta = max(
                maximum_delta,
                abs(Fraction(proposal.proposed_value) - Fraction(proposal.baseline_value)),
            )
        if previous_sequence is None or event.observation.sequence > previous_sequence:
            previous_sequence = event.observation.sequence
        if event.observation.timestamp_s <= event.clock_before_s and (
            previous_capture is None or event.observation.timestamp_s > previous_capture
        ):
            previous_capture = event.observation.timestamp_s
    internal_errors += rejections[R.INTERNAL_ERROR]
    summary = ReplaySummary(
        len(scenario.events),
        proposal_count,
        eligible_count,
        rejections,
        rejections[R.DRIVER_OVERRIDE],
        rejections[R.CONTROLLER_SATURATED],
        maximum_delta,
        violations,
        internal_errors,
    )
    report = ReplayReport(
        scenario,
        tuple(off_results),
        tuple(shadow_results),
        summary,
        ReplayLatency(tuple(off_ns), tuple(shadow_ns)),
    )
    return report, tuple(sample_counts)
