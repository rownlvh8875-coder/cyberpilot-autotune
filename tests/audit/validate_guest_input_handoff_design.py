"""Offline synthetic design audit, never a guest/FD/backend/execution qualification."""

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from tests.audit.guest_input_handoff_examples import CASES, example
from tests.audit.guest_input_handoff_model import (
    CLOCK,
    COHORT_FIELDS,
    CONTEXT_FIELDS,
    EVENT_FIELDS,
    MEMBER_FIELDS,
    PERMISSIONS,
    VERSION,
    evaluate,
)

ROOT = Path(__file__).resolve().parents[2]
BASE = "0652c87c5e1da83d2cf4a3336713b9839e929ae3"
PINNED_PATHS = (
    "compatibility/guest_build_receipt/models.py",
    "compatibility/guest_build_receipt/evaluation.py",
    "compatibility/guest_consumption/producer.py",
    "compatibility/guest_consumption/guest/probe.c",
    "compatibility/guest_input_seal/guest/probe.c",
    "compatibility/guest_input_seal/wire.py",
    "docs/evidence/guest_input_seal_sources.json",
)
WIRE_TYPES = {
    "UInt64": frozenset(
        (
            "seq",
            "time_ns",
            "namespace_generation",
            "consumer_task_generation",
            "consumer_exec_generation",
            "consumer_fd_table_generation",
            "object_generation",
            "pin_generation",
            "dev",
            "ino",
            "bytes",
            "transfer_generation",
            "fd",
            "binding_generation",
            "ofd_generation",
            "seal_mask",
            "extra_fd_count",
            "offset",
            "returned_len",
            "exit_code",
            "drop_count",
            "task_generation",
            "exec_generation",
            "fd_table_generation",
        )
    ),
    "SHA256": frozenset(
        (
            "vm_profile_digest",
            "observer_profile_digest",
            "consumer_image_digest",
            "manifest_digest",
            "context_digest",
            "bundle_digest",
            "inventory_digest",
            "sha256",
            "image_digest",
        )
    ),
    "OpaqueId": frozenset(("session_id", "attempt_id", "object_id", "ofd_id")),
    "Bool": frozenset(("complete", "cloexec")),
    "GitCommitSha1": frozenset(("source_revision",)),
    "LogicalName": frozenset(("name",)),
    "ObjectRefSet": frozenset(("members",)),
    "HexBytes": frozenset(("returned_bytes_hex",)),
    "Enum": frozenset(("clock_domain", "access_mode", "exit_kind")),
    "ConsumerCohort": frozenset(("bootstrap_cohort", "cohort", "predecessor", "successor")),
}


def _check(condition: bool) -> None:
    if not condition:
        raise ValueError("handoff design content/scope mismatch")


def _keys(value: Any, names: set[str]) -> None:
    _check(type(value) is dict and set(value) == names)


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _check(key not in result)
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("nonfinite design value: " + value)


def load(kind: str) -> Any:
    _check(kind in ("schema", "cases", "sources"))
    raw = (ROOT / f"docs/evidence/guest_input_handoff_design_{kind}.json").read_bytes()
    _check(len(raw) <= 2 * 1024 * 1024)
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite)


def _fields(rows: Any, expected: frozenset[str], stage: str) -> None:
    _check(type(rows) is list and len(rows) == len(expected))
    names = []
    for row in rows:
        _keys(row, {"field", "type", "unit", "stage", "required", "availability"})
        _check(type(row["field"]) is str and row["field"] in expected)
        field = row["field"]
        wire_type = next(kind for kind, names in WIRE_TYPES.items() if field in names)
        unit = (
            "ns"
            if field == "time_ns"
            else "bytes"
            if field in {"bytes", "offset", "returned_len"}
            else "none"
        )
        _check(
            type(row["field"]) is str
            and row["stage"] == stage
            and row["required"] is True
            and row["availability"] == "EXPLICIT_UNKNOWN_REJECTED_FOR_CONSISTENCY"
            and row["type"] == wire_type
            and row["unit"] == unit
        )
        names.append(row["field"])
    _check(len(set(names)) == len(names) and set(names) == expected)


def validate_schema(data: Any) -> None:
    _keys(
        data,
        {
            "schema",
            "graph_version",
            "scope",
            "evidence_kind",
            "encoding",
            "clock_domain",
            "preferred_transport",
            "runtime_producer_implemented",
            "runtime_qualified",
            "permissions",
            "limits",
            "context_fields",
            "member_fields",
            "cohort_fields",
            "event_fields",
            "proof_obligations",
        },
    )
    _check(
        data["schema"] == "guest-input-handoff-semantic-design-v2"
        and data["graph_version"] == VERSION
        and data["scope"] == "DATA_FD_ONLY"
        and data["evidence_kind"] == "SYNTHETIC"
        and data["encoding"] == "CANONICAL_JSON_DESIGN_NOT_RUNTIME_WIRE"
        and data["clock_domain"] == CLOCK
        and data["preferred_transport"] == "CONTROLLED_INHERITANCE_POST_EXEC_BARRIER"
        and data["runtime_producer_implemented"] is False
        and data["runtime_qualified"] is False
    )
    _keys(data["permissions"], set(PERMISSIONS))
    _check(all(v is False for v in data["permissions"].values()))
    _check(
        data["limits"]
        == {"members": 16, "bytes_per_member": 4096, "events": 1024, "json_bytes": 2097152}
    )
    _fields(data["context_fields"], CONTEXT_FIELDS, "CONTEXT")
    _fields(data["member_fields"], MEMBER_FIELDS, "MANIFEST")
    _fields(data["cohort_fields"], COHORT_FIELDS, "COHORT")
    _keys(data["event_fields"], set(EVENT_FIELDS))
    for kind, names in EVENT_FIELDS.items():
        _fields(data["event_fields"][kind], names, kind)
    obligations = data["proof_obligations"]
    _check(type(obligations) is list and len(obligations) == 7)
    expected = {
        "COMPLETE_DATA_SET",
        "PIN_SEAL_INTERVAL",
        "CONSUMER_FD_OFD_COHORT",
        "EXEC_TRANSFER_BARRIER",
        "INDEPENDENT_FD_INVENTORY",
        "ACTUAL_CONSUMPTION_JOIN",
        "AUTH_EXECUTOR_PROMOTION",
    }
    ids = []
    for obligation in obligations:
        _keys(obligation, {"id", "runtime_status", "meaning"})
        _check(
            type(obligation["id"]) is str
            and obligation["runtime_status"] in {"UNQUALIFIED", "NOT_IMPLEMENTED"}
            and type(obligation["meaning"]) is str
            and bool(obligation["meaning"])
        )
        ids.append(obligation["id"])
    _check(len(set(ids)) == 7 and set(ids) == expected)


def validate_cases(data: Any) -> int:
    _keys(data, {"schema", "evidence_kind", "runtime_qualified", "cases"})
    _check(
        data["schema"] == "guest-input-handoff-counterexamples-v1"
        and data["evidence_kind"] == "SYNTHETIC"
        and data["runtime_qualified"] is False
    )
    _check(type(data["cases"]) is list and len(data["cases"]) == len(CASES))
    count = 0
    for index, (row, (name, status, reason)) in enumerate(
        zip(data["cases"], CASES, strict=True), 1
    ):
        _keys(row, {"id", "variant", "expected_status", "expected_reason"})
        _check(
            row
            == {
                "id": f"HD{index:02d}",
                "variant": name,
                "expected_status": status,
                "expected_reason": reason,
            }
        )
        decision = evaluate(example(name))
        _check(
            decision["status"] == status
            and decision["reasons"] == ([] if reason is None else [reason])
            and decision["overall"] == "BLOCKED"
            and all(v is False for v in decision["permissions"].values())
        )
        count += int(status == "SYNTHETIC_GRAPH_CONSISTENT")
    return count


def validate_sources(data: Any) -> tuple[int, int]:
    _keys(
        data,
        {"schema", "repository", "base_revision", "source_encoding", "runtime_qualified", "files"},
    )
    _check(
        data["schema"] == "guest-input-handoff-source-references-v1"
        and data["repository"] == "https://github.com/rownlvh8875-coder/cyberpilot-autotune"
        and data["base_revision"] == BASE
        and data["runtime_qualified"] is False
        and data["source_encoding"] == "EXACT_GIT_BLOB_NOT_RUNTIME_INPUT_RECEIPT"
    )
    _check(type(data["files"]) is list and len(data["files"]) == len(PINNED_PATHS))
    names = []
    range_count = 0
    for row in data["files"]:
        _keys(row, {"path", "bytes", "sha256", "git_blob_sha1", "ranges"})
        _check(
            type(row["path"]) is str and row["path"] in PINNED_PATHS and row["path"] not in names
        )
        names.append(row["path"])
        try:
            raw = subprocess.check_output(
                ["git", "-C", str(ROOT), "cat-file", "blob", BASE + ":" + row["path"]],
                stderr=subprocess.PIPE,
                env=dict(os.environ, GIT_NO_LAZY_FETCH="1"),
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError("pinned Git blob unavailable; no lazy fetch or substitute") from error
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        _check(
            type(row["bytes"]) is int
            and len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"]
            and blob == row["git_blob_sha1"]
        )
        lines = raw.splitlines(keepends=True)
        _check(type(row["ranges"]) is list and bool(row["ranges"]))
        for claim in row["ranges"]:
            _keys(claim, {"start", "end", "claim", "sha256"})
            _check(
                type(claim["start"]) is int
                and type(claim["end"]) is int
                and 1 <= claim["start"] <= claim["end"] <= len(lines)
                and type(claim["claim"]) is str
                and bool(claim["claim"])
            )
            _check(
                hashlib.sha256(b"".join(lines[claim["start"] - 1 : claim["end"]])).hexdigest()
                == claim["sha256"]
            )
            range_count += 1
    return len(names), range_count


def validate() -> dict[str, object]:
    validate_schema(load("schema"))
    positive = validate_cases(load("cases"))
    files, ranges = validate_sources(load("sources"))
    return {
        "audit": "GUEST_INPUT_HANDOFF_DESIGN_AUDIT_PASS",
        "synthetic_cases": len(CASES),
        "synthetic_consistent": positive,
        "pinned_git_files": files,
        "pinned_git_ranges": ranges,
        "overall": "BLOCKED",
        "runtime_producer_implemented": False,
        "runtime_qualified": False,
        "permissions": dict.fromkeys(PERMISSIONS, False),
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
