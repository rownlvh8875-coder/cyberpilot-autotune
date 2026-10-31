"""Offline frozen original-byte replay; no build,VM,synthetic or authority bridge."""

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

from .contracts import CASES
from .model import assess
from .runner import ASSETS, IMAGE_SHA, ROOT, VM
from .wire import parse_serial

BUILD = ROOT / "docs/evidence/guest_bootstrap_build.json"
ACTUAL = ROOT / "docs/evidence/guest_bootstrap_actual.json"
SOURCES = ROOT / "docs/evidence/guest_bootstrap_sources.json"
BUILD_DIGEST = "73397bf232b2d67079e61fb349979a4fa11ccd08a046bc882818205a0aff9f72"
ACTUAL_DIGEST = "59f6e5d611796e4fbb0d30d2eb56ae96b54827f9be7d4edf589a723ebd1c1fbb"
SOURCE_DIGEST = "1552ce47223de3e54006face5255200ec411988b59c1e0a612437e1ec82af54e"
IMAGE_BYTES = (336451, 336455, 336458, 336454, 336458, 336461, 336465, 336459, 336453, 336454)
ATTEMPTS = (472, 472, 472, 7, 471, 473, 473, 280, 472, 277)
FAILURES = (0, 1, 344, 0, 0, 0, 0, 0, 0, 0)
COMMITTED = ((1, 2), (1, 2), (), (), (1, 2), (1, 2), (1, 2), (1,), (1,), (1,))
LINK_COUNTS = (8, 6, 0, 0, 7, 8, 8, 8, 8, 8)
# Independent literal wire examples were written before the source hooks.
# Sorted raw token dictionaries only; never run actual records through PR41's oracle.
SEMANTIC_SHA = (
    "0679d67ba321e8a72c07f9cb2a2b02500aee76ceec3ece84be667b095d98462e",
    "7753d8a2f18e6d3360a879823c44d789d99e7eeafea3746b6b98b7c35097f54c",
    "ead4db99e2599977c32e9e4d418d86b9173585709491a7ea3e50197e0f474765",
    "d6d8dc0b2c5892ce3ac918c2bdb76db82f10e97e0c453cc76cc508a9869c8daf",
    "38943565dc8c885ee7de9cb2eba15041b0a20bff84fca60b5b99e386376e307f",
    "5647c7d8a6d8ce29bf236005f94a6191b4c8c4f886289a3d2473e7e913aeacd6",
    "1eb8ff33dc0eb6d88ea3ee02c01dfd29d9a0ffb0f3a60184f91f8fba4cd3d39a",
    "15ea67703e8b565274c2b4fb8207d275960bb2ec3d2e16a4289ceffdf99b2837",
    "3067bedb94860ec86012f656ead61512c0c4caf5d675e22f54c1fde992e7318b",
    "6bd97e922eed9005b89ddfe8f9bc4bbc71d161602ec8432ec423a6e385202f17",
)


def validate_build(data: Any) -> None:
    require(digest(data) == BUILD_DIGEST, "FIXED_BUILD_COHORT_DRIFT")
    for row in data["sources"]:
        _record(row, row["path"], (ROOT / row["path"]).read_bytes())


def validate_actual(data: Any, build_raw: bytes) -> dict[str, Any]:
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
        data["schema"] == "guest-bootstrap-actual-v1"
        and data["evidence_class"] == "OBSERVED_UNTRUSTED"
        and data["runtime_qualified"] is False
        and data["build_manifest_sha256"] == hashlib.sha256(build_raw).hexdigest(),
        "UNQUALIFIED_EXACT_CAPTURE_COHORT",
    )
    shape(data["baseline"], {"serial", "serial_base64", "expected"})
    baseline = _serial(data["baseline"], "baseline-serial.txt")
    require(
        data["baseline"]["expected"] == "MISSING_EXPERIMENTAL_CONTROL_INTERFACE"
        and b"CPB_UNAVAILABLE errno=2" in baseline
        and b"CPB_DRIVER ok=1" not in baseline,
        "ACTUAL_NEGATIVE_BASELINE_REQUIRED",
    )
    rows = data["captures"]
    require(type(rows) is list and len(rows) == 10, "FIXED_TEN_CAPTURES_REQUIRED")
    total = 0
    failures, links, unknown, missing, sequences = [], [], [], [], []
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
            if line.startswith(b"CPB_EVENT ")
        ]
        require(digest(tokens) == SEMANTIC_SHA[i], "WRONG_ORIGIN_IDENTITY_STAGE_OR_CONTEXT")
        require(
            capture.case == case
            and capture.attempted == ATTEMPTS[i]
            and capture.failed == FAILURES[i]
            and result.local_accounting_balanced
            and capture.root_id == (None if i == 3 else 7 if i == 4 else 8)
            and result.committed_stage_sequences == COMMITTED[i]
            and result.seed_walk_recorded_complete is (i != 3)
            and len(result.seed_to_first_copy_links) == LINK_COUNTS[i]
            and result.unknown_present_count == (2 if i == 4 else 0)
            and result.missing_origin_witness_ids == ((6,) if i == 1 else ()),
            "ACTUAL_FIXED_DIAGNOSTIC_MISMATCH",
        )
        require(
            result.status == "BLOCKED"
            and result.evidence_class == "OBSERVED_UNTRUSTED"
            and not result.allocation_history_complete
            and not result.atomic_cut_proven
            and not result.runtime_qualified
            and result.actual_global_drops is None
            and result.actual_prohibited_operations is None
            and all(v is False for _, v in result.permissions),
            "NO_RUNTIME_AUTHORITY",
        )
        total += len(capture.events)
        failures.append(capture.failed)
        links.append(len(result.seed_to_first_copy_links))
        unknown.append(result.unknown_present_count)
        missing.append(list(result.missing_origin_witness_ids))
        sequences.append(list(result.committed_stage_sequences))
    # Freeze original byte cohort INCLUDING nonce/boot annotations,not just semantics.
    # This hash is content identity,never authenticity/freshness/authorization.
    require(digest(data) == ACTUAL_DIGEST, "FROZEN_ORIGINAL_CAPTURE_BYTES_CHANGED")
    return dict(
        actual_cases=10,
        raw_events=total,
        local_failures=failures,
        first_copy_link_counts=links,
        unknown_present_reads=unknown,
        missing_origin_witness_ids=missing,
        committed_stage_sequences=sequences,
    )


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
    report = validate_actual(load(ACTUAL), BUILD.read_bytes())
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
    report.update(
        source_bytes_verified=source_verified,
        source_files=(7, 10),
        source_ranges=45,
        assets_verified=verify_assets,
        evidence_class="OBSERVED_UNTRUSTED",
        status="BLOCKED",
        allocation_history_complete=False,
        atomic_cut_proven=False,
        runtime_qualified=False,
        actual_global_drops=None,
        actual_prohibited_operations=None,
        permissions=dict(PERMISSIONS),
    )
    return report


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
