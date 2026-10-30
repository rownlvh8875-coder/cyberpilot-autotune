"""Pure parsing and content identity. No execution or trust establishment."""

import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from .records import HarmlessFixtureResult, HarmlessObservations, field_names


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> Any:
    raise ValueError("nonfinite JSON: " + value)


def _exact(data: Any, names: set[str]) -> dict[str, Any]:
    if type(data) is not dict or set(data) != names:
        raise ValueError("missing/unknown keys or wrong shape")
    return data


def validate_harmless_result(raw: str) -> HarmlessFixtureResult:
    if type(raw) is not str:
        raise ValueError("expected JSON string")
    data = _exact(
        json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite),
        field_names(HarmlessFixtureResult),
    )
    data["actual_observations"] = HarmlessObservations(
        **_exact(data["actual_observations"], field_names(HarmlessObservations))
    )
    return HarmlessFixtureResult(**data)


def result_digest(result: HarmlessFixtureResult) -> str:
    if type(result) is not HarmlessFixtureResult:
        raise ValueError("expected untrusted fixture report")
    result.__post_init__()
    raw = json.dumps(
        asdict(result), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return sha256(raw.encode("utf-8")).hexdigest()
