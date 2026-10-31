"""Offline original-byte replay; no producer, synthetic admission or qualification."""

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
from tests.guest_raw_lifetime.model import PERMISSIONS, require

from .model import CASES, assess, parse_serial
from .runner import ASSETS, IMAGE_SHA, ROOT, VM

BUILD = ROOT / "docs/evidence/guest_fork_copy_build.json"
ACTUAL = ROOT / "docs/evidence/guest_fork_copy_actual.json"
SOURCES = ROOT / "docs/evidence/guest_fork_copy_sources.json"
BUILD_DIGEST = "2a417b806377f3c4cc3248bc2dbbd558652aefe2eb36e485d9263b0301dfbe81"
SOURCE_DIGEST = "052c163c802505b5a96a33d6e0d75aa016fdfb6bdcbbbd32299db9efe8e1f0a2"
IMAGE_BYTES = (336170, 336174, 336177, 336178, 336173, 336173)
# Raw token dictionaries from literal expected wire written before source hooks.
# This comparison never converts observed records to the old synthetic oracle.
SEMANTIC_SHA = (
    "6189a803f78826106614c0b81ed442af92f7f87aae0617043b855445849ae5ca",
    "adf76f6b8d8115f5952fd1e2f0ef67be58f1b58843ae2760840acfde46f18085",
    "39ca7efca26dc368a748bae32aecccdd12fdd6e4650036cbec4bed8a2edfff1a",
    "0a493877e812a9f6f7ad5dec6f67ae9431dabbaec1b6e9ff54adafad5d12088f",
    "61c4b7bc4eb6c9ac7ad485ed8ff1b217d77a66095add501eb07ce9b6ee32359e",
    "e69f640f4d13e690d72980f133dfd798ba6e08dc8313713291c41899c1c7778c",
)


def validate_build(data: Any) -> None:
    require(digest(data) == BUILD_DIGEST, "FIXED_BUILD_COHORT_DRIFT")
    for row in data["sources"]:
        _record(row, row["path"], (ROOT / row["path"]).read_bytes())


def validate_actual(data: Any, build_raw: bytes) -> tuple[int, list[int], list[list[int]]]:
    validate_build(json.loads(build_raw))
    shape(
        data,
        {
            "schema",
            "evidence_class",
            "runtime_qualified",
            "build_manifest_sha256",
            "baseline",
            "captures",
        },
    )
    require(
        data["schema"] == "guest-fork-copy-actual-v1"
        and data["evidence_class"] == "OBSERVED_UNTRUSTED"
        and data["runtime_qualified"] is False
        and data["build_manifest_sha256"] == hashlib.sha256(build_raw).hexdigest(),
        "UNQUALIFIED_EXACT_CAPTURE_COHORT",
    )
    shape(data["baseline"], {"serial", "serial_base64", "expected"})
    baseline = _serial(data["baseline"], "baseline-serial.txt")
    require(
        data["baseline"]["expected"] == "MISSING_EXPERIMENTAL_CONTROL_INTERFACE"
        and b"CPC_UNAVAILABLE errno=2" in baseline
        and b"CPC_DRIVER ok=1" not in baseline,
        "ACTUAL_NEGATIVE_BASELINE_REQUIRED",
    )
    rows = data["captures"]
    require(type(rows) is list and len(rows) == 6, "FIXED_SIX_CAPTURES_REQUIRED")
    total, failures, sequences = 0, [], []
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
        tokens = [
            dict(t.split("=") for t in line.decode().split()[1:])
            for line in raw.splitlines()
            if line.startswith(b"CPC_EVENT ")
        ]
        require(digest(tokens) == SEMANTIC_SHA[i], "WRONG_STAGE_ROLE_IDENTITY_OR_INJECTION")
        expected = ((1, 2), (1,), (), (1,), (1,), (1,))[i]
        require(
            capture.case == case
            and capture.copies == 2
            and capture.attempted == (392, 392, 392, 200, 392, 198)[i]
            and capture.failed == (0, 1, 264, 0, 0, 0)[i]
            and result.local_accounting_balanced
            and result.committed_stage_sequences == expected
            and result.identity_complete is False,
            "ACTUAL_FIXED_DIAGNOSTIC_MISMATCH",
        )
        require(
            result.status == "BLOCKED"
            and not result.runtime_qualified
            and not result.atomic_cut_proven
            and result.actual_global_drops is None
            and all(v is False for _, v in result.permissions),
            "NO_AUTHORITY",
        )
        total += len(capture.events)
        failures.append(capture.failed)
        sequences.append(list(expected))
    return total, failures, sequences


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
    build = load(BUILD)
    validate_build(build)
    events, failures, sequences = validate_actual(load(ACTUAL), BUILD.read_bytes())
    source_verified = validate_sources(load(SOURCES), pristine_root, patched_root)
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
        actual_cases=6,
        raw_copy_records=events,
        local_failures=failures,
        committed_stage_sequences=sequences,
        identity_complete=[False] * 6,
        baseline_missing_interface=True,
        source_bytes_verified=source_verified,
        source_files=(7, 10),
        source_ranges=57,
        assets_verified=verify_assets,
        evidence_class="OBSERVED_UNTRUSTED",
        status="BLOCKED",
        actual_global_drops=None,
        actual_prohibited_operations=None,
        atomic_cut_proven=False,
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
