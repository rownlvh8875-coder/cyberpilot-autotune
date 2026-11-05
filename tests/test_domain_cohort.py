"""Native integrated D lifecycle on private regular files; NOT real cgroups."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PIN = "e19ebd8c77df6bb47fdb1dd5e3561ee4caacb0e8515a946e78c14bdbc078898b"
DRIVER_PIN = "c7c6d2fbae7504fd83648bf057f9b740cb723d6cc6466aca03065d80ed68b8c7"


@pytest.fixture(scope="session")
def domain_build(tmp_path_factory):
    out = tmp_path_factory.mktemp("domain-cohort-build")
    source = ROOT / "src/native_e_lab/domain_supervisor.c"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == DOMAIN_PIN
    text = source.read_text()
    assert text.count("int main(int argc, char **argv)") == 1
    (out / "domain_reference.c").write_text(
        text.replace(
            "int main(int argc, char **argv)", "int dr_reference_main(int argc, char **argv)"
        )
    )
    source = ROOT / "tests/native/cohort_driver.c"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == DRIVER_PIN
    text = source.read_text().replace(
        "int main(int argc,char **argv)", "int dr_driver_main(int argc,char **argv)"
    )
    for symbol in ["syscall", "mkdirat", "waitid", "close", "clock_gettime"]:
        text = text.replace("__wrap_" + symbol, "dr_reference_" + symbol)
    (out / "cohort_driver_reference.c").write_text(text)
    cc = [
        "cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(out),
        "-I",
        str(ROOT / "src/native_e_lab"),
        "-I",
        str(ROOT / "tests/native"),
    ]
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
            str(ROOT / "research/domain_cohort/worker.c"),
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
            str(ROOT / "tests/native/domain_cohort_driver.c"),
            str(ROOT / "tests/native/cohort_manager.c"),
            str(ROOT / "research/domain_cohort/peer.c"),
            str(ROOT / "research/domain_cohort/policy.c"),
            str(ROOT / "tests/native/worker_entry_credential_shim.c"),
            str(out / "credential-shim.o"),
            str(ROOT / "research/factory_manager/request.c"),
            "-Wl,--wrap=sendmsg",
            "-Wl,--wrap=recvmsg",
            "-Wl,--wrap=close",
            "-Wl,--wrap=sd_bus_call",
            "-Wl,--wrap=shutdown",
            "-Wl,--wrap=waitid",
            "-Wl,--wrap=syscall",
            "-Wl,--wrap=mkdirat",
            "-Wl,--wrap=clock_gettime",
            "-Wl,--wrap=poll",
            "-Wl,--wrap=__poll_chk",
            "-Wl,--wrap=fstatfs",
            "-Wl,--wrap=openat",
            "-Wl,--wrap=write",
            "-Wl,--wrap=unlinkat",
            "-l:libsystemd.so.0",
            "-o",
            str(out / "domain-fixture"),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
    return out


def execute(domain_build, tmp_path, case="normal"):
    (tmp_path / "lab-fixtures").mkdir(mode=0o700)
    result = subprocess.run(
        [str(domain_build / "domain-fixture"), case],
        cwd=tmp_path,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert not result.stderr, result.stderr
    items = [json.loads(line) for line in result.stdout.splitlines()]
    reports = [x for x in items if "outcome" in x]
    audits = [x["domain_audit"] for x in items if "domain_audit" in x]
    assert len(reports) == 1 and len(audits) == 1
    report = reports[0]
    assert report["actual_manager"] is False and report["cgroup_authority"] is False
    assert report["credential_kernel_verified"] is False
    return result, report, audits[0]


def test_original_d_lifecycle_in_manager_owned_e(domain_build, tmp_path):
    result, report, audit = execute(domain_build, tmp_path)
    assert result.returncode == 0, (report, audit)
    assert report["worker_entry_verified"] is True and report["parent_removed"] is True
    assert audit["D_created"] == 1 and audit["birth_into_D_requests"] == 1
    assert audit["kill_writes"] == 1 and audit["original_worker_waits"] == 1
    assert audit["D_removed"] == 1
    assert audit["containment"] == "SIMULATED"
    assert report["library_close_result"] == "UNAVAILABLE"
    assert not list((tmp_path / "lab-fixtures").iterdir())


@pytest.mark.parametrize(
    "case",
    [
        "unbound_regular_P",
        "members_extra",
        "members_E",
        "descendants",
        "missing_stat",
        "events_populated",
        "events_duplicate",
        "name_replaced",
        "D_fd_reused",
        "kill_partial",
        "kill_unknown",
        "kill_close_unknown",
        "domain_wait_unknown",
        "not_sigkill",
        "cancel_w_birth",
        "late_duplicate",
        "worker_wrong_sender",
        "P_threaded",
        "D_create_error",
        "D_open_error",
        "kill_open_error",
        "late_descendant",
        "events_missing",
        "D_unlink_error",
        "D_unlink_unknown",
        "D_close_unknown",
        "domain_wait_exit137",
        "W_generation_clock_once",
        "P_partial_same_inode",
    ],
)
def test_unknown_domain_never_reclaims_or_retries(domain_build, tmp_path, case):
    result, report, audit = execute(domain_build, tmp_path, case)
    assert result.returncode != 0, (case, report, audit)
    assert report["worker_entry_verified"] is None
    assert audit["D_created"] <= 1 and audit["birth_into_D_requests"] <= 1
    assert audit["kill_writes"] <= 1 and audit["original_worker_waits"] <= 1
    if case not in ["late_duplicate", "D_unlink_unknown", "D_close_unknown"]:
        assert audit["D_removed"] == 0
    assert report["parent_removed"] is False
    assert audit["foreign_close_attempts"] == 0
    if case == "W_generation_clock_once":
        assert audit["kill_writes"] == 0
    if case == "P_partial_same_inode":
        assert audit["D_created"] == 0 and audit["birth_into_D_requests"] == 0


def test_no_real_cgroup_backend_rejects_before_domain_creation(domain_build, tmp_path):
    _, report, audit = execute(domain_build, tmp_path, "unbound_regular_P")
    assert report["worker_started"] is False
    assert audit["D_created"] == 0 and audit["birth_into_D_requests"] == 0
