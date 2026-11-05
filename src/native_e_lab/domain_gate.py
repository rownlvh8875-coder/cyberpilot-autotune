"""Fixed gate for a NEW delegated lab service, not an importable permission."""

import dataclasses
import json
import os
import re
import select
import sys
from pathlib import Path

from native_e_lab.domain import _run_domain_fixed
from native_e_lab.gate import _kernel_limits


def _scope(unit: str) -> dict[str, object]:
    if not re.fullmatch(r"native-e-domain-[0-9a-f]{32}\.service", unit):
        raise ValueError("NOT_FACTORY_SCOPE")
    rows = Path("/proc/self/cgroup").read_text().splitlines()
    if len(rows) != 1 or not rows[0].startswith("0::/"):
        raise ValueError("CGROUP_UNKNOWN")
    member = rows[0][3:]
    if ".." in member.split("/") or Path(member).name != unit:
        raise ValueError("NOT_FACTORY_SCOPE")
    parent = Path("/sys/fs/cgroup") / member.lstrip("/")
    if parent.is_symlink() or parent.stat().st_uid != os.geteuid():
        raise ValueError("PARENT_OWNER_UNKNOWN")
    if (parent / "cgroup.type").read_text().strip() != "domain":
        raise ValueError("PARENT_TYPE_UNKNOWN")
    if not os.access(parent, os.W_OK, effective_ids=True):
        raise ValueError("PARENT_UNWRITABLE")
    return {
        "new_external_scope_checked": True,
        "parent_writable_metadata": os.access(parent, os.W_OK, effective_ids=True),
    }


def main() -> int:
    if len(sys.argv) != 3 or os.geteuid() == 0 or not re.fullmatch("[0-9a-f]{32}", sys.argv[1]):
        return 2
    if not select.select([sys.stdin], [], [], 8)[0]:
        return 3
    if sys.stdin.buffer.read(36) != ("GO " + sys.argv[1] + "\n").encode():
        return 4
    try:
        limits = _kernel_limits()
        scope = _scope(sys.argv[2])
    except (OSError, ValueError) as exc:
        reason = exc.args[0] if isinstance(exc, ValueError) else type(exc).__name__
        print(
            json.dumps(
                {"status": "BLOCKED_DOMAIN_SCOPE", "worker_executed": False, "reason": reason}
            )
        )
        return 5
    obs = _run_domain_fixed()
    print(
        json.dumps(
            {
                "status": obs.outcome,
                "observation": dataclasses.asdict(obs),
                "worker_executed": True
                if obs.worker_exit is not None
                else False
                if obs.outcome == "UNAVAILABLE" and obs.supervisor_exit == 78
                else "UNKNOWN",
                "kernel_limits": limits,
                "scope": scope,
                "flags": obs.flags,
                "provider_registration": obs.provider_registration,
                "custody_qualified": False,
            }
        )
    )
    return 0 if obs.outcome == "SYNTHETIC_DOMAIN_STOPPED" else 6


if __name__ == "__main__":
    raise SystemExit(main())
