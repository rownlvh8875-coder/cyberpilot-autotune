"""Versioned strict JSON and content-only digests; never trust or authorization."""

import hashlib
import json
from dataclasses import asdict, fields
from enum import StrEnum
from typing import Any

from .models import (
    BuildCompletion,
    BuildIdentity,
    BuildMaterial,
    BuildOutput,
    BuildReceipt,
    EvidenceKind,
    ExitKind,
    InputUse,
    MaterialRole,
    PromotionReceipt,
    TaskImage,
    UseKind,
)

MAX_JSON_BYTES = 64 * 1024 * 1024
Root = BuildIdentity | BuildReceipt | PromotionReceipt
SCHEMAS = {
    BuildIdentity: "guest-build-identity-v1",
    BuildReceipt: "guest-build-consumption-v1",
    PromotionReceipt: "guest-output-promotion-v1",
}


def encode_receipt(value: Root) -> str:
    if type(value) not in SCHEMAS:
        raise ValueError("unsupported receipt root")
    value.__post_init__()
    raw = json.dumps(
        {"schema": SCHEMAS[type(value)], "payload": asdict(value)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    if len(raw.encode()) > MAX_JSON_BYTES:
        raise ValueError("encoded receipt exceeds resource bound")
    return raw


def receipt_digest(value: Root) -> str:
    return hashlib.sha256(encode_receipt(value).encode()).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate receipt field")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("nonfinite receipt number: " + value)


def _payload(raw: str, schema: str) -> dict[str, Any]:
    if type(raw) is not str or len(raw.encode()) > MAX_JSON_BYTES:
        raise ValueError("invalid receipt text/resource bound")
    try:
        value = json.loads(raw, object_pairs_hook=_unique, parse_constant=_constant)
    except (RecursionError, UnicodeError) as error:
        raise ValueError("receipt nesting or encoding invalid") from error
    if (
        type(value) is not dict
        or set(value) != {"schema", "payload"}
        or value["schema"] != schema
        or type(value["payload"]) is not dict
    ):
        raise ValueError("unsupported receipt envelope or stage")
    return value["payload"]


def _fields(cls: type[Any], data: Any) -> dict[str, Any]:
    if type(data) is not dict or set(data) != {field.name for field in fields(cls)}:
        raise ValueError("unknown or missing receipt fields")
    return dict(data)


def _enum[E: StrEnum](cls: type[E], value: Any) -> E:
    if type(value) is not str:
        raise ValueError("invalid receipt enum")
    return cls(value)


def _rows[T](
    data: Any, cls: type[T], enum_field: tuple[str, type[StrEnum]] | None = None
) -> tuple[T, ...]:
    if type(data) is not list or len(data) > 50000:
        raise ValueError("invalid receipt array")
    result = []
    for row in data:
        values = _fields(cls, row)
        if enum_field is not None:
            name, kind = enum_field
            values[name] = _enum(kind, values[name])
        result.append(cls(**values))
    return tuple(result)


def parse_build(raw: str) -> BuildReceipt:
    data = _fields(BuildReceipt, _payload(raw, SCHEMAS[BuildReceipt]))
    data["identity"] = BuildIdentity(**_fields(BuildIdentity, data["identity"]))
    completion = _fields(BuildCompletion, data["completion"])
    if completion["exit_kind"] is not None:
        completion["exit_kind"] = _enum(ExitKind, completion["exit_kind"])
    data["completion"] = BuildCompletion(**completion)
    data["materials"] = _rows(data["materials"], BuildMaterial, ("role", MaterialRole))
    data["images"] = _rows(data["images"], TaskImage)
    data["uses"] = _rows(data["uses"], InputUse, ("kind", UseKind))
    data["outputs"] = _rows(data["outputs"], BuildOutput)
    data["evidence_kind"] = _enum(EvidenceKind, data["evidence_kind"])
    return BuildReceipt(**data)


def parse_promotion(raw: str) -> PromotionReceipt:
    return PromotionReceipt(**_fields(PromotionReceipt, _payload(raw, SCHEMAS[PromotionReceipt])))
