"""All values are synthetic, test-only and unrelated to vehicle tuning."""

from dataclasses import dataclass

from cyberpilot_autotune.contracts import ObservationSnapshot, TuningProposal


@dataclass
class FakeClock:
    value: float = 10.0

    def now_s(self) -> float:
        return self.value


class ScriptedLearner:
    def __init__(self, output=(), error=None):
        self.output = output
        self.error = error
        self.calls = 0

    def observe(self, snapshot: ObservationSnapshot) -> tuple[TuningProposal, ...]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.output
