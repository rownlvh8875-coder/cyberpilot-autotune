"""Frozen source-byte/citation audit,not C semantics or runtime qualification."""

import argparse
import base64
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any

from tests.audit.fd_ofd_lifetime_model import need, shape
from tests.audit.validate_kernel_lifetime_feasibility import load

from .model import CLAIMS, BoundaryAudit, assess

ROOT = Path(__file__).resolve().parents[2]
BASE = "37c0e614f01e13b5e6078178b3712c0ec6ba4495"
SOURCES = ROOT / "docs/evidence/bootstrap_tag_initialization_sources.json"
RESULT = ROOT / "docs/evidence/bootstrap_tag_initialization_result.json"
SOURCE_DIGEST = "4b0712a7d12069a74032f8f9f91861bf22397436927a278818968d9f647930af"
RESULT_DIGEST = "fa31c1cb5f87a523ffa915497874cb07b9e91e9f9d856bbb6f6d1b370606dbea"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_RANGE_BYTES = 256 * 1024


def _digest(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _hex(value: Any, size: int) -> bool:
    return type(value) is str and re.fullmatch("[0-9a-f]{" + str(size) + "}", value) is not None


def _path(value: Any) -> str:
    need(
        type(value) is str
        and re.fullmatch(r"[A-Za-z0-9_/.-]{1,128}", value) is not None
        and not value.startswith("/")
        and ".." not in PurePosixPath(value).parts
        and str(PurePosixPath(value)) == value,
        "RELATIVE_SOURCE_PATH_REQUIRED",
    )
    return str(value)


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    need(len(raw) <= MAX_SOURCE_BYTES, "SOURCE_RESOURCE_BOUND")
    return raw


def verify_excerpt(span: Any) -> bytes:
    """Verify embedded bytes/claimed line count,not their C meaning or location."""
    shape(span, {"claim", "start", "end", "sha256", "source_base64"})
    need(
        type(span["claim"]) is str
        and re.fullmatch("[A-Z][A-Z0-9_]{0,63}", span["claim"]) is not None
        and type(span["start"]) is int
        and type(span["end"]) is int
        and 1 <= span["start"] <= span["end"] <= MAX_SOURCE_BYTES
        and _hex(span["sha256"], 64)
        and type(span["source_base64"]) is str
        and len(span["source_base64"]) <= MAX_RANGE_BYTES * 2,
        "SOURCE_EXCERPT_METADATA",
    )
    try:
        raw = base64.b64decode(span["source_base64"], validate=True)
    except ValueError as exc:
        raise ValueError("SOURCE_EXCERPT_ENCODING") from exc
    need(
        0 < len(raw) <= MAX_RANGE_BYTES
        and hashlib.sha256(raw).hexdigest() == span["sha256"]
        and len(raw.splitlines(keepends=True)) == span["end"] - span["start"] + 1,
        "SOURCE_EXCERPT_DRIFT",
    )
    return raw


def verify_source_file(root: Path, row: Any) -> None:
    """Standalone byte check only;the outer catalog freezes admitted paths/cohort."""
    need(type(row) is dict, "SOURCE_RECORD_REQUIRED")
    shape(
        row,
        {"path", "bytes", "sha256", "git_blob_sha1"} | ({"ranges"} if "ranges" in row else set()),
    )
    path = _path(row["path"])
    need(
        type(row["bytes"]) is int
        and 0 < row["bytes"] <= MAX_SOURCE_BYTES
        and _hex(row["sha256"], 64)
        and _hex(row["git_blob_sha1"], 40),
        "SOURCE_BLOB_METADATA",
    )
    raw = _read(root / path)
    need(
        row["bytes"] == len(raw)
        and row["sha256"] == hashlib.sha256(raw).hexdigest()
        and row["git_blob_sha1"]
        == hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "SOURCE_BLOB_DRIFT",
    )
    if "ranges" in row:
        need(
            type(row["ranges"]) is list and 0 < len(row["ranges"]) <= len(CLAIMS),
            "SOURCE_RANGES_REQUIRED",
        )
        lines = raw.splitlines(keepends=True)
        for span in row["ranges"]:
            chunk = verify_excerpt(span)
            need(b"".join(lines[span["start"] - 1 : span["end"]]) == chunk, "SOURCE_RANGE_DRIFT")


def validate_sources(
    data: Any, pristine_root: Path | None = None, patched_root: Path | None = None
) -> frozenset[str]:
    # Exact finite source profile BEFORE any metadata-derived filesystem read.
    need(_digest(data) == SOURCE_DIGEST, "SOURCE_CATALOG_DRIFT")
    need((pristine_root is None) == (patched_root is None), "BOTH_SOURCE_ROOTS_REQUIRED")
    need(data["base_revision"] == BASE, "SOURCE_REVISION_DRIFT")
    claims: set[str] = set()
    for row in data["patched_files"]:
        for span in row["ranges"]:
            verify_excerpt(span)
            need(span["claim"] not in claims, "DUPLICATE_SOURCE_CLAIM")
            claims.add(span["claim"])
    need(frozenset(claims) == CLAIMS, "CLAIM_COHORT")
    for row in data["repository_files"]:
        raw = _read(ROOT / _path(row["path"]))
        need(
            row["bytes"] == len(raw) and row["sha256"] == hashlib.sha256(raw).hexdigest(),
            "PR42_REPOSITORY_BYTES_CHANGED",
        )
    if pristine_root is not None and patched_root is not None:
        for name, root in (("pristine_files", pristine_root), ("patched_files", patched_root)):
            for row in data[name]:
                verify_source_file(root, row)
    return frozenset(claims)


def validate_result(data: Any, claims: frozenset[str]) -> BoundaryAudit:
    need(_digest(data) == RESULT_DIGEST, "RESULT_CATALOG_DRIFT")
    need(
        data["base_revision"] == BASE and data["source_catalog_digest"] == SOURCE_DIGEST,
        "RESULT_SOURCE_COHORT",
    )
    result = assess(data["boundaries"], claims)
    need(
        data["evidence_class"] == result.evidence_class
        and data["status"] == result.status
        and data["permissions"] == dict(result.permissions)
        and all(v is False for v in data["permissions"].values())
        and all(
            getattr(result, k) is False and v is False for k, v in data["qualification"].items()
        )
        and data["actual_global_drops"] is None
        and data["actual_prohibited_operations"] is None
        and data["prior_observations_reclassified"] is False,
        "SOURCE_AUDIT_HAS_NO_AUTHORITY",
    )
    return result


def validate(pristine_root: Path | None = None, patched_root: Path | None = None) -> dict[str, Any]:
    claims = validate_sources(load(SOURCES), pristine_root, patched_root)
    decision = validate_result(load(RESULT), claims)
    report = asdict(decision)
    report.update(
        subjects=len(decision.boundaries),
        open_obligations=sum(len(b.open_obligations) for b in decision.boundaries),
        source_files=dict(pristine=9, patched=11),
        embedded_source_ranges=len(claims),
        embedded_range_hashes_verified=True,
        external_source_bytes_verified=pristine_root is not None,
        source_interpretations_machine_proven=False,
        actual_runtime_executions_this_task=0,
        prior_observations_reclassified=False,
        source_catalog_digest=SOURCE_DIGEST,
        permissions=dict(decision.permissions),
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pristine-root", type=Path)
    parser.add_argument("--patched-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.pristine_root, args.patched_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
