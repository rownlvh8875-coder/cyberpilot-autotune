"""Catch narrowing, float conversion, implicit unknowns and evidence promotion."""

from dataclasses import FrozenInstanceError

import pytest

from tests.epoch_encoding_design.model import (
    EpochScalar,
    PipelineDecision,
    assess_pipeline,
    content_digest,
    decode_design,
    encode_design,
)

PREFIX = (
    b"EPOCH_U64_DESIGN_V2 schema=raw-epoch-u64-design-v2 evidence=SYNTHETIC_ONLY "
    b"reference=11b7d1e538851ee4d93ceb5477a57a805833217c0c2824e711a0796de1c22044 "
    b"capture=POST_EXISTING_REFERENCE_PRE_STORE emit=SAVED_SCALARS_AFTER_STORE "
)
BOUNDARIES = (
    (0, b"0"),
    (1, b"1"),
    (4294967295, b"4294967295"),
    (4294967296, b"4294967296"),
    (4294967297, b"4294967297"),
    (9007199254740991, b"9007199254740991"),
    (9007199254740993, b"9007199254740993"),
    (9223372036854775807, b"9223372036854775807"),
    (9223372036854775808, b"9223372036854775808"),
    (18446744073709551614, b"18446744073709551614"),
    (18446744073709551615, b"18446744073709551615"),
)


@pytest.mark.parametrize(("value", "decimal"), BOUNDARIES)
def test_literal_uint64_survives_all_synthetic_layers(value, decimal):
    wire = PREFIX + b"availability=OBSERVED raw_epoch=" + decimal + b"\n"
    epoch = EpochScalar(value)
    assert encode_design(epoch) == wire
    assert decode_design(wire).value == value
    result = assess_pipeline(epoch, epoch, epoch, wire, epoch)
    assert result.reasons == () and result.consistent and result.available
    assert result.evidence_class == "SYNTHETIC_ONLY" and result.status == "BLOCKED"
    assert all(flag is False for _, flag in result.permissions)
    assert result.runtime_qualified is result.type_fidelity_qualified is False
    assert result.actual_epoch_loss is result.actual_global_drops is None
    assert result.future_producer_revision is None


def test_unavailable_is_not_observed_zero_and_objects_are_frozen():
    missing = EpochScalar(None)
    wire = PREFIX + b"availability=UNAVAILABLE raw_epoch=UNAVAILABLE\n"
    assert encode_design(missing) == wire and decode_design(wire) == missing
    result = assess_pipeline(missing, missing, missing, wire, missing)
    assert result.consistent and not result.available and result.status == "BLOCKED"
    assert content_digest(missing) != content_digest(EpochScalar(0))
    assert content_digest(EpochScalar(1)) == content_digest(EpochScalar(1))
    with pytest.raises(FrozenInstanceError):
        missing.value = 0


@pytest.mark.parametrize(
    "value",
    [True, False, 0.0, 1.0, float("nan"), float("inf"), -1, 18446744073709551616, "1", [], {}],
)
def test_scalar_rejects_nonexact_or_out_of_domain_values(value):
    with pytest.raises(ValueError):
        EpochScalar(value)


@pytest.mark.parametrize(
    "tail",
    [
        b"availability=OBSERVED raw_epoch=01\n",
        b"availability=OBSERVED raw_epoch=+1\n",
        b"availability=OBSERVED raw_epoch=-1\n",
        b"availability=OBSERVED raw_epoch=1.0\n",
        b"availability=OBSERVED raw_epoch=18446744073709551616\n",
        b"availability=OBSERVED raw_epoch=UNAVAILABLE\n",
        b"availability=UNAVAILABLE raw_epoch=0\n",
        b"availability=False raw_epoch=0\n",
        b"availability=OBSERVED raw_epoch=0\r\n",
        b"availability=OBSERVED raw_epoch=0",
        b"availability=OBSERVED raw_epoch=0\n\n",
        b"availability=OBSERVED raw_epoch=\xff\n",
        b"availability=OBSERVED raw_epoch=0 extra=0\n",
        b"raw_epoch=0 availability=OBSERVED\n",
        b"availability=OBSERVED raw_epoch= 0\n",
        b"availability=OBSERVED raw_epoch=0 raw_epoch=0\n",
    ],
)
def test_wire_rejects_noncanonical_or_ambiguous_values(tail):
    with pytest.raises(ValueError):
        decode_design(PREFIX + tail)


@pytest.mark.parametrize(
    "raw",
    [
        b"CPR_META version=1\nCPR_END\n",
        b"CPR_META version=2\nCPR_END\n",
        PREFIX.replace(b"design-v2", b"design-v1") + b"availability=OBSERVED raw_epoch=0\n",
        PREFIX.replace(b"11b7d", b"01b7d") + b"availability=OBSERVED raw_epoch=0\n",
        PREFIX.replace(b"POST_EXISTING_REFERENCE_PRE_STORE", b"POINTER_READ")
        + b"availability=OBSERVED raw_epoch=0\n",
        PREFIX.replace(b"SAVED_SCALARS_AFTER_STORE", b"CONTROLLER_OUTPUT")
        + b"availability=OBSERVED raw_epoch=0\n",
        PREFIX.replace(b"SYNTHETIC_ONLY", b"OBSERVED_UNTRUSTED")
        + b"availability=OBSERVED raw_epoch=0\n",
        b"x" * 513,
        b"",
        "not bytes",
        None,
    ],
)
def test_wire_rejects_other_profiles_stages_sources_and_types(raw):
    with pytest.raises(ValueError):
        decode_design(raw)


@pytest.mark.parametrize(
    ("values", "reason"),
    [
        ((4294967296, 0, 0, 0, 0), "SOURCE_SAVED_MISMATCH"),
        ((1, 1, 0, 0, 0), "SAVED_BUFFER_MISMATCH"),
        ((1, 1, 1, 0, 0), "BUFFER_WIRE_MISMATCH"),
        ((1, 1, 1, 1, 0), "WIRE_DECODED_MISMATCH"),
        ((None, 0, 0, 0, 0), "SOURCE_SAVED_MISMATCH"),
        (
            (
                9007199254740993,
                9007199254740992,
                9007199254740992,
                9007199254740992,
                9007199254740992,
            ),
            "SOURCE_SAVED_MISMATCH",
        ),
    ],
)
def test_independent_layer_mismatch_is_rejected(values, reason):
    source, saved, buffered, wire, decoded = map(EpochScalar, values)
    result = assess_pipeline(source, saved, buffered, encode_design(wire), decoded)
    assert not result.consistent and result.reasons == (reason,)


@pytest.mark.parametrize("index", range(5))
def test_pipeline_rejects_untyped_scalar_substitutions(index):
    values = [EpochScalar(0)] * 3 + [encode_design(EpochScalar(0)), EpochScalar(0)]
    values[index] = 0
    with pytest.raises(ValueError):
        assess_pipeline(*values)


def test_codec_rejects_untyped_epoch():
    with pytest.raises(ValueError):
        encode_design(0)


@pytest.mark.parametrize(
    ("reasons", "available"),
    [
        (["SOURCE_SAVED_MISMATCH"], False),
        ("SOURCE_SAVED_MISMATCH", False),
        ((1,), False),
        (("RUNTIME_QUALIFIED",), False),
        ((), 0),
        ((), None),
    ],
)
def test_decision_constructor_does_not_retain_mutable_or_untyped_state(reasons, available):
    with pytest.raises(ValueError):
        PipelineDecision(reasons, available)
