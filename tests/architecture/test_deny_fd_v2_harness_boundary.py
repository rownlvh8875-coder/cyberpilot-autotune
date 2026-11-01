"""Explicit successor delta; no historical guard is silently skipped."""

import importlib
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_current_delta_is_exact_22():
    name = "tests.history_transition.deny_fd_v2_harness_successor"
    assert importlib.util.find_spec(name) is not None, "closed harness successor required"
    v = importlib.import_module(name)
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", v.BASE, "HEAD"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    assert changed == set(v.NEW_PATHS) | set(v.MODIFIED)
    assert len(changed) == 22
    assert len(v.validate_harness_successor(ROOT)) == 20
