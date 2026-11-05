"""Native private sd-bus/M/E fixtures; no actual system manager or unit."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def binaries(tmp_path_factory):
    out = tmp_path_factory.mktemp("factory-build")
    cc = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    commands = [
        cc
        + [
            str(ROOT / "tests/native/factory_manager_driver.c"),
            str(ROOT / "tests/native/factory_fake_manager.c"),
            str(ROOT / "research/factory_manager/request.c"),
            "-Wl,--wrap=sd_bus_new",
            "-Wl,--wrap=sd_bus_set_fd",
            "-Wl,--wrap=sd_bus_negotiate_fds",
            "-Wl,--wrap=sd_bus_set_bus_client",
            "-Wl,--wrap=sd_bus_get_bus_id",
            "-Wl,--wrap=sd_bus_send",
            "-Wl,--wrap=sd_bus_call",
            "-Wl,--wrap=sd_bus_message_append_basic",
            "-Wl,--wrap=sd_bus_message_open_container",
            "-Wl,--wrap=sd_bus_message_close_container",
            "-Wl,--wrap=close",
            "-Wl,--wrap=waitid",
            "-Wl,--wrap=syscall",
            "-l:libsystemd.so.0",
            "-o",
            str(out / "factory-fixture"),
        ],
        cc
        + [
            str(ROOT / "research/factory_manager/factory.c"),
            str(ROOT / "research/factory_manager/unbound.c"),
            str(ROOT / "research/factory_manager/request.c"),
            "-l:libsystemd.so.0",
            "-o",
            str(out / "factory-unbound"),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
    return out


def execute(binaries, case="normal"):
    result = subprocess.run(
        [str(binaries / "factory-fixture"), case],
        cwd=binaries,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=12,
    )
    assert not result.stderr, result.stderr
    report = json.loads(result.stdout)
    assert report["actual_manager"] is False
    assert report["actual_unit_created"] is False
    assert report["worker_started"] is False
    return result, report


def test_real_private_sdbus_fd_and_manager_owned_e_lifecycle(binaries):
    result, report = execute(binaries)
    assert result.returncode == 0, report
    assert report["outcome"] == "PRIVATE_MANAGER_PROTOCOL_COMPLETE"
    assert report["start_attempts"] == 1
    assert report["e_birth"] is True
    assert report["e_parent_is_manager"] is True
    assert report["factory_adopted_e_pidfd"] is False
    assert report["explicit_e_shutdown"] is True
    assert report["manager_endpoint_retained"] is True
    assert report["cleanup"] == "NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE"


def test_unbound_default_does_not_open_any_host_manager_or_create_e(binaries):
    result = subprocess.run(
        [str(binaries / "factory-unbound")],
        capture_output=True,
        text=True,
        timeout=5,
    )
    report = json.loads(result.stdout)
    assert result.returncode != 0
    assert report["outcome"] == "UNAVAILABLE"
    assert report["start_attempts"] == 0 and report["e_birth"] is False


@pytest.mark.parametrize(
    "case",
    [
        "no_fds",
        "subscribe_error",
        "match_error",
        "wrong_owner",
        "owner_changed",
        "early_job",
        "wrong_job",
        "wrong_unit",
        "duplicate_job",
        "failed_job",
        "start_error",
        "start_timeout",
        "cancel_after_submit",
        "wrong_reply_type",
        "extra_property",
        "extra_fd",
        "bad_limit",
        "bad_mode",
        "bad_addref",
        "e_no_shutdown",
        "e_wrong_nonce",
        "e_extra",
        "unref_error",
        "wait_unknown",
        "close_unknown",
        "late_duplicate",
        "late_owner_change",
        "duplicate_after_reply",
        "client_no_fds",
        "not_bus_client",
        "bad_signature",
        "fd_wrong_type",
        "duplicate_property",
        "manager_wait_unknown",
        "bus_fd_reuse",
        "subscribe_cancel",
        "clone_return_uncertain",
        "generation_changed",
        "event_wrong_sender",
    ],
)
def test_unknown_or_invalid_lifecycle_never_completes_or_retries(binaries, case):
    result, report = execute(binaries, case)
    assert result.returncode != 0, (case, report)
    assert report["outcome"] != "PRIVATE_MANAGER_PROTOCOL_COMPLETE"
    assert report["start_attempts"] in (0, 1)
    assert report["cleanup"] != "CONFIRMED"


def test_new_backend_is_closed_and_not_a_resource_recovery_api():
    source = (ROOT / "research/factory_manager/factory.c").read_text()
    for forbidden in [
        "sd_bus_open_system(",
        "sd_bus_open_user(",
        "sd_bus_set_address(",
        "getenv(",
        "system(",
        "execvp(",
        "systemctl",
    ]:
        assert forbidden not in source
    assert "fm_run_fixed(void)" in source


def test_library_void_teardown_result_stays_unavailable(binaries):
    _, report = execute(binaries)
    assert report.get("library_close_result") == "UNAVAILABLE"
    assert report["cleanup"] != "CONFIRMED"


def test_second_factory_attempt_in_same_process_creates_nothing(binaries):
    result = subprocess.run(
        [str(binaries / "factory-fixture"), "twice"],
        cwd=binaries,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=12,
    )
    reports = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(reports) == 2
    assert reports[0]["outcome"] == "PRIVATE_MANAGER_PROTOCOL_COMPLETE"
    assert reports[1]["outcome"] == "ALREADY_ATTEMPTED"
    assert reports[1]["start_attempts"] == 0 and reports[1]["e_birth"] is None


@pytest.mark.parametrize("case", ["constructor_before_library", "constructor_before_transfer"])
def test_constructor_failure_releases_original_native_fds(binaries, case):
    result, report = execute(binaries, case)
    assert result.returncode != 0
    assert report["start_attempts"] == 0 and report["e_birth"] is False
