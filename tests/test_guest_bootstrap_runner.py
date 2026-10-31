"""Fixed explicit guest interface tests; no test boots QEMU or executes guest ELF."""

import gzip
import importlib
import importlib.util

import pytest


def api(name):
    module = "tests.guest_bootstrap." + name
    assert importlib.util.find_spec(module) is not None, "missing fixed guest API"
    return importlib.import_module(module)


@pytest.mark.parametrize("case", ["", "NORMAL;sh", "READ_LOSS", True, None, ["NORMAL"]])
def test_arbitrary_case_cannot_reach_asset_reads_or_process(case):
    with pytest.raises(ValueError, match="FIXED_CASE_REQUIRED"):
        api("runner").capture(case)


def test_image_is_deterministic_and_contains_only_the_fixed_driver_and_case():
    builder = api("image").build_image
    image = builder(b"\x7fELF\x02\x01synthetic", "SEED_FAIL")
    assert image == builder(b"\x7fELF\x02\x01synthetic", "SEED_FAIL")
    raw = gzip.decompress(image)
    assert b"SEED_FAIL" in raw and b"dev/console\0" in raw and b"TRAILER!!!\0" in raw
    assert b"/workspace" not in raw
    with pytest.raises(ValueError):
        builder(b"notELF", "NORMAL")


def test_frozen_vm_has_no_host_devices_network_sharedfs_or_arbitrary_payload(tmp_path):
    runner = api("runner")
    args = runner.arguments(tmp_path / "owned.gz")
    assert args[args.index("-kernel") + 1] == str(runner.ASSETS / "patched-bzImage")
    assert args[args.index("-smp") + 1] == "1" and args[args.index("-m") + 1] == "512M"
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert args[args.index("-nic") + 1] == "none" and args[args.index("-monitor") + 1] == "none"
    assert not {"-enable-kvm", "-drive", "-fsdev", "-virtfs", "-netdev", "-device"} & set(args)
