"""Fixed prepared QEMU recipe only. No outer-host policy or automatic fallback."""

import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from compatibility.containment_backend_harmless.host_cases import (
    FIXTURES,
    check_case,
    parse_guest_log,
)
from compatibility.containment_backend_harmless.vm_runner import (
    MANIFEST as BASE_MANIFEST,
)
from compatibility.containment_backend_harmless.vm_runner import (
    qemu_arguments,
    verified_manifest,
    verify_file,
)

from .contracts import PERMISSIONS
from .evaluation import evaluate_capture
from .image import build_collector_image
from .validation import parse_capture

MANIFEST = Path(__file__).with_name("guest") / "build_manifest.json"


def load_assets() -> tuple[dict[str, Any], dict[str, tuple[int, bytes]], bytes]:
    data = json.loads(MANIFEST.read_text())
    if (
        data["scope"] != "SAME_SOFTWARE_GUEST_SYSCALL_CAPTURE_ONLY"
        or set(data["permissions"]) != set(PERMISSIONS)
        or any(v is not False for v in data["permissions"].values())
    ):
        raise ValueError("unsupported scope/permissions")
    if hashlib.sha256(BASE_MANIFEST.read_bytes()).hexdigest() != data["base_manifest_sha256"]:
        raise ValueError("frozen fixture manifest changed")
    paths = {r["path"] for r in data["inputs"]}
    if data["collector_path"] not in paths:
        raise ValueError("collector not hash-bound")
    for record in data["inputs"]:
        path = Path(record["path"])
        if not path.is_absolute():
            path = Path(__file__).parents[2] / path
        verify_file(path, record["sha256"])
    original = verified_manifest()
    files = {
        r["guest_path"]: (r["mode"], Path(r["path"]).read_bytes()) for r in original["guest_files"]
    }
    binary = Path(data["collector_path"]).read_bytes()
    if not binary.startswith(b"\x7fELF\x02\x01"):
        raise ValueError("collector is not built native ELF64")
    return original, files, binary


def execute(selected: tuple[str, ...]) -> int:
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(x not in FIXTURES for x in selected)
    ):
        return 2
    try:
        original, files, binary = load_assets()
        root = Path(original["vm_root"])
        outcome = 0
        for fixture in selected:
            with tempfile.TemporaryDirectory(
                prefix="hf-collector-", dir="/workspace/scratch"
            ) as owned:
                image = Path(owned) / "guest.cpio.gz"
                image.write_bytes(build_collector_image(files, binary, (fixture,)))
                process = subprocess.run(
                    qemu_arguments(root, image),
                    input=b"",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                    check=False,
                    env={
                        "QEMU_MODULE_DIR": str(root / "sysroot/usr/lib/x86_64-linux-gnu/qemu"),
                        "PATH": "/usr/bin:/bin",
                        "LANG": "C",
                    },
                )
            log = process.stdout.decode("utf-8", errors="strict")
            print("GUEST_CASE_BEGIN", fixture)
            sys.stdout.write(log)
            print("GUEST_CASE_END", fixture)
            if (
                process.returncode
                or ("ACTUAL_GUEST_KERNEL=" + original["guest_kernel"]) not in log
                or original["guest_btf_sha256"] not in log
            ):
                return 2
            records = parse_guest_log(log, (fixture,))
            capture = parse_capture(log)
            assessment = evaluate_capture(capture)
            print(
                "CAPTURE_ASSESSMENT",
                json.dumps({"fixture_id": fixture, **asdict(assessment)}, sort_keys=True),
            )
            if (
                capture.fixture_id != fixture
                or any(check_case(r) for r in records)
                or not assessment.fd_profile_complete
            ):
                outcome = 2
        return outcome
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print("GUEST_CAPTURE_UNAVAILABLE:", error, file=sys.stderr)
        return 2
