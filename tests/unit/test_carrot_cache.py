"""Exact cache behavior; capacity values are synthetic caller policy."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.cache import ExactCache
from cyberpilot_autotune.integrations.carrot.errors import CarrotInputError
from tests.fixtures.carrot_readers import healthy
from tests.fixtures.carrot_v2 import complete


def test_cache_exact_lookup_eviction_and_idempotence():
    attempt, _ = complete()
    value = attempt.source_command
    cache = ExactCache(2)
    cache.put(1, value, healthy())
    cache.put(2, value, healthy())
    cache.put(2, value, healthy())
    assert cache.lookup(1).evidence == value
    assert cache.lookup(3) is None and len(cache) == 2
    cache.put(3, value, healthy())
    assert cache.lookup(1) is None and cache.lookup(2).evidence == value


def test_conflicting_key_is_poisoned_including_conflicting_health():
    attempt, _ = complete()
    value = attempt.source_command
    cache = ExactCache(2)
    cache.put(1, value, healthy())
    cache.put(1, replace(value, desired_target_curvature_inv_m=0.5), healthy())
    assert cache.is_ambiguous(1) and cache.lookup(1) is None
    cache.put(1, value, healthy())
    assert cache.lookup(1) is None
    cache.put(2, value, healthy())
    cache.put(2, value, replace(healthy(), valid=False))
    assert cache.lookup(2) is None


@pytest.mark.parametrize("key", [0, -1, True, 2**64])
def test_timestamp_keys_are_present_uint64(key):
    attempt, _ = complete()
    cache = ExactCache(1)
    with pytest.raises(CarrotInputError):
        cache.put(key, attempt.source_command, healthy())


def test_capacity_has_no_default_and_rejects_invalid_values():
    for value in (0, -1, True):
        with pytest.raises(CarrotInputError):
            ExactCache(value)


def test_invalid_lookup_keys_never_alias_a_numeric_key():
    attempt, _ = complete()
    cache = ExactCache(1)
    cache.put(1, attempt.source_command, healthy())
    for key in (None, True, 0, -1, 2**64):
        assert cache.lookup(key) is None
        assert not cache.is_ambiguous(key)


def test_cache_cannot_store_a_borrowed_reader_or_unqualified_health():
    cache = ExactCache(1)
    with pytest.raises(CarrotInputError):
        cache.put(1, object(), healthy())
