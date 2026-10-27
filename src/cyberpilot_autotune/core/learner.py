"""Learners consume immutable canonical observations and return bounded data."""

from typing import Protocol, runtime_checkable

from cyberpilot_autotune.contracts import ObservationSnapshot, TuningProposal


class Learner(Protocol):
    def observe(self, snapshot: ObservationSnapshot) -> tuple[TuningProposal, ...]:
        """Return proposals only; no IO, global state or input/registry mutation."""
        ...


@runtime_checkable
class ResettableLearner(Learner, Protocol):
    """Optional lifecycle for evidence invalidated before/after learner work."""

    def reset(self) -> None:
        """Discard evidence; do not perform IO or reset stream ordering."""
        ...
