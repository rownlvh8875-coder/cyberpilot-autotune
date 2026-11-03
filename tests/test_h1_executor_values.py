"""Closed values and BPF behavior,not execution or authority evidence."""

import importlib
import struct
from dataclasses import FrozenInstanceError, fields
from hashlib import sha256

import pytest


def api():
    try:
        return importlib.import_module("tests.audit_compatibility_executor.contracts")
    except ModuleNotFoundError:
        pytest.fail("closed synthetic contracts not implemented")


def test_closed_request_values():
    m = api()
    assert {c.value for c in m.SyntheticCase} == {
        "FD_CLOSED",
        "DIRECTORY_READ_ONLY",
        "DESCENDANT_NETWORK",
        "TIMEOUT_SETSID",
        "OUTPUT_FLOOD",
        "MISSING_MOUNT",
        "NONZERO_EXIT",
        "SUPERVISOR_ABORT",
    }
    request = m.SyntheticRequest(m.SyntheticCase.FD_CLOSED, "/tmp/owned-parent")
    assert [f.name for f in fields(request)] == ["case", "owner_directory"]
    with pytest.raises(FrozenInstanceError):
        request.owner_directory = "/other"
    request.validate()


@pytest.mark.parametrize(
    "field,value",
    [
        ("case", "FD_CLOSED"),
        ("case", True),
        ("owner_directory", None),
        ("owner_directory", "relative"),
        ("owner_directory", "/a/../b"),
        ("owner_directory", "/a//b"),
        ("owner_directory", "/a\0b"),
        ("owner_directory", "/"),
    ],
)
def test_invalid_or_forged_values(field, value):
    m = api()
    kwargs = dict(case=m.SyntheticCase.FD_CLOSED, owner_directory="/tmp/owner")
    kwargs[field] = value
    with pytest.raises(ValueError):
        m.SyntheticRequest(**kwargs)
    valid = m.SyntheticRequest(m.SyntheticCase.FD_CLOSED, "/tmp/owner")
    object.__setattr__(valid, field, value)
    with pytest.raises(ValueError):
        valid.validate()


@pytest.mark.parametrize(
    "errors,missing,cleanup,outcome",
    [
        ([], [], "CONFIRMED", "SYNTHETIC_OBSERVATION_COMPLETE"),
        (["NONZERO_EXIT"], ["NO_POLICY"], "UNCONFIRMED", "REJECTED"),
        ([], ["UNSUPPORTED"], "CONFIRMED", "UNAVAILABLE"),
        ([], [], "UNCONFIRMED", "UNAVAILABLE"),
    ],
)
def test_fixed_blocked_results(errors, missing, cleanup, outcome):
    m = api()
    result = m.SyntheticResult(
        m.SyntheticCase.FD_CLOSED, outcome, errors, missing, cleanup, b"out", b"err", None
    )
    errors.append("AFTER_CONSTRUCTION")
    missing.append("AFTER_CONSTRUCTION")
    assert result.errors == (() if outcome != "REJECTED" else ("NONZERO_EXIT",))
    assert "AFTER_CONSTRUCTION" not in result.unavailable
    assert result.status == "BLOCKED"
    assert len(result.permissions) == 9
    assert all(value is False for _, value in result.permissions)
    assert result.content_identity_only is True
    assert result.historical_execution is False
    assert result.integrated_admission is False
    assert result.historical_replay == "UNAVAILABLE"
    result.validate()
    with pytest.raises(FrozenInstanceError):
        result.outcome = "H_PASSED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("outcome", "H_PASSED"),
        ("outcome", "REJECTED"),
        ("case", "FD_CLOSED"),
        ("errors", [""]),
        ("errors", "bad"),
        ("errors", [1]),
        ("unavailable", None),
        ("cleanup", True),
        ("stdout", bytearray()),
        ("stderr", "not-bytes"),
        ("stdout", b"x" * 65537),
        ("run_directory", "../old"),
    ],
)
def test_result_revalidates_every_supplied_field(field, value):
    m = api()
    kwargs = dict(
        case=m.SyntheticCase.FD_CLOSED,
        outcome="SYNTHETIC_OBSERVATION_COMPLETE",
        errors=(),
        unavailable=(),
        cleanup="CONFIRMED",
        stdout=b"",
        stderr=b"",
        run_directory=None,
    )
    kwargs[field] = value
    with pytest.raises(ValueError):
        m.SyntheticResult(**kwargs)
    kwargs[field] = dict(
        case=m.SyntheticCase.FD_CLOSED,
        outcome="SYNTHETIC_OBSERVATION_COMPLETE",
        errors=(),
        unavailable=(),
        cleanup="CONFIRMED",
        stdout=b"",
        stderr=b"",
        run_directory=None,
    )[field]
    result = m.SyntheticResult(**kwargs)
    object.__setattr__(result, field, value)
    with pytest.raises(ValueError):
        result.validate()


def execute_filter(raw, arch, syscall):
    """Tiny independent interpreter for only this registered classic BPF subset."""
    rows = list(struct.iter_unpack("<HBBI", raw))
    acc, index = 0, 0
    while True:
        op, yes, no, value = rows[index]
        if op == 0x20:
            acc = {0: syscall, 4: arch}[value]
        elif op == 0x15:
            index += yes if acc == value else no
        elif op == 0x35:
            index += yes if acc >= value else no
        else:
            assert op == 6
            return value
        index += 1


def test_seccomp_exact_bytes():
    api()
    raw = importlib.import_module("tests.audit_compatibility_executor.seccomp").seccomp_bytes()
    assert (
        sha256(raw).hexdigest()
        == "12e1d308af4e6ed61ae5beccc2c3d2fc3f89506e13215ad31965e97c6fe66901"
    )
    assert execute_filter(raw, 0xC000003E, 41) == 0x00050001
    assert execute_filter(raw, 0xC000003E, 442) == 0x00050001
    assert execute_filter(raw, 0xC000003E, 0) == 0x7FFF0000
    assert execute_filter(raw, 0x40000003, 0) == 0x80000000
    assert execute_filter(raw, 0xC000003E, 0x40000000) == 0x80000000
