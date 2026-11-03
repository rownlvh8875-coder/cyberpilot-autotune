"""Canonical closed wire values with no reader, persistence or producer."""

import json
from typing import Any

from .contracts import (
    SPECS,
    WIRE_SCHEMA,
    PreparationProfilePolicy,
    PreparationProfileRecord,
    need,
    normalized_fields,
)


def _body(value: Any) -> Any:
    if type(value) in SPECS:
        return {name: _body(item) for name, item in normalized_fields(value, type(value)).items()}
    if type(value) is tuple:
        return [_body(item) for item in value]
    return value


def _canonical(value: Any, expected: type, kind: str) -> bytes:
    normalized_fields(value, expected)
    return json.dumps(
        {"schema": WIRE_SCHEMA, "kind": kind, "body": _body(value)},
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_policy(policy: PreparationProfilePolicy) -> bytes:
    return _canonical(policy, PreparationProfilePolicy, "POLICY")


def canonical_profile(record: PreparationProfileRecord) -> bytes:
    return _canonical(record, PreparationProfileRecord, "RECORD")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    need(len({key for key, _ in pairs}) == len(pairs))
    return dict(pairs)


def _not_numeric(text: str) -> Any:
    raise ValueError("float/nonfinite wire value is forbidden")


def _decode_dto(raw: Any, cls: type) -> Any:
    need(type(raw) is dict and set(raw) == {name for name, _ in SPECS[cls]})
    return cls(**{name: _decode_value(raw[name], spec) for name, spec in SPECS[cls]})


def _decode_value(raw: Any, spec: tuple[Any, ...]) -> Any:
    if spec[0] == "nullable":
        return None if raw is None else _decode_value(raw, spec[1])
    if spec[0] == "dto":
        return _decode_dto(raw, spec[1])
    if spec[0] == "table":
        if raw is None:
            return None
        need(type(raw) is list)
        return tuple(_decode_dto(item, spec[1]) for item in raw)
    if spec[0] == "codes":
        need(type(raw) is list)
        return tuple(raw)
    return raw


def _decode(raw: bytes, cls: type, kind: str) -> Any:
    need(type(raw) is bytes and 0 < len(raw) <= 1048576 and not raw.startswith(b"\xef\xbb\xbf"))
    try:
        doc = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_not_numeric,
            parse_constant=_not_numeric,
        )
        need(type(doc) is dict and set(doc) == {"schema", "kind", "body"})
        need(doc["schema"] == WIRE_SCHEMA and doc["kind"] == kind)
        return _decode_dto(doc["body"], cls)
    except (UnicodeError, RecursionError, OverflowError) as exc:
        raise ValueError("invalid preparation-profile wire encoding") from exc


def decode_policy(raw: bytes) -> PreparationProfilePolicy:
    return _decode(raw, PreparationProfilePolicy, "POLICY")


def decode_profile(raw: bytes) -> PreparationProfileRecord:
    return _decode(raw, PreparationProfileRecord, "RECORD")
