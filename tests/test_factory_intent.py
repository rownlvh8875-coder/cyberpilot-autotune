"""Native intent transaction, real private FS + synthetic manager; no host apply."""

import json
import os
import signal
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def binaries(tmp_path_factory):
    out = tmp_path_factory.mktemp("intent-build")
    cc = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-fvisibility=hidden"]
    extra = os.environ.get("FI_TEST_CFLAGS", "").split()
    sources = [
        str(ROOT / x)
        for x in [
            "research/factory_intent/intent.c",
            "research/factory_intent/factory.c",
            "research/factory_manager/factory.c",
            "research/factory_manager/request.c",
        ]
    ]
    # Historical main is renamed only in a disposable build copy.
    old = (ROOT / "research/factory_manager/factory.c").read_text()
    reference = out / "factory_reference.c"
    reference.write_text(
        old.replace(
            '#include "../parent_handoff/handoff.c"',
            '#include "' + str(ROOT / "research/parent_handoff/handoff.c") + '"',
        )
        .replace(
            '#include "internal.h"',
            '#include "' + str(ROOT / "research/factory_manager/internal.h") + '"',
        )
        .replace(
            "int main(void) {return fm_run_fixed();}",
            "int fi_reference_main(void) {return fm_run_fixed();}",
        )
    )
    sources[2] = str(reference)
    wrappers = [
        "openat",
        "write",
        "pread",
        "__pread_chk",
        "fsync",
        "close",
        "clock_gettime",
        "getrandom",
        "fcntl",
        "sd_bus_call",
        "syscall",
    ]
    cmd = (
        cc
        + extra
        + sources
        + [
            str(ROOT / "tests/native/factory_intent_driver.c"),
            str(ROOT / "tests/native/factory_fake_manager.c"),
        ]
    )
    cmd += ["-Wl,--wrap=" + x for x in wrappers]
    cmd += ["-l:libsystemd.so.0", "-o", str(out / "fixture")]
    r = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
    assert r.returncode == 0, r.stderr
    cmd = (
        cc
        + extra
        + sources
        + [
            str(ROOT / "research/factory_intent/unbound.c"),
            str(ROOT / "research/factory_manager/unbound.c"),
            "-DFI_STANDALONE",
            "-l:libsystemd.so.0",
            "-o",
            str(out / "unbound"),
        ]
    )
    r = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return out


@pytest.fixture
def scope(tmp_path):
    tmp_path.chmod(0o700)
    (tmp_path / "state").mkdir(mode=0o700)
    return tmp_path


def execute(binaries, scope, case="normal"):
    r = subprocess.run(
        [str(binaries / "fixture"), case],
        cwd=scope,
        env={"LANG": "C.UTF-8"},
        text=True,
        capture_output=True,
        timeout=14,
    )
    assert not r.stderr, r.stderr
    lines = [json.loads(x) for x in r.stdout.splitlines()]
    assert lines
    return r, lines[-1], lines


def test_durable_intent_precedes_manager_and_is_never_removed(binaries, scope):
    r, data, lines = execute(binaries, scope)
    assert r.returncode == 0, data
    assert data["outcome"] == "PRIVATE_FACTORY_WITH_DURABLE_INTENT"
    assert data["intent_created"] is True and data["intent_durable"] is True
    assert data["manager_invoked"] is True and data["native_release"] == "PARTIAL_REFS_RETAINED"
    assert lines[0]["start_attempts"] == 1
    assert data["actual_manager"] is False and data["worker_started"] is False
    leaf = scope / "state/attempt.intent"
    assert stat.S_IMODE(leaf.stat().st_mode) == 0o600
    assert leaf.stat().st_size == 64 and leaf.stat().st_nlink == 1
    before = leaf.read_bytes()
    r, data, lines = execute(binaries, scope)
    assert r.returncode != 0 and data["outcome"] == "DENIED_EXISTING_INTENT"
    assert data["manager_invoked"] is False and len(lines) == 1
    assert leaf.read_bytes() == before


def test_default_unbound_creates_nothing(binaries, scope):
    r = subprocess.run(
        [str(binaries / "unbound")], cwd=scope, capture_output=True, text=True, timeout=4
    )
    data = json.loads(r.stdout)
    assert r.returncode != 0 and data["outcome"] == "UNAVAILABLE"
    assert data["intent_created"] is False and data["manager_invoked"] is False
    assert not list((scope / "state").iterdir())


@pytest.mark.parametrize(
    "kind", ["empty", "garbage", "receipt", "symlink", "directory", "fifo", "hardlink"]
)
def test_preexisting_intent_never_becomes_authority(binaries, scope, kind):
    leaf = scope / "state/attempt.intent"
    target = scope / "foreign"
    target.write_bytes(b'{"outcome":"SUCCESS","intent_durable":true}')
    if kind == "symlink":
        leaf.symlink_to(target)
    elif kind == "directory":
        leaf.mkdir()
    elif kind == "fifo":
        os.mkfifo(leaf)
    elif kind == "hardlink":
        leaf.hardlink_to(target)
    else:
        leaf.write_bytes(
            b"" if kind == "empty" else target.read_bytes() if kind == "receipt" else b"bad"
        )
    r, data, lines = execute(binaries, scope)
    assert r.returncode != 0 and data["outcome"] == "DENIED_EXISTING_INTENT"
    assert data["manager_invoked"] is False and len(lines) == 1
    assert target.read_bytes() == b'{"outcome":"SUCCESS","intent_durable":true}'


@pytest.mark.parametrize(
    "case",
    [
        "partial_write",
        "write_unknown",
        "file_fsync",
        "root_fsync",
        "short_read",
        "tamper",
        "root_replace",
        "leaf_replace",
        "leaf_unlink",
        "file_mode",
        "file_hardlink",
        "root_mode",
        "file_fd_reuse",
        "file_same_inode_reuse",
        "root_fd_reuse",
        "root_same_inode_reuse",
        "scope_partial",
        "anchor_failure",
        "clock_failure",
        "random_failure",
        "random_short",
        "open_unknown",
        "zero_write",
        "negative_write",
        "file_fsync_unknown",
        "root_fsync_unknown",
        "file_socket_reuse",
        "root_socket_reuse",
        "read_unknown",
        "clock_invalid",
    ],
)
def test_failure_cannot_start_manager_or_retry(binaries, scope, case):
    r, data, lines = execute(binaries, scope, case)
    assert r.returncode != 0, (case, data)
    assert data["manager_invoked"] is False and len(lines) == 1
    assert (
        data["intent_durable"] is not True
        or data["outcome"] != "PRIVATE_FACTORY_WITH_DURABLE_INTENT"
    )
    assert data["write_calls"] <= 1 and data["file_fsync_calls"] <= 1
    assert data["root_fsync_calls"] <= 1 and data["start_after_intent_failure"] == 0
    if case in {
        "file_fd_reuse",
        "file_same_inode_reuse",
        "root_fd_reuse",
        "root_same_inode_reuse",
        "file_socket_reuse",
        "root_socket_reuse",
    }:
        assert data["foreign_fd_open"] is True


@pytest.mark.parametrize(
    "case", ["close_unknown", "close_fd_reuse", "manager_failure", "post_manager_tamper"]
)
def test_late_unknown_preserves_intent_and_denies_next_process(binaries, scope, case):
    r, data, _ = execute(binaries, scope, case)
    assert r.returncode != 0 and data["manager_invoked"] is True
    assert data["outcome"] != "PRIVATE_FACTORY_WITH_DURABLE_INTENT"
    assert (scope / "state/attempt.intent").exists()
    if case == "close_fd_reuse":
        assert data["foreign_fd_open"] is True
    r, data, _ = execute(binaries, scope)
    assert r.returncode != 0 and data["manager_invoked"] is False


def test_same_process_second_request_is_denied_without_scope_lookup(binaries, scope):
    r, data, lines = execute(binaries, scope, "twice")
    assert r.returncode != 0 and data["outcome"] == "ALREADY_ATTEMPTED"
    assert data["manager_invoked"] is False
    assert sum(x.get("start_attempts", 0) for x in lines) == 1
    assert data["scope_calls"] == 1
    assert data["intent_durable"] is None


def test_parallel_factories_have_exactly_one_winner(binaries, scope):
    jobs = [
        subprocess.Popen(
            [str(binaries / "fixture"), "normal"],
            cwd=scope,
            env={"LANG": "C.UTF-8"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for _ in range(2)
    ]
    values = []
    for job in jobs:
        out, err = job.communicate(timeout=14)
        assert not err
        values.append([json.loads(x) for x in out.splitlines()])
    assert sorted(job.returncode for job in jobs) == [0, 20]
    assert sum(line.get("start_attempts", 0) for group in values for line in group) == 1
    assert sorted(group[-1]["outcome"] for group in values) == [
        "DENIED_EXISTING_INTENT",
        "PRIVATE_FACTORY_WITH_DURABLE_INTENT",
    ]


@pytest.mark.parametrize("case", ["pause_after_create", "pause_after_durable"])
def test_new_attempt_after_original_process_killed_is_denied(binaries, scope, case):
    job = subprocess.Popen(
        [str(binaries / "fixture"), case],
        cwd=scope,
        env={"LANG": "C.UTF-8"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Only this newly created direct child's original Popen handle is signalled.
    import select

    assert select.select([job.stdout], [], [], 3)[0]
    assert job.stdout.readline() == "PAUSED\n"
    job.send_signal(signal.SIGKILL)
    out, err = job.communicate(timeout=4)
    assert job.returncode == -signal.SIGKILL and not out and not err
    r, data, lines = execute(binaries, scope)
    assert r.returncode != 0 and data["outcome"] == "DENIED_EXISTING_INTENT"
    assert data["manager_invoked"] is False and len(lines) == 1


def test_unbound_rejects_command_arguments(binaries, scope):
    r = subprocess.run(
        [str(binaries / "unbound"), "--recover"], cwd=scope, capture_output=True, timeout=4
    )
    assert r.returncode != 0 and not list((scope / "state").iterdir())


def test_fixed_api_cannot_read_receipts_or_control_existing_host_resources():
    text = "\n".join(
        (ROOT / "research/factory_intent" / x).read_text()
        for x in ["factory.c", "intent.c", "unbound.c"]
    )
    for forbidden in [
        "unlink(",
        "unlinkat(",
        "system(",
        "getenv(",
        "sd_bus_open_system(",
        "sd_bus_open_user(",
        "pidfd_open(",
        "execvp(",
        "ftruncate(",
        "flock(",
    ]:
        assert forbidden not in text
    assert "fi_run_fixed(void)" in text


@pytest.mark.parametrize("kind", ["root_symlink", "root_mode", "parent_mode", "missing_root"])
def test_wrong_scope_rejected_before_intent(binaries, scope, kind):
    if kind == "root_symlink":
        (scope / "state").rename(scope / "actual")
        (scope / "state").symlink_to(scope / "actual")
    elif kind == "root_mode":
        (scope / "state").chmod(0o750)
    elif kind == "parent_mode":
        scope.chmod(0o750)
    else:
        (scope / "state").rename(scope / "absent")
    r, data, lines = execute(binaries, scope)
    assert r.returncode != 0 and not data["manager_invoked"] and len(lines) == 1
    assert data["intent_created"] is False


@pytest.mark.parametrize("case", ["leaf_anchor_reuse", "root_anchor_reuse"])
def test_final_anchor_replacement_is_never_closed_by_inode_only_check(binaries, scope, case):
    r, data, _ = execute(binaries, scope, case)
    assert data["foreign_fd_open"] is True
    assert data["native_release"] != "CONFIRMED"
    assert (scope / "state/attempt.intent").exists()


@pytest.mark.parametrize(
    "case", ["open_unknown", "write_unknown", "file_fsync_unknown", "root_fsync_unknown"]
)
def test_unknown_durability_is_null_not_false(binaries, scope, case):
    r, data, _ = execute(binaries, scope, case)
    assert r.returncode != 0 and data["manager_invoked"] is False
    assert data["intent_durable"] is None


def test_existing_marker_durability_is_not_inferred(binaries, scope):
    (scope / "state/attempt.intent").write_bytes(b"uninspected existing marker")
    r, data, _ = execute(binaries, scope)
    assert r.returncode != 0 and data["intent_durable"] is None


def test_pause_fixture_has_an_independent_time_bound(binaries, scope):
    job = subprocess.Popen(
        [str(binaries / "fixture"), "pause_after_create"],
        cwd=scope,
        env={"LANG": "C.UTF-8"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        import select

        assert select.select([job.stdout], [], [], 3)[0]
        assert job.stdout.readline() == "PAUSED\n"
        assert job.wait(timeout=6) == -signal.SIGALRM
    finally:
        if job.poll() is None:
            job.kill()
        job.communicate(timeout=4)
    r, data, _ = execute(binaries, scope)
    assert r.returncode != 0 and not data["manager_invoked"]
