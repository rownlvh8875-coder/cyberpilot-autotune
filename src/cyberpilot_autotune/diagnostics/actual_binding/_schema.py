"""Closed shapes for six supplied documents. Never inspect the opaque raw roles."""

from typing import cast

from .constants import (
    ASSET_KEYS,
    BODY_KEYS,
    CASES,
    DOCUMENT_ROLES,
    ENV_KEYS,
    HEADER_KEYS,
    MODE,
    ORIGIN,
    PERMISSIONS,
    RAW_ROLES,
    VERSION,
)
from .values import hex_value, optional_hex, uint

type JsonValue = None | bool | int | str | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


def _obj(value: JsonValue, keys: tuple[str, ...]) -> bool:
    return type(value) is dict and set(value) == set(keys)


def _text(value: JsonValue) -> bool:
    return type(value) is str and "\0" not in value


def _path(value: JsonValue) -> bool:
    return (
        type(value) is str
        and value.startswith("/")
        and len(value.encode("utf-8")) <= 4096
        and ".." not in value.split("/")
        and not any(c in value for c in "\0\r\n")
    )


def _argv(value: JsonValue) -> bool:
    return type(value) is list and bool(value) and all(_text(x) and bool(x) for x in value)


def _map(value: JsonValue, keys: tuple[str, ...], kind: str) -> bool:
    if not _obj(value, keys):
        return False
    data = cast(JsonObject, value)
    if kind == "hash":
        return all(optional_hex(x) for x in data.values())
    if kind == "env":
        return all(x is None or _text(x) for x in data.values())
    if kind == "checks":
        return all(
            x in ("MATCHED_REPORTED", "MISMATCH_REPORTED", "UNAVAILABLE") for x in data.values()
        )
    return all(x in ("FINALIZED_REPORTED", "UNAVAILABLE") for x in data.values())


def _clock(value: JsonValue) -> bool:
    keys = ("domain", "cohort_sha256", "context_material_sha256", "generation", "context_status")
    if not _obj(value, keys):
        return False
    d = cast(JsonObject, value)
    if d["domain"] != "HOST_MONOTONIC_NS":
        return False
    parts = (d["cohort_sha256"], d["context_material_sha256"], d["generation"])
    if d["context_status"] == "UNAVAILABLE":
        return all(x is None for x in parts)
    return (
        d["context_status"] == "REPORTED"
        and hex_value(parts[0], 64)
        and hex_value(parts[1], 64)
        and uint(parts[2])
    )


def _fds(value: JsonValue) -> bool:
    if type(value) is not list or not all(uint(x, 31) for x in value):
        return False
    numbers = cast(list[int], value)
    return numbers == sorted(set(numbers))


def _profile(value: JsonValue) -> bool:
    keys = ("expected_fds", "installed_fds", "cause_fds", "decision_kind", "decision_value")
    if not _obj(value, keys):
        return False
    d = cast(JsonObject, value)
    return (
        all(_fds(d[k]) for k in keys[:3])
        and d["decision_kind"] in ("DENY", "RESULT")
        and d["decision_value"]
        in ("UNEXPECTED_FD", "NO_DENIAL", "UNSUPPORTED_MISSING", "UNSUPPORTED_MIXED")
    )


def _process(value: JsonValue) -> bool:
    keys = ("observation_kind", "process_identity_sha256", "pid", "returncode", "termination")
    if not _obj(value, keys):
        return False
    d = cast(JsonObject, value)
    code = d["returncode"]
    return (
        d["observation_kind"]
        in ("TOOL_REPORTED", "PRODUCER_RECORD_REPORTED", "DIRECT_REAP_REPORTED", "UNAVAILABLE")
        and optional_hex(d["process_identity_sha256"])
        and (d["pid"] is None or uint(d["pid"], 31))
        and (code is None or type(code) is int and -(2**31) <= code < 2**31)
        and d["termination"] in ("NOT_STARTED", "EXITED", "SIGNALLED", "UNKNOWN")
    )


def _descriptors(value: JsonValue) -> bool:
    if not _obj(value, RAW_ROLES):
        return False
    for v in cast(JsonObject, value).values():
        if not _obj(v, ("availability", "byte_length", "sha256")):
            return False
        d = cast(JsonObject, v)
        if d["availability"] == "UNAVAILABLE":
            if d["byte_length"] is not None or d["sha256"] is not None:
                return False
        elif (
            d["availability"] != "PRESENT"
            or not uint(d["byte_length"])
            or not hex_value(d["sha256"], 64)
        ):
            return False
    return True


def _field(role: str, key: str, value: JsonValue) -> bool:
    if key.endswith("_sha256") or key == "host_interpreter_sha256_observed":
        return optional_hex(value)
    if key in ("expected_assets", "observed_assets"):
        return _map(value, ASSET_KEYS, "hash")
    if key in ("environment", "host_environment_observed"):
        return _map(value, ENV_KEYS, "env")
    if key == "asset_checks":
        return _map(value, ASSET_KEYS, "checks")
    if key == "raw_close_states":
        return _map(value, RAW_ROLES, "close")
    if key == "declared_case_profile":
        return _profile(value)
    if key == "producer_record_schema":
        return type(value) is str
    if key in ("host_cli_argv", "host_cli_argv_observed", "expected_qemu_argv"):
        return value is None and key != "host_cli_argv" or _argv(value)
    if key in ("host_cli_cwd", "planned_destination", "original_case_directory"):
        return _path(value)
    if key == "environment_scope":
        return value == "DECLARED_NONSECRET_ALLOWLIST_NOT_FULL_ENV"
    if key == "observation_kind":
        return value == "REPORTED_NOT_ATTESTED"
    if key.endswith("_ns"):
        return value is None or uint(value)
    if key == "event_ordinal":
        return type(value) is int and value == ("preflight", "intent", "exit", "snapshot").index(
            role
        )
    if key == "reported_source_ids":
        return _obj(value, ("producer_attempt_id", "guest_capture_id")) and all(
            x is None or hex_value(x, 32) for x in cast(JsonObject, value).values()
        )
    if key in ("cli_observation", "qemu_observation"):
        return _process(value)
    if key == "capture_outcome":
        return value in ("COMPLETE_REPORTED", "PARTIAL_REPORTED", "FAILED_REPORTED")
    if key == "failure_stage":
        return value in (
            "NONE",
            "PREFLIGHT",
            "INTENT",
            "LAUNCH",
            "COLLECT",
            "CLOSE",
            "PERSIST",
            "EXIT_OBSERVATION",
            "UNKNOWN",
        )
    if key == "host_context_observation_kind":
        return value in ("LAUNCH_BOUNDARY_REPORTED", "UNAVAILABLE")
    return _descriptors(value)


def _header_issues(role: str, value: JsonValue) -> tuple[str, ...]:
    if not _obj(value, HEADER_KEYS):
        return ("DOCUMENT_SHAPE_INVALID",)
    h = cast(JsonObject, value)
    issues = []
    text_fields = ("contract_version", "role", "mode", "origin", "status")
    valid = (
        all(type(h[k]) is str for k in text_fields)
        and type(h["synthetic"]) is bool
        and h["role"] in DOCUMENT_ROLES
        and h["case"] in CASES
        and hex_value(h["workflow_run_id"], 32)
        and hex_value(h["workflow_attempt_id"], 32)
        and hex_value(h["producer_implementation_revision"], 40)
        and hex_value(h["producer_source_revision"], 40)
        and hex_value(h["capture_implementation_sha256"], 64)
        and _clock(h["host_clock_context"])
    )
    if not valid:
        issues.append("DOCUMENT_SHAPE_INVALID")
    if type(h["contract_version"]) is str and h["contract_version"] != VERSION:
        issues.append("UNSUPPORTED_VERSION")
    if h["mode"] != MODE or h["origin"] != ORIGIN or h["synthetic"] is not False:
        issues.append("WRONG_ORIGIN")
    if type(h["role"]) is str and h["role"] != role:
        issues.append("CONTEXT_MISMATCH")
    pkeys = tuple(k for k, _ in PERMISSIONS)
    if not _obj(h["permissions"], pkeys) or not all(
        type(v) is bool for v in cast(JsonObject, h["permissions"]).values()
    ):
        issues.append("DOCUMENT_SHAPE_INVALID")
    elif any(cast(JsonObject, h["permissions"]).values()):
        issues.append("PERMISSION_ESCALATION")
    if h["status"] != "BLOCKED":
        issues.append("PERMISSION_ESCALATION")
    return tuple(issues)


def document_issues(role: str, value: JsonValue) -> tuple[str, ...]:
    if not _obj(value, ("header", "body")):
        return ("DOCUMENT_SHAPE_INVALID",)
    d = cast(JsonObject, value)
    issues = list(_header_issues(role, d["header"]))
    body = d["body"]
    if not _obj(body, dict(BODY_KEYS)[role]):
        return (*issues, "DOCUMENT_SHAPE_INVALID")
    b = cast(JsonObject, body)
    for key, v in b.items():
        if key == "raw_descriptors" and type(v) is dict and set(v) != set(RAW_ROLES):
            issues.append("ROLE_SET_INVALID")
        elif not _field(role, key, v):
            issues.append("DOCUMENT_SHAPE_INVALID")
    if (
        role == "baseline"
        and type(b["producer_record_schema"]) is str
        and b["producer_record_schema"] != "deny-fd-v2-dual-acquisition-v1"
    ):
        issues.append("UNSUPPORTED_VERSION")
    return tuple(issues)
