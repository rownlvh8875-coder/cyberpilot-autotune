"""Allowlisted, frozen terminal summaries; no reader, config or raw exception IO."""

import json
from collections import Counter
from dataclasses import asdict, dataclass

from cyberpilot_autotune.adapters.carrot_receipt_contract import MappingDecision

from .config import TOPICS


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    uptime_s: float
    session_state: str
    received_counts: tuple[tuple[str, int], ...]
    healthy_transport_count: int
    receipt_attempt_count: int
    accepted_mapping_count: int
    rejection_counts: tuple[tuple[str, int], ...]
    duplicate_cohort_count: int
    poisoned_key_count: int
    cc_eviction_count: int
    cs_eviction_count: int
    session_fault_count: int
    latest_cohort_key: tuple[int, int] | None
    latest_control_active: bool | None
    latest_controller_saturated: bool | None
    latest_source_valid: bool | None
    latest_snapshot_available: bool
    fault_reason: str | None


class Diagnostics:
    def __init__(self) -> None:
        self.received = dict.fromkeys(TOPICS, 0)
        self.healthy_count = 0
        self.accepted_count = 0
        self.rejections: Counter[str] = Counter()
        self.latest: MappingDecision | None = None
        self.fault_count = 0

    def record(self, decision: MappingDecision) -> None:
        self.latest = decision
        if decision.snapshot is not None:
            self.accepted_count += 1
        else:
            self.rejections[decision.reason.value] += 1


def format_summary(snapshot: DiagnosticSnapshot) -> str:
    return json.dumps(asdict(snapshot), sort_keys=True, separators=(",", ":"), allow_nan=False)
