"""Strict wire parsing/canonical identity, never a factual trust verifier."""

import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from .contracts import Capture, TraceEvent


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def exact(raw: str, keys: set[str]) -> dict[str, Any]:
    data = json.loads(raw, object_pairs_hook=unique)
    if type(data) is not dict or set(data) != keys:
        raise ValueError("unknown/missing wire keys")
    return data


def parse_capture(raw: str) -> Capture:
    if type(raw) is not str:
        raise ValueError("expected text capture")
    raw.encode("utf-8")
    header = None
    footer = None
    events = []
    for line in raw.replace("\r\n", "\n").splitlines():
        if "Kernel panic" in line:
            raise ValueError("guest panicked")
        if line.startswith("TRACE_BEGIN "):
            if header is not None or footer is not None:
                raise ValueError("duplicate capture")
            header = exact(line[12:], {"version", "fixture_id", "clock_domain"})
        elif line.startswith("TRACE_EVENT "):
            if header is None or footer is not None:
                raise ValueError("event outside capture")
            events.append(
                TraceEvent(
                    **exact(line[12:], {"kind", "seq", "mono_ns", "task", "tid", "image", "values"})
                )
            )
        elif line.startswith("TRACE_END "):
            if header is None or footer is not None:
                raise ValueError("invalid capture end")
            footer = exact(line[10:], {"events", "tasks", "live", "root_status"})
        elif line.startswith("TRACE_"):
            raise ValueError("unknown capture record")
    if header is None or footer is None:
        raise ValueError("incomplete kernel capture")
    return Capture(
        events=tuple(events),
        end_values=tuple(footer[k] for k in ("events", "tasks", "live", "root_status")),
        **header,
    )


def capture_digest(capture: Capture) -> str:
    if type(capture) is not Capture:
        raise ValueError("expected capture")
    capture.__post_init__()
    raw = json.dumps(
        asdict(capture), sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False
    ).encode()
    return sha256(raw).hexdigest()
