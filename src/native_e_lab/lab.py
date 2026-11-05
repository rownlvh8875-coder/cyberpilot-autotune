"""One factory-named external systemd lab, never an E-created internal D."""

import json
import os
import secrets
import stat
import subprocess
import time
from pathlib import Path

EXPECTED = {
    "RuntimeMaxUSec": "30s",
    "TimeoutStopUSec": "5s",
    "MemoryMax": "134217728",
    "MemorySwapMax": "0",
    "TasksMax": "8",
    "CPUQuotaPerSecUSec": "250ms",
}
# Unknown pipe objects are retained, never retried or recovered by numeric FD.
_UNCERTAIN_PIPES: list[object] = []

PROPERTIES = tuple(EXPECTED) + ("LoadState", "ActiveState", "Transient", "InvocationID")


def _parse_properties(raw: str) -> dict[str, str]:
    result = {}
    for line in raw.splitlines():
        key, sep, value = line.partition("=")
        if not sep or not key or key in result:
            raise ValueError("AMBIGUOUS_PROPERTY")
        result[key] = value
    return result


def _verify_limits(values: dict[str, str]) -> None:
    if any(values.get(k) != v for k, v in EXPECTED.items()):
        raise ValueError("LIMIT_UNVERIFIED")


def _bus_environment() -> dict[str, str]:
    runtime = Path("/run/user") / str(os.geteuid())
    bus = runtime / "bus"
    if runtime.is_symlink() or not stat.S_ISSOCK(bus.stat().st_mode):
        raise ValueError("USER_BUS_UNAVAILABLE")
    if runtime.stat().st_uid != os.geteuid() or bus.stat().st_uid != os.geteuid():
        raise ValueError("USER_BUS_OWNER")
    return {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "XDG_RUNTIME_DIR": str(runtime),
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=" + str(bus),
    }


def run_user_lab() -> dict[str, object]:
    return _run_user_lab(False)


def _run_user_lab(domain: bool) -> dict[str, object]:
    """No caller-selectable unit/command/receipt; original job used for completion only."""
    if os.geteuid() == 0:
        return {"status": "BLOCKED_ROOT", "worker_executed": False}
    env = _bus_environment()
    token = secrets.token_hex(16)
    unit = (
        ("native-e-domain-" if domain else "native-e-research-")
        + secrets.token_hex(16)
        + ".service"
    )
    check = subprocess.run(
        ["/usr/bin/systemctl", "--user", "show", "--property=LoadState", "--", unit],
        env=env,
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    if check.stdout.strip() != "LoadState=not-found":
        return {"status": "BLOCKED_UNIT_COLLISION_OR_UNKNOWN", "worker_executed": False}
    import sys

    gate = Path(__file__).with_name("domain_gate.py" if domain else "gate.py")
    args = [
        "/usr/bin/systemd-run",
        "--user",
        "--pipe",
        "--wait",
        "--collect",
        "--quiet",
        "--service-type=exec",
        "--unit=" + unit,
    ]
    for setting in (
        "RuntimeMaxSec=30s",
        "TimeoutStopSec=5s",
        "MemoryMax=128M",
        "MemorySwapMax=0",
        "TasksMax=8",
        "CPUQuota=25%",
    ):
        args.append("--property=" + setting)
    if domain:
        args.append("--property=Delegate=yes")
    args += [
        "--",
        "/usr/bin/env",
        "-i",
        "LANG=C.UTF-8",
        sys.executable,
        "-I",
        "-B",
        str(gate),
        token,
    ]
    if domain:
        args.append(unit)
    job: subprocess.Popen[str] | None = None
    verified: dict[str, str] | None = None
    released = False
    primary: BaseException | None = None
    result: dict[str, object] = {"status": "BLOCKED", "worker_executed": False}
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
        end = time.monotonic() + 5
        while time.monotonic() < end:
            got = subprocess.run(
                [
                    "/usr/bin/systemctl",
                    "--user",
                    "show",
                    "--no-pager",
                    "--property=" + ",".join(PROPERTIES + (("Delegate",) if domain else ())),
                    "--",
                    unit,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if got.returncode == 0:
                values = _parse_properties(got.stdout)
                if values.get("ActiveState") == "active":
                    _verify_limits(values)
                    if domain and values.get("Delegate") != "yes":
                        raise ValueError("DOMAIN_DELEGATION_UNAVAILABLE")
                    if values.get("Transient") != "yes" or not values.get("InvocationID"):
                        raise ValueError("UNIT_IDENTITY_UNKNOWN")
                    verified = values
                    break
            if job.poll() is not None:
                break
            time.sleep(0.1)
        # communicate owns only the original fresh job. No stop-by-name or reattachment.
        released = verified is not None
        out, err = job.communicate("GO " + token + "\n" if verified else "", timeout=38)
        if job.returncode != 0:
            diagnostic = None
            if domain and len(out) <= 16384:
                try:
                    value = json.loads(out)
                    if type(value) is dict:
                        diagnostic = {
                            k: v
                            for k, v in value.items()
                            if k
                            in {
                                "status",
                                "reason",
                                "worker_executed",
                                "observation",
                                "scope",
                                "kernel_limits",
                                "flags",
                                "provider_registration",
                            }
                        }
                except ValueError:
                    pass
            return {
                "gate_observation": diagnostic,
                "status": "BLOCKED_GATE_OR_JOB",
                "worker_executed": "UNKNOWN" if released else False,
                "exit": job.returncode,
                "stderr_type": "PRESENT" if err else "EMPTY",
                "limits_verified": verified is not None,
            }
        result = json.loads(out)
        result["unit_exit"] = job.returncode
        result["loaded_limits"] = {k: verified[k] for k in EXPECTED} if verified else None
        result["external_unit_is_internal_D"] = False
        if domain:
            result["loaded_delegation"] = verified.get("Delegate") if verified else None
        return result
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        primary = exc
        result["status"] = "UNKNOWN_" + type(exc).__name__
        result["cleanup"] = "UNKNOWN"
        result["worker_executed"] = "UNKNOWN" if released else False
        return result
    except BaseException as exc:
        primary = exc
        raise
    finally:
        secondary: BaseException | None = None
        if job is not None:
            # Close only retained pipes; no second wait/kill/recovery on uncertain outcome.
            for stream in (job.stdin, job.stdout, job.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except BaseException as exc:
                        _UNCERTAIN_PIPES.append(stream)
                        secondary = secondary or exc
        if secondary is not None:
            if primary is not None:
                primary.add_note("CLEANUP_UNKNOWN")
            else:
                secondary.add_note("CLEANUP_UNKNOWN")
                raise secondary
