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


def capture_api():
    assert importlib.util.find_spec("tests.deny_fd_v2_transport.capture") is not None, (
        "separate capture validation required"
    )
    return importlib.import_module("tests.deny_fd_v2_transport.capture")


def synthetic_result(monkeypatch):
    from tests.deny_fd_v2_transport.assets import TransportAssets
    from tests.test_deny_fd_v2_harness_assets import synthetic_assets
    from tests.test_deny_fd_v2_harness_capture import serial

    c = contracts()
    old, _, _ = synthetic_assets(monkeypatch)
    assets = TransportAssets(old.preflight())
    result = c.TransportProcessResult(
        c.StreamEvidence(serial(assets.base), True, None),
        c.StreamEvidence(b"kernel noise\n", True, None),
        0,
        "EXITED",
        None,
    )
    return assets, result


def test_console_noise_is_not_a_telemetry_decoder_exception(monkeypatch):
    a, result = synthetic_result(monkeypatch)
    capture = capture_api().validate_capture(result, "DFD01", a)
    assert len(capture.events) == 11


def test_telemetry_noise_is_not_stripped(monkeypatch):
    from dataclasses import replace

    a, result = synthetic_result(monkeypatch)
    bad = replace(
        result.telemetry,
        raw=result.telemetry.raw.replace(b"DFD2_EXEC\n", b"DFD2_EXEC\nkernel noise\n"),
    )
    with pytest.raises(ValueError):
        capture_api().validate_capture(replace(result, telemetry=bad), "DFD01", a)


@pytest.mark.parametrize("field", ("console_error", "incomplete", "collector_error", "nonzero"))
def test_valid_telemetry_cannot_erase_other_failures(monkeypatch, field):
    from dataclasses import replace

    a, result = synthetic_result(monkeypatch)
    if field == "console_error":
        result = replace(
            result, console=replace(result.console, complete=False, error="read failed")
        )
    elif field == "incomplete":
        result = replace(result, telemetry=replace(result.telemetry, complete=False))
    elif field == "collector_error":
        result = replace(result, error="selector teardown failed")
    else:
        result = replace(result, exit_code=1, termination="NONZERO_EXIT")
    with pytest.raises(ValueError):
        capture_api().validate_capture(result, "DFD01", a)


def record(monkeypatch, **changes):
    a, result = synthetic_result(monkeypatch)
    c = contracts()
    assert hasattr(c, "TransportAcquisitionRecord"), "dual acquisition record required"
    values = dict(
        case="DFD01",
        attempt_id="1" * 32,
        source_revision=a.base.source_revision,
        source_manifest_digest=a.base.source_manifest_digest,
        probe_sha256="2" * 64,
        vm_cohort_digest=a.base.vm_cohort_digest,
        kernel_sha256=a.base.kernel_sha256,
        kernel_config_sha256="3" * 64,
        transport_profile_digest="4" * 64,
        init_sha256="5" * 64,
        image_sha256="6" * 64,
        argv=["fixed-qemu"],
        result=result,
        host_start_ns=1,
        host_end_ns=2,
    )
    return c.TransportAcquisitionRecord(**(values | changes))


def test_new_record_is_not_old_single_stream_schema(monkeypatch):
    r = record(monkeypatch)
    metadata = r.metadata()
    assert metadata["schema"] == "deny-fd-v2-dual-acquisition-v1"
    assert metadata["telemetry"]["raw_sha256"] != metadata["console"]["raw_sha256"]
    assert metadata["status"] == "BLOCKED"
    assert all(value is False for value in metadata["permissions"].values())
    assert r.content_digest == r.content_digest
    metadata["permissions"]["application_authorized"] = True
    assert all(value is False for value in r.metadata()["permissions"].values())


@pytest.mark.parametrize(
    "changes",
    (
        {"host_start_ns": False},
        {"host_end_ns": 0},
        {"host_end_ns": 2**64},
        {"source_revision": "main"},
        {"argv": []},
        {"argv": ["bad\0arg"]},
    ),
)
def test_bad_record_context_rejected(monkeypatch, changes):
    with pytest.raises(ValueError):
        record(monkeypatch, **changes)


def test_record_defensively_copies_argv_and_binds_each_stream(monkeypatch):
    from dataclasses import replace

    args = ["fixed-qemu"]
    r = record(monkeypatch, argv=args)
    args.append("unsafe")
    assert r.argv == ("fixed-qemu",)
    changed = replace(r.result, console=replace(r.result.console, raw=b"different console"))
    assert replace(r, result=changed).content_digest != r.content_digest
    with pytest.raises(FrozenInstanceError):
        r.result = changed
