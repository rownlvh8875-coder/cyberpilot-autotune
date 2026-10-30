"""Offline prototype content/range audit, never runtime/build qualification."""

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

from compatibility.guest_consumption.checks import check_case
from compatibility.guest_consumption.vm_runner import observation_from_log, validate_build_manifest

ROOT = Path(__file__).resolve().parents[2]


def validate(kernel_source: Path | None = None) -> dict[str, object]:
    package = ROOT / "compatibility/guest_consumption"
    raw_manifest = (package / "guest/build_manifest.json").read_bytes()
    manifest = json.loads(raw_manifest)
    validate_build_manifest(manifest)
    for record in manifest["sources"]:
        raw = (package / record["path"]).read_bytes()
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("local producer source changed")
    sources = json.loads((ROOT / "docs/evidence/guest_consumption_sources.json").read_text())
    old = json.loads((ROOT / "docs/evidence/guest_collector_sources.json").read_text())
    if (
        sources["source_archive_sha256"] != old["source_archive_sha256"]
        or sources["authenticated_package"] != old["authenticated_package"]
        or sources["runtime_qualified"] is not False
    ):
        raise ValueError("kernel component identity/qualification changed")
    if kernel_source is not None:
        for record in sources["files"]:
            raw = (kernel_source / record["path"]).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if (
                len(raw) != record["bytes"]
                or hashlib.sha256(raw).hexdigest() != record["sha256"]
                or blob != record["git_blob_sha1"]
            ):
                raise ValueError("kernel file/blob identity changed")
            lines = raw.splitlines(keepends=True)
            for claim in record["ranges"]:
                if (
                    not 1 <= claim["start"] <= claim["end"] <= len(lines)
                    or hashlib.sha256(
                        b"".join(lines[claim["start"] - 1 : claim["end"]])
                    ).hexdigest()
                    != claim["sha256"]
                ):
                    raise ValueError("kernel semantic range changed")
    evidence = json.loads(
        gzip.decompress((package / "evidence/actual-captures.json.gz").read_bytes())
    )
    if (
        evidence["binary"] != manifest["binary"]
        or evidence["capture_source_manifest_sha256"] != hashlib.sha256(raw_manifest).hexdigest()
    ):
        raise ValueError("capture source/binary cohort mismatch")
    for record in evidence["captures"]:
        raw = base64.b64decode(record["serial_base64"], validate=True)
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("serial evidence changed")
        observed = observation_from_log(
            raw.decode(), manifest["binary"]["sha256"], manifest["binary"]["bytes"]
        )
        if observed.capture.case != record["case"] or check_case(observed, record["case"]):
            raise ValueError("fixed fixture observation mismatch")
    if {r["case"] for r in evidence["captures"]} != {f"CP{i:02d}" for i in range(1, 8)} or len(
        evidence["captures"]
    ) != 7:
        raise ValueError("capture set incomplete/duplicated")
    return {
        "local_sources_verified": True,
        "kernel_source_bytes_verified": kernel_source is not None,
        "kernel_files": len(sources["files"]),
        "ranges": sum(len(r["ranges"]) for r in sources["files"]),
        "actual_capture_replays": 7,
        "runtime_qualified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-source", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.kernel_source), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
