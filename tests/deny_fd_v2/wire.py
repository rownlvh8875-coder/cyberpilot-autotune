"""Strict physical v2 framing. Header claims never prove actual acquisition."""

import json
from typing import NoReturn

from .contracts import Capture, Event, require


def _invalid_number(value: str) -> NoReturn:
    raise ValueError("float/nonfinite JSON forbidden")


def decode(raw: bytes) -> Capture:
    require(type(raw) is bytes and len(raw) <= 1024 * 1024 and raw.endswith(b"\n"))
    lines = raw.split(b"\n")[:-1]
    lines = [line[:-1] if line.endswith(b"\r") else line for line in lines]
    markers = (b"DFD2_EXEC", b"DFD2_PROBE_EXIT=0", b"DFD2_DONE")
    require(all(lines.count(marker) == 1 for marker in markers))
    a, b, c = (lines.index(marker) for marker in markers)
    require(a < b < c and c == b + 1)
    require(not any(b"DFD2" in line or b"HFD" in line for line in lines[:a] + lines[c + 1 :]))
    events = []
    for line in lines[a + 1 : b]:
        require(len(line) <= 4096 and line.startswith(b"DFD2 "))
        try:
            row = json.loads(
                line[5:].decode("ascii"),
                parse_float=_invalid_number,
                parse_constant=_invalid_number,
            )
        except (ValueError, UnicodeError) as error:
            raise ValueError("invalid physical v2 JSON") from error
        require(type(row) is list and len(row) >= 3)
        events.append(Event(row[0], row[1], row[2], tuple(row[3:])))
        require(len(events) <= 1024)
    return Capture(tuple(events))
