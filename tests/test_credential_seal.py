"""Native credential component; every component syscall is interposed, never forwarded."""

import errno
import struct
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def build_probe(tmp_path):
    out = tmp_path / "seal-probe"
    command = [
        "cc",
        "-std=c11",
        "-O0",
        "-g",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(ROOT / "research/credential_seal"),
        str(ROOT / "research/credential_seal/seal.c"),
        str(ROOT / "tests/native/credential_seal_driver.c"),
        "-Wl,--wrap=syscall",
        "-o",
        str(out),
    ]
    built = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert built.returncode == 0, built.stderr
    return out


def execute(tmp_path, mode, scenario="normal", fail_at=0):
    probe = build_probe(tmp_path)
    result = subprocess.run(
        [str(probe), mode, scenario, str(fail_at), "fixture"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, (result.returncode, result.stderr)
    return result.stdout


def policy(tmp_path):
    return [tuple(map(int, x.split(","))) for x in execute(tmp_path, "filter").splitlines()]


def verdict(program, nr, args=(), arch=0xC000003E):
    """Independent classic-BPF interpreter, not the C builder's predicates."""
    data = struct.pack("<iIQ6Q", nr, arch, 0, *(tuple(args) + (0,) * (6 - len(args))))
    a = 0
    pc = 0
    for _ in range(512):
        code, jt, jf, k = program[pc]
        if code == 0x20:
            a = struct.unpack_from("<I", data, k)[0]
            pc += 1
        elif code == 0x15:
            pc += 1 + (jt if a == k else jf)
        elif code == 0x35:
            pc += 1 + (jt if a >= k else jf)
        elif code == 0x06:
            return k
        else:
            pytest.fail(f"unsupported BPF opcode {code}")
        assert 0 <= pc < len(program)
    pytest.fail("unbounded BPF program")


@pytest.mark.parametrize(
    "nr,args,want",
    [
        (117, (18001, 18001, 18001), 0x7FFF0000),
        (119, (18002, 18002, 18002), 0x7FFF0000),
        (116, (0, 0), 0x7FFF0000),
        (117, (0, 18001, 18001), 0x50000 | errno.EPERM),
        (117, (18001, 17001, 18001), 0x50000 | errno.EPERM),
        (117, (18001, 18001, 17001), 0x50000 | errno.EPERM),
        (117, (18001 | (1 << 32), 18001, 18001), 0x50000 | errno.EPERM),
        (119, (18002, 18002 | (1 << 32), 18002), 0x50000 | errno.EPERM),
        (116, (1, 0), 0x50000 | errno.EPERM),
        (116, (0, 1234), 0x50000 | errno.EPERM),
        (116, (1 << 32, 0), 0x50000 | errno.EPERM),
        (105, (0,), 0x50000 | errno.EPERM),  # setuid
        (113, (0, 0), 0x50000 | errno.EPERM),  # setreuid
        (122, (0,), 0x50000 | errno.EPERM),  # setfsuid
        (106, (0,), 0x50000 | errno.EPERM),
        (114, (0, 0), 0x50000 | errno.EPERM),
        (123, (0,), 0x50000 | errno.EPERM),
        (0x40000000 | 117, (18001,) * 3, 0x80000000),
        (1, (), 0x7FFF0000),  # unrelated write: this is NOT a complete sandbox
    ],
)
def test_generated_policy_restricts_real_syscall_arguments(tmp_path, nr, args, want):
    assert verdict(policy(tmp_path), nr, args) == want


def test_non_native_abi_fails_closed(tmp_path):
    assert verdict(policy(tmp_path), 117, (18001,) * 3, arch=0x40000003) == 0x80000000


@pytest.mark.parametrize("mode,want", [("worker", "18001"), ("owner", "17001")])
def test_seal_executes_fixed_order_and_readback_without_reentry(tmp_path, mode, want):
    output = execute(tmp_path, mode)
    rows = dict(line.split("=", 1) for line in output.splitlines())
    assert rows["result"] == "0"
    assert rows["repeat"] == "3"
    assert rows["repeat_writes"] == "0"
    assert rows["uid"] == want
    assert rows["cap"] == "0" and rows["groups"] == "0"
    operations = rows["trace"].split(",")
    assert operations[0] == "filter"
    assert operations.index("groups") < operations.index("capclear")
    if mode == "worker":
        assert operations.index("groups") < operations.index("gid") < operations.index("uid")
        assert operations.index("uid") < operations.index("ambient") < operations.index("capclear")
        assert operations[-1] == "pdeath"
    else:
        assert "uid" not in operations and "gid" not in operations and "pdeath" not in operations


@pytest.mark.parametrize(
    "scenario",
    [
        "bad_profile",
        "initial_uid",
        "initial_caps",
        "initial_ambient",
        "initial_nnp",
        "threads",
        "missing",
        "duplicate",
        "oversize",
        "read_error",
    ],
)
def test_unproven_preflight_never_mutates_credentials(tmp_path, scenario):
    rows = dict(line.split("=", 1) for line in execute(tmp_path, "worker", scenario).splitlines())
    assert rows["result"] == "1"
    assert rows["writes"] == "0"
    assert rows["repeat"] == "3"


@pytest.mark.parametrize("step", range(1, 8))
def test_ambiguous_mutation_consumes_attempt_without_retry_or_rollback(tmp_path, step):
    rows = dict(
        line.split("=", 1) for line in execute(tmp_path, "worker", "normal", step).splitlines()
    )
    assert rows["result"] == "2"
    assert rows["writes"] == str(step)
    assert rows["repeat"] == "3" and rows["repeat_writes"] == "0"


@pytest.mark.parametrize(
    "scenario",
    [
        "saved_uid",
        "fs_uid",
        "saved_gid",
        "fs_gid",
        "post_caps",
        "post_ambient",
        "post_groups",
        "post_nnp",
        "post_missing",
        "post_duplicate",
        "pdeath_wrong",
    ],
)
def test_readback_mismatch_is_unknown_not_authorization(tmp_path, scenario):
    rows = dict(line.split("=", 1) for line in execute(tmp_path, "worker", scenario).splitlines())
    assert rows["result"] == "2"
    assert rows["repeat"] == "3" and rows["repeat_writes"] == "0"


@pytest.mark.parametrize(
    "flags,want",
    [
        ([], 0),
        (["-D__ILP32__=1"], 1),
    ],
)
def test_actual_compile_guard_accepts_lp64_but_rejects_x32(tmp_path, flags, want):
    source = (ROOT / "research/credential_seal/seal.c").read_text()
    start = source.index("#if !defined(__x86_64__)")
    end = source.index("#endif", start) + len("#endif")
    # Compile the REAL guard, without libc multilib headers masking its result.
    checked = subprocess.run(
        ["cc", "-std=c11", "-x", "c", "-fsyntax-only", *flags, "-"],
        input=source[start:end] + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (checked.returncode != 0) == bool(want), checked.stderr


@pytest.mark.parametrize(
    "scenario,writes,closes",
    [
        ("pre_close_error", 0, 1),
        ("post_open_error", 7, 1),
        ("post_read_error", 7, 2),
        ("post_close_error", 7, 2),
        ("pdeath_query_error", 7, 1),
    ],
)
def test_readback_io_uncertainty_never_retries_or_advances(tmp_path, scenario, writes, closes):
    rows = dict(line.split("=", 1) for line in execute(tmp_path, "worker", scenario).splitlines())
    assert rows["result"] == "2"
    assert rows["writes"] == str(writes)
    assert rows["close_calls"] == str(closes)
    assert rows["repeat_calls"] == "0" and rows["repeat_writes"] == "0"


def test_same_attempt_reentry_has_no_nested_syscall_or_security_write(tmp_path):
    rows = dict(
        line.split("=", 1) for line in execute(tmp_path, "worker", "reentrant").splitlines()
    )
    assert rows["result"] == "0"
    assert rows["nested_result"] == "3"
    assert rows["nested_calls"] == "0" and rows["nested_writes"] == "0"
    assert rows["writes"] == "7"
