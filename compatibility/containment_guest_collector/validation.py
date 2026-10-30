"""Strict wire parsing/canonical identity, never a factual trust verifier."""

import json
import re
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


def exact(raw: str, keys: set[str]) -> tuple[dict[str, Any], int]:
    raw = raw.lstrip()
    data, end = json.JSONDecoder(object_pairs_hook=unique).raw_decode(raw)
    suffix = raw[end:].strip()
    if suffix and re.fullmatch(r"\[\s*\d+\.\d+\] [^\r\n]*", suffix) is None:
        raise ValueError("unknown trailing bytes outside JSON frame")
    if type(data) is not dict or set(data) != keys:
        raise ValueError("unknown/missing wire keys")
    return data, int(bool(suffix))


def parse_capture(raw: str) -> Capture:
    if type(raw) is not str:
        raise ValueError("expected text capture")
    raw.encode("utf-8")
    header = None
    footer = None
    events = []
    interleavings = 0
    for line in raw.replace("\r\n", "\n").splitlines():
        if "Kernel panic" in line:
            raise ValueError("guest panicked")
        if line.startswith("TRACE_BEGIN "):
            if header is not None or footer is not None:
                raise ValueError("duplicate capture")
            header, adjacent = exact(line[12:], {"version", "fixture_id", "clock_domain"})
            interleavings += adjacent
        elif line.startswith("TRACE_EVENT "):
            if header is None or footer is not None:
                raise ValueError("event outside capture")
            data, adjacent = exact(
                line[12:], {"kind", "seq", "mono_ns", "task", "tid", "image", "values"}
            )
            interleavings += adjacent
            events.append(TraceEvent(**data))
        elif line.startswith("TRACE_END "):
            if header is None or footer is not None:
                raise ValueError("invalid capture end")
            footer, adjacent = exact(line[10:], {"events", "tasks", "live", "root_status"})
            interleavings += adjacent
        elif line.startswith("TRACE_"):
            raise ValueError("unknown capture record")
    if header is None or footer is None:
        raise ValueError("incomplete kernel capture")
    return Capture(
        events=tuple(events),
        end_values=tuple(footer[k] for k in ("events", "tasks", "live", "root_status")),
        console_interleavings=interleavings,
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
