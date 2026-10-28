"""Synthetic resource and no-repair properties."""

from hypothesis import given
from hypothesis import strategies as st

from cyberpilot_autotune.integrations.carrot.cache import ExactCache
from tests.fixtures.carrot_adapter import healthy
from tests.fixtures.carrot_v2 import complete


@given(st.integers(1, 10), st.lists(st.integers(1, 100), max_size=100))
def test_cache_never_exceeds_capacity_and_preserves_only_exact_keys(capacity, keys):
    source = complete()[0].source_command
    cache = ExactCache(capacity)
    expected = set()
    for key in keys:
        cache.put(key, source, healthy())
        expected.add(key)
        if len(expected) > capacity:
            expected.remove(min(expected))
        assert len(cache) <= capacity
        assert {k for k in range(1, 101) if cache.lookup(k) is not None} == expected


@given(st.integers(1, 2**64 - 1))
def test_poisoned_key_cannot_be_repaired_while_retained(key):
    source = complete()[0].source_command
    cache = ExactCache(2)
    cache.put(key, source, healthy())
    cache.poison(key)
    cache.put(key, source, healthy())
    assert cache.lookup(key) is None and cache.is_ambiguous(key)
