"""Offline SYNTHETIC design audit, never a source producer or inventory adapter."""

import argparse
import json
from pathlib import Path
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need
from tests.audit.kernel_lifetime_witness import analyze_copy, copy_orders
from tests.audit.validate_fd_ofd_lifetime_design import validate_source_record
from tests.audit.validate_kernel_lifetime_feasibility import load as load
from tests.guest_raw_lifetime.audit import _record, digest

from .model import FIELDS, SOURCE_HASHES, evaluate

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "docs/evidence/fork_copy_design_sources.json"
SCHEMA = ROOT / "docs/evidence/fork_copy_design_schema.json"
CASES = ROOT / "docs/evidence/fork_copy_design_cases.json"
SOURCE_DIGEST = "b59956a24f830fc1a783210778786400853c6f1b63e232a3b9bd11f31c3620fa"
SCHEMA_DIGEST = "9cc994a4b8bf362163be9b38aebfd6fb8ac68698ae654c311417dbc2b5cc04b5"
CASE_DIGEST = "21c4547b71b120d491b70d6415353432432df1afa753db93144ceb799c59da81"


def validate_schema(data: Any) -> None:
    need(digest(data) == SCHEMA_DIGEST, "SEMANTIC_SCHEMA_DRIFT")
    actual = {row["kind"]: {f["field"] for f in row["fields"]} for row in data["stages"]}
    need(actual == {k: {"n"} | v for k, v in FIELDS.items()}, "IMPLEMENTED_STAGE_COHORT_DRIFT")


def validate_sources(
    data: Any, kernel_root: Path | None = None, pristine_root: Path | None = None
) -> tuple[bool, bool]:
    need(digest(data) == SOURCE_DIGEST, "SOURCE_REFERENCE_DRIFT")
    for row in data["repository_files"]:
        _record(row, row["path"], (ROOT / row["path"]).read_bytes())
    hashes = {row["path"]: row["sha256"] for row in data["patched_files"]}
    need(
        hashes["fs/file.c"] == SOURCE_HASHES["source_sha256"]
        and hashes["kernel/fork.c"] == SOURCE_HASHES["fork_sha256"]
        and hashes["include/linux/fdtable.h"] == SOURCE_HASHES["fdtable_sha256"],
        "WRONG_IMPLEMENTED_SOURCE_COHORT",
    )
    for name, root in (("patched_files", kernel_root), ("pristine_files", pristine_root)):
        if root is None:
            continue
        for row in data[name]:
            with (root / row["path"]).open("rb") as stream:
                raw = stream.read(4 * 1024 * 1024 + 1)
            need(len(raw) <= 4 * 1024 * 1024, "SOURCE_BOUND")
            validate_source_record(row, raw)
    return kernel_root is not None, pristine_root is not None


def validate_cases(data: Any) -> tuple[int, int]:
    need(digest(data) == CASE_DIGEST, "SYNTHETIC_CATALOG_DRIFT")
    consistent = 0
    for row in data["cases"]:
        result = evaluate(row["payload"])
        need(result.consistent is row["expected_consistent"], "SYNTHETIC_OUTCOME_MISMATCH")
        if row["expected_reason"] is not None:
            need(row["expected_reason"] in result.reasons, "SYNTHETIC_REASON_MISMATCH")
        need(
            result.status == "BLOCKED"
            and not result.atomic_cut_proven
            and not result.runtime_producer_implemented
            and result.actual_global_drops is None
            and result.actual_prohibited_operations is None
            and all(v is False for _, v in result.permissions),
            "NO_RUNTIME_AUTHORITY",
        )
        consistent += result.consistent
    return len(data["cases"]), consistent


def validate(kernel_root: Path | None = None, pristine_root: Path | None = None) -> dict[str, Any]:
    validate_schema(load(SCHEMA))
    patched, pristine = validate_sources(load(SOURCES), kernel_root, pristine_root)
    count, consistent = validate_cases(load(CASES))
    orders = copy_orders()
    return dict(
        synthetic_cases=count,
        synthetic_consistent_cases=consistent,
        synthetic_copy_orders=len(orders),
        synthetic_copies_without_cut=sum(not analyze_copy(p).has_cut for p in orders),
        proposed_records_per_copy=196,
        existing_buffer_capacity=128,
        kernel_bytes_verified=patched,
        pristine_bytes_verified=pristine,
        source_files=(3, 4),
        source_ranges=36,
        status="BLOCKED",
        runtime_producer_implemented=False,
        atomic_cut_proven=False,
        actual_copy_records=None,
        actual_global_drops=None,
        actual_prohibited_operations=None,
        permissions=dict(PERMISSIONS),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-source", type=Path)
    parser.add_argument("--pristine-source", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.kernel_source, args.pristine_source), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
