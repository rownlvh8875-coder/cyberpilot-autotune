"""The external adapter owns validated units, freshness and source validity."""

from typing import Protocol

from cyberpilot_autotune.contracts import ObservationSnapshot


class ObservationAdapter[Source](Protocol):
    def to_observation(self, source: Source, *, now_s: float) -> ObservationSnapshot:
        """Read only. Never mutate controllers, Params, actuators or external state."""
        ...
