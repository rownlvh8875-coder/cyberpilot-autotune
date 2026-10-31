"""Conditional design behavior;positive premises never qualify source/runtime."""

import copy
import importlib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from tests.fixtures.tag_read_protocol import example, scenarios

ROOT = Path(__file__).resolve().parents[1]


def api():
    assert (ROOT / "tests/tag_read_protocol/model.py").is_file(), "MISSING_TAG_READ_PROTOCOL"
    return importlib.import_module("tests.tag_read_protocol.model").evaluate


@pytest.mark.parametrize(
    ("name", "payload", "expected"), scenarios(), ids=lambda v: v if isinstance(v, str) else None
)
def test_independent_lifetime_publication_context_and_causal_premises(name, payload, expected):
    result = api()(payload)
    assert result.premises_consistent is expected, (name, result.reasons)
    assert (result.proposed_snapshot is not None) is expected
    assert bool(result.reasons) is not expected
    assert result.status == "BLOCKED" and result.evidence_class == "SYNTHETIC_ONLY"
    assert result.actual_global_drops is result.actual_prohibited_operations is None
    assert all(value is False for _, value in result.permissions)
    for field in (
        "runtime_producer_implemented",
        "target_lifetime_proven",
        "tag_publication_qualified",
        "source_happens_before_proven",
        "allocation_history_complete",
        "atomic_cut_proven",
        "runtime_qualified",
    ):
        assert getattr(result, field) is False


def test_snapshot_is_defensive_and_frozen_not_a_live_object_or_permission():
    payload = example()
    result = api()(payload)
    before = copy.deepcopy(result)
    payload["observed_identity"]["cookie"] = 99
    payload["membership"]["root_after"] = 99
    payload["graph"]["edges"].clear()
    assert result == before
    snapshot = result.proposed_snapshot
    assert (
        snapshot.object_kind,
        snapshot.cookie,
        snapshot.epoch,
        snapshot.generation,
        snapshot.origin,
        snapshot.cohort,
        snapshot.root,
        snapshot.membership_generation,
    ) == ("OFD", 17, 1, 0, "ALLOCATION", "synthetic-boot-a", 5, 0)
    with pytest.raises(FrozenInstanceError):
        snapshot.cookie = 99
    with pytest.raises(ValueError):
        replace(result, runtime_qualified=True)


def test_unknown_false_and_integer_zero_are_not_interchangeable_evidence():
    p = example()
    p["writer"]["components_initialized"] = None
    unknown = api()(p)
    p["writer"]["components_initialized"] = False
    actual_false = api()(p)
    p["writer"]["components_initialized"] = 0
    integer_zero = api()(p)
    assert not any(r.premises_consistent for r in (unknown, actual_false, integer_zero))
    assert len({unknown.reasons, actual_false.reasons, integer_zero.reasons}) == 3


def test_consistently_fabricated_labels_cannot_gain_runtime_or_application_authority():
    p = example()
    p["identity"]["cookie"] = p["observed_identity"]["cookie"] = 999
    p["reader"]["witness_identity"]["cookie"] = 999
    p["writer"]["witness_identity"]["cookie"] = 999
    result = api()(p)
    assert result.premises_consistent
    assert not result.target_lifetime_proven and not result.source_happens_before_proven
    assert result.status == "BLOCKED" and all(v is False for _, v in result.permissions)


@pytest.mark.parametrize("section", ["reader", "writer"])
def test_lifetime_and_publication_witness_must_bind_the_exact_subject_not_just_a_claim(section):
    p = example()
    p[section].pop("witness_identity", None)
    assert not api()(p).premises_consistent


@pytest.mark.parametrize("payload", [None, False, 0, [], (), {"schema": "CPBv1"}])
def test_malformed_or_real_domain_payload_never_defaults_to_valid_synthetic_read(payload):
    result = api()(payload)
    assert not result.premises_consistent and result.proposed_snapshot is None


@pytest.mark.parametrize("field", ["identity", "writer", "reader", "membership", "source", "graph"])
def test_missing_structural_context_is_rejected(field):
    p = example()
    del p[field]
    assert not api()(p).premises_consistent


@pytest.mark.parametrize("value", [True, -1, 2**64, 1.0, float("nan"), float("inf")])
def test_identity_numbers_must_be_finite_exact_uint64_not_bool_or_approximation(value):
    p = example()
    p["identity"]["cookie"] = value
    assert not api()(p).premises_consistent


@pytest.mark.parametrize("value", [None, False, [], "ref_begin", ["ref_begin"], [[], "read_begin"]])
def test_malformed_causal_edge_is_reasoned_rejection_not_a_crash(value):
    p = example()
    p["graph"]["edges"].append(value)
    result = api()(p)
    assert not result.premises_consistent and result.reasons
