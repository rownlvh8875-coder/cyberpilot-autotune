"""Immutable result with an enforced baseline identity invariant."""

from collections.abc import Mapping
from dataclasses import dataclass

from cyberpilot_autotune.runtime.mode import RuntimeMode

from .decision import DiagnosticEvent, GateDecision
from .proposal import TuningProposal
from .validation import ValidationError, count, parameters, typed_tuple


@dataclass(frozen=True, slots=True)
class EngineResult:
    mode: RuntimeMode
    observation_sequence: int | None
    proposals: tuple[TuningProposal, ...]
    gate_decisions: tuple[GateDecision, ...]
    baseline_parameters: Mapping[str, float]
    effective_parameters: Mapping[str, float]
    events: tuple[DiagnosticEvent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.mode, RuntimeMode):
            raise ValidationError("only typed OFF and SHADOW modes are supported")
        if self.observation_sequence is not None:
            count(self.observation_sequence, "observation_sequence")
        for name, item_type in (
            ("proposals", TuningProposal),
            ("gate_decisions", GateDecision),
            ("events", DiagnosticEvent),
        ):
            object.__setattr__(self, name, typed_tuple(getattr(self, name), item_type))
        baseline = parameters(self.baseline_parameters)
        effective = parameters(self.effective_parameters)
        if effective != baseline:
            raise ValidationError("effective parameters must equal baseline")
        object.__setattr__(self, "baseline_parameters", baseline)
        object.__setattr__(self, "effective_parameters", baseline)
