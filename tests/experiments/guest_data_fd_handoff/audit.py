"""Offline exact source/capture replay, not runtime or executor qualification."""

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from compatibility.guest_input_closure.filesystem import read_regular
from compatibility.guest_input_closure.inventory import unique_object

from .model import CASES as CASES
from .model import PERMISSIONS as PERMISSIONS
from .model import check_case, parse_serial, require, sha

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "tests/experiments/guest_data_fd_handoff/"
SOURCES = tuple(
    PREFIX + name
    for name in (
        "__init__.py",
        "model.py",
        "runner.py",
        "audit.py",
        "guest/probe.c",
    )
) + (
    "compatibility/guest_consumption/guest/sha256.h",
    "compatibility/guest_consumption/vm_runner.py",
    "compatibility/guest_input_seal/vm_runner.py",
)
BUILD = "docs/evidence/guest_data_fd_handoff_build.json"
EVIDENCE = "docs/evidence/guest_data_fd_handoff_actual.json.gz"
ASSETS = Path("/workspace/scratch/data-fd-handoff-producer.xax7ID")
VM_DIGEST = "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c"


def uint(value: Any) -> None:
    require(type(value) is int and 0 <= value < 2**64, "exact unsigned integer")


def record(value: Any, expected: str) -> None:
    require(
        type(value) is dict
        and set(value) == {"path", "bytes", "sha256"}
        and value["path"] == expected,
        "fixed path record",
    )
    uint(value["bytes"])
    sha(value["sha256"])


def validate_build(data: Any) -> None:
    require(
        type(data) is dict
        and set(data)
        == {
            "schema",
            "base_revision",
            "vm_cohort_digest",
            "binary",
            "sources",
            "build_command",
            "permissions",
            "build_input_closure_qualified",
        },
        "fixed build manifest",
    )
    require(
        data["schema"] == "guest-data-fd-handoff-build-v1"
        and data["base_revision"] == "74e3fdc67c2695a48035bf51758721f48bd5ae05"
        and data["vm_cohort_digest"] == VM_DIGEST
        and data["build_input_closure_qualified"] is False,
        "unqualified fixed build cohort",
    )
    require(
        type(data["permissions"]) is dict
        and set(data["permissions"]) == dict(PERMISSIONS).keys()
        and all(v is False for v in data["permissions"].values()),
        "all operational permissions fixed false",
    )
    record(data["binary"], "data-fd-handoff-probe")
    require(
        type(data["sources"]) is list and len(data["sources"]) == len(SOURCES),
        "complete fixed source vector",
    )
    for row, path in zip(data["sources"], SOURCES, strict=True):
        record(row, path)
    require(
        type(data["build_command"]) is str and 0 < len(data["build_command"]) < 2048,
        "actual build command record",
    )


def validate_evidence(data: Any, manifest: dict[str, Any], manifest_raw: bytes) -> tuple[int, int]:
    validate_build(manifest)
    require(
        type(data) is dict
        and set(data)
        == {"schema", "binary", "capture_source_manifest_sha256", "captures", "runtime_qualified"}
        and data["schema"] == "guest-data-fd-handoff-actual-v1"
        and data["runtime_qualified"] is False
        and data["binary"] == manifest["binary"]
        and data["capture_source_manifest_sha256"] == hashlib.sha256(manifest_raw).hexdigest(),
        "unqualified exact capture cohort",
    )
    require(
        type(data["captures"]) is list and len(data["captures"]) == 9,
        "all nine fixed actual captures",
    )
    positive = 0
    for row, case in zip(data["captures"], CASES, strict=True):
        require(
            type(row) is dict
            and set(row) == {"case", "bytes", "sha256", "serial_base64", "image_sha256"}
            and row["case"] == case,
            "unique ordered fixed captures",
        )
        uint(row["bytes"])
        sha(row["sha256"])
        sha(row["image_sha256"])
        require(
            type(row["serial_base64"]) is str and len(row["serial_base64"]) <= 1400000,
            "bounded original serial",
        )
        try:
            raw = base64.b64decode(row["serial_base64"], validate=True)
        except ValueError as exc:
            raise ValueError("invalid original capture encoding") from exc
        require(
            len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "original serial bytes changed",
        )
        checked = check_case(parse_serial(raw, case), manifest["binary"]["sha256"])
        require(
            checked.transport_observed == (case in ("HH01", "HH07", "HH08", "HH09")),
            "actual fixed diagnostic does not match expected observation",
        )
        positive += int(checked.transport_observed)
    return 9, positive


def _read(root: Path, path: str, limit: int, anchored: bool = False) -> bytes:
    if anchored:
        return read_regular(root, path, limit)
    # Offline replay, never execution-time sealing. Fixed manifest paths only.
    value = (root / path).read_bytes()
    require(len(value) <= limit, "offline input bound")
    return value


def load_build(*, anchored: bool = False) -> tuple[dict[str, Any], bytes]:
    raw = _read(ROOT, BUILD, 1024 * 1024, anchored)
    data = json.loads(raw, object_pairs_hook=unique_object)
    validate_build(data)
    for row in data["sources"]:
        value = _read(ROOT, row["path"], 4 * 1024 * 1024, anchored)
        require(
            len(value) == row["bytes"] and hashlib.sha256(value).hexdigest() == row["sha256"],
            "producer source changed",
        )
    return data, raw


def validate_kernel_record(row: dict[str, Any], raw: bytes) -> None:
    require(
        type(row) is dict and set(row) == {"path", "bytes", "sha256", "git_blob_sha1", "ranges"},
        "kernel source record",
    )
    uint(row["bytes"])
    require(
        row["bytes"] == len(raw)
        and row["sha256"] == hashlib.sha256(raw).hexdigest()
        and row["git_blob_sha1"]
        == hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "exact kernel file/blob required",
    )
    require(type(row["ranges"]) is list and bool(row["ranges"]), "semantic ranges required")
    lines = raw.split(b"\n")
    for claim in row["ranges"]:
        require(
            type(claim) is dict and set(claim) == {"claim", "start", "end", "sha256"},
            "kernel range claim",
        )
        start, stop = claim["start"], claim["end"]
        uint(start)
        uint(stop)
        require(
            1 <= start <= stop < len(lines)
            and hashlib.sha256(b"\n".join(lines[start - 1 : stop]) + b"\n").hexdigest()
            == claim["sha256"],
            "exact source semantic range required",
        )


KERNEL_FILES = frozenset(
    {
        "fs/proc/fd.c",
        "kernel/kcmp.c",
        "kernel/pid.c",
        "fs/file.c",
        "fs/exec.c",
        "include/uapi/linux/kcmp.h",
        "mm/memfd.c",
        "include/uapi/linux/memfd.h",
    }
)


def validate_kernel(root: Path | None) -> tuple[int, int]:
    data = json.loads(
        _read(ROOT, "docs/evidence/guest_data_fd_handoff_sources.json", 1024 * 1024),
        object_pairs_hook=unique_object,
    )
    require(
        data["source_archive_sha256"]
        == "ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33"
        and data["runtime_qualified"] is False
        and {r["path"] for r in data["files"]} == KERNEL_FILES
        and len(data["files"]) == len(KERNEL_FILES),
        "fixed Debian source reference cohort",
    )
    if root is not None:
        for row in data["files"]:
            validate_kernel_record(row, _read(root, row["path"], 4 * 1024 * 1024))
    return len(data["files"]), sum(len(r["ranges"]) for r in data["files"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-source", type=Path)
    args = parser.parse_args()
    files, ranges = validate_kernel(args.kernel_source)
    print(
        json.dumps(
            {
                "source_files": files,
                "source_ranges": ranges,
                "source_bytes_verified": args.kernel_source is not None,
            }
        )
    )
    manifest, raw = load_build()
    evidence = json.loads(
        gzip.decompress(_read(ROOT, EVIDENCE, 1024 * 1024)), object_pairs_hook=unique_object
    )
    count, positive = validate_evidence(evidence, manifest, raw)
    print(
        json.dumps(
            {
                "actual_replays": count,
                "scoped_transports": positive,
                "status": "BLOCKED",
                "runtime_qualified": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
