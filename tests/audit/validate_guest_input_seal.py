"""Offline byte/range and fixed diagnostic replay; no qualification or execution."""

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from compatibility.guest_input_seal.contracts import CASES
from compatibility.guest_input_seal.evaluation import evaluate
from compatibility.guest_input_seal.vm_runner import ROOT, validate_build_manifest
from compatibility.guest_input_seal.wire import parse_guest_capture


def validate_evidence(evidence: Any, manifest: dict[str, Any], manifest_raw: bytes) -> int:
    if (
        type(evidence) is not dict
        or set(evidence)
        != {"schema", "binary", "capture_source_manifest_sha256", "captures", "runtime_qualified"}
        or evidence["schema"] != "guest-input-seal-actual-v1"
        or evidence["runtime_qualified"] is not False
        or evidence["binary"] != manifest.get("binary")
        or evidence["capture_source_manifest_sha256"] != hashlib.sha256(manifest_raw).hexdigest()
        or type(evidence["captures"]) is not list
        or len(evidence["captures"]) != 8
    ):
        raise ValueError("invalid/incomplete capture bundle")
    cases = []
    positive = 0
    for row in evidence["captures"]:
        if type(row) is not dict or set(row) != {"case", "bytes", "sha256", "serial_base64"}:
            raise ValueError("invalid capture row")
        raw = base64.b64decode(row["serial_base64"], validate=True)
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("raw serial identity changed")
        text = raw.decode("utf-8", errors="strict")
        capture = parse_guest_capture(text)
        decision = evaluate(capture)
        if capture.case != row["case"] or not decision.scenario_recognized:
            raise ValueError("fixed diagnostic mismatch")
        positive += int(decision.object_seal_observed)
        cases.append(row["case"])
    if set(cases) != set(CASES) or len(set(cases)) != 8 or positive != 4:
        raise ValueError("missing/duplicate diagnostic cases")
    return positive


def validate(kernel_source: Path | None = None) -> dict[str, object]:
    package = ROOT / "compatibility/guest_input_seal"
    manifest_raw = (package / "guest/build_manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    validate_build_manifest(manifest)
    for row in manifest["sources"]:
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("local producer source changed")
    sources = json.loads((ROOT / "docs/evidence/guest_input_seal_sources.json").read_bytes())
    old = json.loads((ROOT / "docs/evidence/guest_collector_sources.json").read_bytes())
    if (
        sources["source_archive_sha256"] != old["source_archive_sha256"]
        or sources["authenticated_package"] != old["authenticated_package"]
        or sources["runtime_qualified"] is not False
    ):
        raise ValueError("kernel component identity/qualification changed")
    if kernel_source is not None:
        for row in sources["files"]:
            raw = (kernel_source / row["path"]).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if (
                len(raw) != row["bytes"]
                or hashlib.sha256(raw).hexdigest() != row["sha256"]
                or blob != row["git_blob_sha1"]
            ):
                raise ValueError("kernel file/blob changed")
            lines = raw.splitlines(keepends=True)
            for claim in row["ranges"]:
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
    positive = validate_evidence(evidence, manifest, manifest_raw)
    return {
        "local_sources_verified": True,
        "kernel_source_bytes_verified": kernel_source is not None,
        "kernel_files": len(sources["files"]),
        "ranges": sum(len(r["ranges"]) for r in sources["files"]),
        "actual_capture_replays": 8,
        "scoped_object_seal_observations": positive,
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
