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
    assert git("rev-parse", "HEAD").decode().strip() == merge
    assert git("show", "-s", "--format=%P", merge).decode().strip().split() == [
        evidence["original_base"],
        source,
    ]
    assert git("rev-parse", merge + "^{tree}") == git("rev-parse", source + "^{tree}")
    assert git("diff", "--name-only").strip() == b""
    for item in evidence["schema_files"]:
        data = git("show", source + ":" + item["path"])
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert (reference / item["path"]).read_bytes() == data
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", required=True, type=Path)
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

    return pytest.main(
        [
            str(ROOT / "tests"),
            str(ROOT / "compatibility/carrot"),
            "-q",
            "--cov=cyberpilot_autotune",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
