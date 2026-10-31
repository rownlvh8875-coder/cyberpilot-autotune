"""Frozen memory-only observed CPB structures; no scientific/application authority."""

from dataclasses import dataclass, field

from tests.guest_raw_lifetime.model import PERMISSIONS

CASES = (
    "NORMAL",
    "SEED_LOSS",
    "SMALL_BUFFER",
    "SEED_FAIL",
    "UNSEEDED_OFD",
    "RESEED_REJECTED",
    "EARLY_ARM_REJECTED",
    "CONSTRUCTOR_FAIL",
    "TASK_FAIL",
    "ALLOC_FAIL",
)
Value = str | int | bool | None


@dataclass(frozen=True)
class Event:
    n: int
    epoch: int
    kind: str
    values: tuple[tuple[str, Value], ...]


@dataclass(frozen=True)
class Capture:
    case: str
    capacity: int
    copies: int
    root_id: int | None
    boot_nonce: str
    epoch: int
    seed_walk: str
    forked: bool
    attempted: int
    reserved: int
    committed: int
    failed: int
    discarded: int
    pending: int
    events: tuple[Event, ...]


@dataclass(frozen=True)
class SeedBinding:
    fd: int
    presence: str
    file_id: int | None
    origin: str
    open_bit: bool
    cloexec_bitmap_bit: bool
    binding_cloexec: bool | None


@dataclass(frozen=True)
class CopyBinding:
    copy_id: int
    fd: int
    presence: str
    file_id: int | None
    origin: str
    open_after: bool
    cloexec_bitmap_bit: bool
    binding_cloexec: bool | None


@dataclass(frozen=True)
class Decision:
    local_accounting_balanced: bool
    local_loss_observed: bool
    seed_walk_recorded_complete: bool
    seed_bindings: tuple[SeedBinding, ...]
    copy_bindings: tuple[CopyBinding, ...]
    committed_stage_sequences: tuple[int, ...]
    seed_to_first_copy_links: tuple[tuple[int, int], ...]
    first_observed_cookies: tuple[int, ...]
    allocation_cookies: tuple[int, ...]
    unknown_present_count: int
    missing_origin_witness_ids: tuple[int, ...]
    reasons: tuple[str, ...]
    evidence_class: str = field(default="OBSERVED_UNTRUSTED", init=False)
    status: str = field(default="BLOCKED", init=False)
    allocation_history_complete: bool = field(default=False, init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)
