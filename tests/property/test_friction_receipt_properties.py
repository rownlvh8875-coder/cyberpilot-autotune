"""Content identity and causal/type boundaries, never statistical qualification."""

import struct
from dataclasses import asdict, replace

from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.observability import validation as v
from cyberpilot_autotune.observability.types import (
    CURRENT,
    RUNTIME,
    ControllerMode,
    Precision,
    digest,
)
from tests.fixtures.friction_receipt import complete


@settings(max_examples=25, deadline=None)
@given(cycle=st.integers(min_value=0, max_value=10000))
def test_equal_fields_and_reordered_sources_have_equal_content_digest(cycle):
    a = complete(cycle)
    b = replace(a, sources=tuple(reversed(a.sources)))
    assert a.digest == b.digest == complete(cycle).digest
    fields = asdict(a)
    reordered = dict(reversed(list(fields.items())))
    assert digest(fields) == digest(reordered)


@settings(max_examples=25, deadline=None)
@given(value=st.integers(min_value=0, max_value=2**64 - 1))
def test_generation_mutates_content_and_requires_matching_snapshot(value):
    receipt = complete()
    changed = replace(receipt, cycle=replace(receipt.cycle, geometry_generation=value))
    if value != 3:
        assert changed.digest != receipt.digest
        assert v.evaluate(changed, v.ObservationPolicy()).status.value == "REJECTED"


def test_none_zero_false_and_float32_rounding_never_share_raw_identity():
    receipt = complete()
    observed = receipt.signals.roll
    assert (
        replace(
            receipt, signals=replace(receipt.signals, roll=replace(observed, value=None))
        ).digest
        != receipt.digest
    )
    assert (
        replace(receipt, limits=replace(receipt.limits, steering_pressed=None)).digest
        != receipt.digest
    )
    direct = replace(receipt.stages.callback_output_raw, value=0.1)
    rounded = replace(
        direct, value=struct.unpack("f", struct.pack("f", 0.1))[0], precision=Precision.FLOAT32
    )
    assert direct.value != rounded.value
    assert digest(asdict(direct)) != digest(asdict(rounded))


def test_source_revision_and_mode_change_content_identity_without_promoting_authority():
    receipt = complete()
    assert CURRENT != RUNTIME
    for changed in (
        replace(receipt, cycle=replace(receipt.cycle, source_revision=RUNTIME)),
        replace(receipt, controller_mode=ControllerMode.CUSTOM),
    ):
        assert changed.digest != receipt.digest
        assert v.evaluate(changed, v.ObservationPolicy()).status.value == "REJECTED"


def test_downstream_pair_identity_and_unapplied_candidate_change_are_not_epoch_parameters():
    from cyberpilot_autotune.observability.types import AlignmentMethod

    before = complete(10)
    after = complete(11)

    def aligned(receipt, pair):
        return replace(
            receipt,
            context=replace(
                receipt.context,
                delay=replace(
                    receipt.context.delay,
                    alignment_method=AlignmentMethod.SINGLE_DOWNSTREAM_PAIR,
                    alignment_version="pair-v1",
                    correction_count=1,
                    sample_pair_id=pair,
                ),
            ),
        )

    before = aligned(before, "a" * 64)
    after = aligned(after, "b" * 64)
    after = replace(
        after,
        context=replace(
            after.context,
            geometry=replace(
                after.context.geometry,
                live_parameters_ratio=0.43000001,
                requested_center_to_front_percent=51,
            ),
        ),
    )
    assert before.epoch_digest == after.epoch_digest
    assert v.evaluate(after, v.ObservationPolicy(), previous=before).status.value == "ELIGIBLE"


def test_duplicate_source_sequence_with_mismatched_timestamp_rejects_even_without_opaque_id():
    before = complete(10)
    after = complete(11)
    role = before.sources[0].role
    old = replace(before.sources[0], source_identity=None)
    new = replace(after.sources[0], sequence=old.sequence, source_identity=None)
    before = replace(before, sources=(old, *before.sources[1:]))
    after = replace(after, sources=(new, *after.sources[1:]))
    assert new.role == role
    assert "SOURCE_TIMESTAMP_MISMATCH" in {
        r.value for r in v.evaluate(after, v.ObservationPolicy(), previous=before).reasons
    }


def test_pinned_feedforward_compensation_argument_and_request_sign_are_checked():
    receipt = complete(error=0.5, q=0.0, compensation=False)
    assert "CALLBACK_FLAG_INCONSISTENT" in {
        r.value for r in v.evaluate(receipt, v.ObservationPolicy()).reasons
    }
    receipt = complete()
    requested = replace(
        receipt.stages.requested_torque, value=-receipt.stages.requested_torque.value
    )
    bad = replace(receipt, stages=replace(receipt.stages, requested_torque=requested))
    assert "PID_STAGE_INCONSISTENT" in {
        r.value for r in v.evaluate(bad, v.ObservationPolicy()).reasons
    }
