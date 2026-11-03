"""Inspect supplied bytes only. Snapshot match is never H execution or authority."""

import json
from hashlib import sha256
from typing import Any, cast

from .contracts import (
    BINDING_FIELDS,
    DECLARATIONS,
    DIAGNOSTIC_RULES,
    ERROR,
    GAP_PAIRS,
    NULLABLE_CONTAINERS,
    PROFILES,
    REDACTED,
    SOURCE_ARRAY_LENGTHS,
    SOURCE_LEAF_RULES,
    SOURCE_OBJECT_KEYS,
    STRING_VALUES,
    MappingReason,
    PreflightMappingDecision,
    PreflightRunBinding,
    SourceDiagnostic,
    TargetGap,
    check_leaf,
    default_meaning,
    need,
    validate_dto,
)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    need(len({key for key, _ in pairs}) == len(pairs))
    return dict(pairs)


def _reject_number(text: str) -> Any:
    raise ValueError(ERROR)


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _source_shape(value: Any, pointer: str = "") -> None:
    if value is None and pointer in NULLABLE_CONTAINERS:
        return
    objects, arrays = dict(SOURCE_OBJECT_KEYS), dict(SOURCE_ARRAY_LENGTHS)
    if pointer in objects:
        need(type(value) is dict and set(value) == set(objects[pointer]))
        for key in objects[pointer]:
            _source_shape(value[key], pointer + "/" + _escape(key))
    elif pointer in arrays:
        need(type(value) is list and len(value) == arrays[pointer])
        for i, child in enumerate(value):
            _source_shape(child, pointer + "/" + str(i))
    else:
        check_leaf(value, dict(SOURCE_LEAF_RULES)[pointer])


def _parse(raw: bytes) -> dict[str, Any]:
    try:
        doc = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
        _source_shape(doc)
        return cast(dict[str, Any], doc)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        pass
    # Outside the exception handler: no input-bearing parser exception chain.
    raise ValueError(ERROR)


def _at(document: Any, pointer: str) -> Any:
    value = document
    for part in pointer.split("/")[1:]:
        if value is None:
            return None
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if type(value) is list else value[key]
    return value


def map_registered_preflight(
    raw: bytes,
    binding: PreflightRunBinding | None = None,
    *,
    source_profile_id: str = "REGISTERED_PREFLIGHT_R0",
) -> PreflightMappingDecision:
    need(type(raw) is bytes and 0 < len(raw) <= 32768 and not raw.startswith(b"\xef\xbb\xbf"))
    need(type(source_profile_id) is str and source_profile_id in dict(PROFILES))
    if binding is not None:
        validate_dto(binding, PreflightRunBinding)
    document = _parse(raw)
    expected = dict(dict(PROFILES)[source_profile_id])
    digest = sha256(raw).hexdigest()
    errors: list[MappingReason] = []
    missing: list[MappingReason] = []

    def error(code: str, subject: str) -> None:
        errors.append(MappingReason(code, subject))

    if digest != expected["observation_sha256"]:
        error("REGISTERED_SNAPSHOT_CONTENT_MISMATCH", "source")
    for pointer, value in DECLARATIONS:
        if _at(document, pointer) != value:
            error("SOURCE_DECLARATION_CONTRADICTION", "source:" + pointer)
    for path, tool in document["tools"].items():
        correct = None if tool["sha256"] is None else tool["sha256"] == tool["expected_sha256"]
        if tool["pin_matches"] is not correct:
            error(
                "SOURCE_TOOL_RELATION_INCONSISTENT",
                "source:/tools/" + _escape(path) + "/pin_matches",
            )
    for name in ("fcntl", "resource"):
        api = document["native_apis"][name]
        if (api["module_available"] and api["required_apis_present"] is None) or (
            not api["module_available"] and api["required_apis_present"] is not None
        ):
            error(
                "SOURCE_TOOL_RELATION_INCONSISTENT",
                "source:/native_apis/" + name + "/required_apis_present",
            )
    cgroup = document["cgroup"]
    if cgroup["status"] == "MEMBERSHIP_OBSERVED_NOT_DELEGATION":
        coherent = cgroup["membership_confirmed"] is True and cgroup["controls"] is not None
    elif cgroup["status"] == "UNAVAILABLE_MEMBERSHIP":
        coherent = (
            cgroup["membership_confirmed"] is not True
            and cgroup["directory"] is None
            and cgroup["controls"] is None
        )
    else:
        coherent = (
            cgroup["membership_confirmed"] is None
            and cgroup["directory"] is None
            and cgroup["controls"] is None
        )
    if not coherent:
        error("SOURCE_DECLARATION_CONTRADICTION", "source:/cgroup/status")
    context_expected = {
        "actions": True,
        "repository": expected["repository"],
        "run_id": str(expected["run_id"]),
        "run_attempt": str(expected["attempt"]),
        "sha": expected["source_revision"],
    }
    for name, context_value in context_expected.items():
        actual = document["execution_context"][name]
        subject = "source:/execution_context/" + name
        if actual is None:
            missing.append(MappingReason("CALLER_CONTEXT_UNAVAILABLE", subject))
        elif actual != context_value:
            error("SOURCE_CONTEXT_MISMATCH", subject)
    if binding is None:
        missing.append(MappingReason("BINDING_UNAVAILABLE", "binding"))
    else:
        for name in BINDING_FIELDS:
            actual = getattr(binding, name)
            if actual is None:
                missing.append(MappingReason("BINDING_VALUE_UNAVAILABLE", "binding." + name))
            elif actual != expected[name]:
                error("BINDING_VALUE_MISMATCH", "binding." + name)
    diagnostics = []
    for pointer, _, _ in DIAGNOSTIC_RULES:
        value = _at(document, pointer)
        meaning = default_meaning(pointer)
        if value is None:
            meaning = "SOURCE_VALUE_UNAVAILABLE"
        elif type(value) is str and value not in dict(STRING_VALUES).get(pointer, ()):
            value, meaning = REDACTED, "SOURCE_TEXT_REDACTED"
        elif pointer.startswith("/tools/") and pointer.endswith("/pin_matches") and value is False:
            tool = _at(document, pointer.rsplit("/", 1)[0])
            if tool["sha256"] is not None and tool["sha256"] != tool["expected_sha256"]:
                meaning = "LEGACY_TOOL_PIN_MISMATCH"
        diagnostics.append(SourceDiagnostic(pointer, value, meaning))
    result = PreflightMappingDecision(
        source_profile_id,
        digest,
        tuple(diagnostics),
        tuple(TargetGap(*p) for p in GAP_PAIRS),
        tuple(errors),
        tuple(missing),
    )
    validate_dto(result, PreflightMappingDecision)
    return result
