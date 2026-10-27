"""Learners consume immutable canonical observations and return bounded data."""

from typing import Protocol

from cyberpilot_autotune.contracts import ObservationSnapshot, TuningProposal


class Learner(Protocol):
    def observe(self, snapshot: ObservationSnapshot) -> tuple[TuningProposal, ...]:
        """Return proposals only; no IO, global state or input/registry mutation."""
        ...
