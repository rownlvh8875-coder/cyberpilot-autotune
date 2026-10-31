"""Immutable decoded scalars; direct constructors are not a security boundary."""

from dataclasses import dataclass, field

from tests.guest_raw_lifetime.model import PERMISSIONS

CASES = (
    "NORMAL",
    "SEED_LOSS",
    "SMALL_BUFFER",
    "UNSEEDED_OFD",
    "CONSTRUCTOR_FAIL",
    "SNAPSHOT_LOSS",
    "POINTER_LOSS",
)
Value = int | str


@dataclass(frozen=True)
class Event:
    n: int
    kind: str
    values: tuple[tuple[str, Value], ...]


@dataclass(frozen=True)
class Capture:
    case: str
    capacity: int
    copies: int
    root: int
    boot_nonce: str
    counts: tuple[int, ...]
    events: tuple[Event, ...]


@dataclass(frozen=True)
class Snapshot:
    copy_id: int
    fd: int
    read_ordinal: int
    raw_cookie: int
    raw_scope: int
    raw_epoch: int
    raw_origin: int
    logical_cookie: int | None
    pointer_record_n: int | None
    reference_record_n: int | None
    store_record_n: int | None
    source_join_complete: bool
    generation: None = field(default=None, init=False)
    lifetime_witness: None = field(default=None, init=False)
    publication_witness: None = field(default=None, init=False)
    membership_witness: None = field(default=None, init=False)


@dataclass(frozen=True)
class Decision:
    snapshots: tuple[Snapshot, ...]
    local_accounting_balanced: bool
    local_loss_observed: bool
    reasons: tuple[str, ...]
    evidence_class: str = field(default="OBSERVED_UNTRUSTED", init=False)
    status: str = field(default="BLOCKED", init=False)
    runtime_qualified: bool = field(default=False, init=False)
    tag_publication_qualified: bool = field(default=False, init=False)
    target_lifetime_proven: bool = field(default=False, init=False)
    source_happens_before_proven: bool = field(default=False, init=False)
    allocation_history_complete: bool = field(default=False, init=False)
    atomic_cut_proven: bool = field(default=False, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)
