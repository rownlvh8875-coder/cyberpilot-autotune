"""A deterministic, stateless and proposal-free learner."""

from dataclasses import dataclass

from cyberpilot_autotune.contracts import ObservationSnapshot, TuningProposal


@dataclass(frozen=True, slots=True)
class NoOpLearner:
    def observe(self, snapshot: ObservationSnapshot) -> tuple[TuningProposal, ...]:
        return ()
