"""Deterministic metadata identities, never signatures or source attestation."""

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from cyberpilot_autotune.contracts.validation import ValidationError


def _projection(value: object) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValidationError("nonfinite knowledge metadata")
        return value  # JSON preserves 1 versus 1.0, including signed float zero.
    if isinstance(value, Enum):
        return _projection(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _projection(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValidationError("canonical metadata keys must be text")
        return {key: _projection(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_projection(item) for item in value]
    raise ValidationError("unsupported knowledge metadata value")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        _projection(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
