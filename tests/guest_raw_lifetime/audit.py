"""Offline fixed source/artifact replay. No guest execution or qualification."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from compatibility.containment_backend_harmless.vm_runner import verify_vm
from tests.audit.fd_ofd_lifetime_model import shape
from tests.audit.validate_fd_ofd_lifetime_design import validate_source_record
from tests.audit.validate_kernel_lifetime_feasibility import load

from .model import CASES, RawEvent, assess, parse_serial, require
from .runner import ASSETS, IMAGE_SHA, ROOT, VM

BUILD = ROOT / "docs/evidence/guest_raw_lifetime_build.json"
ACTUAL = ROOT / "docs/evidence/guest_raw_lifetime_actual.json"
SOURCES = ROOT / "docs/evidence/guest_raw_lifetime_sources.json"
BUILD_DIGEST = "99475c83f2b52bc8ae14f26fa70289a93c9a746c6d0d17a03b752c913ccdfac5"
SOURCE_DIGEST = "1b9df1083bc06703ef4bd9057d9c9c91cb74bedce5af66a62c22508ac3cfa4de"
IMAGE_BYTES = (335986, 335992, 335995)


def digest(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def validate_build(data: Any) -> None:
    # Exact finite prototype, not a generic build-schema validator or authority.
    require(digest(data) == BUILD_DIGEST, "FIXED_BUILD_COHORT_DRIFT")
    for row in data["sources"]:
        raw = (ROOT / row["path"]).read_bytes()
        require(
            len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "PRODUCER_SOURCE_CHANGED",
        )


def _record(data: Any, path: str, raw: bytes | None = None) -> None:
    shape(data, {"path", "bytes", "sha256"})
    require(
        data["path"] == path
        and type(data["bytes"]) is int
        and 0 <= data["bytes"] < 2**64
        and type(data["sha256"]) is str
        and len(data["sha256"]) == 64
        and all(c in "0123456789abcdef" for c in data["sha256"]),
        "EXACT_BYTE_RECORD",
    )
    if raw is not None:
        require(
            len(raw) == data["bytes"] and hashlib.sha256(raw).hexdigest() == data["sha256"],
            "ORIGINAL_BYTES_CHANGED",
        )


def _serial(row: Any, label: str) -> bytes:
    require(
        type(row["serial_base64"]) is str and len(row["serial_base64"]) <= 1400000,
        "SERIAL_ENCODING_BOUND",
    )
    try:
        raw = base64.b64decode(row["serial_base64"], validate=True)
    except ValueError as exc:
        raise ValueError("INVALID_ORIGINAL_SERIAL_ENCODING") from exc
    require(len(raw) <= 1024 * 1024, "SERIAL_BOUND")
    _record(row["serial"], label, raw)
    return raw


def _semantic(e: RawEvent) -> tuple[object, ...]:
    return e.kind, e.table_id, e.file_id, e.old_id, e.fd, e.flags


# Source/driver-specific expected effects, independently literal, not inferred IDs.
NORMAL_EFFECTS = (
    ("FILE_NEW", None, 1, None, None, 0),
    ("INSTALL", None, 1, None, 5, 1),
    ("REPLACE", None, 1, None, 40, 0),
    ("FLAGS", None, 1, None, 40, 1),
    ("REPLACE", None, 1, 1, 40, 1),
    ("TABLE_NEW", 2, None, None, None, 0),
    ("CLOSE", 2, 1, None, 5, 0),
    ("CLOSE", 2, 1, None, 40, 0),
    ("TABLE_FREE", 2, None, None, None, 0),
    ("CLOSE", None, 1, None, 5, 0),
    ("CLOSE", None, 1, None, 40, 0),
    ("FILE_FREE", None, 1, None, None, 0),
)


def validate_actual(data: Any, build_raw: bytes) -> tuple[int, list[int]]:
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
        data["schema"] == "guest-raw-lifetime-actual-v1"
        and data["evidence_class"] == "OBSERVED_UNTRUSTED"
        and data["runtime_qualified"] is False
        and data["build_manifest_sha256"] == hashlib.sha256(build_raw).hexdigest(),
        "UNQUALIFIED_EXACT_CAPTURE_COHORT",
    )
    shape(data["baseline"], {"serial", "serial_base64", "expected"})
    require(
        data["baseline"]["expected"] == "MISSING_EXPERIMENTAL_CONTROL_INTERFACE",
        "ACTUAL_NEGATIVE_BASELINE_REQUIRED",
    )
    baseline = _serial(data["baseline"], "baseline-serial.txt")
    require(
        b"CPL_UNAVAILABLE errno=2" in baseline and b"CPL_DRIVER ok=1" not in baseline,
        "ACTUAL_NEGATIVE_BASELINE_REQUIRED",
    )
    rows = data["captures"]
    require(type(rows) is list and len(rows) == 3, "FIXED_THREE_CAPTURES_REQUIRED")
    count, failures = 0, []
    for index, (row, case) in enumerate(zip(rows, CASES, strict=True)):
        shape(row, {"case", "serial", "serial_base64", "image"})
        require(row["case"] == case, "FIXED_CASE_ORDER")
        raw = _serial(row, "final-" + case + "-serial.txt")
        _record(row["image"], case + "-initrd.gz")
        require(
            row["image"]["sha256"] == IMAGE_SHA[case]
            and row["image"]["bytes"] == IMAGE_BYTES[index],
            "FIXED_IMAGE_COHORT",
        )
        captured = parse_serial(raw)
        result = assess(captured)
        require(
            captured.case == case
            and captured.attempted == 12
            and captured.failed == (0, 1, 10)[index]
            and result.local_accounting_balanced,
            "ACTUAL_FIXED_DIAGNOSTIC_MISMATCH",
        )
        expected_seq = (tuple(range(1, 13)), (1, *range(3, 13)), (1, 2))[index]
        require(
            tuple(e.seq for e in captured.events) == expected_seq
            and tuple(_semantic(e) for e in captured.events)
            == tuple(NORMAL_EFFECTS[n - 1] for n in expected_seq),
            "WRONG_STAGE_OR_IDENTITY_SUBSTITUTION",
        )
        require(
            result.status == "BLOCKED"
            and result.actual_global_drops is None
            and all(v is False for _, v in result.permissions),
            "NO_AUTHORITY",
        )
        count += len(captured.events)
        failures.append(captured.failed)
    return count, failures


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
    events, failures = validate_actual(load(ACTUAL), BUILD.read_bytes())
    source_verified = validate_sources(source, pristine_root, patched_root)
    if verify_assets:
        records = [
            (ASSETS / build[n]["path"], build[n])
            for n in ("kernel", "init", "actual_config", "baseline_kernel")
        ]
        records += [
            (Path(build[n]["path"]), build[n])
            for n in (
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
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            require(
                path.stat().st_size == row["bytes"] and actual == row["sha256"],
                "PREPARED_ASSET_DRIFT",
            )
        verify_vm(VM)
    return {
        "actual_cases": 3,
        "raw_events": events,
        "local_failures": failures,
        "baseline_missing_interface": True,
        "kernel_source_bytes_verified": source_verified,
        "source_files": (5, 7),
        "source_ranges": 22,
        "assets_verified": verify_assets,
        "status": "BLOCKED",
        "actual_global_drops": None,
        "runtime_qualified": False,
    }


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
