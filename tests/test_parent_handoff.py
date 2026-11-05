"""Real native F/E/SCM_RIGHTS on private regular dirs; no cgroup or service authority."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def execute(tmp_path, case, *, tracker_failure=False):
    binary = tmp_path / "parent-handoff-test"
    built = subprocess.run(
        [
            "cc",
            "-std=c11",
            "-O0",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(ROOT / "tests/native/parent_handoff_driver.c"),
            "-Wl,--wrap=sendmsg",
            "-Wl,--wrap=shutdown",
            "-Wl,--wrap=close",
            "-Wl,--wrap=waitid",
            "-Wl,--wrap=recvmsg",
            "-Wl,--wrap=fstatfs",
            "-Wl,--wrap=fcntl",
            "-Wl,--wrap=_exit",
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert built.returncode == 0, built.stderr
    (tmp_path / "lab-fixtures").mkdir(mode=0o700)
    result = subprocess.run(
        [str(binary), case],
        cwd=tmp_path,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=8,
    )
    report = json.loads(result.stdout)
    assert report["peer_exit"] in (
        (None, 0, 20, 137, 98) if tracker_failure else (None, 0, 20, 137)
    ), (result.stderr, report)
    if not tracker_failure:
        assert not result.stderr, result.stderr
    return result, report


def test_original_private_parent_handoff_completes_without_payload(tmp_path):
    result, report = execute(tmp_path, "normal")
    assert result.returncode == 0, result.stderr
    assert report == {
        "outcome": "PARENT_HANDOFF_FIXTURE_COMPLETE",
        "cleanup": "CONFIRMED",
        "peer_exit": 0,
        "parent_removed": True,
        "cgroup_authority": False,
        "worker_started": False,
    }
    assert not list((tmp_path / "lab-fixtures").iterdir())


@pytest.mark.parametrize(
    "case",
    [
        "nonce",
        "generation",
        "sequence",
        "stage",
        "no_fd",
        "extra_fd",
        "truncated_fd",
        "wrong_type",
        "wrong_dir",
        "empty",
        "oversize",
        "partial_prefix",
        "partial_body",
        "duplicate_grant",
        "extra_bytes",
        "omit_commit",
        "missing_eof",
        "send_uncertain",
        "send_error",
        "close_unknown",
        "wait_unknown",
        "fd_reuse",
        "name_replaced",
        "getfd_error",
        "no_cloexec",
        "replay_hello",
        "rights_on_commit",
        "rights_on_ready",
    ],
)
def test_invalid_or_ambiguous_handoff_never_completes_or_deletes_unknown_parent(tmp_path, case):
    result, report = execute(tmp_path, case)
    assert result.returncode == 20, (case, result.stderr, report)
    assert report["outcome"] == "REJECTED"
    assert report["cleanup"] == "UNKNOWN"
    assert report["parent_removed"] is False
    assert report["worker_started"] is False and report["cgroup_authority"] is False
    assert list((tmp_path / "lab-fixtures").iterdir())


@pytest.mark.parametrize("case", ["forbidden_fs", "forbidden_fs_v1"])
def test_forbidden_filesystem_is_rejected_before_any_parent_creation(tmp_path, case):
    result, report = execute(tmp_path, case)
    assert result.returncode == 20
    assert report["parent_removed"] is False
    assert not list((tmp_path / "lab-fixtures").iterdir())


def test_final_base_close_uncertainty_preserves_removal_fact_without_recreation(tmp_path):
    result, report = execute(tmp_path, "base_close_unknown")
    assert result.returncode == 20
    assert report["cleanup"] == "UNKNOWN"
    assert report["parent_removed"] is True
    assert not list((tmp_path / "lab-fixtures").iterdir())


def test_descriptor_accounting_detects_an_injected_duplicate_close_attempt(tmp_path):
    result, report = execute(tmp_path, "double_close_probe", tracker_failure=True)
    assert result.returncode == 20
    assert report["peer_exit"] == 98
    assert "not consumed exactly once" in result.stderr
