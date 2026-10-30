"""Hand-authored untrusted reports, never actual kernel or operational authority."""

from typing import Any


def fixture_report() -> dict[str, Any]:
    return {
        "schema_version": "harmless-backend-fixture-v1",
        "evidence_kind": "UNTRUSTED_FIXTURE_REPORT",
        "fixture_id": "HF01",
        "evidence_cohort_digest": "a" * 64,
        "outcome": "PASS_NAMED_HARMLESS_FIXTURE",
        "actual_observations": {
            "kernel_build_digest": "1" * 64,
            "kernel_config_digest": "2" * 64,
            "btf_digest": "3" * 64,
            "source_loader_digest": "4" * 64,
            "object_receipt_digest": "5" * 64,
            "fd_lineage_digest": "6" * 64,
            "guard_active": True,
            "collector_bound": True,
            "process_lineage_complete": True,
            "trace_complete": True,
            "tree_exit_observed": True,
            "broker_effects_observed": False,
            "clock_domain": "guest-monotonic-ns-v1",
            "successful_prohibited_handles": 0,
            "successful_prohibited_effects": 0,
        },
        "reasons": [],
        "runtime_qualified": False,
        "device_class_qualified": False,
        "policy_adopted": False,
        "candidate_generation_allowed": False,
        "application_authorized": False,
        "runtime_accepted": False,
        "owner_proposal_allowed": False,
    }
