"""Immutable stream evidence cannot manufacture completeness or authority."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest


def contracts():
    assert importlib.util.find_spec("tests.deny_fd_v2_transport") is not None, (
        "transport package required"
    )
    return importlib.import_module("tests.deny_fd_v2_transport.contracts")


@pytest.mark.parametrize("raw", (None, False, bytearray(b"x"), "x", b"x" * 1048577))
def test_invalid_stream_bytes_rejected(raw):
    with pytest.raises(ValueError):
        contracts().StreamEvidence(raw, False, None)


@pytest.mark.parametrize("complete", (None, 0, 1, "true"))
def test_unknown_completeness_not_defaulted(complete):
    with pytest.raises(ValueError):
        contracts().StreamEvidence(b"", complete, None)


def test_zero_bytes_is_real_empty_not_unavailable():
    stream = contracts().StreamEvidence(b"", True, None)
    assert stream.raw == b"" and stream.complete is True
    with pytest.raises(FrozenInstanceError):
        stream.raw = b"changed"


@pytest.mark.parametrize("error", ("", "bad\0error", "x" * 4001, False, 0))
def test_invalid_stream_error_rejected(error):
    with pytest.raises(ValueError):
        contracts().StreamEvidence(b"", False, error)


def test_collector_error_cannot_be_complete():
    with pytest.raises(ValueError):
        contracts().StreamEvidence(b"prefix", True, "read failed")


def test_stream_roles_are_independent_and_immutable():
    c = contracts()
    result = c.TransportProcessResult(
        c.StreamEvidence(b"DFD2", True, None),
        c.StreamEvidence(b"kernel", True, None),
        0,
        "EXITED",
        None,
    )
    assert result.telemetry.raw == b"DFD2"
    assert result.console.raw == b"kernel"
    assert all(value is False for _, value in result.permissions)


def test_aggregate_limit_covers_both_streams():
    c = contracts()
    with pytest.raises(ValueError):
        c.TransportProcessResult(
            c.StreamEvidence(b"a" * 600000, False, None),
            c.StreamEvidence(b"b" * 600000, False, None),
            None,
            "OUTPUT_LIMIT",
            None,
        )


@pytest.mark.parametrize("exit_code", (False, 1.5, "0", 2**31))
def test_unknown_exit_not_zero_or_bool(exit_code):
    c = contracts()
    with pytest.raises(ValueError):
        c.TransportProcessResult(
            c.StreamEvidence(b"", False, None),
            c.StreamEvidence(b"", False, None),
            exit_code,
            "IO_ERROR",
            None,
        )
