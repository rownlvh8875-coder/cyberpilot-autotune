"""Explicit fixed compilation only. No guest runner or executable invocation."""

import hashlib
import json
import os
import re
import stat
import struct
import subprocess
from pathlib import Path

from .contracts import PERMISSIONS

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "docs/evidence/deny_fd_v2_sources.json"
SOURCES = tuple(
    "tests/deny_fd_v2/" + p
    for p in (
        "__init__.py",
        "build.py",
        "contracts.py",
        "guest/probe.c",
        "validation.py",
        "wire.py",
    )
)
COMPILER = "/usr/bin/cc"


def _revision(value: object) -> str:
    if type(value) is not str or re.fullmatch("[0-9a-f]{40}", value) is None:
        raise ValueError("exact source revision required")
    return value


def _git(*args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            stderr=subprocess.PIPE,
            timeout=30,
            env=dict(
                os.environ,
                GIT_NO_LAZY_FETCH="1",
                GIT_NO_REPLACE_OBJECTS="1",
                GIT_OPTIONAL_LOCKS="0",
            ),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("source Git objects unavailable; no fetch/fallback") from error


def _read_regular(path: Path) -> bytes:
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("regular source/artifact required")
        return path.read_bytes()
    except OSError as error:
        raise ValueError("source/artifact unavailable") from error


def _canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def describe_sources(revision: str) -> dict[str, object]:
    revision = _revision(revision)
    _git("rev-parse", "--verify", revision + "^{commit}")
    records = []
    for path in SOURCES:
        entry = _git("ls-tree", revision, "--", path).decode().split()
        if len(entry) != 4 or entry[0:2] != ["100644", "blob"] or entry[3] != path:
            raise ValueError("fixed source path/mode missing")
        raw = _git("show", revision + ":" + path)
        records.append(
            {
                "path": path,
                "mode": entry[0],
                "git_blob_sha1": entry[2],
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return {
        "schema": "deny-fd-v2-source-manifest-v1",
        "repo": "rownlvh8875-coder/cyberpilot-autotune",
        "source_revision": revision,
        "sources": records,
    }


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate source manifest key")
        result[key] = value
    return result


def _verified_sources() -> tuple[dict[str, object], str, bytes]:
    data: dict[str, object] = json.loads(_read_regular(ROOT / MANIFEST), object_pairs_hook=_unique)
    if type(data) is not dict:
        raise ValueError("source manifest object required")
    revision = _revision(data.get("source_revision"))
    if data != describe_sources(revision):
        raise ValueError("source manifest does not match exact raw source set")
    pinned = {path: _git("show", revision + ":" + path) for path in SOURCES}
    for path in SOURCES:
        if _read_regular(ROOT / path) != pinned[path]:
            raise ValueError("working source differs from pinned source")
    return data, revision, pinned["tests/deny_fd_v2/guest/probe.c"]


def _static_elf(raw: bytes) -> None:
    if len(raw) < 64 or raw[:7] != b"\x7fELF\x02\x01\x01":
        raise ValueError("ELF64 little-endian artifact required")
    identity = struct.unpack_from("<HH", raw, 16)
    offset = struct.unpack_from("<Q", raw, 32)[0]
    size, count = struct.unpack_from("<HH", raw, 54)
    if (
        identity != (2, 62)
        or size != 56
        or count == 0
        or offset < 64
        or offset + size * count > len(raw)
    ):
        raise ValueError("fixed static x86_64 executable layout required")
    if any(struct.unpack_from("<I", raw, offset + i * size)[0] in (2, 3) for i in range(count)):
        raise ValueError("dynamic/interpreter segment forbidden")


def compile_fixed_probe(destination: Path) -> dict[str, object]:
    data, revision, source = _verified_sources()
    if not isinstance(destination, Path) or destination.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("new owned destination outside checkout required")
    destination = destination.resolve()
    try:
        destination.mkdir()
    except OSError as error:
        raise ValueError("destination must not exist and parent must be available") from error
    digest = hashlib.sha256(_canonical(data)).hexdigest()
    copied = destination / "probe.c"
    copied.write_bytes(source)
    output = destination / "deny-fd-v2-probe"
    command = [
        COMPILER,
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-static",
        "-no-pie",
        '-DSOURCE_REVISION="' + revision + '"',
        '-DSOURCE_MANIFEST_DIGEST="' + digest + '"',
        str(copied),
        "-o",
        str(output),
    ]
    try:
        version = subprocess.run(
            [COMPILER, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        result = subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60
        )
    except (OSError, subprocess.SubprocessError) as error:
        log = getattr(error, "stdout", None) or str(error).encode()
        (destination / "compiler-failure.log").write_bytes(log)
        raise ValueError("compiler unavailable/failed; target never executed") from error
    (destination / "compiler.log").write_bytes(result.stdout)
    if _read_regular(copied) != source:
        raise ValueError("compiler input changed during compilation")
    raw = _read_regular(output)
    _static_elf(raw)
    record = {
        "schema": "deny-fd-v2-compile-record-v1",
        "source_revision": revision,
        "source_manifest_digest": digest,
        "compiler_version": version.stdout.decode("utf-8", "replace"),
        "command": command,
        "binary": {
            "path": output.name,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "runtime_qualified": False,
        "build_input_closure_qualified": False,
        "permissions": dict(PERMISSIONS),
    }
    (destination / "build-record.json").write_bytes(_canonical(record) + b"\n")
    return record
