"""Offline fixed source/serial replay. No build, guest execution or qualification."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from compatibility.containment_backend_harmless.vm_runner import verify_vm
from tests.audit.fd_ofd_lifetime_model import shape
from tests.audit.validate_fd_ofd_lifetime_design import validate_source_record
from tests.audit.validate_kernel_lifetime_feasibility import load as load
from tests.guest_raw_lifetime.audit import _record, _serial, digest
from tests.guest_raw_lifetime.model import PERMISSIONS

from .model import CASES, RawEvent, assess, parse_serial, require
from .runner import ASSETS, IMAGE_SHA, ROOT, VM

BUILD = ROOT / "docs/evidence/guest_root_scope_build.json"
ACTUAL = ROOT / "docs/evidence/guest_root_scope_actual.json"
SOURCES = ROOT / "docs/evidence/guest_root_scope_sources.json"
BUILD_DIGEST = "927d7d9d98dbc29518784ade0e93f5406ae103c2d10ef70ca21baf7c25baa54b"
SOURCE_DIGEST = "eafdb5fb25bfc9b9fbd2bcc98df43bc8ebf6f6bb1e001ee415d534681807690c"
IMAGE_BYTES = (336065, 336075, 336072)

# Hand-audited fixed source/driver semantic sequence. No reconstruction from PIDs,
# addresses, expected times or downstream inventory; monotonic time is annotation.
# kind, actor task, subject task, namespace, OFD, old cookie, FD, CLOEXEC.
NORMAL_EFFECTS = (
    ("TASK_ALLOC", None, 1, None, None, None, None, None),
    ("TABLE_NEW", None, 1, 2, None, None, None, None),
    ("TASK_COMMIT", None, 1, 2, None, None, None, None),
    ("FILE_NEW", 1, None, None, 3, None, None, None),
    ("INSTALL", 1, None, 2, 3, None, 5, 1),
    ("REPLACE", 1, None, 2, 3, None, 40, 0),
    ("FLAGS", 1, None, 2, 3, None, 40, 1),
    ("REPLACE", 1, None, 2, 3, 3, 40, 1),
    ("TASK_ALLOC", 1, 4, None, None, None, None, None),
    ("TABLE_NEW", 1, 4, 5, None, 2, None, None),
    ("TASK_COMMIT", 1, 4, 5, None, None, None, None),
    ("CLOSE", 4, None, 5, 3, None, 5, None),
    ("CLOSE", 4, None, 5, 3, None, 40, None),
    ("TABLE_FREE", 4, None, 5, None, None, None, None),
    ("CLOSE", 1, None, 2, 3, None, 5, None),
    ("CLOSE", 1, None, 2, 3, None, 40, None),
    ("FILE_FREE", 1, None, None, 3, None, None, None),
    ("TABLE_FREE", 1, None, 2, None, None, None, None),
)


def validate_build(data: Any) -> None:
    require(digest(data) == BUILD_DIGEST, "FIXED_BUILD_COHORT_DRIFT")
    for row in data["sources"]:
        _record(row, row["path"], (ROOT / row["path"]).read_bytes())


def _semantic(e: RawEvent) -> tuple[object, ...]:
    return e.kind, e.actor_id, e.task_id, e.table_id, e.file_id, e.old_id, e.fd, e.flags


def validate_actual(data: Any, build_raw: bytes) -> tuple[int, list[int], list[bool]]:
    validate_build(json.loads(build_raw))
    shape(
        data,
        {
            "schema",
            "evidence_class",
            "build_manifest_sha256",
            "captures",
            "baseline",
            "runtime_qualified",
        },
    )
    require(
        data["schema"] == "guest-root-scope-actual-v1"
        and data["evidence_class"] == "OBSERVED_UNTRUSTED"
        and data["runtime_qualified"] is False
        and data["build_manifest_sha256"] == hashlib.sha256(build_raw).hexdigest(),
        "UNQUALIFIED_EXACT_CAPTURE_COHORT",
    )
    shape(data["baseline"], {"serial", "serial_base64", "expected"})
    baseline = _serial(data["baseline"], "baseline-serial.txt")
    require(
        data["baseline"]["expected"] == "MISSING_EXPERIMENTAL_CONTROL_INTERFACE"
        and b"CPS_UNAVAILABLE errno=2" in baseline
        and b"CPS_DRIVER ok=1" not in baseline,
        "ACTUAL_NEGATIVE_BASELINE_REQUIRED",
    )
    rows = data["captures"]
    require(type(rows) is list and len(rows) == 3, "FIXED_THREE_CAPTURES_REQUIRED")
    count, failures, observed = 0, [], []
    for i, (row, case) in enumerate(zip(rows, CASES, strict=True)):
        shape(row, {"case", "serial", "serial_base64", "image"})
        require(row["case"] == case, "FIXED_CASE_ORDER")
        raw = _serial(row, "final-" + case + "-serial.txt")
        _record(row["image"], case + "-initrd.gz")
        require(
            row["image"]["sha256"] == IMAGE_SHA[case] and row["image"]["bytes"] == IMAGE_BYTES[i],
            "FIXED_IMAGE_COHORT",
        )
        capture = parse_serial(raw)
        result = assess(capture)
        seqs = (tuple(range(1, 19)), tuple(range(2, 19)), (1, 2))[i]
        require(
            capture.case == case
            and capture.root_id == 1
            and capture.attempted == 18
            and capture.failed == (0, 1, 16)[i]
            and result.local_accounting_balanced
            and result.root_creation_observed is (i == 0),
            "ACTUAL_FIXED_DIAGNOSTIC_MISMATCH",
        )
        require(
            tuple(e.seq for e in capture.events) == seqs
            and tuple(_semantic(e) for e in capture.events)
            == tuple(NORMAL_EFFECTS[n - 1] for n in seqs),
            "WRONG_STAGE_ROLE_OR_IDENTITY_SUBSTITUTION",
        )
        require(
            result.status == "BLOCKED"
            and result.actual_global_drops is None
            and all(v is False for _, v in result.permissions),
            "NO_AUTHORITY",
        )
        count += len(capture.events)
        failures.append(capture.failed)
        observed.append(result.root_creation_observed)
    return count, failures, observed


def validate_sources(
    data: Any, pristine_root: Path | None = None, patched_root: Path | None = None
) -> bool:
    require(digest(data) == SOURCE_DIGEST, "SOURCE_REFERENCE_DRIFT")
    require((pristine_root is None) == (patched_root is None), "BOTH_SOURCE_ROOTS_REQUIRED")
    if pristine_root is None or patched_root is None:
        return False
    for name, root in (("pristine_files", pristine_root), ("patched_files", patched_root)):
        for row in data[name]:
            with (root / row["path"]).open("rb") as stream:
                raw = stream.read(4 * 1024 * 1024 + 1)
            require(len(raw) <= 4 * 1024 * 1024, "SOURCE_BOUND")
            validate_source_record(row, raw)
    return True


def validate(
    pristine_root: Path | None = None,
    patched_root: Path | None = None,
    *,
    verify_assets: bool = False,
) -> dict[str, Any]:
    build, source = load(BUILD), load(SOURCES)
    validate_build(build)
    events, failures, observed = validate_actual(load(ACTUAL), BUILD.read_bytes())
    source_verified = validate_sources(source, pristine_root, patched_root)
    if verify_assets:
        records = [
            (ASSETS / build[n]["path"], build[n]) for n in ("kernel", "init", "actual_config")
        ]
        records += [
            (Path(build[n]["path"]), build[n])
            for n in (
                "baseline_kernel",
                "source_archive",
                "source_package",
                "dependency_index",
                "dependency_inrelease",
            )
        ]
        records += [
            (Path(r["path"]), r) for n in ("tools", "dependency_packages") for r in build[n]
        ]
        for path, row in records:
            with path.open("rb") as stream:
                sha = hashlib.file_digest(stream, "sha256").hexdigest()
            require(
                path.stat().st_size == row["bytes"] and sha == row["sha256"], "PREPARED_ASSET_DRIFT"
            )
        verify_vm(VM)
    return dict(
        actual_cases=3,
        raw_events=events,
        local_failures=failures,
        root_creation_observed=observed,
        baseline_missing_interface=True,
        kernel_source_bytes_verified=source_verified,
        source_files=(7, 9),
        source_ranges=43,
        assets_verified=verify_assets,
        status="BLOCKED",
        actual_global_drops=None,
        actual_prohibited_operations=None,
        runtime_qualified=False,
        permissions=dict(PERMISSIONS),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pristine-root", type=Path)
    parser.add_argument("--patched-root", type=Path)
    parser.add_argument("--verify-assets", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            validate(args.pristine_root, args.patched_root, verify_assets=args.verify_assets),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
