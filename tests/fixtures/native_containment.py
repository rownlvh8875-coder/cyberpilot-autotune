"""Hand-authored synthetic values only; no observed system facts."""

from typing import Any


def synthetic_case() -> dict[str, Any]:
    return {
        "schema_version": "synthetic-native-containment-case-v1",
        "evidence_kind": "SYNTHETIC",
        "source_cohort_digest": "a" * 64,
        "actor_id": "synthetic-child",
        "process_generation": 1,
        "exec_generation": 2,
        "clock_domain": "synthetic-monotonic-ns-v1",
        "modeled_proofs": {
            "input_closure_complete": True,
            "enforcement_observed_active": True,
            "source_loader_immutable": True,
            "process_stage_bound": True,
            "resource_resolution_bound": True,
            "capture_guard_bound": True,
            "trace_complete": True,
            "observer_intact": True,
        },
        "cpu_backend": "CPU:LLVM",
        "successful_prohibited_handles": 0,
        "successful_prohibited_effects": 0,
        "events": [
            {
                "sequence": 1,
                "mono_time_ns": 100,
                "actor_id": "synthetic-child",
                "process_generation": 1,
                "exec_generation": 2,
                "clock_domain": "synthetic-monotonic-ns-v1",
                "operation_class": "OPEN",
                "requested_endpoint": "/dev/kfd",
                "flags": ["O_RDWR", "O_CLOEXEC"],
                "resolved_kind": "PRIVATE_NAMESPACE_ABSENCE",
                "resolution_bound": True,
                "result_known": True,
                "errno_name": "ENOENT",
                "fd_created_or_imported": False,
                "effect_observed": False,
            }
        ],
        "candidate_generation_allowed": False,
        "application_authorized": False,
        "runtime_accepted": False,
        "owner_proposal_allowed": False,
    }
