"""Fixed guest execution boundary tests never launch a VM or host-execute its ELF."""

import gzip
import importlib
import importlib.util

import pytest


def api(name):
    module = "tests.guest_fork_copy." + name
    assert importlib.util.find_spec(module) is not None, "missing fixed copy runner"
    return importlib.import_module(module)


@pytest.mark.parametrize("case", ["", "sh", "NORMAL;sh", True, None, ["NORMAL"]])
def test_arbitrary_case_is_rejected_before_input_reads_or_execution(case):
    with pytest.raises(ValueError, match="FIXED_CASE_REQUIRED"):
        api("runner").capture(case)


def test_fixed_image_contains_exact_case_no_host_path_and_is_deterministic():
    build = api("image").build_image
    first = build(b"\x7fELF\x02\x01test", "CONSTRUCTOR_FAIL")
    assert first == build(b"\x7fELF\x02\x01test", "CONSTRUCTOR_FAIL")
    raw = gzip.decompress(first)
    assert b"CONSTRUCTOR_FAIL" in raw and b"dev/console\0" in raw
    assert b"/workspace" not in raw
    with pytest.raises(ValueError):
        build(b"not ELF", "NORMAL")


def test_fixed_vm_no_host_kernel_kvm_network_devices_or_arbitrary_commands(tmp_path):
    runner = api("runner")
    args = runner.arguments(tmp_path / "image.gz")
    for key, value in (
        ("-accel", "tcg,thread=single"),
        ("-smp", "1"),
        ("-m", "512M"),
        ("-nic", "none"),
        ("-monitor", "none"),
    ):
        assert args[args.index(key) + 1] == value
    assert args[args.index("-kernel") + 1] == str(runner.ASSETS / "patched-bzImage")
    assert not {"-drive", "-fsdev", "-virtfs", "-enable-kvm", "-netdev", "-device"} & set(args)
