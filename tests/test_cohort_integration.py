"""M-owned E -> original P -> fixed W; credential changes simulated only."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def cohort_build(tmp_path_factory):
    out = tmp_path_factory.mktemp("cohort-build")
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
            str(ROOT / "tests/native/cohort_driver.c"),
            str(ROOT / "tests/native/cohort_manager.c"),
            str(ROOT / "research/cohort_integration/peer.c"),
            str(ROOT / "tests/native/worker_entry_credential_shim.c"),
            str(out / "credential-shim.o"),
            str(ROOT / "research/factory_manager/request.c"),
            "-Wl,--wrap=sendmsg",
            "-Wl,--wrap=recvmsg",
            "-Wl,--wrap=close",
            "-Wl,--wrap=mkdirat",
            "-Wl,--wrap=clock_gettime",
            "-Wl,--wrap=sd_bus_call",
            "-Wl,--wrap=shutdown",
            "-Wl,--wrap=waitid",
            "-Wl,--wrap=syscall",
            "-l:libsystemd.so.0",
            "-o",
            str(out / "cohort-fixture"),
        ],
        cc
        + [
            str(ROOT / "research/cohort_integration/cohort.c"),
            str(ROOT / "research/factory_manager/unbound.c"),
            str(ROOT / "research/factory_manager/request.c"),
            "-l:libsystemd.so.0",
            "-o",
            str(out / "cohort-unbound"),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
    return out


def execute(cohort_build, tmp_path, case="normal", *, unbound=False):
    if not unbound:
        (tmp_path / "lab-fixtures").mkdir(mode=0o700)
    result = subprocess.run(
        [str(cohort_build / ("cohort-unbound" if unbound else "cohort-fixture"))]
        + ([] if unbound else [case]),
        cwd=tmp_path,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=24,
    )
    assert not result.stderr, result.stderr
    items = [json.loads(line) for line in result.stdout.splitlines()]
    reports = [item for item in items if "outcome" in item]
    audits = [item["audit"] for item in items if "audit" in item]
    if not unbound:
        assert len(audits) == 1
        for report in reports:
            report["_audit"] = audits[0]
    assert reports
    for report in reports:
        assert report["actual_manager"] is False
        assert report["actual_unit_created"] is False
        assert report["cgroup_authority"] is False
        assert report["credential_kernel_verified"] is False
        assert report["factory_adopted_e_pidfd"] is False
    return result, reports[-1]


def test_manager_created_e_completes_original_p_and_fixed_worker(cohort_build, tmp_path):
    result, report = execute(cohort_build, tmp_path)
    assert result.returncode == 0, report
    assert report["outcome"] == "PRIVATE_COHORT_PROTOCOL_COMPLETE"
    assert report["start_attempts"] == 1
    for fact in [
        "e_birth",
        "worker_started",
        "parent_removed",
        "worker_entry_verified",
        "manager_owned_e",
        "explicit_e_shutdown",
    ]:
        assert report[fact] is True, (fact, report)
    assert report["library_close_result"] == "UNAVAILABLE"
    assert report["cleanup"] == "NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE"
    assert not list((tmp_path / "lab-fixtures").iterdir())


def test_default_unbound_creates_no_parent_or_process(cohort_build, tmp_path):
    result, report = execute(cohort_build, tmp_path, unbound=True)
    assert result.returncode != 0
    assert report["outcome"] == "UNAVAILABLE"
    assert report["start_attempts"] == 0
    assert report["e_birth"] is False and report["worker_started"] is False
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "case",
    [
        "grant_nonce",
        "grant_generation",
        "grant_cohort",
        "grant_sequence",
        "grant_empty",
        "grant_oversize",
        "grant_partial",
        "grant_no_fd",
        "grant_extra_fd",
        "grant_wrong_type",
        "commit_duplicate",
        "commit_extra",
        "ready_early_eof",
        "final_no_shutdown",
        "final_extra",
        "final_ack_error",
        "worker_seal",
        "owner_seal",
        "prebirth_filter",
        "worker_exec_error",
        "worker_wrong_sender",
        "cancel_e_birth",
        "cancel_w_birth",
        "manager_wait_unknown",
        "worker_wait_unknown",
        "factory_wait_unknown",
        "parent_close_unknown",
        "parent_name_replaced",
        "parent_fd_reused",
        "late_duplicate",
        "late_owner_change",
        "duplicate_after_reply",
        "start_timeout",
        "wrong_owner",
    ],
)
def test_cross_boundary_failure_never_promotes_or_retries(cohort_build, tmp_path, case):
    result, report = execute(cohort_build, tmp_path, case)
    assert result.returncode != 0, report
    assert report["outcome"] != "PRIVATE_COHORT_PROTOCOL_COMPLETE"
    assert report["cleanup"] == "UNKNOWN"
    assert report["start_attempts"] in (0, 1)
    assert report["worker_entry_verified"] is None
    assert report["parent_removed"] is False


def test_same_process_second_attempt_creates_nothing(cohort_build, tmp_path):
    result, report = execute(cohort_build, tmp_path, "twice")
    assert result.returncode != 0
    assert report["outcome"] == "ALREADY_ATTEMPTED" and report["start_attempts"] == 0
    assert not list((tmp_path / "lab-fixtures").iterdir())


def test_late_failure_preserves_observed_worker_birth(cohort_build, tmp_path):
    _, report = execute(cohort_build, tmp_path, "late_duplicate")
    assert report["worker_started"] is True
    assert report["worker_entry_verified"] is None


def test_original_creation_and_wait_are_each_once(cohort_build, tmp_path):
    _, report = execute(cohort_build, tmp_path)
    audit = report["_audit"]
    assert audit["births"] == [1, 1, 1]
    assert audit["waits"] == [1, 1, 1]
    assert audit["exec_attempts"] == 1
    assert audit["start_attempts"] == 1 and audit["unrefs"] == 1


@pytest.mark.parametrize(
    "case",
    [
        "cancel_e_birth",
        "cancel_w_birth",
        "worker_wait_unknown",
        "manager_wait_unknown",
        "factory_wait_unknown",
    ],
)
def test_cancel_or_unknown_consumes_original_handle_only_once(cohort_build, tmp_path, case):
    _, report = execute(cohort_build, tmp_path, case)
    audit = report["_audit"]
    assert all(n <= 1 for n in audit["births"] + audit["waits"])
    assert audit["start_attempts"] <= 1 and audit["exec_attempts"] <= 1


def test_single_unavailable_context_clock_rejects_before_worker(cohort_build, tmp_path):
    result, report = execute(cohort_build, tmp_path, "context_clock_once")
    assert result.returncode != 0, report
    assert report["worker_entry_verified"] is None
    assert report["_audit"]["births"][2] == 0
