"""Independent full-frame expectations; never infer values from C output tokens."""

import subprocess

import pytest

from tests.epoch_decoder_bridge import native
from tests.epoch_decoder_bridge.native import probe_frame
from tests.epoch_decoder_bridge.validation import check_frame

LITERALS = (
    0,
    1,
    4294967295,
    4294967296,
    4294967297,
    9007199254740991,
    9007199254740993,
    9223372036854775807,
    9223372036854775808,
    18446744073709551614,
    18446744073709551615,
)


@pytest.fixture(scope="module")
def compiled_frame(tmp_path_factory):
    return probe_frame(tmp_path_factory.mktemp("epoch-full-c-frame"))


def test_actual_c_stdout_reaches_full_decoder_with_all_literal_values(compiled_frame):
    assert type(compiled_frame) is bytes
    assert compiled_frame.replace(b"\r\n", b"\n").startswith(b"CPR2_DRIVER ok=1\n")
    assert compiled_frame.count(b"CPR2_EVENT ") == 11
    assert b"raw_epoch=9007199254740993 " in compiled_frame
    assert b"raw_epoch=18446744073709551615 " in compiled_frame
    result = check_frame(compiled_frame)
    assert tuple(dict(event.values)["raw_epoch"] for event in result.events) == LITERALS
    assert result.status == "BLOCKED" and result.evidence_class == "WIRE_BYTES_UNTRUSTED"
    assert result.runtime_qualified is result.source_binding_qualified is False
    assert result.lossless_runtime_qualified is False
    assert result.actual_epoch_loss is result.actual_global_drops is None
    assert all(value is False for _, value in result.permissions)


@pytest.mark.parametrize("mutation", ["saved32", "buffer32", "signed", "format32"])
def test_native_type_or_format_mutations_fail_compilation(tmp_path, mutation):
    with pytest.raises(subprocess.CalledProcessError):
        probe_frame(tmp_path, mutation)


@pytest.mark.parametrize("mutation", ["mask32", "float", "reread"])
def test_syntactically_valid_lossy_c_output_fails_the_independent_cohort_gate(tmp_path, mutation):
    raw = probe_frame(tmp_path, mutation)
    with pytest.raises(ValueError, match="EXPECTED_EVENT_COHORT"):
        check_frame(raw)


@pytest.mark.parametrize("mutation", ["unknown_status", "legacy_marker"])
def test_bad_actual_c_status_or_marker_output_is_not_upgraded(tmp_path, mutation):
    with pytest.raises(ValueError):
        check_frame(probe_frame(tmp_path, mutation))


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"raw_epoch=0 ", b"raw_epoch=1 "),
        (b"raw_scope=0", b"raw_scope=1"),
        (b"raw_cookie=6", b"raw_cookie=7"),
        (b"fd=5", b"fd=6"),
        (b"source=2", b"source=3"),
        (b"dest=9", b"dest=10"),
        (b"actor=1", b"actor=2"),
        (b"task=8", b"task=9"),
        (b"scope=8", b"scope=9"),
        (b"raw_origin=1", b"raw_origin=2"),
        (b"read_ordinal=1 ", b"read_ordinal=2 "),
        (b"local=1 ", b"local=2 "),
        (b"copy=1", b"copy=2"),
        (b"case=NORMAL", b"case=SEED_LOSS"),
        (b"root=8", b"root=9"),
        (b"0123456789abcdef0123456789abcdef", b"1123456789abcdef0123456789abcdef"),
        (
            b"raw_epoch_status=OBSERVED raw_epoch=0 ",
            b"raw_epoch_status=UNAVAILABLE raw_epoch=UNAVAILABLE ",
        ),
    ],
)
def test_correct_width_with_wrong_value_or_context_is_not_accepted(compiled_frame, before, after):
    with pytest.raises(ValueError):
        check_frame(compiled_frame.replace(before, after, 1))


def test_partial_empty_duplicate_or_legacy_frame_never_passes(compiled_frame):
    for raw in (
        b"",
        compiled_frame[:-1],
        compiled_frame + compiled_frame,
        compiled_frame.replace(b"CPR2_", b"CPR_"),
    ):
        with pytest.raises(ValueError):
            check_frame(raw)


def test_crlf_transport_is_decoded_without_changing_scalar_meaning(compiled_frame):
    crlf = compiled_frame.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    assert check_frame(crlf) == check_frame(compiled_frame)


def test_probe_does_not_overwrite_existing_directory_or_accept_open_mutations(tmp_path):
    with pytest.raises(ValueError, match="MUTATION"):
        probe_frame(tmp_path, "arbitrary-code")
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match="EMPTY_OWNED"):
        probe_frame(tmp_path)
    assert sentinel.read_bytes() == b"keep"


def test_source_bundle_drift_is_rejected_before_any_compile_input_write(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"not trusted source")
    owned = tmp_path / "owned"
    owned.mkdir()
    monkeypatch.setattr(native, "INPUTS", bad)
    with pytest.raises(ValueError, match="NATIVE_INPUT_BYTES_DRIFT"):
        probe_frame(owned)
    assert list(owned.iterdir()) == []


def test_coherent_but_partial_frame_is_not_the_complete_expected_cohort(compiled_frame):
    lines = compiled_frame.replace(b"\r\n", b"\n").splitlines(keepends=True)
    partial = b"".join(lines[:3] + lines[3:13] + lines[-2:])
    partial = partial.replace(
        b"attempted=11 reserved=11 committed=11", b"attempted=10 reserved=10 committed=10"
    )
    with pytest.raises(ValueError, match="EXPECTED_FRAME_COHORT"):
        check_frame(partial)


def test_coherent_local_loss_or_another_valid_stage_cannot_pass(compiled_frame):
    raw = compiled_frame.replace(b"attempted=11", b"attempted=12").replace(b"failed=0", b"failed=1")
    with pytest.raises(ValueError, match="EXPECTED_FRAME_COHORT"):
        check_frame(raw)
    lines = compiled_frame.replace(b"\r\n", b"\n").splitlines(keepends=True)
    lines[3] = (
        b"CPR2_EVENT n=1 epoch=1 kind=NODE object=6 role=OFD origin=FIRST_OBSERVED "
        b"stage=PRE_ARM_SEED generation=0\n"
    )
    with pytest.raises(ValueError, match="EXPECTED_EVENT_COHORT"):
        check_frame(b"".join(lines))
