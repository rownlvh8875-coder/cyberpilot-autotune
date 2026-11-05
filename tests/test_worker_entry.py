"""Fixed native entry witness; security syscalls are NEVER forwarded in fixture mode."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def entry_build(tmp_path_factory):
    out = tmp_path_factory.mktemp("worker-entry-build")
    cc = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    commands = [
        cc
        + [
            "-nostdlib",
            "-static",
            "-fno-pie",
            "-no-pie",
            "-fno-stack-protector",
            "-fno-builtin",
            "-Wl,-e,_start",
            str(ROOT / "research/worker_entry/fixed_worker.c"),
            "-o",
            str(out / "fixed-worker"),
        ],
        cc
        + [
            "-Dsyscall=entry_test_syscall",
            "-c",
            str(ROOT / "research/worker_entry/entry_credential.c"),
            "-o",
            str(out / "credential-shim.o"),
        ],
        cc
        + [
            str(ROOT / "tests/native/worker_entry_driver.c"),
            str(ROOT / "tests/native/worker_entry_credential_shim.c"),
            str(out / "credential-shim.o"),
            "-Wl,--wrap=sendmsg",
            "-Wl,--wrap=recvmsg",
            "-Wl,--wrap=waitid",
            "-Wl,--wrap=close",
            "-Wl,--wrap=syscall",
            "-Wl,--wrap=poll",
            "-Wl,--wrap=__poll_chk",
            "-Wl,--wrap=clock_gettime",
            "-o",
            str(out / "entry-fixture"),
        ],
        cc
        + [
            str(ROOT / "research/worker_entry/integration.c"),
            str(ROOT / "research/worker_entry/entry_credential.c"),
            "-o",
            str(out / "entry-unwrapped"),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
    return out


def execute(entry_build, tmp_path, case="normal", *, unwrapped=False):
    (tmp_path / "lab-fixtures").mkdir(mode=0o700)
    binary = entry_build / ("entry-unwrapped" if unwrapped else "entry-fixture")
    result = subprocess.run(
        [str(binary)] if unwrapped else [str(binary), case],
        cwd=tmp_path,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert not result.stderr, result.stderr
    report = json.loads(result.stdout)
    assert report["cgroup_authority"] is False
    assert report["credential_kernel_verified"] is False
    return result, report


def test_real_fixed_exec_fd_parent_witness_with_simulated_credentials(entry_build, tmp_path):
    result, report = execute(entry_build, tmp_path)
    assert result.returncode == 0, report
    assert report["outcome"] == "FIXED_ENTRY_FIXTURE_COMPLETE"
    for field in [
        "original_exec",
        "fd_entry",
        "parent_relation",
        "kernel_sender",
        "parent_removed",
    ]:
        assert report[field] is True, (field, report)
    assert report["cleanup"] == "CONFIRMED"
    assert report["credential_boundary"] == "SIMULATED"
    assert not list((tmp_path / "lab-fixtures").iterdir())


def test_unwrapped_current_user_rejects_before_worker_birth(entry_build, tmp_path):
    result, report = execute(entry_build, tmp_path, unwrapped=True)
    assert result.returncode != 0
    assert report["outcome"] == "REJECTED"
    assert report["worker_started"] is False
    assert report["credential_boundary"] == "LIVE_PREFLIGHT_REJECTED"


@pytest.mark.parametrize(
    "case",
    [
        "nonce",
        "cohort",
        "generation",
        "sequence",
        "stage",
        "empty",
        "oversize",
        "partial_prefix",
        "partial_body",
        "extra",
        "rights",
        "wrong_sender",
        "missing_credentials",
        "credentials_uid",
        "credentials_gid",
        "image_identity",
        "parent_identity",
        "fd_mask",
        "exec_error",
        "early_exit",
        "leaked_directory",
        "owner_seal",
        "worker_seal",
        "prebirth_filter",
        "wait_unknown",
        "close_unknown",
        "duplicate",
        "truncated_control",
        "duplicate_credentials",
        "eof_credentials",
        "received_rights",
        "image_reuse",
        "owner_dead",
        "owner_dead_late",
        "clock_unavailable",
        "cancel_birth",
        "cancel_worker_birth",
        "preexec_message",
        "bind_magic",
        "bind_stage",
        "bind_sequence",
        "bind_parent",
        "bind_empty",
        "bind_oversize",
        "bind_partial",
        "finish_nonce",
        "finish_sequence",
    ],
)
def test_entry_failures_never_become_authority_or_retry(entry_build, tmp_path, case):
    result, report = execute(entry_build, tmp_path, case)
    assert result.returncode != 0, (case, report)
    assert report["outcome"] == "REJECTED"
    assert report["cleanup"] == "UNKNOWN"
    if case == "cancel_worker_birth":
        assert report["worker_started"] is True
    assert report["peer_exit"] != 98
    assert report["original_exec"] is None
    assert report["parent_removed"] is False


def test_new_entry_does_not_change_frozen_qualification_state():
    state = json.loads((ROOT / "evidence_parent_handoff.json").read_text())
    # Existing passive record is not an input to native execution/cleanup.
    assert state is not None
    text = (ROOT / "research/worker_entry/integration.c").read_text()
    assert "getenv(" not in text
    assert "argv" not in text
    assert "execveat" in text
    assert os.geteuid() != 0


def test_sealed_original_bytes_reject_inplace_mutation(entry_build, tmp_path):
    import shutil

    shutil.copy2(entry_build / "entry-fixture", tmp_path / "entry-fixture")
    shutil.copy2(entry_build / "fixed-worker", tmp_path / "fixed-worker")
    result = subprocess.run(
        [str(tmp_path / "entry-fixture"), "seal_probe"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"write_rejected": True, "truncate_rejected": True}


def test_source_name_replacement_after_capture_does_not_retarget_exec(entry_build, tmp_path):
    import shutil

    shutil.copy2(entry_build / "entry-fixture", tmp_path / "entry-fixture")
    shutil.copy2(entry_build / "fixed-worker", tmp_path / "fixed-worker")
    result, report = execute(tmp_path, tmp_path, "path_replaced")
    assert result.returncode == 0, report
    assert report["original_exec"] is True
    assert (tmp_path / "fixed-worker").stat().st_size == 3


@pytest.mark.parametrize("kind", ["empty", "script", "symlink", "writable", "dynamic"])
def test_untrusted_or_unsupported_worker_artifact_rejected(entry_build, tmp_path, kind):
    import shutil

    shutil.copy2(entry_build / "entry-fixture", tmp_path / "entry-fixture")
    worker = tmp_path / "fixed-worker"
    if kind == "symlink":
        worker.symlink_to(entry_build / "fixed-worker")
    elif kind == "dynamic":
        shutil.copy2("/usr/bin/true", worker)
    else:
        if kind == "writable":
            shutil.copy2(entry_build / "fixed-worker", worker)
        else:
            worker.write_bytes(b"#!/bin/sh\nexit 0\n" if kind == "script" else b"")
        worker.chmod(0o777 if kind == "writable" else 0o700)
    result, report = execute(tmp_path, tmp_path)
    assert result.returncode != 0 and report["worker_started"] is False


def test_final_ack_failure_preserves_completed_worker_birth_fact(entry_build, tmp_path):
    result, report = execute(entry_build, tmp_path, "final_ack")
    assert result.returncode != 0
    assert report["worker_started"] is True
    assert report["original_exec"] is None


def test_unknown_owner_exit_is_not_reported_as_no_worker_birth(entry_build, tmp_path):
    result, report = execute(entry_build, tmp_path, "unknown_owner_exit")
    assert result.returncode != 0
    assert report["worker_started"] is None


def test_recv_error_does_not_inspect_untouched_control_buffer(entry_build, tmp_path):
    result = subprocess.run(
        [str(entry_build / "entry-fixture"), "recv_error_probe"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"error_return": True, "control_unchanged": True}
