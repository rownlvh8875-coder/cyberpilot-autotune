"""Portable frozen metadata checks; explicit roots verify bytes, never runtime."""

import argparse
import json
from pathlib import Path
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need
from tests.bootstrap_tag_audit.audit import _digest, verify_excerpt, verify_source_file
from tests.copy_reference_audit.audit import (
    ROOT,
    load_catalog,
)
from tests.copy_reference_audit.audit import (
    SOURCES as REFERENCE_SOURCES,
)
from tests.copy_reference_audit.audit import (
    validate_sources as validate_reference_sources,
)

from .cohort import BUILD_DIGEST, SOURCE_DIGEST

SOURCES = ROOT / "docs/evidence/guest_epoch_u64_sources.json"
BUILD = ROOT / "docs/evidence/guest_epoch_u64_build.json"
CHANGED = frozenset({"include/linux/cptagread.h", "fs/proc/cpcopy.c"})


def validate_sources(data: Any, source_root: Path | None = None) -> None:
    need(_digest(data) == SOURCE_DIGEST, "SOURCE_CATALOG_DRIFT")
    reference = load_catalog(REFERENCE_SOURCES)
    validate_reference_sources(reference)
    for row in data["kernel_files"]:
        for span in row["ranges"]:
            verify_excerpt(span)
        if source_root is not None:
            verify_source_file(source_root, row)
    for row in data["repository_files"] + data["patch_chain"]:
        verify_source_file(ROOT, row)
    native = load_catalog(ROOT / "tests/guest_epoch_u64/native_inputs.json")
    need(native["files"] == data["kernel_files"][:3], "EXACT_NATIVE_SOURCE_EXCERPTS")
    if source_root is not None:
        for row in reference["kernel_files"]:
            if row["path"] not in CHANGED:
                verify_source_file(source_root, row)


def validate_build(data: Any, assets_root: Path | None = None) -> None:
    need(_digest(data) == BUILD_DIGEST, "BUILD_CATALOG_DRIFT")
    need(
        data["source_catalog_digest"] == SOURCE_DIGEST
        and data["runtime_qualified"] is data["build_input_closure_qualified"] is False
        and data["actual_v2_capture_available"] is False
        and data["permissions"] == dict(PERMISSIONS),
        "NO_OFFLINE_BUILD_AUTHORITY",
    )
    if assets_root is not None:
        for row in data["assets"]:
            verify_source_file(assets_root, row)


def validate(source_root: Path | None = None, assets_root: Path | None = None) -> dict[str, Any]:
    sources, build = load_catalog(SOURCES), load_catalog(BUILD)
    validate_sources(sources, source_root)
    validate_build(build, assets_root)
    return dict(
        evidence_class="STATIC_SOURCE_BUILD_AUDIT_ONLY",
        status="BLOCKED",
        source_bytes_verified=source_root is not None,
        build_assets_bytes_verified=assets_root is not None,
        source_catalog_digest=SOURCE_DIGEST,
        build_catalog_digest=BUILD_DIGEST,
        offline_build_evidence_recorded=True,
        source_interpretations_machine_proven=False,
        toolchain_bytes_reverified=False,
        build_input_closure_qualified=False,
        runtime_qualified=False,
        actual_v2_capture_available=False,
        actual_guest_executions_this_task=0,
        actual_epoch_loss=None,
        actual_global_drops=None,
        permissions=dict(PERMISSIONS),
        kernel_files=len(sources["kernel_files"]),
        embedded_ranges=sum(len(row["ranges"]) for row in sources["kernel_files"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--assets-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.source_root, args.assets_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
