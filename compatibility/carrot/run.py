"""Explicit developer preflight then offline tests; never imported by the adapter."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_reference(reference):
    evidence = json.loads(
        (ROOT / "docs/evidence/carrot_phase8b_schema_compatibility.json").read_text(
            encoding="utf-8"
        )
    )

    def git(*args):
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={reference}", *args], cwd=reference
        )

    merge = evidence["integration_merge"]
    source = evidence["source_revision"]
    hyundai = json.loads(
        (ROOT / "docs/evidence/hyundai_santafe_override_capability.json").read_text(
            encoding="utf-8"
        )
    )
    runtime = json.loads(
        (ROOT / "docs/evidence/carrot_phase8b2a_runtime_contract.json").read_text(encoding="utf-8")
    )
    assert runtime["source_revision"] == source and runtime["integration_revision"] == merge
    assert (hyundai["source_revision"], hyundai["integration_merge"], hyundai["original_base"]) == (
        source,
        merge,
        evidence["original_base"],
    )
    assert git("rev-parse", "HEAD").decode().strip() == merge
    assert git("show", "-s", "--format=%P", merge).decode().strip().split() == [
        evidence["original_base"],
        source,
    ]
    assert git("rev-parse", merge + "^{tree}") == git("rev-parse", source + "^{tree}")
    assert git("diff", "--name-only").strip() == b""
    for item in evidence["schema_files"] + hyundai["source_files"] + runtime["source_files"]:
        data = git("show", source + ":" + item["path"])
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert (reference / item["path"]).read_bytes() == data
        lines = data.splitlines(keepends=True)
        for span in item.get("inspected_ranges", ()):
            inspected = b"".join(lines[span["start_line"] - 1 : span["end_line"]])
            assert hashlib.sha256(inspected).hexdigest() == span["sha256"]
    for fixture in runtime["actual_schema_fixtures"]:
        raw = (ROOT / fixture["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == fixture["sha256"]
        cases = json.loads(raw)["cases"]
        assert fixture["expected_result_hashes"] == [
            dict(
                id=case["id"],
                sha256=hashlib.sha256(
                    json.dumps(
                        case["expected"], sort_keys=True, separators=(",", ":"), allow_nan=False
                    ).encode()
                ).hexdigest(),
            )
            for case in cases
        ]
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", required=True, type=Path)
    parser.add_argument("--sidecar-only", action="store_true")
    args = parser.parse_args()
    reference = args.reference_checkout.resolve()
    verify_reference(reference)
    sys.path.insert(0, str(reference))
    os.environ["CARROT_REFERENCE_CHECKOUT"] = str(reference)
    sys.dont_write_bytecode = True

    def no_network(event, args):
        # Coverage uses the local hostname for a private data-file suffix; it
        # performs no socket/DNS/network operation. All actual socket IO is denied.
        if event.startswith("socket.") and event != "socket.gethostname":
            raise AssertionError("NETWORK_FORBIDDEN_AFTER_SETUP")

    sys.addaudithook(no_network)
    import pytest

    paths = [str(ROOT / "tests"), str(ROOT / "compatibility/carrot")]
    if args.sidecar_only:
        paths = [str(path) for path in sorted((ROOT / "tests/unit").glob("test_sidecar*.py"))]
        paths += [
            str(ROOT / "tests/architecture/test_sidecar_boundary.py"),
            str(ROOT / "tests/unit/test_carrot_cache_metrics.py"),
            str(ROOT / "compatibility/carrot/test_sidecar_streams.py"),
        ]
    return pytest.main(
        [
            *paths,
            "-q",
            "--cov=cyberpilot_autotune.integrations.carrot.sidecar"
            if args.sidecar_only
            else "--cov=cyberpilot_autotune",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-fail-under=95" if args.sidecar_only else "--cov-fail-under=90",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
