"""Actual successor delta is separate from original-source assertion replay."""

import subprocess
from pathlib import Path

from tests.architecture.test_deny_fd_v2_harness_boundary import violations
from tests.history_transition import deny_fd_v2_transport_successor as successor

ROOT = Path(__file__).resolve().parents[2]


def test_actual_transport_delta_is_exact_22():
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", successor.BASE, "HEAD"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    assert changed == successor.MODIFIED | successor.NEW_PATHS
    assert len(changed) == 22
    assert len(successor.validate_transport_successor(ROOT)) == 20


def test_transport_has_no_network_legacy_application_or_owner_bridge():
    for path in (ROOT / "tests/deny_fd_v2_transport").glob("*.py"):
        assert violations(path.read_bytes()) == [], path.name


def test_installed_product_remains_base_identical():
    assert (
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                successor.BASE,
                "HEAD",
                "--",
                "src",
                ".github",
                "compatibility",
                "native_patches",
            ],
            cwd=ROOT,
        )
        == b""
    )
