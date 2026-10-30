"""Fixed opt-in runner/image must not become an arbitrary execution surface."""

import subprocess
from pathlib import Path

import pytest

from tests.fixtures.guest_consumption import INPUT, module


def test_observed_program_size_must_match_pinned_binary_profile():
    from tests.fixtures.guest_consumption import PROGRAM_SHA, rows, text

    r = rows()
    r[1]["values"][3] = 2
    with pytest.raises(ValueError):
        module("vm_runner").observation_from_log(text(r), PROGRAM_SHA, binary_size=1)


def guest_files():
    from compatibility.containment_backend_harmless.guest_image import GUEST_FILES

    return {name: (0o100444 if name == "guard.bpf.o" else 0o100755, b"x") for name in GUEST_FILES}


def test_derived_image_carries_exact_inputs_and_separate_fixed_program():
    from compatibility.guest_input_closure.archive import parse_image

    binary = b"\x7fELF\x02\x01example"
    image = module("image").build_image(guest_files(), binary, "CP01")
    entries = {e.path: e for e in parse_image(image)}
    assert entries["consumption-probe"].data == binary
    assert (
        entries["input/sample.bin"].data == INPUT and entries["input/sample.bin"].mode == 0o100444
    )
    assert entries["etc/guest-consumption-scope"].mode == 0o100444
    assert entries["harmless-fixtures"].data == b"x"


@pytest.mark.parametrize("case", ["", "CP00", "HF01", "CP01;id", "CP01 CP02", None])
def test_unknown_case_cannot_produce_an_image_or_start_a_guest(case):
    with pytest.raises(ValueError):
        module("image").build_image(guest_files(), b"binary", case)
    with pytest.raises(ValueError):
        module("vm_runner").capture_case(case)


def test_missing_guest_asset_or_nonelf_payload_does_not_create_an_image():
    image = module("image")
    for assets, binary in (({}, b"\x7fELF\x02\x01"), (guest_files(), b"not ELF")):
        with pytest.raises(ValueError):
            image.build_image(assets, binary, "CP01")


@pytest.mark.parametrize("image_name", ["/owned/new.cpio.gz", "/owned/with space.cpio.gz"])
def test_qemu_recipe_has_no_network_disks_shares_monitor_or_passthrough(image_name):
    image = Path(image_name)
    args = module("vm_runner").qemu_arguments(image)
    for option, value in (
        ("-accel", "tcg,thread=single"),
        ("-smp", "1"),
        ("-m", "768M"),
        ("-nic", "none"),
        ("-monitor", "none"),
        ("-initrd", str(image)),
    ):
        assert args[args.index(option) + 1] == value
    assert not set(args) & {"-drive", "-hda", "-fsdev", "-virtfs", "-qmp", "-enable-kvm", "-device"}


def test_default_cli_and_arbitrary_options_have_no_io_or_execution(monkeypatch, capsys):
    cli = module("host_main")

    def forbidden(*args, **kwargs):
        raise AssertionError("default CLI attempted IO/process")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    for args in (
        [],
        ["--all"],
        ["--capture", "HF01"],
        ["--capture", "CP01", "--command", "sh"],
        ["--capture", "CP01;id"],
    ):
        assert cli.main(args) == 2 and capsys.readouterr().out == ""


def test_binary_manifest_cannot_enable_permissions_or_choose_another_binary():
    runner = module("vm_runner")
    for value in (
        {},
        {"schema": "future"},
        {"permissions": {"application_authorized": True}},
        {"binary": {"path": "/bin/sh"}},
    ):
        with pytest.raises(ValueError):
            runner.validate_build_manifest(value)


def test_failed_guest_keeps_original_raw_bytes_and_does_not_retry(monkeypatch, tmp_path):
    import tempfile

    runner = module("vm_runner")
    real_temporary_directory = tempfile.TemporaryDirectory
    monkeypatch.setattr(runner.sys, "platform", "linux")
    monkeypatch.setattr(
        runner, "_load_assets", lambda: (guest_files(), b"\x7fELF\x02\x01example", {})
    )
    monkeypatch.setattr(
        runner.tempfile,
        "TemporaryDirectory",
        lambda **kwargs: real_temporary_directory(dir=tmp_path),
    )
    raw = b"original-console:" + b"x" * 6000 + b"\xff"
    calls = []

    def failed_guest(args, **kwargs):
        calls.append(args)
        assert args[args.index("-nic") + 1] == "none" and kwargs["timeout"] == 180
        assert Path(args[args.index("-initrd") + 1]).is_file()
        return subprocess.CompletedProcess(args, 2, raw)

    monkeypatch.setattr(runner.subprocess, "run", failed_guest)
    with pytest.raises(runner.CaptureUnavailable) as caught:
        runner.capture_case("CP01")
    assert caught.value.raw == raw and len(calls) == 1
