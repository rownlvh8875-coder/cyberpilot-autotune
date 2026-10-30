"""Unavailable values and object/generation identities must remain immutable."""

from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.guest_build_receipt import build, identity, models, promotion


def test_nested_input_lists_are_defensively_copied_and_sorted_without_reordering_events():
    b = build()
    rows = list(reversed(b.materials))
    copied = replace(b, materials=rows)
    rows.clear()
    assert copied.materials == b.materials and copied.uses == b.uses
    with pytest.raises(FrozenInstanceError):
        copied.start_ns = 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_id", ""),
        ("attempt_id", "bad/id"),
        ("source_digest", False),
        ("toolchain_digest", "ABC"),
        ("clock_domain", ""),
    ],
)
def test_invalid_identity_cannot_silently_coerce_or_alias_a_cohort(field, value):
    with pytest.raises(ValueError):
        replace(identity(), **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("generation", False),
        ("generation", -1),
        ("generation", 2**64),
        ("size", float("inf")),
        ("sha256", None),
        ("logical_path", "../outside"),
        ("logical_path", "/data/Params"),
        ("logical_path", "a//b"),
        ("role", "SOURCE"),
    ],
)
def test_material_identity_has_exact_scalar_path_and_enum_types(field, value):
    with pytest.raises(ValueError):
        replace(build().materials[0], **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("task_generation", 0),
        ("exec_generation", True),
        ("parent_generation", 0),
        ("start_ns", float("nan")),
        ("finish_ns", None),
    ],
)
def test_image_binding_does_not_default_an_unknown_generation_or_clock(field, value):
    with pytest.raises(ValueError):
        replace(build().images[0], **{field: value})


def test_none_is_available_in_partial_receipts_but_not_a_synthetic_zero():
    b = build()
    partial = replace(
        b, start_ns=None, finish_ns=None, identity=replace(b.identity, source_digest=None)
    )
    assert partial.start_ns is None and partial.identity.source_digest is None
    assert replace(b.uses[1], length=None).length is None
    assert replace(b.uses[1], length=0).length == 0
    assert replace(promotion(), quiesced_ns=None).quiesced_ns is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("sequence", 0),
        ("kind", "READ_BYTES"),
        ("length", False),
        ("offset", -1),
        ("range_digest", "NaN"),
    ],
)
def test_use_stream_rejects_ambiguous_scalars_and_unsupported_kinds(field, value):
    with pytest.raises(ValueError):
        replace(build().uses[1], **{field: value})


def test_exit_signal_and_code_are_not_interchangeable_status_numbers():
    m = models()
    c = build().completion
    assert replace(c, exit_kind=None, exit_code=None).exit_code is None
    assert (
        replace(c, exit_kind=m.ExitKind.SIGNALLED, exit_code=None, term_signal=9).term_signal == 9
    )
    for changes in (
        {"term_signal": 9},
        {"exit_kind": None},
        {"dropped_events": False},
        {"sequence_complete": 0},
    ):
        with pytest.raises(ValueError):
            replace(c, **changes)


def test_duplicate_set_identities_cannot_hide_in_canonical_sorting():
    b = build()
    for field in ("materials", "images", "outputs"):
        with pytest.raises(ValueError):
            replace(b, **{field: getattr(b, field) * 2})
