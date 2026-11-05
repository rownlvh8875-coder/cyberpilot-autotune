"""Blocked synthetic gate: worker starts only after verified manager and kernel limits."""

import dataclasses
import json
import os
import re
import select
import sys
from pathlib import Path

from native_e_lab.runner import run_fixed


def _kernel_limits() -> dict[str, str]:
    member = [
        s[3:] for s in Path("/proc/self/cgroup").read_text().splitlines() if s.startswith("0::")
    ]
    if len(member) != 1 or ".." in member[0].split("/"):
        raise ValueError("CGROUP_MAPPING_UNKNOWN")
    # Current namespace only; does not identify the host root or a custody domain.
    mounts = [
        s.split()
        for s in Path("/proc/self/mountinfo").read_text().splitlines()
        if " - cgroup2 " in s
    ]
    if len(mounts) != 1 or mounts[0][3] != "/" or mounts[0][4] != "/sys/fs/cgroup":
        raise ValueError("CGROUP_MAPPING_UNKNOWN")
    path = Path("/sys/fs/cgroup") / member[0].lstrip("/")
    values = {
        name: (path / name).read_text().strip()
        for name in ("memory.max", "memory.swap.max", "pids.max", "cpu.max")
    }
    quota, period = values["cpu.max"].split()
    if (
        values["memory.max"] != "134217728"
        or values["memory.swap.max"] != "0"
        or values["pids.max"] != "8"
        or not quota.isdecimal()
        or not period.isdecimal()
        or int(period) <= 0
        or int(quota) * 4 != int(period)
    ):
        raise ValueError("KERNEL_LIMIT_UNVERIFIED")
    return values


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch("[0-9a-f]{32}", sys.argv[1]) or os.geteuid() == 0:
        return 2
    if not select.select([sys.stdin], [], [], 8)[0]:
        return 3
    if sys.stdin.buffer.read(36) != ("GO " + sys.argv[1] + "\n").encode():
        return 4
    try:
        values = _kernel_limits()
    except (OSError, ValueError):
        print(json.dumps({"status": "BLOCKED_KERNEL_LIMIT", "worker_executed": False}))
        return 5
    obs = run_fixed()
    print(
        json.dumps(
            {
                "status": obs.outcome,
                "worker_executed": (
                    True
                    if obs.worker_exit is not None
                    else False
                    if obs.cleanup == "NOT_CREATED"
                    or (
                        obs.outcome == "UNAVAILABLE"
                        and "CLONE3_UNAVAILABLE" in obs.errors
                        and obs.supervisor_exit == 78
                    )
                    else "UNKNOWN"
                ),
                "kernel_limits": values,
                "observation": dataclasses.asdict(obs),
                "flags": obs.flags,
                "provider_registration": obs.provider_registration,
                "internal_D": "NOT_IMPLEMENTED",
            }
        )
    )
    return 0 if obs.outcome == "SYNTHETIC_COMPLETE" else 6


if __name__ == "__main__":
    raise SystemExit(main())
