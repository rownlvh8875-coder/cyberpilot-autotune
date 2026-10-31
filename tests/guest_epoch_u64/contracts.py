"""Decoded raw bytes, not attested execution; constructors are not an authority boundary."""

from dataclasses import dataclass, field

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS

Value = int | str | None


@dataclass(frozen=True)
class EventV2:
    n: int
    kind: str
    values: tuple[tuple[str, Value], ...]


@dataclass(frozen=True)
class CaptureV2:
    case: str
    capacity: int
    copies: int
    root: int
    boot_nonce: str
    counts: tuple[int, ...]
    events: tuple[EventV2, ...]
    version: int = field(default=2, init=False)
    profile: str = field(default="POST_REFERENCE_RAW_EPOCH_U64_V2", init=False)
    evidence_class: str = field(default="WIRE_BYTES_UNTRUSTED", init=False)
    status: str = field(default="BLOCKED", init=False)
    runtime_qualified: bool = field(default=False, init=False)
    source_binding_qualified: bool = field(default=False, init=False)
    lossless_runtime_qualified: bool = field(default=False, init=False)
    actual_epoch_loss: None = field(default=None, init=False)
    actual_global_drops: None = field(default=None, init=False)
    actual_prohibited_operations: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)
