"""The only packaged learner: deterministic, stateless and proposal-free."""

from dataclasses import dataclass

from cyberpilot_autotune.contracts import ObservationSnapshot, TuningProposal


@dataclass(frozen=True, slots=True)
class NoOpLearner:
    def observe(self, snapshot: ObservationSnapshot) -> tuple[TuningProposal, ...]:
        return ()
