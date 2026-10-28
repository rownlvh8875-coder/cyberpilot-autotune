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


@runtime_checkable
class LearningRequirements(Learner, Protocol):
    """Optional explicit learner requirement; common admission must be at least as strict."""

    @property
    def minimum_speed_mps(self) -> float:
        """Return a finite nonnegative, caller-supplied speed threshold."""
        ...
