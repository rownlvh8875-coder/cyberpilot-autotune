"""Metadata identity properties without network, clocks or controller execution."""

from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from tests.fixtures.knowledge import parameter


@given(st.dictionaries(st.text(min_size=1, max_size=12), st.integers(), max_size=12))
def test_random_mapping_order_cannot_change_canonical_identity(values):
    from cyberpilot_autotune.knowledge.canonical import canonical_digest

    assert canonical_digest(values) == canonical_digest(dict(reversed(tuple(values.items()))))


@given(st.integers(min_value=1, max_value=10000))
def test_ui_range_changes_identity_without_changing_type_or_creating_policy(delta):
    from cyberpilot_autotune.contracts import ParameterSpec

    p = parameter()
    changed = replace(p, ui_catalog_max=p.ui_catalog_max + delta)
    assert changed.digest != p.digest
    assert changed.storage_scale == p.storage_scale
    assert not isinstance(changed, ParameterSpec)
    assert not hasattr(changed, "baseline") and not hasattr(changed, "authorization")
