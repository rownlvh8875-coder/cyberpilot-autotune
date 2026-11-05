import pytest

from native_e_lab.lab import EXPECTED, _parse_properties, _verify_limits


def test_exact_limits():
    assert _verify_limits(EXPECTED) is None


@pytest.mark.parametrize("field", list(EXPECTED))
@pytest.mark.parametrize("value", ["", "infinity", "0", "999999999"])
def test_missing_unbounded_or_different_limits_block(field, value):
    values = dict(EXPECTED)
    values[field] = value
    if value == EXPECTED[field]:
        assert _verify_limits(values) is None
    else:
        with pytest.raises(ValueError):
            _verify_limits(values)


def test_missing_property_unknown_not_zero():
    values = dict(EXPECTED)
    del values["MemorySwapMax"]
    with pytest.raises(ValueError):
        _verify_limits(values)


@pytest.mark.parametrize("raw", ["MemoryMax=1\nMemoryMax=1", "NoSeparator"])
def test_duplicate_or_unparseable_properties_rejected(raw):
    with pytest.raises(ValueError):
        _parse_properties(raw)
