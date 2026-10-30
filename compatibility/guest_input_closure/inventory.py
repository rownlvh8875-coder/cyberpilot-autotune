"""Strict canonical inventories: content identity only, never trusted origin."""

import hashlib
import json
from dataclasses import asdict
from typing import Any

from .contracts import InputEntry, InputSnapshot

VERSION = "guest-input-snapshot-v1"


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def parse_snapshot(raw: str) -> InputSnapshot:
    data = json.loads(raw, object_pairs_hook=unique_object)
    if type(data) is not dict or set(data) != {"version", "entries"} or data["version"] != VERSION:
        raise ValueError("unsupported snapshot envelope")
    if type(data["entries"]) is not list or len(data["entries"]) > 50000:
        raise ValueError("invalid inventory list")
    fields = {"root", "path", "kind", "mode", "size", "sha256", "target"}
    entries = []
    for row in data["entries"]:
        if type(row) is not dict or set(row) != fields:
            raise ValueError("unsupported entry fields")
        entries.append(InputEntry(**row))
    return InputSnapshot(tuple(entries))


def snapshot_json(snapshot: InputSnapshot) -> str:
    snapshot.__post_init__()
    return json.dumps(
        {"version": VERSION, "entries": [asdict(e) for e in snapshot.entries]},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def snapshot_digest(snapshot: InputSnapshot) -> str:
    return hashlib.sha256(snapshot_json(snapshot).encode()).hexdigest()


def compare_snapshots(expected: InputSnapshot, actual: InputSnapshot) -> tuple[str, ...]:
    expected.__post_init__()
    actual.__post_init__()
    before = {(e.root, e.path): e for e in expected.entries}
    after = {(e.root, e.path): e for e in actual.entries}
    reasons = []
    for key in sorted(before.keys() | after.keys()):
        name = "/".join(key)
        if key not in after:
            reasons.append("INPUT_MISSING:" + name)
        elif key not in before:
            reasons.append("UNDECLARED_INPUT:" + name)
        else:
            for field, reason in (
                ("kind", "KIND_CHANGED"),
                ("mode", "MODE_CHANGED"),
                ("size", "SIZE_CHANGED"),
                ("sha256", "CONTENT_CHANGED"),
                ("target", "LINK_CHANGED"),
            ):
                if getattr(before[key], field) != getattr(after[key], field):
                    reasons.append(reason + ":" + name)
    return tuple(reasons)
