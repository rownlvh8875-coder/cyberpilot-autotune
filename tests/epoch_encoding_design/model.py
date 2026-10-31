"""UInt64 scalar fidelity specification, not C ABI or runtime qualification."""

import hashlib
import re
from dataclasses import dataclass, field

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS

PREFIX = (
    b"EPOCH_U64_DESIGN_V2 schema=raw-epoch-u64-design-v2 evidence=SYNTHETIC_ONLY "
    b"reference=11b7d1e538851ee4d93ceb5477a57a805833217c0c2824e711a0796de1c22044 "
    b"capture=POST_EXISTING_REFERENCE_PRE_STORE emit=SAVED_SCALARS_AFTER_STORE "
)
MISMATCH_REASONS = (
    "SOURCE_SAVED_MISMATCH",
    "SAVED_BUFFER_MISMATCH",
    "BUFFER_WIRE_MISMATCH",
    "WIRE_DECODED_MISMATCH",
)


@dataclass(frozen=True)
class EpochScalar:
    value: int | None

    def __post_init__(self) -> None:
        if self.value is not None and (
            type(self.value) is not int or not 0 <= self.value <= 18446744073709551615
        ):
            raise ValueError("EXACT_UINT64_OR_UNAVAILABLE_REQUIRED")


def encode_design(epoch: EpochScalar) -> bytes:
    if type(epoch) is not EpochScalar:
        raise ValueError("TYPED_EPOCH_REQUIRED")
    tail = (
        b"availability=UNAVAILABLE raw_epoch=UNAVAILABLE\n"
        if epoch.value is None
        else b"availability=OBSERVED raw_epoch=" + str(epoch.value).encode("ascii") + b"\n"
    )
    return PREFIX + tail


def decode_design(raw: bytes) -> EpochScalar:
    if type(raw) is not bytes or len(raw) > 512 or not raw.startswith(PREFIX):
        raise ValueError("DESIGN_ONLY_FRAME_REQUIRED")
    tail = raw[len(PREFIX) :]
    if tail == b"availability=UNAVAILABLE raw_epoch=UNAVAILABLE\n":
        return EpochScalar(None)
    match = re.fullmatch(rb"availability=OBSERVED raw_epoch=(0|[1-9][0-9]{0,19})\n", tail)
    if match is None:
        raise ValueError("CANONICAL_UINT64_REQUIRED")
    return EpochScalar(int(match[1]))


def content_digest(epoch: EpochScalar) -> str:
    """Content identity of fixture bytes only; not authenticity or authority."""
    return hashlib.sha256(encode_design(epoch)).hexdigest()


@dataclass(frozen=True)
class PipelineDecision:
    reasons: tuple[str, ...]
    available: bool
    evidence_class: str = field(default="SYNTHETIC_ONLY", init=False)
    status: str = field(default="BLOCKED", init=False)
    runtime_qualified: bool = field(default=False, init=False)
    type_fidelity_qualified: bool = field(default=False, init=False)
    actual_epoch_loss: None = field(default=None, init=False)
    actual_global_drops: None = field(default=None, init=False)
    future_producer_revision: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)

    def __post_init__(self) -> None:
        if (
            type(self.reasons) is not tuple
            or any(
                type(reason) is not str or reason not in MISMATCH_REASONS for reason in self.reasons
            )
            or type(self.available) is not bool
        ):
            raise ValueError("IMMUTABLE_TYPED_DECISION_REQUIRED")

    @property
    def consistent(self) -> bool:
        return not self.reasons


def assess_pipeline(
    source: EpochScalar,
    saved: EpochScalar,
    buffered: EpochScalar,
    wire: bytes,
    decoded: EpochScalar,
) -> PipelineDecision:
    if any(type(value) is not EpochScalar for value in (source, saved, buffered, decoded)):
        raise ValueError("TYPED_EPOCH_REQUIRED")
    wire_epoch = decode_design(wire)
    chain = (source, saved, buffered, wire_epoch, decoded)
    return PipelineDecision(
        tuple(
            name
            for name, left, right in zip(MISMATCH_REASONS, chain[:-1], chain[1:], strict=True)
            if left != right
        ),
        all(value.value is not None for value in chain),
    )
