"""Run only five original tests in a coherent, verified, immutable-base snapshot."""

import hashlib
import io
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
BASE = "cfc31c36c1fa99c7d00d9609c5360b9e07894d7e"
CONTAINMENT_CASE = (
    "tests/test_strict_containment_input.py::"
    "test_original_entrypoints_remain_unrepaired_and_unmigrated"
)
HANDOFF_CASE_PREFIX = (
    "tests/test_strict_handoff_limits.py::"
    "test_original_validator_still_accepts_float_equal_metadata"
)
CASES = (
    CONTAINMENT_CASE,
    HANDOFF_CASE_PREFIX + "[members]",
    HANDOFF_CASE_PREFIX + "[bytes_per_member]",
    HANDOFF_CASE_PREFIX + "[events]",
    HANDOFF_CASE_PREFIX + "[json_bytes]",
)


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
        raise ValueError("frozen Git snapshot unavailable; no fetch or fallback") from error


def materialize_snapshot(destination: Path) -> None:
    """Write only to a new owned test directory; source revision is not selectable."""
    expected = {}
    for row in _git("ls-tree", "-rz", "--full-tree", BASE).split(b"\0"):
        if not row:
            continue
        header, name = row.split(b"\t", 1)
        mode, kind, blob = header.split()
        path = name.decode("utf-8")
        if (
            mode not in (b"100644", b"100755")
            or kind != b"blob"
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or path in expected
        ):
            raise ValueError("unsupported frozen tree entry")
        expected[path] = (mode, blob.decode("ascii"))
    if not expected:
        raise ValueError("empty frozen tree")
    destination.mkdir()  # must not overwrite or merge an existing directory
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(_git("archive", "--format=tar", BASE))) as archive:
        for member in archive:
            if member.isdir():
                continue
            if not member.isfile() or member.name not in expected or member.name in seen:
                raise ValueError("unexpected frozen archive entry")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("missing frozen archive bytes")
            raw = stream.read()
            mode, blob = expected[member.name]
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if actual != blob:
                raise ValueError("frozen archive is not exact Git blob bytes")
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            target.chmod(0o755 if mode == b"100755" else 0o644)
            seen.add(member.name)
    if seen != set(expected):
        raise ValueError("incomplete frozen archive")


def run_frozen_case(node_id: str) -> None:
    """No arbitrary command, revision or node; child imports no repaired modules."""
    if type(node_id) is not str or node_id not in CASES:
        raise ValueError("unapproved historical test node")
    with TemporaryDirectory(prefix="cyberpilot-frozen-characterization-") as temporary:
        snapshot = Path(temporary) / "snapshot"
        materialize_snapshot(snapshot)
        environment = dict(os.environ)
        for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_CURRENT_TEST"):
            environment.pop(name, None)
        environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "--override-ini=addopts=",
                "--",
                node_id,
            ],
            cwd=snapshot,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0 and re.search(r"\b1 passed\b", result.stdout), (
            result.stdout + result.stderr
        )
