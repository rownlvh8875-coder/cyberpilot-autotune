"""Observer counters describe actual cache transitions without exposing entries."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cyberpilot_autotune.integrations.carrot.cache import ExactCache
from tests.fixtures.carrot_adapter import healthy
from tests.fixtures.carrot_v2 import complete


def test_metric_counts_poison_transition_once_and_actual_oldest_eviction():
    attempt, _ = complete()
    entry = attempt.source_command
    cache = ExactCache(1)
    cache.put(1, entry, healthy())
    cache.put(1, entry, healthy())
    assert cache.metrics.poisoned_key_count == cache.metrics.eviction_count == 0
    cache.put(1, replace(entry, desired_target_curvature_inv_m=1.0), healthy())
    cache.poison(1)
    assert cache.metrics.poisoned_key_count == 1
    cache.put(2, entry, healthy())
    assert cache.metrics.entries == 1 and cache.metrics.eviction_count == 1
    cache.poison(3)
    assert cache.metrics.poisoned_key_count == 2 and cache.metrics.eviction_count == 2
    with pytest.raises(FrozenInstanceError):
        cache.metrics.eviction_count = 0
