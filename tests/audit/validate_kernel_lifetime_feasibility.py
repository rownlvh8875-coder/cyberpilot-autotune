"""Read-only offline source-design audit, never a runtime observer qualification."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .fd_ofd_lifetime_model import PERMISSIONS, need, shape
from .kernel_lifetime_witness import analyze_copy, copy_orders
from .validate_fd_ofd_lifetime_design import strict_equal, validate_source_record

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "docs/evidence/kernel_lifetime_feasibility_sources.json"
MATRIX = ROOT / "docs/evidence/kernel_lifetime_feasibility_matrix.json"
SOURCE_DIGEST = "7cdd11d7af34384ed2f6d411e039a9c7b1ebbe4639f963a3da5333284c4b668b"
OBLIGATIONS = {
    "namespace_lifetime",
    "ofd_lifetime",
    "binding_mutations",
    "copy_cut",
    "exec_cut",
    "task_and_scope",
    "loss_accounting",
    "arm_drain_cpu",
    "perturbation",
}
REFERENCES = {
    "namespace_lifetime": {"NS_LAYOUT", "NS_RESIZE", "NS_COPY", "NS_END"},
    "ofd_lifetime": {"OFD_ALLOC", "OFD_BACKING", "OFD_FREE", "OFD_FPUT"},
    "binding_mutations": {"FD_INSTALL", "FD_CLOSE", "FD_FLAGS", "FD_REPLACE"},
    "copy_cut": {"NS_COPY", "FD_INSTALL", "FORK_FILES", "UNSHARE"},
    "exec_cut": {"EXEC_EFFECT", "EXEC_CLOSE", "EXEC_EVENT"},
    "task_and_scope": {"SCHED_TASK", "SCHED_FORK", "SCHED_EXEC", "FORK_EVENT", "FORK_FILES"},
    "loss_accounting": {"RING_RESERVE", "RING_COMMIT", "RING_DOC"},
    "arm_drain_cpu": {"TRACE_UNREGISTER", "CPU_COHORT", "RING_DOC"},
    "perturbation": {"NS_COPY", "UNSHARE", "OFD_FPUT", "CPU_COHORT"},
}


def load(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in pairs:
            need(k not in out, "DUPLICATE_JSON_FIELD")
            out[k] = v
        return out

    def invalid(value: str) -> None:
        raise ValueError("NONFINITE_JSON: " + value)

    with path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    need(len(raw) <= 1024 * 1024, "MANIFEST_TOO_LARGE")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def audit_sources(data: Any, kernel_root: Path | None = None) -> set[str]:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    need(hashlib.sha256(canonical).hexdigest() == SOURCE_DIGEST, "SOURCE_MANIFEST_DRIFT")
    # Digest pins the exact finite path/range/profile cohort before any file read.
    claims = {claim["claim"] for row in data["files"] for claim in row["ranges"]}
    if kernel_root is not None:
        for row in data["files"]:
            with (kernel_root / row["path"]).open("rb") as stream:
                raw = stream.read(4 * 1024 * 1024 + 1)
            need(len(raw) <= 4 * 1024 * 1024, "SOURCE_RESOURCE_BOUND")
            validate_source_record(row, raw)
    return claims


def audit_matrix(data: Any, claims: set[str]) -> int:
    shape(
        data,
        {
            "schema",
            "evidence_class",
            "status",
            "runtime_qualified",
            "actual_dropped_events",
            "permissions",
            "rows",
        },
    )
    need(
        data["schema"] == "kernel-lifetime-feasibility-matrix-v1"
        and data["evidence_class"] == "SOURCE_DESIGN_ONLY"
        and data["status"] == "BLOCKED"
        and data["runtime_qualified"] is False
        and data["actual_dropped_events"] is None
        and strict_equal(data["permissions"], dict(PERMISSIONS)),
        "NO_RUNTIME_QUALIFICATION_OR_AUTHORITY",
    )
    rows = data["rows"]
    need(type(rows) is list and len(rows) == len(OBLIGATIONS), "OBLIGATION_COHORT_DRIFT")
    seen = set()
    for row in rows:
        shape(row, {"id", "claims", "current_source", "instrumented_design", "blockers"})
        need(type(row["id"]) is str and row["id"] not in seen, "DUPLICATE_OBLIGATION")
        seen.add(row["id"])
        need(
            row["current_source"] == "NO_GO_CURRENT_PROFILE"
            and row["instrumented_design"] == "CONDITIONAL_DESIGN_ONLY",
            "DESIGN_IS_NOT_QUALIFIED_IMPLEMENTATION",
        )
        for key in ("claims", "blockers"):
            values = row[key]
            need(
                type(values) is list
                and bool(values)
                and all(type(v) is str and bool(v) for v in values),
                "EVIDENCE_GAP_REQUIRED",
            )
        need(set(row["claims"]) <= claims, "UNKNOWN_SOURCE_CLAIM")
        need(set(row["claims"]) == REFERENCES.get(row["id"]), "WRONG_OBLIGATION_SOURCE_COHORT")
    need(seen == OBLIGATIONS, "OBLIGATION_COHORT_DRIFT")
    return len(rows)


def validate(kernel_root: Path | None = None) -> dict[str, Any]:
    sources = load(SOURCES)
    claims = audit_sources(sources, kernel_root)
    count = audit_matrix(load(MATRIX), claims)
    orders = copy_orders()
    return {
        "source_files": len(sources["files"]),
        "source_ranges": len(claims),
        "kernel_bytes_verified": kernel_root is not None,
        "obligations": count,
        "synthetic_copy_orders": len(orders),
        "synthetic_copies_without_cut": sum(not analyze_copy(p).has_cut for p in orders),
        "current_profile": "NO_GO_CURRENT_PROFILE",
        "instrumented_design": "CONDITIONAL_DESIGN_ONLY",
        "status": "BLOCKED",
        "runtime_qualified": False,
        "actual_dropped_events": None,
        "permissions": dict(PERMISSIONS),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-source", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.kernel_source), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
