"""Strict physical-LF frames and content-only canonical digest."""

import hashlib
import json
from dataclasses import asdict
from typing import Any

from .contracts import SealCapture, SealEvent


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate capture field")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("nonfinite scalar: " + value)


def parse_capture(text: str) -> SealCapture:
    if type(text) is not str or len(text.encode()) > 1024 * 1024:
        raise ValueError("capture text outside bound")
    events: list[SealEvent] = []
    try:
        for line in text.split("\n"):
            if "SEAL " not in line:
                continue
            if not line.startswith("SEAL ") or len(events) >= 64:
                raise ValueError("interleaved capture/resource overflow")
            data = json.loads(line[5:], object_pairs_hook=_unique, parse_constant=_nonfinite)
            if (
                type(data) is not dict
                or set(data) != {"seq", "time_ns", "kind", "label", "values"}
                or type(data["values"]) is not list
            ):
                raise ValueError("unknown/missing capture fields")
            events.append(SealEvent(**data))
    except (RecursionError, UnicodeError) as error:
        raise ValueError("invalid capture encoding/nesting") from error
    return SealCapture(tuple(events))


def capture_digest(capture: SealCapture) -> str:
    capture.__post_init__()
    return hashlib.sha256(
        json.dumps(asdict(capture), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def parse_guest_capture(text: str) -> SealCapture:
    """Require a unique, complete, ordered execution envelope; content only."""
    capture = parse_capture(text)
    lines = text.split("\n")
    expected = {
        "ACTUAL_GUEST_KERNEL": "ACTUAL_GUEST_KERNEL=6.12.113+deb13-cloud-amd64",
        "INPUT_SEAL_PROBE_EXIT": "INPUT_SEAL_PROBE_EXIT 0",
        "INPUT_SEAL_GUEST_DONE": "INPUT_SEAL_GUEST_DONE",
    }
    positions: dict[str, int] = {}
    framed = []
    for index, line in enumerate(lines):
        if line.startswith("SEAL "):
            framed.append(index)
        for token, exact in expected.items():
            if token not in line:
                continue
            if index == len(lines) - 1 or line.removesuffix("\r") != exact or token in positions:
                raise ValueError("malformed/duplicate/unterminated execution marker")
            positions[token] = index
    if set(positions) != set(expected):
        raise ValueError("execution envelope incomplete")
    if not (
        positions["ACTUAL_GUEST_KERNEL"] < framed[0]
        and framed[-1] < positions["INPUT_SEAL_PROBE_EXIT"] < positions["INPUT_SEAL_GUEST_DONE"]
    ):
        raise ValueError("execution envelope order invalid")
    return capture
