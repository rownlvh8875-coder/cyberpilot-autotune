"""Bounded synthetic schema. Decoding never starts an engine or reads files."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from types import MappingProxyType
from typing import Any, cast

from cyberpilot_autotune.contracts import (
    ObservationSnapshot,
    OutOfRangePolicy,
    ParameterSpec,
    ValidationError,
)
from cyberpilot_autotune.contracts.validation import nonnegative, parameters, text, typed_tuple
from cyberpilot_autotune.core.residual import ResidualStatisticsConfig
from cyberpilot_autotune.safety.gate import GateConfig

MAX_REPLAY_BYTES = 256 * 1024
MAX_EVENTS = 1000


class UnsupportedConfigurationError(ValidationError):
    """Structurally recognizable replay configuration that this version cannot run."""


CANONICAL_UNITS: Mapping[str, str] = MappingProxyType(
    {
        "timestamp_s": "s",
        "source_age_s": "s",
        "speed_mps": "m/s",
        "desired_curvature_inv_m": "1/m",
        "measured_curvature_inv_m": "1/m",
        "lateral_acceleration_mps2": "m/s^2",
    }
)


def _clock_coordinate(value: float, name: str) -> None:
    # Engine Clock readings are binary64; decoding must not change a time identity.
    if nonnegative(value, name) != value:
        raise ValidationError("clock coordinates must be losslessly representable as binary64")


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    clock_before_s: float
    clock_after_s: float
    observation: ObservationSnapshot

    def __post_init__(self) -> None:
        _clock_coordinate(self.clock_before_s, "clock_before_s")
        _clock_coordinate(self.clock_after_s, "clock_after_s")
        if self.clock_after_s < self.clock_before_s:
            raise ValidationError("replay clock regressed during an event")
        if type(self.observation) is not ObservationSnapshot:
            raise ValidationError("replay event requires ObservationSnapshot")
        snapshot = replace(self.observation)
        _clock_coordinate(snapshot.timestamp_s, "timestamp_s")
        if not snapshot.context_key.startswith("synthetic/"):
            raise ValidationError("replay context must be explicitly synthetic")
        object.__setattr__(self, "observation", snapshot)


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    schema_version: int
    scope: str
    learner_version: str
    time_domain: str
    monotonic_origin_s: float
    units: Mapping[str, str]
    baseline_parameters: Mapping[str, float]
    parameter_spec: ParameterSpec
    gate_config: GateConfig
    learner_config: ResidualStatisticsConfig
    events: tuple[ReplayEvent, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise ValidationError("schema version must be an integer")
        if self.schema_version != 1:
            raise UnsupportedConfigurationError("unsupported replay schema version")
        for name in ("scope", "learner_version", "time_domain"):
            text(getattr(self, name), name)
        if self.scope != "SYNTHETIC_TEST_ONLY" or self.learner_version != "residual-ewma-v1":
            raise UnsupportedConfigurationError("unsupported scope or learner version")
        if self.time_domain != "synthetic.monotonic.v1":
            raise UnsupportedConfigurationError("unknown replay clock domain")
        _clock_coordinate(self.monotonic_origin_s, "monotonic_origin_s")
        if not isinstance(self.units, Mapping) or set(self.units) != set(CANONICAL_UNITS):
            raise ValidationError("canonical units must have exact fields")
        for unit_value in self.units.values():
            text(unit_value, "unit")
        if dict(self.units) != CANONICAL_UNITS:
            raise UnsupportedConfigurationError("unsupported canonical units")
        if (
            type(self.parameter_spec) is not ParameterSpec
            or type(self.gate_config) is not GateConfig
            or type(self.learner_config) is not ResidualStatisticsConfig
        ):
            raise ValidationError("invalid replay configuration types")
        spec, gate, learner = (
            replace(self.parameter_spec),
            replace(self.gate_config),
            replace(self.learner_config),
        )
        if not spec.parameter_id.startswith("synthetic.") or spec.persistence_eligible:
            raise UnsupportedConfigurationError("only nonpersistent synthetic specs are admitted")
        baseline = parameters(self.baseline_parameters)
        if set(baseline) != {spec.parameter_id}:
            raise ValidationError("replay baseline must bind the single declared parameter")
        if not spec.lower_bound <= baseline[spec.parameter_id] <= spec.upper_bound:
            raise ValidationError("trusted replay baseline must be inside its specification")
        if gate.minimum_speed_mps < learner.minimum_speed_mps:
            raise UnsupportedConfigurationError("common admission weaker than learner policy")
        events = typed_tuple(self.events, ReplayEvent)
        if not 0 < len(events) <= MAX_EVENTS:
            raise ValidationError("replay must contain 1..1000 events")
        events = tuple(replace(event) for event in events)
        previous_clock = self.monotonic_origin_s
        for event in events:
            snapshot = event.observation
            if (
                event.clock_before_s < previous_clock
                or snapshot.timestamp_s < self.monotonic_origin_s
            ):
                raise ValidationError("event is outside the declared monotonic clock domain")
            previous_clock = event.clock_after_s
        for name, value in (
            ("units", MappingProxyType(dict(self.units))),
            ("baseline_parameters", baseline),
            ("parameter_spec", spec),
            ("gate_config", gate),
            ("learner_config", learner),
            ("events", events),
        ):
            object.__setattr__(self, name, value)


def _object(value: object, expected: set[str]) -> dict[str, Any]:
    # Any is restricted to this validated JSON-constructor boundary.
    if type(value) is not dict or set(value) != expected:
        raise ValidationError("replay object has missing or unknown fields")
    return cast(dict[str, Any], value)


def _names(cls: type[Any]) -> set[str]:
    return {field.name for field in fields(cls)}


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate replay JSON key")
        result[key] = value
    return result


def _nonfinite(token: str) -> None:
    raise ValidationError("non-finite JSON tokens are not admitted")


def load_replay(document: str) -> ReplayScenario:
    """Decode a bounded synthetic JSON string; no file/network/engine access."""
    if type(document) is not str:
        raise ValidationError("replay input must be a JSON string")
    try:
        if len(document.encode("utf-8")) > MAX_REPLAY_BYTES:
            raise ValidationError("replay JSON exceeds 256 KiB")
        value = json.loads(document, object_pairs_hook=_unique, parse_constant=_nonfinite)
    except ValidationError:
        raise
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise ValidationError("invalid replay JSON") from exc
    data = _object(value, _names(ReplayScenario))
    spec = _object(data["parameter_spec"], _names(ParameterSpec)).copy()
    text(spec["out_of_range_policy"], "out_of_range_policy")
    if spec["out_of_range_policy"] != "REJECT":
        raise UnsupportedConfigurationError("only explicit REJECT policy is admitted")
    spec["out_of_range_policy"] = OutOfRangePolicy.REJECT
    raw_events = data["events"]
    if type(raw_events) is not list or not 0 < len(raw_events) <= MAX_EVENTS:
        raise ValidationError("invalid replay event collection")
    events = []
    for raw in raw_events:
        event = _object(raw, _names(ReplayEvent))
        snapshot = ObservationSnapshot(**_object(event["observation"], _names(ObservationSnapshot)))
        events.append(ReplayEvent(event["clock_before_s"], event["clock_after_s"], snapshot))
    return ReplayScenario(
        schema_version=data["schema_version"],
        scope=data["scope"],
        learner_version=data["learner_version"],
        time_domain=data["time_domain"],
        monotonic_origin_s=data["monotonic_origin_s"],
        units=data["units"],
        baseline_parameters=data["baseline_parameters"],
        parameter_spec=ParameterSpec(**spec),
        gate_config=GateConfig(**_object(data["gate_config"], _names(GateConfig))),
        learner_config=ResidualStatisticsConfig(
            **_object(data["learner_config"], _names(ResidualStatisticsConfig))
        ),
        events=tuple(events),
    )
