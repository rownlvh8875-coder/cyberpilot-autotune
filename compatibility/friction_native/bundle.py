"""Exact pinned native overlay builder; never modifies the source reference."""

import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "native_patches/friction_observation"
PIN = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
HELPER = "openpilot/selfdrive/controls/lib/friction_observation.py"
EDIT_PATHS = (
    "openpilot/cereal/custom.capnp",
    "openpilot/cereal/log.capnp",
    "openpilot/cereal/services.py",
    "openpilot/common/pid.py",
    "openpilot/selfdrive/controls/lib/latcontrol_torque.py",
    "openpilot/selfdrive/controls/controlsd.py",
    HELPER,
)


def git_bytes(reference, path):
    return subprocess.check_output(["git", "-C", str(reference), "show", f"{PIN}:{path}"])


def instrument(original):
    manifest = json.loads((ROOT / "docs/evidence/carrot_friction_patch_sources.json").read_text())
    expected = {f["path"]: f["sha256"] for f in manifest["files"] if f["revision"] == PIN}
    for path in EDIT_PATHS[:-1]:
        if path not in original or hashlib.sha256(original[path]).hexdigest() != expected[path]:
            raise ValueError("SOURCE_PIN:" + path)
    result = dict(original)
    edits = json.loads((ASSETS / "edits.json").read_text())
    for path, changes in edits.items():
        value = result[path].decode()
        suffix = ""
        if path == "openpilot/common/pid.py":
            value, separator, suffix = value.partition("class MultiplicativeUnwindPID:")
            suffix = separator + suffix
        for old, new in changes:
            if value.count(old) != 1:
                raise ValueError("EDIT_SITE:" + path)
            value = value.replace(old, new, 1)
        result[path] = (value + suffix).encode()
    receipt = (ASSETS / "receipt.capnp").read_text().split("\n", 1)[1]
    old = "struct CustomReserved3 @0xda96579883444c35 {\n}"
    if result[EDIT_PATHS[0]].count(old.encode()) != 1:
        raise ValueError("RESERVED_SLOT")
    result[EDIT_PATHS[0]] = result[EDIT_PATHS[0]].replace(old.encode(), receipt.encode())
    result[HELPER] = (ASSETS / "friction_observation.py").read_bytes()
    return result


def originals(reference):
    return {path: git_bytes(reference, path) for path in EDIT_PATHS[:-1]}


def patch(original, revised):
    return "".join(
        "".join(
            difflib.unified_diff(
                original.get(path, b"").decode().splitlines(True),
                revised[path].decode().splitlines(True),
                fromfile="a/" + path if path in original else "/dev/null",
                tofile="b/" + path,
            )
        )
        for path in EDIT_PATHS
    )


def build(reference, destination):
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("DESTINATION_NOT_EMPTY")
    original = originals(reference)
    revised = instrument(original)
    for path, raw in revised.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return original, revised
