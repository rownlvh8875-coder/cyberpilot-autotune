"""Trusted bounded toy only. Inert import;no arbitrary code/command/source input."""

import errno
import json
import os
import resource
import socket
import subprocess
import sys
import time
from pathlib import Path


def _observe() -> dict[str, object]:
    import ctypes

    state = {
        line.split(":")[0]: line.split(":")[1].strip()
        for line in Path("/proc/self/status").read_text().splitlines()
        if line.split(":")[0] in ("CapEff", "NoNewPrivs", "Seccomp")
    }
    operations = {
        "create": lambda: os.open("/protected/new", os.O_WRONLY | os.O_CREAT, 0o600),
        "write": lambda: os.open("/protected/canary", os.O_WRONLY),
        "rename": lambda: os.rename("/protected/canary", "/protected/other"),
        "unlink": lambda: os.unlink("/protected/canary"),
        "link": lambda: os.link("/protected/canary", "/protected/linked"),
    }
    denied = {}
    for name, operation in operations.items():
        try:
            handle = operation()
        except OSError as error:
            denied[name] = error.errno
        else:
            if type(handle) is int:
                os.close(handle)
            denied[name] = 0
    try:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except OSError as error:
        socket_errno = error.errno
    else:
        connection.close()
        socket_errno = 0
    libc = ctypes.CDLL(None, use_errno=True)
    ctypes.set_errno(0)
    libc.unshare(ctypes.c_int(0x10000000))
    userns_errno = ctypes.get_errno()
    identities = json.loads(Path("/identities.json").read_bytes())
    inherited = []
    for fd in range(64):
        try:
            value = os.fstat(fd)
        except OSError:
            continue
        inherited.append([value.st_dev, value.st_ino])
    Path("/scratch/positive").write_bytes(b"SYNTHETIC_SCRATCH_OK\n")
    return {
        "controls": state,
        "namespaces": {
            key: os.readlink("/proc/self/ns/" + key)
            for key in ("user", "pid", "net", "mnt", "ipc", "uts")
        },
        "read": Path("/protected/canary").read_bytes() == b"SYNTHETIC_ONLY_PROTECTED_V1\n",
        "denied": denied,
        "socket_errno": socket_errno,
        "userns_errno": userns_errno,
        "leaked_objects": [value for value in identities["victims"] if value in inherited],
        "inherited_filter": identities["filter"] in inherited,
        "host_hidden": not any(
            Path(p).exists() for p in ("/workspace", "/run/docker.sock", "/var/run/docker.sock")
        ),
        "environment_keys": sorted(os.environ),
        "limits": {
            key: resource.getrlimit(limit)
            for key, limit in (
                ("CPU", resource.RLIMIT_CPU),
                ("AS", resource.RLIMIT_AS),
                ("FSIZE", resource.RLIMIT_FSIZE),
                ("NOFILE", resource.RLIMIT_NOFILE),
                ("CORE", resource.RLIMIT_CORE),
            )
        },
    }


def main(argv: tuple[str, ...]) -> int:
    if len(argv) != 1 or argv[0] not in (
        "FD_CLOSED",
        "DIRECTORY_READ_ONLY",
        "DESCENDANT_NETWORK",
        "TIMEOUT_SETSID",
        "OUTPUT_FLOOD",
        "MISSING_MOUNT",
        "NONZERO_EXIT",
        "SUPERVISOR_ABORT",
        "descendant",
        "heartbeat",
    ):
        return 2
    action = argv[0]
    if action == "heartbeat":
        end = time.monotonic() + 3
        while time.monotonic() < end:
            with open("/scratch/heartbeat", "ab") as stream:
                stream.write(b".")
            time.sleep(0.03)
        return 0
    if action in ("TIMEOUT_SETSID", "SUPERVISOR_ABORT"):
        child = subprocess.Popen(
            [sys.executable, "-I", "-B", "-S", "/payload.py", "heartbeat"],
            start_new_session=True,
            close_fds=True,
        )
        end = time.monotonic() + 3
        while time.monotonic() < end:
            time.sleep(0.03)
        child.wait(timeout=1)
        return 0
    if action == "OUTPUT_FLOOD":
        os.write(1, b"o" * 32768)
        os.write(2, b"e" * 32769)
        return 0
    if action == "NONZERO_EXIT":
        print("OWNED_NONZERO_CONTROL", flush=True)
        return 7
    if action == "MISSING_MOUNT":
        Path("/scratch/payload-ran").write_bytes(b"SHOULD_NOT_EXIST")
        return 1
    observed = _observe()
    if action != "descendant":
        child_result = subprocess.run(
            [sys.executable, "-I", "-B", "-S", "/payload.py", "descendant"],
            capture_output=True,
            timeout=2,
            close_fds=True,
            check=False,
        )
        observed["descendant"] = json.loads(child_result.stdout)
    print(json.dumps(observed, sort_keys=True), flush=True)
    return 0 if observed["socket_errno"] == errno.EPERM else 1


if __name__ == "__main__":
    raise SystemExit(main(tuple(sys.argv[1:])))
