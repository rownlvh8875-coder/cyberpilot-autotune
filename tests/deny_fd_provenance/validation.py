"""Pure synthetic point consistency, not runtime or application admission."""

import json
from dataclasses import asdict
from hashlib import sha256

from .contracts import (
    CaptureContext,
    ClockDomain,
    DenialDecision,
    DenialReason,
    DenialReceipt,
    DenialStage,
    EvidenceKind,
    InventoryPolicyContext,
    Outcome,
    PointRef,
    RejectionReason,
)


def _cohort(ref: PointRef) -> tuple[CaptureContext, int, DenialStage]:
    return ref.context, ref.snapshot_id, ref.stage


def _before(left: PointRef, right: PointRef) -> bool:
    return left.seq < right.seq and left.time_ns < right.time_ns


def evaluate(receipt: DenialReceipt) -> DenialDecision:
    if type(receipt) is not DenialReceipt:
        raise ValueError("expected denial receipt")
    receipt.__post_init__()

    def reject(reason: RejectionReason) -> DenialDecision:
        return DenialDecision(Outcome.REJECTED, (reason,))

    r = receipt
    if r.ref.context.evidence_kind is not EvidenceKind.SYNTHETIC:
        return reject(RejectionReason.PRODUCER_NOT_IMPLEMENTED)
    if r.ref.context.clock_domain is not ClockDomain.SYNTHETIC_MONOTONIC_NS:
        return reject(RejectionReason.WRONG_CLOCK_DOMAIN)
    if r.ref.stage is not DenialStage.PRE_EXEC_INVENTORY:
        return reject(RejectionReason.UNSUPPORTED_STAGE)
    if r.reason is not DenialReason.UNEXPECTED_FD:
        return reject(RejectionReason.UNSUPPORTED_REASON)
    if r.operation_fd is not None:
        return reject(RejectionReason.INVENTORY_HAS_OPERATION_FD)
    if r.policy.expected_fds is None:
        return reject(RejectionReason.MISSING_POLICY)
    if r.snapshot is None:
        return reject(RejectionReason.MISSING_SNAPSHOT)
    snapshot = r.snapshot
    if snapshot.observed_fds is None:
        return reject(RejectionReason.MISSING_INVENTORY)
    if r.cause_fds is None:
        return reject(RejectionReason.MISSING_CAUSE_FDS)
    if r.cause_refs is None:
        return reject(RejectionReason.MISSING_CAUSE_REFS)
    if _cohort(snapshot.ref) != _cohort(r.ref):
        return reject(RejectionReason.COHORT_MISMATCH)
    if not _before(snapshot.ref, r.ref):
        return reject(RejectionReason.EVENT_ORDER_INVALID)
    by_fd = {}
    sequences = set()
    for witness in snapshot.fd_witnesses:
        if witness.fd in by_fd or witness.ref.seq in sequences:
            return reject(RejectionReason.DUPLICATE_WITNESS)
        if _cohort(witness.ref) != _cohort(r.ref):
            return reject(RejectionReason.COHORT_MISMATCH)
        if not _before(witness.ref, snapshot.ref):
            return reject(RejectionReason.EVENT_ORDER_INVALID)
        by_fd[witness.fd] = witness.ref
        sequences.add(witness.ref.seq)
    ordered = sorted(snapshot.fd_witnesses, key=lambda witness: witness.ref.seq)
    if any(not _before(a.ref, b.ref) for a, b in zip(ordered, ordered[1:], strict=False)):
        return reject(RejectionReason.EVENT_ORDER_INVALID)
    if set(by_fd) != set(snapshot.observed_fds):
        return reject(RejectionReason.INCOMPLETE_WITNESS_SET)
    expected, observed = set(r.policy.expected_fds), set(snapshot.observed_fds)
    if expected - observed:
        return reject(RejectionReason.UNSUPPORTED_MISSING_OR_MIXED_INVENTORY)
    unexpected = observed - expected
    if not unexpected:
        return reject(RejectionReason.NO_UNEXPECTED_FD)
    if tuple(sorted(unexpected)) != r.cause_fds:
        return reject(RejectionReason.CAUSE_SET_MISMATCH)
    if tuple(by_fd[fd] for fd in r.cause_fds) != r.cause_refs:
        return reject(RejectionReason.CAUSE_REFERENCE_MISMATCH)
    return DenialDecision(Outcome.SYNTHETIC_DIAGNOSTIC_CONSISTENT, ())


def _digest(value: dict[str, object]) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return sha256(raw.encode("utf-8")).hexdigest()


def canonical_digest(receipt: DenialReceipt) -> str:
    if type(receipt) is not DenialReceipt:
        raise ValueError("expected denial receipt")
    receipt.__post_init__()
    return _digest(asdict(receipt))


def policy_digest(policy: InventoryPolicyContext) -> str:
    if type(policy) is not InventoryPolicyContext:
        raise ValueError("expected inventory policy")
    policy.__post_init__()
    return _digest(asdict(policy))
