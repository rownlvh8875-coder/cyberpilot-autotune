"""Bounded timestamp-exact immutable evidence; no message readers or IO."""

from dataclasses import dataclass, replace

from cyberpilot_autotune.adapters.carrot_receipt_contract import (
    SourceCarStateEvidence,
    SourceCommandEvidence,
)

from .errors import CarrotInputError
from .health import TopicHealthEvidence, uint64


def capacity(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise CarrotInputError("INVALID_CACHE_CAPACITY")
    return value


@dataclass(frozen=True, slots=True)
class CacheEntry[T]:
    evidence: T
    health: TopicHealthEvidence


@dataclass(frozen=True, slots=True)
class CacheMetrics:
    entries: int
    poisoned_key_count: int
    eviction_count: int


class ExactCache[T: SourceCommandEvidence | SourceCarStateEvidence]:
    def __init__(self, maximum_entries: int) -> None:
        self._capacity = capacity(maximum_entries)
        self._entries: dict[int, CacheEntry[T] | None] = {}
        self._poisoned_key_count = 0
        self._eviction_count = 0

    @property
    def metrics(self) -> CacheMetrics:
        return CacheMetrics(len(self._entries), self._poisoned_key_count, self._eviction_count)

    def __len__(self) -> int:
        return len(self._entries)

    def put(self, timestamp_ns: int, evidence: T, health: TopicHealthEvidence) -> None:
        uint64(timestamp_ns)
        if (
            type(evidence) not in (SourceCommandEvidence, SourceCarStateEvidence)
            or type(health) is not TopicHealthEvidence
        ):
            raise CarrotInputError("INVALID_CACHE_EVIDENCE")
        entry = CacheEntry(replace(evidence), replace(health))
        if timestamp_ns in self._entries:
            if self._entries[timestamp_ns] != entry:
                if self._entries[timestamp_ns] is not None:
                    self._poisoned_key_count += 1
                self._entries[timestamp_ns] = None
            return
        self._entries[timestamp_ns] = entry
        self._trim()

    def _trim(self) -> None:
        if len(self._entries) > self._capacity:
            del self._entries[min(self._entries)]
            self._eviction_count += 1

    def poison(self, timestamp_ns: int) -> None:
        uint64(timestamp_ns)
        if timestamp_ns not in self._entries or self._entries[timestamp_ns] is not None:
            self._poisoned_key_count += 1
        self._entries[timestamp_ns] = None
        self._trim()

    def lookup(self, timestamp_ns: int | None) -> CacheEntry[T] | None:
        if type(timestamp_ns) is not int or not 0 < timestamp_ns < 2**64:
            return None
        return self._entries.get(timestamp_ns)

    def is_ambiguous(self, timestamp_ns: int | None) -> bool:
        if type(timestamp_ns) is not int or not 0 < timestamp_ns < 2**64:
            return False
        return timestamp_ns in self._entries and self._entries[timestamp_ns] is None
