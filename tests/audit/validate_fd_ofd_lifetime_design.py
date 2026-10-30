"""Offline synthetic consistency and exact source reference audit; no runtime qualification."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .fd_ofd_lifetime_model import FIELDS, PERMISSIONS, evaluate, need, shape, uint

ROOT = Path(__file__).resolve().parents[2]
BASE = "3a831fdd423aa98638082eba126519db19f432d6"
PREFIX = "docs/evidence/fd_ofd_lifetime_design_"
ARCHIVE = "ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33"
GIT_PATHS = {
    "docs/guest_data_fd_handoff_contract.md",
    "docs/guest_data_fd_handoff_result.md",
    "tests/experiments/guest_data_fd_handoff/model.py",
    "tests/experiments/guest_data_fd_handoff/guest/probe.c",
}
KERNEL_PATHS = {
    "fs/file.c",
    "kernel/fork.c",
    "fs/exec.c",
    "kernel/kcmp.c",
    "kernel/pid.c",
    "fs/file_table.c",
    "fs/proc/fd.c",
    "include/linux/fdtable.h",
    "include/uapi/linux/kcmp.h",
}


def metadata(name: str, type_name: str | None = None, unit: str | None = None) -> dict[str, str]:
    if type_name is None:
        if name in {"task", "parent", "child", "table", "child_table", "after_table", "ofd", "pin"}:
            type_name, unit = "ResourceKey", "opaque_allocation_lifetime"
        elif name in {"cloexec", "old", "new", "share"}:
            type_name, unit = "Bool", "flag"
        elif name in {"closed", "entries"}:
            type_name, unit = "BindingVector", "canonical_bindings"
        elif name == "object_digest":
            type_name, unit = "SHA256", "context_only_not_OFD_identity"
        elif name == "method":
            type_name, unit = "DupMethod", "source_operation"
        else:
            type_name, unit = "UInt64", "ordinal_or_count"
    return {
        "field": name,
        "type": type_name,
        "unit": unit or "unitless",
        "stage": "SYNTHETIC_LIFECYCLE_MODEL",
        "availability": "REQUIRED_NO_DEFAULT",
    }


def schema_template() -> dict[str, Any]:
    return {
        "schema_version": "fd-ofd-lifetime-design-v1",
        "evidence_class": "SYNTHETIC_ONLY",
        "profile": "PROPOSED_KERNEL_SERIALIZED_LIFETIME_V1",
        "envelope": [
            metadata(n, t, u)
            for n, t, u in (
                ("seq", "UInt64", "source_linearization_ordinal"),
                ("time_ns", "UInt64", "ns"),
                ("cpu", "UInt32", "logical_cpu_id"),
                ("cpu_seq", "UInt64", "per_cpu_source_ordinal"),
                ("context_digest", "SHA256", "content_identity_only"),
                ("kind", "LifecycleKind", "enum"),
                ("data", "KindSpecificVector", "semantic_fields"),
            )
        ],
        "context": [
            metadata(n, t, u)
            for n, t, u in (
                ("session_id", "Token", "local_scope"),
                ("boot_scope", "Token", "local_scope"),
                ("source_revision", "GitSHA1", "source_revision"),
                ("source_digest", "SHA256", "source_manifest"),
                ("scope_digest", "SHA256", "scope_policy"),
                ("profile", "Profile", "proposed_not_qualified"),
                ("clock_domain", "ClockDomain", "synthetic_source_clock"),
                ("cpus", "UInt32Vector", "cpu_cohort"),
            )
        ],
        "coverage": [
            metadata(n, t, u)
            for n, t, u in (
                ("start_fence", "UInt64", "source_ordinal"),
                ("end_fence", "UInt64", "source_ordinal"),
                ("cpus", "CpuCoverageVector", "synthetic_claims_only"),
            )
        ],
        "cpu_coverage": [
            metadata(n, t, u)
            for n, t, u in (
                ("cpu", "UInt32", "logical_cpu_id"),
                ("armed", "Bool", "synthetic_claim"),
                ("drained", "Bool", "synthetic_claim"),
                ("emitted", "UInt64", "synthetic_event_count"),
                ("last_source_seq", "UInt64", "per_cpu_source_watermark"),
                ("dropped", "UInt64", "synthetic_loss_count_not_actual"),
            )
        ],
        "events": {k: [metadata(n) for n in names] for k, names in FIELDS.items()},
        "binding_entry": [
            metadata("fd", "UInt64", "descriptor_number"),
            metadata("slot", "UInt64", "binding_incarnation"),
            metadata("ofd"),
            metadata("cloexec"),
        ],
        "resource_limits": {
            "tasks": 32,
            "tables": 32,
            "ofds": 64,
            "pins": 64,
            "fd_slots": 64,
            "events": 2048,
            "cpus": 8,
            "depth": 24,
            "string_chars": 4096,
        },
        "runtime_qualified": False,
        "permissions": dict(PERMISSIONS),
    }


def strict_equal(value: Any, expected: Any) -> bool:
    if type(value) is not type(expected):
        return False
    if type(expected) is dict:
        return set(value) == set(expected) and all(
            strict_equal(value[k], v) for k, v in expected.items()
        )
    if type(expected) is list:
        return len(value) == len(expected) and all(
            strict_equal(a, b) for a, b in zip(value, expected, strict=True)
        )
    return bool(value == expected)


def validate_schema(data: Any) -> None:
    need(strict_equal(data, schema_template()), "SEMANTIC_SCHEMA_DRIFT")


def validate_catalog(data: Any) -> tuple[int, int]:
    shape(data, {"schema", "evidence_class", "cases", "runtime_qualified", "permissions"})
    need(
        data["schema"] == "fd-ofd-lifetime-cases-v1"
        and data["evidence_class"] == "SYNTHETIC_ONLY"
        and data["runtime_qualified"] is False
        and strict_equal(data["permissions"], dict(PERMISSIONS)),
        "SYNTHETIC_FALSE_AUTHORITY_REQUIRED",
    )
    cases = data["cases"]
    need(type(cases) is list and len(cases) == 43, "COMPLETE_COUNTEREXAMPLE_MATRIX_REQUIRED")
    positives = 0
    names = set()
    for i, row in enumerate(cases, 1):
        shape(row, {"case_id", "name", "expected_consistent", "graph"})
        need(
            row["case_id"] == f"L{i:03d}"
            and type(row["name"]) is str
            and row["name"] not in names
            and type(row["expected_consistent"]) is bool,
            "UNIQUE_EXACT_CASE_REQUIRED",
        )
        names.add(row["name"])
        result = evaluate(row["graph"])
        need(result.model_consistent is row["expected_consistent"], "COUNTEREXAMPLE_VERDICT_DRIFT")
        need(
            result.status == "BLOCKED"
            and result.permissions == PERMISSIONS
            and result.actual_dropped_events is None
            and result.global_prohibited_counts is None,
            "NO_QUALIFICATION_OR_AUTHORITY",
        )
        positives += int(result.model_consistent)
    need(positives == 12, "COMPLETE_COUNTEREXAMPLE_MATRIX_REQUIRED")
    return len(cases), positives


def validate_source_record(row: Any, raw: bytes) -> None:
    shape(row, {"path", "bytes", "sha256", "git_blob_sha1", "ranges"})
    need(
        type(row["path"]) is str
        and uint(row["bytes"]) == len(raw)
        and row["sha256"] == hashlib.sha256(raw).hexdigest()
        and row["git_blob_sha1"]
        == hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "SOURCE_BLOB_DRIFT",
    )
    need(type(row["ranges"]) is list and bool(row["ranges"]), "SOURCE_RANGES_REQUIRED")
    lines = raw.splitlines(keepends=True)
    for claim in row["ranges"]:
        shape(claim, {"claim", "start", "end", "sha256"})
        start, end = uint(claim["start"]), uint(claim["end"])
        need(
            type(claim["claim"]) is str
            and bool(claim["claim"])
            and 1 <= start <= end <= len(lines)
            and hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest() == claim["sha256"],
            "SOURCE_RANGE_DRIFT",
        )


def json_file(path: str) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out = {}
        for key, value in pairs:
            need(key not in out, "DUPLICATE_JSON_FIELD")
            out[key] = value
        return out

    with (ROOT / path).open("rb") as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    need(len(raw) <= 4 * 1024 * 1024, "SOURCE_RESOURCE_BOUND")
    return json.loads(raw, object_pairs_hook=unique)


def validate(kernel_root: Path | None = None) -> dict[str, Any]:
    validate_schema(json_file(PREFIX + "schema.json"))
    cases, positives = validate_catalog(json_file(PREFIX + "cases.json"))
    sources = json_file(PREFIX + "sources.json")
    shape(
        sources,
        {
            "schema",
            "base_revision",
            "source_archive_sha256",
            "authenticated_package",
            "runtime_qualified",
            "git_files",
            "kernel_files",
        },
    )
    need(
        sources["schema"] == "fd-ofd-lifetime-source-refs-v1"
        and sources["base_revision"] == BASE
        and sources["source_archive_sha256"] == ARCHIVE
        and sources["runtime_qualified"] is False,
        "SOURCE_PROFILE_DRIFT",
    )
    for group, paths in (("git_files", GIT_PATHS), ("kernel_files", KERNEL_PATHS)):
        rows = sources[group]
        need(type(rows) is list and len(rows) == len(paths), "SOURCE_COHORT_DRIFT")
        for row in rows:
            shape(row, {"path", "bytes", "sha256", "git_blob_sha1", "ranges"})
            need(type(row["path"]) is str, "SOURCE_COHORT_DRIFT")
        need(
            type(rows) is list and len(rows) == len(paths) and {r["path"] for r in rows} == paths,
            "SOURCE_COHORT_DRIFT",
        )
    need(
        strict_equal(
            sources["authenticated_package"],
            {
                "bytes": 153094996,
                "path": "/workspace/scratch/guest-backend.FY5icM/kernel-source/"
                "linux-source-6.12_6.12.113-1_all.deb",
                "sha256": "6ad4a0316ddefced87cef8cd9a25a268e0cdfe0a10adc5148401f49f90b336b5",
            },
        ),
        "AUTHENTICATED_PACKAGE_PROFILE_DRIFT",
    )
    for row in sources["git_files"]:
        raw = subprocess.check_output(
            [
                "git",
                "--no-replace-objects",
                "-C",
                str(ROOT),
                "cat-file",
                "blob",
                BASE + ":" + row["path"],
            ],
            env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
            timeout=30,
        )
        validate_source_record(row, raw)
    if kernel_root is not None:
        for row in sources["kernel_files"]:
            with (kernel_root / row["path"]).open("rb") as stream:
                raw = stream.read(4 * 1024 * 1024 + 1)
            need(len(raw) <= 4 * 1024 * 1024, "SOURCE_RESOURCE_BOUND")
            validate_source_record(row, raw)
    return {
        "synthetic_cases": cases,
        "consistent_models": positives,
        "git_files": len(GIT_PATHS),
        "kernel_files": len(KERNEL_PATHS),
        "kernel_bytes_verified": kernel_root is not None,
        "ranges": sum(
            len(r["ranges"])
            for rows in (sources["git_files"], sources["kernel_files"])
            for r in rows
        ),
        "status": "BLOCKED",
        "runtime_qualified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-source", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.kernel_source), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
