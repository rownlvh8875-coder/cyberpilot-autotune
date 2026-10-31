"""Offline source and synthetic catalog audit,not producer/runtime qualification."""

import argparse
import json
from pathlib import Path
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need
from tests.audit.validate_fd_ofd_lifetime_design import validate_source_record
from tests.audit.validate_kernel_lifetime_feasibility import load as load
from tests.guest_raw_lifetime.audit import _record, digest

from .model import BINDING_FIELDS, COPY_FIELDS, OBJECT_FIELDS, SOURCE_SHA, evaluate

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs/evidence/inherited_ofd_design_schema.json"
SOURCES = ROOT / "docs/evidence/inherited_ofd_design_sources.json"
CASES = ROOT / "docs/evidence/inherited_ofd_design_cases.json"
SCHEMA_SHA = "078461c5b1ed62166e9325536ab40a791bf8b5753f5e2e28439d131a6cde9bfa"
SOURCE_DIGEST = "bb7871285bc2f40f51f949896bb4fdde7aa63b390e3e821caeda60ba25ace6c7"
CASE_SHA = "61f41dff404ddd13ed3589a9e143b42cf700f943b071e982dae9ea969e4d6206"


def validate_schema(data: Any) -> None:
    need(digest(data) == SCHEMA_SHA, "SEMANTIC_SCHEMA_DRIFT")
    for section, fields in (
        ("objects", OBJECT_FIELDS),
        ("copy", COPY_FIELDS),
        ("bindings", BINDING_FIELDS),
    ):
        need(
            {r["field"] for r in data["sections"][section]} == fields,
            "IMPLEMENTED_SCHEMA_FIELD_MISMATCH",
        )


def validate_sources(data: Any, kernel_root: Path | None = None) -> bool:
    need(digest(data) == SOURCE_DIGEST, "SOURCE_REFERENCE_DRIFT")
    for row in data["repository_files"]:
        _record(row, row["path"], (ROOT / row["path"]).read_bytes())
    reference = next(
        r
        for r in data["repository_files"]
        if r["path"] == "docs/evidence/guest_fork_copy_sources.json"
    )
    need(reference["sha256"] == SOURCE_SHA, "WRONG_PR40_SOURCE_MANIFEST")
    if kernel_root is None:
        return False
    for row in data["kernel_files"]:
        with (kernel_root / row["path"]).open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        need(len(raw) <= 4 * 1024 * 1024, "SOURCE_BOUND")
        validate_source_record(row, raw)
    return True


def validate_cases(data: Any) -> tuple[int, int]:
    need(digest(data) == CASE_SHA, "SYNTHETIC_CATALOG_DRIFT")
    count = 0
    for row in data["cases"]:
        result = evaluate(row["payload"])
        need(
            result.premises_consistent is row["expected_consistent"]
            and [list(link) for link in result.linked_fds] == row["expected_links"],
            "SYNTHETIC_OUTCOME_MISMATCH",
        )
        need(
            result.evidence_class == "SYNTHETIC_ONLY"
            and result.status == "BLOCKED"
            and not result.allocation_history_complete
            and not result.runtime_producer_implemented
            and result.actual_global_drops is None
            and result.actual_prohibited_operations is None
            and all(v is False for _, v in result.permissions),
            "NO_RUNTIME_AUTHORITY",
        )
        count += result.premises_consistent
    return len(data["cases"]), count


def validate(kernel_root: Path | None = None) -> dict[str, Any]:
    validate_schema(load(SCHEMA))
    verified = validate_sources(load(SOURCES), kernel_root)
    cases, consistent = validate_cases(load(CASES))
    return dict(
        synthetic_cases=cases,
        consistent_cases=consistent,
        source_bytes_verified=verified,
        source_files=7,
        source_ranges=13,
        evidence_class="SYNTHETIC_ONLY",
        status="BLOCKED",
        allocation_history_complete=False,
        runtime_producer_implemented=False,
        actual_global_drops=None,
        actual_prohibited_operations=None,
        permissions=dict(PERMISSIONS),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-source", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.kernel_source), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
