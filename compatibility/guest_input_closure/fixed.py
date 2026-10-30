"""Fixed current cached cohort only; no compiler, loader or guest execution."""

import zlib
from pathlib import Path

from .contracts import InputSnapshot
from .filesystem import read_regular, scan_selected, scan_tree
from .inventory import parse_snapshot

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = "compatibility/guest_input_closure/evidence/current-snapshot.json.gz"
TOOLCHAIN = Path("/workspace/scratch/guest-backend.FY5icM/toolchain")
VM_SYSROOT = Path("/workspace/scratch/qemu-vm.Hkx9tc/sysroot")
FIXTURE_BUILD = Path("/workspace/scratch/guest-backend.FY5icM/build")
COLLECTOR_BUILD = Path("/workspace/scratch/guest-collector.SuLzWo/build")
KERNEL_SOURCE = Path("/workspace/scratch/guest-collector.SuLzWo/linux-source-6.12")
FIXTURE_IDS = tuple(f"HF{i:02d}" for i in range(1, 25))
REPO_FILES = (
    tuple(
        "compatibility/containment_backend_harmless/" + path
        for path in (
            "__init__.py",
            "guest_image.py",
            "host_cases.py",
            "host_main.py",
            "records.py",
            "reporting.py",
            "validation.py",
            "vm_runner.py",
            "host/broker.c",
            "host/common.h",
            "host/fixtures.c",
            "host/exec_helper.c",
            "host/guard.bpf.c",
            "host/build_manifest.json",
        )
    )
    + tuple(
        "compatibility/containment_guest_collector/" + path
        for path in (
            "__init__.py",
            "batch.py",
            "contracts.py",
            "evaluation.py",
            "host_main.py",
            "image.py",
            "validation.py",
            "vm_runner.py",
            "guest/collector.c",
            "guest/collector.h",
            "guest/fd_snapshot.c",
            "guest/build_manifest.json",
        )
    )
    + (
        "docs/evidence/guest_collector_sources.json",
        "docs/evidence/containment_backend_guest_sources.json",
    )
)
HOST_FILES = (
    "usr/bin/cc",
    "etc/alternatives/cc",
    "usr/bin/gcc",
    "usr/bin/gcc-14",
    "usr/bin/x86_64-linux-gnu-gcc-14",
    "usr/bin/as",
    "usr/bin/x86_64-linux-gnu-as",
    "usr/bin/ld",
    "usr/bin/x86_64-linux-gnu-ld",
    "usr/bin/x86_64-linux-gnu-ld.bfd",
    "usr/libexec/gcc/x86_64-linux-gnu/14/cc1",
    "usr/libexec/gcc/x86_64-linux-gnu/14/collect2",
    "usr/libexec/gcc/x86_64-linux-gnu/14/lto-wrapper",
    "usr/lib/gcc/x86_64-linux-gnu/14/crtbegin.o",
    "usr/lib/gcc/x86_64-linux-gnu/14/crtbeginT.o",
    "usr/lib/gcc/x86_64-linux-gnu/14/crtend.o",
    "usr/lib/gcc/x86_64-linux-gnu/14/libgcc.a",
    "usr/lib/gcc/x86_64-linux-gnu/14/libgcc_eh.a",
    "usr/lib/x86_64-linux-gnu/libc.a",
    "usr/lib/x86_64-linux-gnu/crt1.o",
    "usr/lib/x86_64-linux-gnu/crti.o",
    "usr/lib/x86_64-linux-gnu/crtn.o",
)
SOURCE_FILES = (
    "kernel/entry/common.c",
    "kernel/ptrace.c",
    "include/linux/ptrace.h",
    "include/uapi/linux/ptrace.h",
    "kernel/fork.c",
    "fs/proc/fd.c",
    "fs/exec.c",
    "kernel/exit.c",
)


def expected_snapshot() -> InputSnapshot:
    compressed = read_regular(REPO, SNAPSHOT_PATH, 4 * 1024 * 1024)
    decoder = zlib.decompressobj(31)
    try:
        raw = decoder.decompress(compressed, 32 * 1024 * 1024 + 1)
        if (
            not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
            or len(raw) > 32 * 1024 * 1024
        ):
            raise ValueError("snapshot gzip outside profile")
        return parse_snapshot(raw.decode("utf-8"))
    except (zlib.error, UnicodeError) as error:
        raise ValueError("invalid snapshot gzip/text") from error


def observe_fixed_inputs() -> tuple[InputSnapshot, tuple[bytes, ...]]:
    from compatibility.containment_guest_collector.image import build_collector_image

    from .legacy import load_checked_assets

    entries = (
        *scan_tree("toolchain_exact_tree", TOOLCHAIN),
        *scan_tree("vm_exact_tree", VM_SYSROOT),
        *scan_selected("repo_selected", REPO, REPO_FILES),
        *scan_selected(
            "fixture_selected", FIXTURE_BUILD, ("harmless-fixtures", "exec-helper", "guard.bpf.o")
        ),
        *scan_selected("collector_selected", COLLECTOR_BUILD, ("syscall-collector",)),
        *scan_selected("host_gcc_selected", Path("/"), HOST_FILES),
        *scan_selected("kernel_selected", KERNEL_SOURCE, SOURCE_FILES),
    )
    actual = InputSnapshot(entries)
    files, collector = load_checked_assets(
        actual,
        {
            "repo_selected": REPO,
            "toolchain_exact_tree": TOOLCHAIN,
            "vm_exact_tree": VM_SYSROOT,
            "fixture_selected": FIXTURE_BUILD,
            "collector_selected": COLLECTOR_BUILD,
            "host_gcc_selected": Path("/"),
        },
    )
    images = tuple(build_collector_image(files, collector, (fixture,)) for fixture in FIXTURE_IDS)
    return actual, images
