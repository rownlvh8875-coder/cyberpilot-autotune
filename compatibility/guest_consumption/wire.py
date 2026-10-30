"""Strict frames; no stdout repair, inferred completion or payload reparsing."""

import hashlib
import json
from dataclasses import asdict
from typing import Any

from .contracts import MAX_RECORDS, CaptureEvent, ConsumptionCapture

MAX_TEXT_BYTES = 64 * 1024 * 1024


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate capture field")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("nonfinite capture scalar: " + value)


def parse_capture(text: str) -> ConsumptionCapture:
    if type(text) is not str or len(text.encode()) > MAX_TEXT_BYTES:
        raise ValueError("capture text outside bound")
    events: list[CaptureEvent] = []
    try:
        for line in text.splitlines():
            if "CONSUMPTION " not in line:
                continue
            if not line.startswith("CONSUMPTION ") or len(events) >= MAX_RECORDS:
                raise ValueError("interleaved capture or resource overflow")
            data = json.loads(line[12:], object_pairs_hook=_unique, parse_constant=_nonfinite)
            if (
                type(data) is not dict
                or set(data) != {"seq", "time_ns", "kind", "task", "image", "values"}
                or type(data["values"]) is not list
            ):
                raise ValueError("unknown/missing capture fields")
            events.append(CaptureEvent(**data))
    except (RecursionError, UnicodeError) as error:
        raise ValueError("invalid capture nesting/encoding") from error
    return ConsumptionCapture(tuple(events))


def capture_digest(capture: ConsumptionCapture) -> str:
    capture.__post_init__()
    return hashlib.sha256(
        json.dumps(asdict(capture), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
