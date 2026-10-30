"""Finite SYNTHETIC counterexamples only; no producer, runtime proof or authority."""

from dataclasses import dataclass
from itertools import permutations


@dataclass(frozen=True)
class CopyWitness:
    copied: tuple[bool, bool]
    source_states: tuple[tuple[bool, bool], ...]
    has_cut: bool


def copy_orders() -> tuple[tuple[str, ...], ...]:
    """Two ascending slot reads and two ordered lockless installations."""
    return tuple(
        p
        for p in permutations(("R0", "R1", "W0", "W1"))
        if p.index("R0") < p.index("R1") and p.index("W0") < p.index("W1")
    )


def analyze_copy(order: tuple[str, ...]) -> CopyWitness:
    """Both slots are reserved before the copy; bool denotes published file presence.

    This is an abstract allowed interleaving, not a real kernel execution or a
    memory-model simulator. A matching state is necessary, not sufficient proof
    of an atomic cut (flags/other slots/provenance are deliberately not modeled).
    """
    if type(order) is not tuple or order not in copy_orders():
        raise ValueError("INVALID_SYNTHETIC_SCHEDULE")
    source = [False, False]
    copied = [False, False]
    states = [(False, False)]
    for op in order:
        slot = int(op[1])
        if op[0] == "W":
            source[slot] = True
            states.append((source[0], source[1]))
        else:
            copied[slot] = source[slot]
    result = (copied[0], copied[1])
    return CopyWitness(result, tuple(states), result in states)


@dataclass(frozen=True)
class CpuLedger:
    """Hypothetical source accounting; not bpf_ringbuf's built-in counters."""

    cpu: int
    attempted: int | None
    reserve_failed: int | None
    reserved: int | None
    committed: int | None
    discarded: int | None
    pending: int | None
    received: int | None
    armed: bool | None
    drained: bool | None


def _uint(value: object, bits: int) -> bool:
    return type(value) is int and 0 <= value < 2**bits


def assess_loss(rows: tuple[CpuLedger, ...], cpus: tuple[int, ...]) -> tuple[str, ...]:
    """Reject inconsistent simulated accounting. Empty reasons != verified capture.

    A complete declared CPU cohort and balanced counters cannot discover a wholly
    uninstrumented source, coherent fabrication, or omissions before attempted++.
    Arm/drain flags here are synthetic premises, never actual barrier witnesses.
    """
    if (
        type(cpus) is not tuple
        or not cpus
        or any(not _uint(cpu, 32) for cpu in cpus)
        or len(set(cpus)) != len(cpus)
    ):
        return ("CPU_COHORT_INVALID",)
    if type(rows) is not tuple or any(type(row) is not CpuLedger for row in rows):
        return ("INVALID_LEDGER",)
    if (
        any(not _uint(row.cpu, 32) for row in rows)
        or len(rows) != len(cpus)
        or {row.cpu for row in rows} != set(cpus)
    ):
        return ("CPU_COHORT_MISMATCH",)
    reasons = set()
    for row in rows:
        values = (
            row.attempted,
            row.reserve_failed,
            row.reserved,
            row.committed,
            row.discarded,
            row.pending,
            row.received,
        )
        if any(v is None for v in values):
            reasons.add("UNKNOWN_COUNTER")
        elif any(not _uint(v, 64) for v in values):
            reasons.add("INVALID_COUNTER")
        else:
            # Narrowing stays explicit so None/bool/float never becomes a count.
            attempted, failed, reserved, committed, discarded, pending, received = (
                int(v) for v in values if v is not None
            )
            if attempted != failed + reserved:
                reasons.add("ATTEMPT_ACCOUNTING_MISMATCH")
            if reserved != committed + discarded + pending:
                reasons.add("RESERVATION_ACCOUNTING_MISMATCH")
            if failed:
                reasons.add("RESERVE_FAILURE")
            if discarded:
                reasons.add("DISCARDED_EVENT")
            if pending:
                reasons.add("PENDING_RESERVATION")
            if received != committed:
                reasons.add("DELIVERY_MISMATCH")
        if row.armed is not True or row.drained is not True:
            reasons.add("UNPROVEN_ARM_DRAIN")
    return tuple(sorted(reasons))
