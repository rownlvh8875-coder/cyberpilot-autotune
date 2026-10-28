"""Deterministic typed encoding for evidence hashes, never data authentication."""

import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from fractions import Fraction
from typing import Any

from cyberpilot_autotune.contracts import ValidationError


def _value(value: object) -> Any:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValidationError("canonical numbers must be finite")
        return {"float64": value.hex()}
    if isinstance(value, Fraction):
        return {"rational": [str(value.numerator), str(value.denominator)]}
    if isinstance(value, Enum):
        return _value(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValidationError("canonical mapping keys must be strings")
        return {key: _value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_value(item) for item in value]
    raise ValidationError("unsupported canonical value type")


def canonical_bytes(value: object) -> bytes:
    """Sorted keys, exact integers, float.hex tags, rational tags and ordered arrays."""
    try:
        return json.dumps(
            _value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("utf-8")
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise ValidationError("invalid canonical value") from exc
