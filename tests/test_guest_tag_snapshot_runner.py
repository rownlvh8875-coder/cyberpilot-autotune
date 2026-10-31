"""Exercise memory image, fixed runner boundary and real scalar-copy helper."""

import importlib
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    try:
        return importlib.import_module("tests.guest_tag_snapshot." + name)
    except ModuleNotFoundError:
        pytest.fail("MISSING_FIXED_TAG_SNAPSHOT_RUNNER")


def test_memory_image_is_deterministic_and_keeps_case_separate():
    build = module("image").build_image
    first = build(b"\x7fELF\x02\x01test-only", "NORMAL")
    assert first.startswith(b"\x1f\x8b") and first == build(b"\x7fELF\x02\x01test-only", "NORMAL")
    assert first != build(b"\x7fELF\x02\x01test-only", "POINTER_LOSS")
    import gzip

    raw = gzip.decompress(first)
    assert b"init\x00" in raw and b"case\x00" in raw and b"NORMAL" in raw


@pytest.mark.parametrize("case", [None, True, "", "../NORMAL", "TASK_FAIL"])
def test_nonfixed_case_cannot_build_or_execute(case):
    with pytest.raises(ValueError, match="FIXED_CASE"):
        module("image").build_image(b"\x7fELF\x02\x01", case)
    with pytest.raises(ValueError, match="FIXED_CASE"):
        module("runner").capture(case)


@pytest.mark.parametrize(
    "binary", [None, b"", b"#!/bin/sh", b"\x7fELF\x01\x01", b"x" * (2**22 + 1)]
)
def test_bad_init_input_rejected_before_image(binary):
    with pytest.raises(ValueError, match="ELF"):
        module("image").build_image(binary, "NORMAL")


def test_arguments_are_software_only_and_use_only_new_fixed_kernel():
    args = module("runner").arguments(Path("/tmp/explicit-image.gz"))
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert args[args.index("-smp") + 1] == "1"
    assert args[args.index("-m") + 1] == "512M"
    assert args[args.index("-nic") + 1] == "none"
    assert Path(args[args.index("-kernel") + 1]) == Path(
        "/workspace/scratch/post-reference-tag-producer.NaoDTY/patched-bzImage"
    )
    assert not {"-enable-kvm", "-virtfs", "-fsdev", "-drive", "-device", "-netdev"} & set(args)


def test_native_saved_scalar_copy_survives_target_mutation(tmp_path):
    if shutil.which("gcc") is None:
        pytest.skip("native C probe requires gcc; explicit author run is separate")
    result = module("native_probe").probe(ROOT, tmp_path)
    assert result.splitlines() == ["SAVED_SCALARS_PASS"]
