"""Execution boundary tests never boot QEMU or execute the guest ELF."""

import hashlib

import pytest

from tests.guest_raw_lifetime import runner


@pytest.mark.parametrize("case", ["OTHER", "", True, None, ["NORMAL"]])
def test_arbitrary_case_fails_before_reading_assets_or_starting_process(case):
    with pytest.raises(ValueError, match="FIXED_CASE_REQUIRED"):
        runner.capture(case)


def test_changed_asset_bytes_cannot_pass_the_fixed_digest(tmp_path):
    path = tmp_path / "payload"
    path.write_bytes(b"fixed")
    assert runner.verify_bytes(path, hashlib.sha256(b"fixed").hexdigest()) == b"fixed"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="FIXED_INPUT_CHANGED"):
        runner.verify_bytes(path, hashlib.sha256(b"fixed").hexdigest())


def test_vm_recipe_has_no_host_kernel_kvm_network_mount_or_arbitrary_command(tmp_path):
    args = runner.arguments(tmp_path / "owned-image.gz")
    assert args[args.index("-kernel") + 1] == str(runner.ASSETS / "patched-bzImage")
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert args[args.index("-smp") + 1] == "1"
    assert args[args.index("-m") + 1] == "512M"
    assert args[args.index("-nic") + 1] == "none"
    assert args[args.index("-monitor") + 1] == "none"
    assert not {"-enable-kvm", "-drive", "-fsdev", "-virtfs", "-netdev"} & set(args)
