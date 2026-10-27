"""Injected monotonic time. Adapters must use the same time domain."""

from dataclasses import dataclass
from time import monotonic
from typing import Protocol


class Clock(Protocol):
    def now_s(self) -> float:
        """Return finite nonnegative monotonic seconds."""
        ...


@dataclass(frozen=True, slots=True)
class MonotonicClock:
    def now_s(self) -> float:
        return monotonic()
