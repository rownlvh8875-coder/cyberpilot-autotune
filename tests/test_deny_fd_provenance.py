"""Synthetic denial provenance, never a repaired or promoted legacy observation."""

import gzip
import hashlib
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec("tests.deny_fd_provenance") is not None
    return (
        importlib.import_module("tests.deny_fd_provenance.contracts"),
        importlib.import_module("tests.deny_fd_provenance.validation"),
    )


def receipt(*, expected=(0,), observed=(0, 3), causes=(3,)):
    c, _ = api()
    context = c.CaptureContext(
        "synthetic-capture",
        "a" * 40,
        "b" * 64,
        c.EvidenceKind.SYNTHETIC,
        c.ClockDomain.SYNTHETIC_MONOTONIC_NS,
        1,
        0,
    )

    def point(seq, slot=None):
        return c.PointRef(context, 7, c.DenialStage.PRE_EXEC_INVENTORY, seq, seq * 100, slot)

    witnesses = tuple(c.FdWitness(point(i + 2, 0), fd) for i, fd in enumerate(observed or ()))
    refs = {w.fd: w.ref for w in witnesses}
    snapshot = c.InventoryWitness(point(len(witnesses) + 2), observed, witnesses)
    return c.DenialReceipt(
        point(len(witnesses) + 3),
        c.DenialReason.UNEXPECTED_FD,
        c.InventoryPolicyContext(expected, 0),
        snapshot,
        None,
        causes,
        None if causes is None else tuple(refs[fd] for fd in causes),
    )


def test_contract_supports_synthetic_inventory_without_authority():
    c, v = api()
    r = receipt()
    decision = v.evaluate(r)
    assert decision.outcome is c.Outcome.SYNTHETIC_DIAGNOSTIC_CONSISTENT
    assert decision.reasons == () and decision.status == "BLOCKED"
    assert len(decision.permissions) == 9 and all(
        value is False for _, value in decision.permissions
    )
    assert r.operation_fd is None and r.policy.configured_subject_fd == 0 and r.cause_fds == (3,)
    assert not hasattr(r, "application_authorized")


@pytest.mark.parametrize(
    "expected,observed,causes", [((3,), (0, 3), (0,)), ((), (0,), (0,)), ((0,), (0, 3, 4), (3, 4))]
)
def test_actual_fd_zero_and_multiple_extras_are_not_case_number_defaults(
    expected, observed, causes
):
    c, v = api()
    assert (
        v.evaluate(receipt(expected=expected, observed=observed, causes=causes)).outcome
        is c.Outcome.SYNTHETIC_DIAGNOSTIC_CONSISTENT
    )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("cause_fds", None, "MISSING_CAUSE_FDS"),
        ("cause_refs", None, "MISSING_CAUSE_REFS"),
        ("snapshot", None, "MISSING_SNAPSHOT"),
        ("operation_fd", 0, "INVENTORY_HAS_OPERATION_FD"),
        ("cause_fds", (), "CAUSE_SET_MISMATCH"),
        ("cause_fds", (0,), "CAUSE_SET_MISMATCH"),
        ("cause_refs", (), "CAUSE_REFERENCE_MISMATCH"),
    ],
)
def test_missing_or_wrong_denial_roles_are_rejected(field, value, reason):
    c, v = api()
    assert v.evaluate(replace(receipt(), **{field: value})).reasons == (c.RejectionReason[reason],)


def test_unknown_inventory_policy_and_empty_inventory_remain_distinct():
    c, v = api()
    r = receipt()
    unknown = replace(r, snapshot=replace(r.snapshot, observed_fds=None))
    empty = receipt(observed=(), causes=())
    assert v.evaluate(unknown).reasons == (c.RejectionReason.MISSING_INVENTORY,)
    assert v.evaluate(empty).reasons == (c.RejectionReason.UNSUPPORTED_MISSING_OR_MIXED_INVENTORY,)
    assert v.canonical_digest(unknown) != v.canonical_digest(empty)
    assert v.evaluate(replace(r, policy=replace(r.policy, expected_fds=None))).reasons == (
        c.RejectionReason.MISSING_POLICY,
    )


@pytest.mark.parametrize(
    "expected,observed,causes,reason",
    [
        ((0, 3), (0,), (), "UNSUPPORTED_MISSING_OR_MIXED_INVENTORY"),
        ((4,), (0, 3), (0, 3), "UNSUPPORTED_MISSING_OR_MIXED_INVENTORY"),
        ((0, 3), (0, 3), (), "NO_UNEXPECTED_FD"),
    ],
)
def test_missing_mixed_and_matching_inventories_never_become_extra_denials(
    expected, observed, causes, reason
):
    c, v = api()
    assert v.evaluate(receipt(expected=expected, observed=observed, causes=causes)).reasons == (
        c.RejectionReason[reason],
    )


def test_unsupported_reason_stage_observed_evidence_and_clock_do_not_fallback():
    c, v = api()
    r = receipt()
    assert v.evaluate(replace(r, reason=c.DenialReason.BINDING_CHANGED)).reasons == (
        c.RejectionReason.UNSUPPORTED_REASON,
    )
    assert v.evaluate(
        replace(r, ref=replace(r.ref, stage=c.DenialStage.SYSCALL_ENTRY))
    ).reasons == (c.RejectionReason.UNSUPPORTED_STAGE,)
    context = replace(r.ref.context, evidence_kind=c.EvidenceKind.OBSERVED_UNTRUSTED)
    assert v.evaluate(replace(r, ref=replace(r.ref, context=context))).reasons == (
        c.RejectionReason.PRODUCER_NOT_IMPLEMENTED,
    )
    context = replace(r.ref.context, clock_domain=c.ClockDomain.GUEST_MONOTONIC_NS)
    assert v.evaluate(replace(r, ref=replace(r.ref, context=context))).reasons == (
        c.RejectionReason.WRONG_CLOCK_DOMAIN,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("capture_id", "different"),
        ("source_revision", "c" * 40),
        ("source_manifest_digest", "d" * 64),
        ("root_birth_ordinal", 2),
        ("exec_ordinal", 1),
        ("fd_table_generation", 0),
        ("ofd_generation", 0),
        ("clock_domain", "guest"),
    ],
)
def test_snapshot_cannot_come_from_another_cohort(field, value):
    c, v = api()
    r = receipt()
    if value == "guest":
        value = c.ClockDomain.GUEST_MONOTONIC_NS
    context = replace(r.ref.context, **{field: value})
    snapshot = replace(r.snapshot, ref=replace(r.snapshot.ref, context=context))
    assert v.evaluate(replace(r, snapshot=snapshot)).reasons == (c.RejectionReason.COHORT_MISMATCH,)


@pytest.mark.parametrize("field,value", [("snapshot_id", 8), ("stage", "other")])
def test_snapshot_identity_and_stage_are_not_latest_seen_context(field, value):
    c, v = api()
    r = receipt()
    if value == "other":
        value = c.DenialStage.OTHER_UNSUPPORTED
    snapshot = replace(r.snapshot, ref=replace(r.snapshot.ref, **{field: value}))
    assert v.evaluate(replace(r, snapshot=snapshot)).reasons == (c.RejectionReason.COHORT_MISMATCH,)


@pytest.mark.parametrize(
    "variant",
    (
        "snapshot_seq",
        "snapshot_time",
        "fd_seq",
        "fd_time",
        "duplicate",
        "missing",
        "wrong_fd",
        "fd_cohort",
        "cause_slot",
        "cause_seq",
    ),
)
def test_source_refs_cannot_be_future_missing_duplicate_or_stale(variant):
    c, v = api()
    r = receipt()
    snapshot = r.snapshot
    rows = list(snapshot.fd_witnesses)
    expected = c.RejectionReason.EVENT_ORDER_INVALID
    if variant.startswith("snapshot_"):
        key = "seq" if variant.endswith("seq") else "time_ns"
        snapshot = replace(snapshot, ref=replace(snapshot.ref, **{key: getattr(r.ref, key)}))
    elif variant.startswith("fd_") and variant != "fd_cohort":
        key = "seq" if variant.endswith("seq") else "time_ns"
        rows[0] = replace(rows[0], ref=replace(rows[0].ref, **{key: getattr(snapshot.ref, key)}))
    elif variant == "duplicate":
        rows[1] = rows[0]
        expected = c.RejectionReason.DUPLICATE_WITNESS
    elif variant == "missing":
        rows.pop()
        expected = c.RejectionReason.INCOMPLETE_WITNESS_SET
    elif variant == "wrong_fd":
        rows[1] = replace(rows[1], fd=4)
        expected = c.RejectionReason.INCOMPLETE_WITNESS_SET
    elif variant == "fd_cohort":
        rows[0] = replace(rows[0], ref=replace(rows[0].ref, snapshot_id=99))
        expected = c.RejectionReason.COHORT_MISMATCH
    else:
        key = "slot_observation_epoch" if variant == "cause_slot" else "seq"
        r = replace(r, cause_refs=(replace(r.cause_refs[0], **{key: 1}),))
        expected = c.RejectionReason.CAUSE_REFERENCE_MISMATCH
    snapshot = replace(snapshot, fd_witnesses=rows)
    assert v.evaluate(replace(r, snapshot=snapshot)).reasons == (expected,)


@pytest.mark.parametrize("value", (True, 0.0, float("nan"), float("inf"), -1, 2**64, "0"))
def test_context_sequence_and_time_require_exact_finite_uint64(value):
    _, _v = api()
    r = receipt()
    for field in ("seq", "time_ns", "snapshot_id"):
        with pytest.raises(ValueError):
            replace(r.ref, **{field: value})
    for field in ("root_birth_ordinal", "exec_ordinal", "fd_table_generation", "ofd_generation"):
        with pytest.raises(ValueError):
            replace(r.ref.context, **{field: value})


@pytest.mark.parametrize("value", (True, 3.0, float("nan"), -1, 2**31, "3"))
def test_fds_are_exact_linux_ints_not_coercible_metadata(value):
    _, _v = api()
    r = receipt()
    with pytest.raises(ValueError):
        replace(r, operation_fd=value)
    with pytest.raises(ValueError):
        replace(r.policy, configured_subject_fd=value)
    with pytest.raises(ValueError):
        replace(r.snapshot.fd_witnesses[0], fd=value)
    with pytest.raises(ValueError):
        replace(r, cause_fds=(value,))


@pytest.mark.parametrize(
    "field,value",
    [
        ("capture_id", ""),
        ("capture_id", chr(0xD800)),
        ("source_revision", "A" * 40),
        ("source_manifest_digest", "f" * 63),
        ("evidence_kind", "SYNTHETIC"),
        ("clock_domain", "SYNTHETIC_MONOTONIC_NS"),
    ],
)
def test_context_identity_is_explicit_and_structural(field, value):
    _, _v = api()
    with pytest.raises(ValueError):
        replace(receipt().ref.context, **{field: value})


def test_defensive_copy_revalidation_and_content_only_digests():
    c, v = api()
    r = receipt()
    values = [0]
    p = c.InventoryPolicyContext(values, 0)
    values.append(3)
    assert p.expected_fds == (0,)
    rows = list(r.snapshot.fd_witnesses)
    snapshot = replace(r.snapshot, fd_witnesses=rows)
    rows.clear()
    assert len(snapshot.fd_witnesses) == 2
    with pytest.raises(FrozenInstanceError):
        r.operation_fd = 0
    assert v.canonical_digest(r) == v.canonical_digest(replace(r))
    assert len(v.canonical_digest(r)) == 64
    assert v.policy_digest(p) != v.policy_digest(replace(p, configured_subject_fd=None))
    other = replace(r, ref=replace(r.ref, context=replace(r.ref.context, source_revision="c" * 40)))
    assert v.canonical_digest(other) != v.canonical_digest(r)
    assert v.canonical_digest(replace(r, operation_fd=0)) != v.canonical_digest(r)
    object.__setattr__(r.snapshot.fd_witnesses[0], "fd", True)
    for action in (v.canonical_digest, v.evaluate):
        with pytest.raises(ValueError):
            action(r)


def test_source_sequence_and_observation_time_order_cannot_disagree():
    c, v = api()
    r = receipt()
    rows = list(r.snapshot.fd_witnesses)
    rows[0] = replace(rows[0], ref=replace(rows[0].ref, time_ns=350))
    malformed = replace(r, snapshot=replace(r.snapshot, fd_witnesses=rows))
    assert v.evaluate(malformed).reasons == (c.RejectionReason.EVENT_ORDER_INVALID,)


def test_semantic_manifest_and_wrong_schema_do_not_create_a_legacy_bridge():
    c, v = api()
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "docs/evidence/deny_fd_provenance_schema.json").read_bytes())
    assert data["receipt_version"] == receipt().schema_version
    assert data["actual_wire_implemented"] is False and data["producer_implemented"] is False
    assert data["runtime_qualified"] is False and data["application_authorized"] is False
    assert data["legacy"]["conversion_allowed"] is False
    for action in (v.evaluate, v.canonical_digest):
        with pytest.raises(ValueError):
            action({"schema": "guest-data-fd-handoff-observed-v1"})
    with pytest.raises(ValueError):
        v.policy_digest({})
    with pytest.raises(ValueError):
        replace(receipt(), schema_version=data["legacy"]["capture_schema"])
    with pytest.raises(ValueError):
        replace(receipt().policy, schema_version="old")
    with pytest.raises(ValueError):
        c.DenialDecision(
            c.Outcome.SYNTHETIC_DIAGNOSTIC_CONSISTENT, [c.RejectionReason.UNSUPPORTED_STAGE]
        )


def test_legacy_source_and_capture_remain_unmodified_not_promoted():
    root = Path(__file__).resolve().parents[1]
    raw = (root / "docs/evidence/guest_data_fd_handoff_actual.json.gz").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "bb052f515908f320ccd46799181b47b9ffbf653b36e100a97e7ee290a40d3469"
    )
    data = json.loads(gzip.decompress(raw))
    assert (
        data["schema"] == "guest-data-fd-handoff-actual-v1" and data["runtime_qualified"] is False
    )
