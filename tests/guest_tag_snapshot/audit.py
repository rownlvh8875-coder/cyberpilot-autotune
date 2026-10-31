"""Read-only original-byte replay; never builds, boots or qualifies a producer."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from compatibility.containment_backend_harmless.vm_runner import verify_vm
from tests.audit.validate_fd_ofd_lifetime_design import validate_source_record
from tests.guest_raw_lifetime.audit import _record, _serial, digest
from tests.guest_raw_lifetime.model import PERMISSIONS, require

from .contracts import CASES
from .model import assess
from .wire import parse_serial

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path("/workspace/scratch/post-reference-tag-producer.NaoDTY")
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc")
BUILD = ROOT / "docs/evidence/guest_tag_snapshot_build.json"
SOURCES = ROOT / "docs/evidence/guest_tag_snapshot_sources.json"
ACTUAL = ROOT / "docs/evidence/guest_tag_snapshot_actual.json"
BUILD_DIGEST = "492b646a04af900945b04f42db2b18261438b02050326ac2d766a801bda8d75b"
SOURCE_DIGEST = "8906f740eeeceff728958494de93c0dd3e57d2f1c5a1e484e88129869dfcfeeb"
ACTUAL_DIGEST = "6e8471f02ca74a80d82357401a2b1e93612e0f7781d2584ce40409120a8ecf31"
ATTEMPTS = (490, 490, 490, 489, 288, 490, 490)
FAILURES = (0, 1, 362, 0, 0, 1, 1)
SNAPSHOTS = (18, 18, 7, 18, 8, 17, 18)
JOINS = (18, 18, 7, 18, 8, 17, 17)
ZEROS = (0, 0, 0, 2, 0, 0, 0)


def validate_build(data: Any) -> None:
    require(digest(data) == BUILD_DIGEST, "FIXED_BUILD_COHORT_DRIFT")
    for row in data["sources"] + data["patch_chain"]:
        _record(row, row["path"], (ROOT / row["path"]).read_bytes())


def validate_sources(data: Any, source_root: Path | None = None) -> bool:
    require(digest(data) == SOURCE_DIGEST, "FROZEN_SOURCE_CATALOG_DRIFT")
    if source_root is None:
        return False
    for row in data["files"]:
        with (source_root / row["path"]).open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        require(len(raw) <= 4 * 1024 * 1024, "SOURCE_BOUND")
        validate_source_record(row, raw)
    return True


def validate_actual(data: Any, build_raw: bytes) -> dict[str, Any]:
    validate_build(json.loads(build_raw))
    require(digest(data) == ACTUAL_DIGEST, "FROZEN_ORIGINAL_CAPTURE_BYTES_CHANGED")
    require(
        data["build_manifest_sha256"] == hashlib.sha256(build_raw).hexdigest(), "WRONG_BUILD_COHORT"
    )
    baseline = _serial(data["baseline"], "baseline-serial.txt")
    require(
        b"CPR_UNAVAILABLE errno=2" in baseline and b"CPR_DRIVER ok=1" not in baseline,
        "ACTUAL_MISSING_INTERFACE_BASELINE_REQUIRED",
    )
    try:
        parse_serial(baseline)
    except ValueError:
        pass
    else:
        raise ValueError("BASELINE_WAS_ADMITTED")
    total = 0
    for index, (row, case) in enumerate(zip(data["captures"], CASES, strict=True)):
        require(row["case"] == case, "FIXED_CASE_ORDER")
        raw = _serial(row, "final-" + case + "-serial.txt")
        _record(row["image"], "final-" + case + "-initrd.gz")
        capture = parse_serial(raw)
        result = assess(capture)
        tokens = [
            dict(t.split("=") for t in line.decode().split()[1:])
            for line in raw.splitlines()
            if line.startswith(b"CPR_EVENT ")
        ]
        require(digest(tokens) == row["semantic_sha256"], "WRONG_RAW_STAGE_CONTEXT_OR_VALUES")
        require(
            capture.case == case
            and capture.counts
            == (
                ATTEMPTS[index],
                ATTEMPTS[index] - FAILURES[index],
                ATTEMPTS[index] - FAILURES[index],
                FAILURES[index],
                0,
                0,
            )
            and result.local_accounting_balanced
            and len(result.snapshots) == SNAPSHOTS[index]
            and sum(s.source_join_complete for s in result.snapshots) == JOINS[index]
            and sum(s.raw_cookie == 0 for s in result.snapshots) == ZEROS[index],
            "ACTUAL_FIXED_DIAGNOSTIC_MISMATCH",
        )
        require(
            result.status == "BLOCKED"
            and result.evidence_class == "OBSERVED_UNTRUSTED"
            and not result.runtime_qualified
            and not result.tag_publication_qualified
            and not result.target_lifetime_proven
            and not result.source_happens_before_proven
            and not result.allocation_history_complete
            and not result.atomic_cut_proven
            and result.actual_global_drops is result.actual_prohibited_operations is None
            and all(v is False for _, v in result.permissions)
            and all(
                s.generation
                is s.lifetime_witness
                is s.publication_witness
                is s.membership_witness
                is None
                for s in result.snapshots
            ),
            "NO_RUNTIME_AUTHORITY",
        )
        total += len(capture.events)
    return dict(
        actual_cases=7,
        raw_events=total,
        snapshot_counts=list(SNAPSHOTS),
        complete_source_joins=list(JOINS),
        raw_zero_counts=list(ZEROS),
        local_failures=list(FAILURES),
    )


def validate(*, source_root: Path | None = None, verify_assets: bool = False) -> dict[str, Any]:
    build_raw = BUILD.read_bytes()
    build = json.loads(build_raw)
    actual = json.loads(ACTUAL.read_bytes())
    report = validate_actual(actual, build_raw)
    source_verified = validate_sources(json.loads(SOURCES.read_bytes()), source_root)
    if verify_assets:
        rows = [(ASSETS / build[k]["path"], build[k]) for k in ("kernel", "init", "actual_config")]
        rows += [
            (Path(build[k]["path"]), build[k])
            for k in (
                "baseline_kernel",
                "source_archive",
                "source_package",
                "dependency_index",
                "dependency_inrelease",
            )
        ]
        rows += [(Path(r["path"]), r) for k in ("tools", "dependency_packages") for r in build[k]]
        for row in [actual["baseline"], *actual["captures"]]:
            for key in ("serial", "image"):
                if key in row:
                    rows.append((ASSETS / row[key]["path"], row[key]))
        for path, record in rows:
            with path.open("rb") as stream:
                sha = hashlib.file_digest(stream, "sha256").hexdigest()
            require(
                path.stat().st_size == record["bytes"] and sha == record["sha256"],
                "PREPARED_OR_RETAINED_ASSET_DRIFT",
            )
        verify_vm(VM)
    report.update(
        source_bytes_verified=source_verified,
        assets_verified=verify_assets,
        evidence_class="OBSERVED_UNTRUSTED",
        status="BLOCKED",
        runtime_qualified=False,
        tag_publication_qualified=False,
        target_lifetime_proven=False,
        source_happens_before_proven=False,
        allocation_history_complete=False,
        atomic_cut_proven=False,
        actual_global_drops=None,
        actual_prohibited_operations=None,
        permissions=dict(PERMISSIONS),
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--verify-assets", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            validate(source_root=args.source_root, verify_assets=args.verify_assets), sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
