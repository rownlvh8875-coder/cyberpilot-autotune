"""Closed preparation schemas. R binds source bytes; Q requires canonical wire bytes."""

import json
import re
from typing import Any, cast

from .contracts import PERMISSIONS, PinnedCompatibilityManifest
from .git_objects import GitImage, oid, require


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def _forbidden(value: str) -> None:
    raise ValueError("noninteger JSON number: " + value)


def decode(raw: bytes, *, wire: bool) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_forbidden,
            parse_constant=_forbidden,
        )
        require(type(value) is dict)
        if wire:
            require(canonical(value) == raw)
        return cast(dict[str, Any], value)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid JSON encoding/depth") from error


def semantic_value(pin: PinnedCompatibilityManifest) -> dict[str, Any]:
    return {
        "schema": "history-audit-compatibility-semantics-v1",
        "profile_id": "ENTRY_COMPOSITION_V1",
        "stage": "PURE_CORE_PREPARATION_NOT_REGISTERED_INTEGRATION",
        "basis": {"M": pin.m, "D": pin.d, "O": pin.o},
        "semantic_paths": list(pin.semantic_paths),
        "active_paths": list(pin.active_paths),
        "manifest_path": pin.manifest_path,
        "inert_root": pin.inert_root,
        "permissions": dict(PERMISSIONS),
        "historical_replay_implemented": False,
        "current_capture_implemented": False,
        "Q_registered": False,
        "I_created": False,
        "old_PR_heads_must_remain_unchanged": True,
    }


def validate_semantics(raw: bytes, pin: PinnedCompatibilityManifest) -> None:
    # Human-readable R is already byte-bound by the pinned commit/tree, not a Q wire document.
    require(canonical(decode(raw, wire=False)) == canonical(semantic_value(pin)))


def descriptor(image: GitImage | None) -> dict[str, Any] | None:
    return (
        None
        if image is None
        else {
            "mode": image.mode,
            "git_blob": image.oid,
            "sha256": image.sha256,
            "bytes": len(image.data),
        }
    )


def content_rows(raw: bytes, pin: PinnedCompatibilityManifest) -> list[dict[str, Any]]:
    value = decode(raw, wire=True)
    supplied = value.get("transition_rows")
    require(type(supplied) is list and all(type(r) is dict for r in supplied))
    rows = cast(list[dict[str, Any]], supplied)
    expected = {
        "schema": "history-audit-compatibility-content-v1",
        "profile_id": "ENTRY_COMPOSITION_V1",
        "semantic_registration_R": pin.r,
        "runtime_qualified": False,
        "permissions": dict(PERMISSIONS),
        "transition_rows": rows,
    }
    require(canonical(value) == canonical(expected))
    require(
        all(
            set(r) == {"path", "operation", "source_preimages", "postimage", "inert_postimage_path"}
            for r in rows
        )
    )
    names = [r["path"] for r in rows]
    require(all(type(p) is str for p in names))
    require(len(set(names)) == len(names) and set(names) == set(pin.active_paths))
    return rows


def validate_descriptor(value: Any) -> None:
    """Validate declared facts even when the corresponding raw source is missing."""
    if value is None:
        return
    require(type(value) is dict and set(value) == {"mode", "git_blob", "sha256", "bytes"})
    require(type(value["mode"]) is str and value["mode"] in ("100644", "100755"))
    require(oid(value["git_blob"]))
    require(
        type(value["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", value["sha256"]) is not None
    )
    require(type(value["bytes"]) is int and value["bytes"] >= 0)
