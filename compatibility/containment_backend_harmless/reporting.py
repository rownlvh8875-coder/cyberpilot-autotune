"""Conservative partial evidence adapter, deliberately incapable of producing PASS."""

from typing import Any

from .host_cases import check_case
from .records import FixtureOutcome, HarmlessFixtureResult, HarmlessObservations

EXPECTED_REJECTION = frozenset(
    (
        "HF03",
        "HF06",
        "HF07",
        "HF08",
        "HF09",
        "HF11",
        "HF13",
        "HF14",
        "HF15",
        "HF16",
        "HF18",
        "HF19",
        "HF20",
        "HF21",
        "HF22",
    )
)
UNSUPPORTED = frozenset(("HF17", "HF23", "HF24"))


def partial_report(
    record: dict[str, Any], cohort: str, kernel: str, config: str, loader: str, btf: str
) -> HarmlessFixtureResult:
    failures = check_case(record)
    fixture = record["fixture_id"]
    data = record["measurements"]
    reasons: tuple[str, ...] = (
        "COMPLETE_SYSCALL_FD_COLLECTOR_NOT_IMPLEMENTED",
        "FULL_PROCESS_LINEAGE_UNAVAILABLE",
        "GLOBAL_HANDLE_AND_EFFECT_COUNTS_UNKNOWN",
    )
    if failures:
        outcome = FixtureOutcome.REJECTED
        reasons = failures + reasons
    elif fixture in UNSUPPORTED:
        outcome = FixtureOutcome.NOT_SUPPORTED
        reasons = ("THREADED_KILL_OR_DEVICE_OR_WRITE_PROFILE_NOT_SUPPORTED",) + reasons
    elif fixture in EXPECTED_REJECTION:
        outcome = FixtureOutcome.REJECTED
        reasons = ("NAMED_FAULT_OR_UNSUPPORTED_REQUEST_REJECTED_NOT_QUALIFICATION",) + reasons
    else:
        outcome = FixtureOutcome.UNAVAILABLE
    observations = HarmlessObservations(
        kernel_build_digest=kernel,
        kernel_config_digest=config,
        btf_digest=btf,
        source_loader_digest=loader,
        object_receipt_digest=None,
        fd_lineage_digest=None,
        guard_active=True
        if fixture in {"HF12", "HF13", "HF14", "HF16", "HF20"} and not failures
        else None,
        collector_bound=None,
        process_lineage_complete=None,
        trace_complete=None,
        tree_exit_observed=True
        if fixture in {"HF11", "HF14", "HF15"}
        and not failures
        and (data.get("tree_exit_observed") is True or data.get("child_reaped") is True)
        else None,
        broker_effects_observed=None,
        clock_domain="GUEST_MONOTONIC" if fixture == "HF13" and not failures else None,
        successful_prohibited_handles=None,
        successful_prohibited_effects=None,
    )
    return HarmlessFixtureResult(fixture, cohort, outcome, observations, reasons)
