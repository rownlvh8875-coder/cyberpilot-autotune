"""Fixed image/VM boundary, never host-executing the ELF or arbitrary user commands."""

import pytest

from compatibility.containment_backend_harmless.guest_image import GUEST_FILES
from compatibility.guest_input_closure.archive import parse_image
from tests.experiments.guest_data_fd_handoff import runner


def test_guest_image_executes_only_fixed_case_and_scope():
    files = {
        name: (0o100444 if name == "guard.bpf.o" else 0o100755, b"fixture") for name in GUEST_FILES
    }
    binary = b"\x7fELF\x02\x01unit-test-not-executable"
    entries = {e.path: e for e in parse_image(runner.build_image(files, binary, "HH01"))}
    assert entries["data-fd-handoff-probe"].data == binary
    init = entries["init"].data
    assert b"/data-fd-handoff-probe --trace HH01\n" in init
    assert b"HFD_EXEC\n" in init and b"HFD_DONE\n" in init
    assert entries["etc/data-fd-handoff-scope"].data == (
        b"guest-data-fd-handoff-v1: fixed software guest only\n"
    )


@pytest.mark.parametrize("case", ["HH00", "HH08", "HH01;sh", None, ["HH01"]])
def test_no_arbitrary_case_or_command(case):
    with pytest.raises(ValueError):
        runner.build_image({}, b"\x7fELF\x02\x01", case)


def test_qemu_fixed_no_disks_network_or_host_probe_execution(tmp_path):
    args = runner.qemu_arguments(tmp_path / "fixed-initrd.gz")
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert args[args.index("-nic") + 1] == "none"
    assert args[args.index("-monitor") + 1] == "none"
    assert not set(args) & {"-drive", "-hda", "-virtfs", "-fsdev", "-qmp", "-enable-kvm"}
    assert "data-fd-handoff-probe" not in args[0]


@pytest.mark.parametrize("cases", [(), ("HH01", "HH01"), ("HH08",), ["HH01"]])
def test_invalid_run_rejected_before_assets_or_vm_access(cases):
    with pytest.raises(ValueError):
        runner.capture_cases(cases)


@pytest.mark.parametrize("timeout", [False, True])
def test_process_failure_retains_raw_bytes_and_completed_cases(monkeypatch, timeout):
    from types import SimpleNamespace

    from tests.test_guest_data_fd_handoff import PROGRAM, rows, serial

    files = {
        name: (0o100444 if name == "guard.bpf.o" else 0o100755, b"fixture") for name in GUEST_FILES
    }
    outcomes = iter(
        [
            SimpleNamespace(returncode=0, stdout=serial(rows())),
            SimpleNamespace(returncode=2, stdout=b"unrepaired failure\n"),
        ]
    )

    # Only external VM execution is replaced; real image/parser/checker run.
    def process(*args, **kwargs):
        result = next(outcomes)
        if timeout and result.returncode == 2:
            raise runner.subprocess.TimeoutExpired(args[0], 180, output=result.stdout)
        return result

    monkeypatch.setattr(runner.subprocess, "run", process)
    with pytest.raises(runner.CaptureUnavailable) as caught:
        runner._capture_cases(b"\x7fELF\x02\x01fake", PROGRAM, ("HH01", "HH02"), files)
    assert caught.value.raw == b"unrepaired failure\n"
    assert len(caught.value.completed) == 1
    assert caught.value.completed[0][0].case == "HH01"
