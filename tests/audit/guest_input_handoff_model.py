"""SYNTHETIC-only design oracle, not a receipt producer, backend or authority."""

import hashlib
import json
import re
from typing import Any

VERSION = "guest-input-handoff-design-v1"
CLOCK = "GUEST_HANDOFF_OBSERVATION_MONOTONIC_NS"
PERMISSIONS = (
    "build_execution_allowed",
    "promotion_authorized",
    "runtime_qualified",
    "device_class_qualified",
    "policy_adopted",
    "candidate_generation_allowed",
    "application_authorized",
    "runtime_accepted",
    "owner_proposal_allowed",
)
MEMBER_FIELDS = frozenset(
    ("name", "object_id", "object_generation", "pin_generation", "dev", "ino", "bytes", "sha256")
)
PIN_FIELDS = frozenset(("object_id", "object_generation", "pin_generation", "dev", "ino"))
FD_FIELDS = frozenset(("fd", "binding_generation", "ofd_id", "ofd_generation"))
EVENT_FIELDS = {
    "PIN": PIN_FIELDS,
    "SEAL": PIN_FIELDS | {"seal_mask", "bytes", "sha256"},
    "STOPPED": frozenset(("inventory_digest", "complete", "extra_fd_count")),
    "TRANSFER": frozenset(("transfer_generation", "bundle_digest", "members")),
    "BIND": PIN_FIELDS
    | FD_FIELDS
    | {"transfer_generation", "access_mode", "cloexec", "seal_mask", "bytes", "sha256"},
    "READY": frozenset(
        ("transfer_generation", "bundle_digest", "inventory_digest", "complete", "extra_fd_count")
    ),
    "PREAD_FULL": FD_FIELDS
    | {"transfer_generation", "offset", "returned_len", "returned_bytes_hex"},
    "CLOSE": FD_FIELDS,
    "FINISH": frozenset(("exit_kind", "exit_code", "complete", "drop_count")),
    "RELEASE": frozenset(("object_id", "object_generation", "pin_generation")),
    "END": frozenset(),
}
CONTEXT_FIELDS = frozenset(
    (
        "session_id",
        "attempt_id",
        "namespace_generation",
        "source_revision",
        "vm_profile_digest",
        "observer_profile_digest",
        "consumer_image_digest",
        "consumer_task_generation",
        "consumer_exec_generation",
        "consumer_fd_table_generation",
        "clock_domain",
        "manifest_digest",
    )
)


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _record(value: Any, fields: frozenset[str], reason: str = "SCHEMA_INVALID") -> None:
    _require(type(value) is dict and set(value) == fields, reason)


def _uint(value: Any) -> bool:
    return type(value) is int and 0 <= value < 2**64


def _sha(value: Any, length: int = 64) -> bool:
    return type(value) is str and re.fullmatch(r"[a-f0-9]{" + str(length) + "}", value) is not None


def _opaque(value: Any) -> bool:
    return (
        type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}", value) is not None
    )


def _key(row: dict[str, Any]) -> tuple[str, int]:
    return row["object_id"], row["object_generation"]


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def graph_digest(graph: dict[str, Any]) -> str:
    """Content only; callers still need evaluate, and neither establishes truth."""
    return _digest({**graph, "manifest": sorted(graph["manifest"], key=lambda m: m["name"])})


def _inventory(context: str, bindings: list[dict[str, Any]]) -> str:
    return _digest(
        {
            "schema": "guest-data-fd-inventory-v1",
            "context_digest": context,
            "bindings": sorted(bindings, key=lambda b: b["fd"]),
        }
    )


def _references(value: Any) -> list[dict[str, Any]]:
    _require(type(value) is list and len(value) <= 16, "MANIFEST_SET_MISMATCH")
    for row in value:
        _record(row, frozenset(("object_id", "object_generation")), "MANIFEST_SET_MISMATCH")
        _require(
            _opaque(row["object_id"]) and _uint(row["object_generation"]), "MANIFEST_SET_MISMATCH"
        )
    return sorted(value, key=_key)


def _validate(graph: Any) -> None:
    _record(graph, frozenset(("schema", "evidence_kind", "context", "manifest", "events")))
    _require(graph["schema"] == VERSION, "SCHEMA_INVALID")
    _require(graph["evidence_kind"] == "SYNTHETIC", "EVIDENCE_KIND_UNSUPPORTED")
    ctx = graph["context"]
    _record(ctx, CONTEXT_FIELDS)
    _require(ctx["clock_domain"] == CLOCK, "CLOCK_DOMAIN_INVALID")
    for field in ("session_id", "attempt_id"):
        _require(_opaque(ctx[field]), "SCHEMA_INVALID")
    for field in (
        "namespace_generation",
        "consumer_task_generation",
        "consumer_exec_generation",
        "consumer_fd_table_generation",
    ):
        _require(_uint(ctx[field]), "SCHEMA_INVALID")
    _require(
        ctx["consumer_task_generation"] > 0 and ctx["consumer_fd_table_generation"] > 0,
        "SCHEMA_INVALID",
    )
    _require(_sha(ctx["source_revision"], 40), "SCHEMA_INVALID")
    for field in (
        "vm_profile_digest",
        "observer_profile_digest",
        "consumer_image_digest",
        "manifest_digest",
    ):
        _require(_sha(ctx[field]), "SCHEMA_INVALID")
    members = graph["manifest"]
    _require(type(members) is list and 1 <= len(members) <= 16, "MANIFEST_INVALID")
    names: set[str] = set()
    objects: dict[tuple[str, int], dict[str, Any]] = {}
    identities: set[tuple[int, int]] = set()
    for member in members:
        _record(member, MEMBER_FIELDS, "MANIFEST_INVALID")
        name = member["name"]
        _require(
            type(name) is str
            and 1 <= len(name) <= 255
            and all(re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", segment) for segment in name.split("/")),
            "MANIFEST_INVALID",
        )
        _require(_opaque(member["object_id"]) and _sha(member["sha256"]), "MANIFEST_INVALID")
        for field in ("object_generation", "pin_generation", "dev", "ino", "bytes"):
            _require(_uint(member[field]), "MANIFEST_INVALID")
        _require(member["ino"] > 0 and member["bytes"] <= 4096, "MANIFEST_INVALID")
        key = _key(member)
        identity = (member["dev"], member["ino"])
        _require(
            name not in names and key not in objects and identity not in identities,
            "MANIFEST_INVALID",
        )
        names.add(name)
        objects[key] = member
        identities.add(identity)
    normalized = sorted(members, key=lambda m: m["name"])
    _require(
        ctx["manifest_digest"]
        == _digest({"schema": "guest-data-input-set-v1", "members": normalized}),
        "MANIFEST_DIGEST_MISMATCH",
    )
    context = _digest(ctx)
    events = graph["events"]
    _require(type(events) is list and 1 <= len(events) <= 1024, "SCHEMA_INVALID")
    pins: set[tuple[str, int]] = set()
    sealed: set[tuple[str, int]] = set()
    released: set[tuple[str, int]] = set()
    bound: dict[int, dict[str, Any]] = {}
    active: dict[int, dict[str, Any]] = {}
    bound_objects: set[tuple[str, int]] = set()
    ofds: set[tuple[str, int]] = set()
    phase = "SETUP"
    transfer: dict[str, Any] | None = None
    previous = 0
    refs = sorted(
        (
            {"object_id": m["object_id"], "object_generation": m["object_generation"]}
            for m in members
        ),
        key=_key,
    )
    for index, event in enumerate(events):
        _record(event, frozenset(("seq", "time_ns", "context_digest", "kind", "data")))
        _require(_uint(event["seq"]) and _uint(event["time_ns"]), "SCHEMA_INVALID")
        _require(event["seq"] == index and event["time_ns"] >= previous, "TIME_ORDER_INVALID")
        previous = event["time_ns"]
        _require(event["context_digest"] == context, "CONTEXT_MISMATCH")
        kind = event["kind"]
        _require(type(kind) is str and kind in EVENT_FIELDS, "UNSUPPORTED_OPERATION")
        data = event["data"]
        _record(data, EVENT_FIELDS[kind])
        if kind in ("PIN", "SEAL", "BIND", "RELEASE"):
            _require(
                _opaque(data["object_id"])
                and _uint(data["object_generation"])
                and _uint(data["pin_generation"]),
                "SCHEMA_INVALID",
            )
        if kind in ("BIND", "PREAD_FULL", "CLOSE"):
            _require(
                all(_uint(data[f]) for f in ("fd", "binding_generation", "ofd_generation"))
                and _opaque(data["ofd_id"]),
                "SCHEMA_INVALID",
            )
        if kind in ("TRANSFER", "BIND", "READY", "PREAD_FULL"):
            _require(_uint(data["transfer_generation"]), "SCHEMA_INVALID")
        if kind in ("PIN", "SEAL", "BIND"):
            _require(_uint(data["dev"]) and _uint(data["ino"]), "SCHEMA_INVALID")
            key = _key(data)
            _require(
                key in objects and all(data[f] == objects[key][f] for f in PIN_FIELDS),
                "OBJECT_BINDING_MISMATCH",
            )
            if kind != "PIN":
                _require(key in pins and key not in released, "PIN_LIFETIME_INVALID")
        if kind == "PIN":
            _require(phase == "SETUP" and key not in pins, "PIN_LIFETIME_INVALID")
            pins.add(key)
        elif kind == "SEAL":
            _require(
                phase == "SETUP"
                and key not in sealed
                and type(data["seal_mask"]) is int
                and data["seal_mask"] == 47
                and _uint(data["bytes"])
                and data["bytes"] == objects[key]["bytes"]
                and data["sha256"] == objects[key]["sha256"],
                "SEAL_INVALID",
            )
            sealed.add(key)
        elif kind in ("STOPPED", "READY"):
            _require(phase == ("SETUP" if kind == "STOPPED" else "BINDING"), "PHASE_ORDER")
            _require(pins == sealed == set(objects), "MANIFEST_SET_MISMATCH")
            _require(
                data["complete"] is True
                and type(data["extra_fd_count"]) is int
                and data["extra_fd_count"] == 0,
                "INVENTORY_INCOMPLETE",
            )
            if kind == "READY":
                _require(bound_objects == set(objects), "MANIFEST_SET_MISMATCH")
                _require(
                    transfer is not None
                    and data["transfer_generation"] == transfer["transfer_generation"]
                    and data["bundle_digest"] == transfer["bundle_digest"],
                    "TRANSFER_COHORT_MISMATCH",
                )
            _require(
                data["inventory_digest"]
                == _inventory(context, [] if kind == "STOPPED" else list(bound.values())),
                "INVENTORY_DIGEST_MISMATCH",
            )
            phase = "STOPPED" if kind == "STOPPED" else "ACTIVE"
        elif kind == "TRANSFER":
            _require(phase == "STOPPED", "PHASE_ORDER")
            transferred = _references(data["members"])
            _require(transferred == refs, "MANIFEST_SET_MISMATCH")
            expected = _digest(
                {
                    "schema": "guest-data-fd-bundle-v1",
                    "context_digest": context,
                    "transfer_generation": data["transfer_generation"],
                    "members": refs,
                }
            )
            _require(data["bundle_digest"] == expected, "TRANSFER_COHORT_MISMATCH")
            transfer = data
            phase = "BINDING"
        elif kind == "BIND":
            _require(phase == "BINDING", "PHASE_ORDER")
            _require(
                transfer is not None
                and data["transfer_generation"] == transfer["transfer_generation"],
                "TRANSFER_COHORT_MISMATCH",
            )
            _require(
                data["access_mode"] == "RDONLY" and data["cloexec"] is True, "FD_ACCESS_INVALID"
            )
            _require(
                type(data["seal_mask"]) is int
                and data["seal_mask"] == 47
                and _uint(data["bytes"])
                and data["bytes"] == objects[key]["bytes"]
                and data["sha256"] == objects[key]["sha256"],
                "OBJECT_BINDING_MISMATCH",
            )
            ofd = (data["ofd_id"], data["ofd_generation"])
            _require(
                data["fd"] not in bound and key not in bound_objects and ofd not in ofds,
                "FD_ALIAS_UNSUPPORTED",
            )
            bound[data["fd"]] = data
            active[data["fd"]] = data
            bound_objects.add(key)
            ofds.add(ofd)
        elif kind in ("PREAD_FULL", "CLOSE"):
            _require(phase == "ACTIVE", "PHASE_ORDER")
            fd = data["fd"]
            _require(
                fd in active and all(data[f] == active[fd][f] for f in FD_FIELDS),
                "FD_LIFETIME_INVALID",
            )
            if kind == "CLOSE":
                del active[fd]
            else:
                _require(
                    transfer is not None
                    and data["transfer_generation"] == transfer["transfer_generation"],
                    "TRANSFER_COHORT_MISMATCH",
                )
                _require(
                    _uint(data["offset"])
                    and _uint(data["returned_len"])
                    and type(data["returned_bytes_hex"]) is str
                    and len(data["returned_bytes_hex"]) <= 8192
                    and re.fullmatch(r"(?:[a-f0-9]{2})*", data["returned_bytes_hex"]) is not None,
                    "SCHEMA_INVALID",
                )
                _require(
                    data["offset"] == 0 and data["returned_len"] == active[fd]["bytes"],
                    "FULL_FILE_STAGE_REQUIRED",
                )
                raw = bytes.fromhex(data["returned_bytes_hex"])
                _require(
                    len(raw) == data["returned_len"]
                    and hashlib.sha256(raw).hexdigest() == active[fd]["sha256"],
                    "READ_CONTENT_MISMATCH",
                )
        elif kind == "FINISH":
            _require(phase == "ACTIVE", "PHASE_ORDER")
            _require(
                not active
                and data["exit_kind"] == "EXITED"
                and type(data["exit_code"]) is int
                and data["exit_code"] == 0
                and data["complete"] is True
                and type(data["drop_count"]) is int
                and data["drop_count"] == 0,
                "COMPLETION_INVALID",
            )
            phase = "FINISHED"
        elif kind == "RELEASE":
            key = _key(data)
            _require(
                phase == "FINISHED"
                and key in pins
                and key not in released
                and data["pin_generation"] == objects[key]["pin_generation"],
                "PIN_LIFETIME_INVALID",
            )
            released.add(key)
        elif kind == "END":
            _require(
                phase == "FINISHED" and released == pins == set(objects), "PIN_LIFETIME_INVALID"
            )
            _require(index == len(events) - 1, "INCOMPLETE_GRAPH")
            phase = "ENDED"
    _require(phase == "ENDED", "INCOMPLETE_GRAPH")
    _require(len(json.dumps(graph, allow_nan=False).encode()) <= 2 * 1024 * 1024, "SCHEMA_INVALID")


def evaluate(graph: Any) -> dict[str, Any]:
    """Only check proposed synthetic relations; consistent never means qualified."""
    try:
        _validate(graph)
        reasons = []
    except ValueError as error:
        reasons = [str(error)]
    return {
        "status": "REJECTED" if reasons else "SYNTHETIC_GRAPH_CONSISTENT",
        "reasons": reasons,
        "overall": "BLOCKED",
        "permissions": dict.fromkeys(PERMISSIONS, False),
        "successful_prohibited_handles": None,
        "successful_prohibited_effects": None,
    }
