"""Bounded canonical provided-document decode, never a loader or raw-content parser."""

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import NoReturn, cast

from ._schema import JsonObject, JsonValue, document_issues
from .constants import (
    DOCUMENT_CAP,
    DOCUMENT_ROLES,
    IMAGE_CAP,
    JSON_RAW_CAP,
    RAW_ROLES,
    REASON_ORDER,
    STREAM_CAP,
    TOTAL_CAP,
)
from .values import ActualDiagnosticBundle, require


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _invalid(value: str) -> NoReturn:
    raise ValueError("non-integer JSON")


def _unique(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    out: JsonObject = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def _unicode(value: JsonValue) -> None:
    if type(value) is str:
        value.encode("utf-8", "strict")
    elif type(value) is list:
        for item in value:
            _unicode(item)
    elif type(value) is dict:
        for k, v in value.items():
            k.encode("utf-8", "strict")
            _unicode(v)


def _parse(raw: bytes) -> JsonValue:
    if raw.startswith(b"\xef\xbb\xbf") or b"\0" in raw:
        raise ValueError("metadata encoding")
    value = cast(
        JsonValue,
        json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=_unique,
            parse_float=_invalid,
            parse_constant=_invalid,
        ),
    )
    _unicode(value)
    if canonical(value) != raw:
        raise ValueError("noncanonical document bytes")
    return value


@dataclass(frozen=True, slots=True)
class _DecodedDocuments:
    documents: dict[str, JsonObject]
    document_sha256: dict[str, str]
    unavailable: tuple[str, ...]
    invalid: tuple[str, ...]
    reasons: tuple[str, ...]
    limited: tuple[str, ...]
    container_valid: bool


def decode_documents(bundle: ActualDiagnosticBundle) -> _DecodedDocuments:
    require(type(bundle) is ActualDiagnosticBundle)
    ActualDiagnosticBundle.__post_init__(bundle)
    docs: dict[str, JsonObject] = {}
    hashes: dict[str, str] = {}
    unavailable: list[str] = []
    invalid: list[str] = []
    issues: list[str] = []
    limited: list[str] = []
    for pairs, roles in ((bundle.documents, DOCUMENT_ROLES), (bundle.raw, RAW_ROLES)):
        if len(pairs) != len(roles) or {k for k, _ in pairs} != set(roles):
            return _DecodedDocuments({}, {}, (), (), ("ROLE_SET_INVALID",), (), False)
    supplied, raw = dict(bundle.documents), dict(bundle.raw)
    for role in DOCUMENT_ROLES:
        value = supplied[role]
        if value is not None and len(value) > DOCUMENT_CAP:
            limited.append("document:" + role)
    for role in ("cli_stdout", "cli_stderr", "record_json", "exit_receipt"):
        value = raw[role]
        if value is not None and len(value) > JSON_RAW_CAP:
            limited.append("raw:" + role)
    image = raw["initrd"]
    if image is not None and len(image) > IMAGE_CAP:
        limited.append("raw:initrd")
    streams = (raw["telemetry"], raw["console"])
    if sum(len(v) for v in streams if v is not None) > STREAM_CAP:
        limited.extend(("raw:telemetry", "raw:console"))
    if (
        limited
        or sum(len(v) for _, v in (*bundle.documents, *bundle.raw) if v is not None) > TOTAL_CAP
    ):
        issues.append("INPUT_LIMIT")
    for role in DOCUMENT_ROLES:
        value = supplied[role]
        if value is None:
            unavailable.append(role)
            issues.append("MISSING_DOCUMENT")
            continue
        if "document:" + role in limited:
            invalid.append(role)
            continue
        hashes[role] = sha256(value).hexdigest()
        try:
            document = _parse(value)
        except (ValueError, UnicodeError, RecursionError):
            invalid.append(role)
            issues.append("PARSE_INVALID")
            continue
        found = document_issues(role, document)
        issues.extend(found)
        if any(r in ("DOCUMENT_SHAPE_INVALID", "ROLE_SET_INVALID") for r in found):
            invalid.append(role)
        else:
            docs[role] = cast(JsonObject, document)
    return _DecodedDocuments(
        docs,
        hashes,
        tuple(unavailable),
        tuple(invalid),
        tuple(r for r in REASON_ORDER if r in issues),
        tuple(limited),
        True,
    )
