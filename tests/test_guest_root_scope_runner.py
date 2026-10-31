"""Fixed source/VM boundary. No test launches QEMU or the guest ELF."""

import gzip
import hashlib
import importlib
import importlib.util

import pytest


def api(name):
    module = "tests.guest_root_scope." + name
    assert importlib.util.find_spec(module) is not None, "missing fixed guest API"
    return importlib.import_module(module)


@pytest.mark.parametrize("case", ["", "NORMAL;sh", "FORCED_LOSS", True, None, ["NORMAL"]])
def test_arbitrary_workload_never_reaches_asset_read_or_process(case):
    with pytest.raises(ValueError, match="FIXED_CASE_REQUIRED"):
        api("runner").capture(case)


def test_image_keeps_exact_new_case_and_only_fixed_members():
    builder = api("image").build_image
    image = builder(b"\x7fELF\x02\x01synthetic", "ROOT_BIRTH_LOSS")
    assert (
        hashlib.sha256(image).hexdigest()
        == hashlib.sha256(builder(b"\x7fELF\x02\x01synthetic", "ROOT_BIRTH_LOSS")).hexdigest()
    )
    raw = gzip.decompress(image)
    assert b"ROOT_BIRTH_LOSS" in raw and b"TRAILER!!!\0" in raw
    assert b"dev/console\0" in raw and b"case\0" in raw
    assert b"/workspace" not in raw
    with pytest.raises(ValueError):
        builder(b"not ELF", "NORMAL")
    with pytest.raises(ValueError):
        builder(b"\x7fELF\x02\x01", "FORCED_LOSS")


def test_fixed_vm_recipe_only_prepared_guest_no_host_devices_or_network(tmp_path):
    runner = api("runner")
    args = runner.arguments(tmp_path / "owned.gz")
    assert args[args.index("-kernel") + 1] == str(runner.ASSETS / "patched-bzImage")
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert args[args.index("-smp") + 1] == "1"
    assert args[args.index("-m") + 1] == "512M"
    assert args[args.index("-nic") + 1] == "none"
    assert args[args.index("-monitor") + 1] == "none"
    assert not {"-enable-kvm", "-drive", "-fsdev", "-virtfs", "-netdev", "-device"} & set(args)


def test_source_drift_rejected_with_original_bound_verifier(tmp_path):
    verify = api("runner").verify_bytes
    path = tmp_path / "fixed"
    path.write_bytes(b"original")
    assert verify(path, hashlib.sha256(b"original").hexdigest()) == b"original"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="FIXED_INPUT_CHANGED"):
        verify(path, hashlib.sha256(b"original").hexdigest())
