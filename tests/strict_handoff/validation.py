"""Exact integer-limit admission before all unchanged legacy schema checks."""

from typing import Any

from tests.audit.validate_guest_input_handoff_design import validate_schema

VALIDATOR_PROFILE = "handoff-limit-exact-int-strict-v1"
_EXPECTED_LIMITS = (
    ("members", 16),
    ("bytes_per_member", 4096),
    ("events", 1024),
    ("json_bytes", 2097152),
)


def validate_schema_strict(data: Any) -> None:
    """Validate an object, not raw JSON, without coercion, repair or qualification."""
    if type(data) is not dict or "limits" not in data:
        raise ValueError("EXACT_INTEGER_LIMITS_REQUIRED")
    limits = data["limits"]
    if type(limits) is not dict or len(limits) != len(_EXPECTED_LIMITS):
        raise ValueError("EXACT_INTEGER_LIMITS_REQUIRED")
    if any(type(key) is not str for key in limits):
        raise ValueError("EXACT_INTEGER_LIMITS_REQUIRED")
    for key, expected in _EXPECTED_LIMITS:
        if key not in limits:
            raise ValueError("EXACT_INTEGER_LIMITS_REQUIRED")
        value = limits[key]
        if type(value) is not int or value != expected:
            raise ValueError("EXACT_INTEGER_LIMITS_REQUIRED")
    validate_schema(data)
