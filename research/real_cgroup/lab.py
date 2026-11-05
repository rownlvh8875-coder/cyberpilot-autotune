"""Fixed bounded fresh user-unit lab. Import is inert; no provider qualification."""

import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

from native_e_lab.lab import EXPECTED as BASE_LIMITS
from native_e_lab.lab import _bus_environment, _parse_properties
from research.real_cgroup.build import build_fixed_kit as _build_kit

EXPECTED = dict(BASE_LIMITS, Delegate="yes", NoNewPrivileges="yes", Slice="-.slice", Restart="no")
_RETAINED: list[subprocess.Popen[str]] = []
_UNCERTAIN_STREAMS: list[object] = []


def _show(args: list[str], env: dict[str, str], *, allow_missing: bool = False) -> dict[str, str]:
    r = subprocess.run(args, env=env, capture_output=True, text=True, timeout=3, check=False)
    if r.returncode and not (
        allow_missing and r.returncode == 4 and r.stdout.strip() == "LoadState=not-found"
    ):
        raise ValueError("READ_UNAVAILABLE")
    return _parse_properties(r.stdout)


def _preflight() -> dict[str, object]:
    env = _bus_environment()
    uid = os.geteuid()
    manager = _show(
        [
            "/usr/bin/systemctl",
            "show",
            f"user@{uid}.service",
            "--property=ActiveState,Delegate,DelegateControllers,ControlGroup,MainPID",
        ],
        env,
    )
    root = _show(
        [
            "/usr/bin/systemctl",
            "--user",
            "show",
            "--property=LoadState,ActiveState,ControlGroup",
            "--",
            "-.slice",
        ],
        env,
    )
    if (
        manager.get("ActiveState") != "active"
        or manager.get("Delegate") != "yes"
        or not {"cpu", "memory", "pids"} <= set(manager.get("DelegateControllers", "").split())
        or root.get("LoadState") != "loaded"
        or root.get("ActiveState") != "active"
        or manager.get("ControlGroup") != root.get("ControlGroup")
    ):
        raise ValueError("EXISTING_DELEGATED_ROOT_UNAVAILABLE")
    member = manager["ControlGroup"]
    if not member.startswith("/") or ".." in member.split("/"):
        raise ValueError("ROOT_MAPPING")
    folder = Path("/sys/fs/cgroup") / member.lstrip("/")
    metadata = {
        name: (folder / name).read_text().strip()
        for name in ["cgroup.type", "cgroup.controllers", "cgroup.subtree_control"]
    }
    if metadata["cgroup.type"] != "domain" or not {"cpu", "memory", "pids"} <= set(
        metadata["cgroup.subtree_control"].split()
    ):
        raise ValueError("EXISTING_CONTROLLERS_NOT_ENABLED")
    # Read only the known existing manager process, not a process inventory.
    pid = int(manager["MainPID"])
    start = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    return {"manager": manager, "root": root, "metadata": metadata, "manager_starttime": start}


def run_fixed_real_lab() -> dict[str, object]:
    if os.geteuid() == 0:
        return {"status": "BLOCKED_ROOT", "worker_executed": False}
    before = _preflight()
    kit = _build_kit()
    result = _launch(kit)
    result["preflight"] = before
    return result


def _launch(kit: Path) -> dict[str, object]:
    env = _bus_environment()
    token = secrets.token_hex(16)
    unit = "native-e-domain-" + secrets.token_hex(16) + ".service"
    collision = subprocess.run(
        ["/usr/bin/systemctl", "--user", "show", "--property=LoadState", "--", unit],
        env=env,
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    if collision.returncode not in (0, 4) or collision.stdout.strip() != "LoadState=not-found":
        return {"status": "BLOCKED_UNIT_COLLISION_OR_UNKNOWN", "worker_executed": False}
    args = [
        "/usr/bin/systemd-run",
        "--user",
        "--pipe",
        "--wait",
        "--collect",
        "--quiet",
        "--service-type=exec",
        "--slice=-.slice",
        "--unit=" + unit,
    ]
    for setting in [
        "RuntimeMaxSec=30s",
        "TimeoutStopSec=5s",
        "MemoryMax=128M",
        "MemorySwapMax=0",
        "TasksMax=8",
        "CPUQuota=25%",
        "Delegate=yes",
        "NoNewPrivileges=yes",
        "Restart=no",
    ]:
        args.append("--property=" + setting)
    args += [
        "--",
        "/usr/bin/env",
        "-i",
        "LANG=C.UTF-8",
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).with_name("gate.py")),
        token,
        unit,
        str(kit),
    ]
    job: subprocess.Popen[str] | None = None
    released = False
    communicate_started = False
    primary: BaseException | None = None
    verified: dict[str, str] | None = None
    result: dict[str, object] = {
        "status": "BLOCKED",
        "worker_executed": False,
        "unit": unit,
        "kit": str(kit),
    }
    try:
        job = subprocess.Popen(
            args,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            close_fds=True,
            cwd="/",
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            values = _show(
                [
                    "/usr/bin/systemctl",
                    "--user",
                    "show",
                    "--no-pager",
                    "--property="
                    + ",".join(
                        tuple(EXPECTED) + ("LoadState", "ActiveState", "Transient", "InvocationID")
                    ),
                    "--",
                    unit,
                ],
                env,
                allow_missing=True,
            )
            if values.get("ActiveState") == "active":
                if (
                    any(values.get(k) != v for k, v in EXPECTED.items())
                    or values.get("LoadState") != "loaded"
                    or values.get("Transient") != "yes"
                    or not re.fullmatch("[0-9a-f]{32}", values.get("InvocationID", ""))
                ):
                    raise ValueError("LOADED_UNIT_CONTRACT")
                verified = values
                break
            if job.poll() is not None:
                break
            time.sleep(0.1)
        released = verified is not None
        communicate_started = True  # communicate exclusively owns pipe closure from now on
        out, err = job.communicate("GO " + token + "\n" if verified else "", timeout=38)
        if len(out) > 32768 or len(err) > 4096:
            raise ValueError("OUTPUT_BOUND")

        def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
            parsed: dict[str, object] = {}
            for key, value in pairs:
                if key in parsed:
                    raise ValueError("DUPLICATE_OUTPUT_KEY")
                parsed[key] = value
            return parsed

        records = [json.loads(line, object_pairs_hook=unique_object) for line in out.splitlines()]
        gates = [r for r in records if type(r) is dict and "gate_pass" in r]
        native = [r for r in records if type(r) is dict and "outcome" in r]
        passed = (
            job.returncode == 0
            and released
            and len(records) == 2
            and records[0] is (gates[0] if len(gates) == 1 else None)
            and records[1] is (native[0] if len(native) == 1 else None)
            and len(gates) == 1
            and gates[0].get("gate_pass") is True
            and len(native) == 1
            and native[0].get("outcome") == "REAL_CGROUP_COHORT_COMPLETE"
            and native[0].get("kernel_domain_verified") is True
            and native[0].get("parent_released") is True
            and native[0].get("worker_started") is True
        )
        result.update(
            {
                "status": "PASS_REAL_CGROUP_LAB" if passed else "BLOCKED_GATE_OR_NATIVE",
                "worker_executed": native[0].get("worker_started")
                if len(native) == 1
                else (False if len(gates) == 1 and gates[0].get("gate_pass") is False else None),
                "exit_code": job.returncode,
                "gate": gates[0] if len(gates) == 1 else None,
                "native": native[0] if len(native) == 1 else None,
                "loaded_limits": {k: verified[k] for k in EXPECTED} if verified else None,
                "external_unit_is_internal_D": False,
                "custody_qualified": False,
                "provider_registration": "UNBOUND",
                "cleanup": "SDK_INTERNAL_CLOSE_UNAVAILABLE",
            }
        )
        return result
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        primary = exc
        result.update(
            {
                "status": "UNKNOWN_" + type(exc).__name__,
                "cleanup": "UNKNOWN",
                "worker_executed": None if released else False,
            }
        )
        if job is not None:
            _RETAINED.append(job)
        return result
    except BaseException as exc:
        primary = exc
        if job is not None:
            _RETAINED.append(job)
        raise
    finally:
        if job is not None and not communicate_started:
            for name in ["stdin", "stdout", "stderr"]:
                stream = getattr(job, name)
                if stream is not None:
                    setattr(job, name, None)  # consume our close ownership before the attempt
                    try:
                        stream.close()
                    except BaseException as exc:
                        _UNCERTAIN_STREAMS.append(stream)
                        if job not in _RETAINED:
                            _RETAINED.append(job)
                        result["cleanup"] = "UNKNOWN"
                        if primary is not None:
                            primary.add_note("PIPE_CLOSE_UNKNOWN")
                        else:
                            raise exc
