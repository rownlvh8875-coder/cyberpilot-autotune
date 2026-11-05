"""Fresh bounded lab gate. Same-PID original-FD exec, never arbitrary payload."""

import io
import json
import os
import re
import select
import sys
import time
from pathlib import Path

# Direct file launch under -I: fixed repository root only, never caller sys.path/env.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from native_e_lab.domain_gate import _scope  # noqa: E402
from native_e_lab.gate import _kernel_limits  # noqa: E402
from research.real_cgroup.build import verify_open_factory  # noqa: E402


def _credentials() -> None:
    fields = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text().splitlines()
        if ":" in line
    )
    if (
        fields.get("NoNewPrivs", "").strip() != "1"
        or int(fields.get("CapEff", "-1").strip(), 16) != 0
    ):
        raise ValueError("CREDENTIAL_PREFLIGHT")


def _read_go(expected: bytes) -> int:
    stream = sys.stdin.buffer
    if not isinstance(stream, (io.BufferedReader, io.BytesIO)):
        return 4
    deadline = time.monotonic() + 8
    data = bytearray()
    while len(data) <= len(expected):
        left = deadline - time.monotonic()
        if left <= 0 or not select.select([sys.stdin], [], [], left)[0]:
            return 3
        chunk = stream.read1(len(expected) + 1 - len(data))
        if not chunk:
            return 0 if bytes(data) == expected else 4
        data.extend(chunk)
    return 4


def main() -> int:
    if (
        len(sys.argv) != 4
        or os.geteuid() == 0
        or not re.fullmatch("[0-9a-f]{32}", sys.argv[1])
        or not re.fullmatch("native-e-domain-[0-9a-f]{32}\\.service", sys.argv[2])
    ):
        return 2
    protocol = _read_go(("GO " + sys.argv[1] + "\n").encode())
    if protocol:
        return protocol
    fd = -1
    try:
        limits = _kernel_limits()
        scope = _scope(sys.argv[2])
        _credentials()
        fd = verify_open_factory(Path(sys.argv[3]))
        print(json.dumps({"gate_pass": True, "kernel_limits": limits, "scope": scope}), flush=True)
        # Original opened ELF; no pathname fallback and no additional F subprocess.
        os.execve(fd, ["fixed-real-cgroup-cohort"], {"LANG": "C.UTF-8"})
    except (OSError, ValueError) as exc:
        print(
            json.dumps({"gate_pass": False, "reason": str(exc), "worker_executed": False}),
            flush=True,
        )
        return 5
    finally:
        if fd >= 0:
            owned = fd
            fd = -1
            os.close(owned)
    return 6


if __name__ == "__main__":
    raise SystemExit(main())
