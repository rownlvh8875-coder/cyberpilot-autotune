"""Closed immutable provenance metadata. No source reader or authority."""

from dataclasses import dataclass, fields
from typing import Any

ERROR = "malformed capture provenance metadata"
UINT64_MAX = 2**64 - 1
PERMISSIONS = (
    ("application_authorized", False),
    ("build_execution_allowed", False),
    ("candidate_generation_allowed", False),
    ("device_class_qualified", False),
    ("owner_proposal_allowed", False),
    ("policy_adopted", False),
    ("promotion_authorized", False),
    ("runtime_accepted", False),
    ("runtime_qualified", False),
)
CATALOG = (
    (("run_id", "REGISTERED_RUN"), ("PREPARED_BINDING",), None),
    (("artifacts.executor_content.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.executor_content.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.bootstrap_content.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.bootstrap_content.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.provider_implementation.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.provider_implementation.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.syscall_policy.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.syscall_policy.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.collection_policy.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.collection_policy.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.toolchain_inventory.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.toolchain_inventory.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.dependency_inventory.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.dependency_inventory.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (
        ("artifacts.private_snapshot_manifest.sha256", "PREPARED_CONTENT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("artifacts.private_snapshot_manifest.sha256", "REVIEWED_CONTENT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("artifacts.full_expected_node_inventory.sha256", "PREPARED_CONTENT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("artifacts.full_expected_node_inventory.sha256", "REVIEWED_CONTENT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("artifacts.materialized_command_manifest.sha256", "PREPARED_CONTENT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("artifacts.materialized_command_manifest.sha256", "REVIEWED_CONTENT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (("artifacts.scope_record.sha256", "PREPARED_CONTENT"), ("PREPARED_BINDING",), None),
    (("artifacts.scope_record.sha256", "REVIEWED_CONTENT"), ("PREPARED_BINDING",), None),
    (
        ("cohorts.O.revision", "CONSUMED_SOURCE:O-PYTEST"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "O-PYTEST",
    ),
    (("cohorts.O.revision", "CONSUMED_SOURCE:O-H6"), ("COMMAND_START", "COMMAND_FINISH"), "O-H6"),
    (("cohorts.O.revision", "CONSUMED_SOURCE:O-H7"), ("COMMAND_START", "COMMAND_FINISH"), "O-H7"),
    (
        ("cohorts.O.tree", "CONSUMED_SOURCE:O-PYTEST"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "O-PYTEST",
    ),
    (("cohorts.O.tree", "CONSUMED_SOURCE:O-H6"), ("COMMAND_START", "COMMAND_FINISH"), "O-H6"),
    (("cohorts.O.tree", "CONSUMED_SOURCE:O-H7"), ("COMMAND_START", "COMMAND_FINISH"), "O-H7"),
    (
        ("cohorts.D.revision", "CONSUMED_SOURCE:D-PYTEST"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-PYTEST",
    ),
    (("cohorts.D.revision", "CONSUMED_SOURCE:D-H6"), ("COMMAND_START", "COMMAND_FINISH"), "D-H6"),
    (
        ("cohorts.D.revision", "CONSUMED_SOURCE:D-COVERAGE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("cohorts.D.tree", "CONSUMED_SOURCE:D-PYTEST"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-PYTEST",
    ),
    (("cohorts.D.tree", "CONSUMED_SOURCE:D-H6"), ("COMMAND_START", "COMMAND_FINISH"), "D-H6"),
    (
        ("cohorts.D.tree", "CONSUMED_SOURCE:D-COVERAGE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-COVERAGE",
    ),
    (("batch_boundary.identity_digest", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), None),
    (("batch_boundary.generation", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), None),
    (("batch_boundary.clock_domain", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), None),
    (("batch_limits.batch_memory_max_bytes.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.batch_memory_max_bytes.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.batch_memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.batch_pids_max.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.batch_pids_max.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.batch_pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.cpu_bandwidth_quota_us.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.cpu_bandwidth_quota_us.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.cpu_bandwidth_quota_us.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.cpu_bandwidth_period_us.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.cpu_bandwidth_period_us.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.cpu_bandwidth_period_us.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (
        ("batch_limits.cpu_usage_accounting_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("batch_limits.cpu_usage_accounting_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        None,
    ),
    (
        ("batch_limits.cpu_usage_accounting_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (
        ("batch_limits.cpu_accounting_latency_bound_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("batch_limits.cpu_accounting_latency_bound_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        None,
    ),
    (
        ("batch_limits.cpu_accounting_latency_bound_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.scratch_max_bytes.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.scratch_max_bytes.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.scratch_max_inodes.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.scratch_max_inodes.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (
        ("batch_limits.retained_combined_stdout_stderr_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("batch_limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        None,
    ),
    (
        ("batch_limits.retained_combined_stdout_stderr_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.batch_wall_limit_ns.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.batch_wall_limit_ns.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.batch_wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (("batch_limits.command_wall_limit_ns.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), None),
    (("batch_limits.command_wall_limit_ns.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.command_wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (
        ("batch_limits.stop_and_cleanup_limit_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        None,
    ),
    (("batch_limits.stop_and_cleanup_limit_ns.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), None),
    (
        ("batch_limits.stop_and_cleanup_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        None,
    ),
    (
        ("commands.O-PYTEST.cohort_id", "CONSUMED_COMMAND_SOURCE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.boundary.identity_digest", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "O-PYTEST",
    ),
    (("commands.O-PYTEST.boundary.generation", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-PYTEST"),
    (
        ("commands.O-PYTEST.boundary.clock_domain", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.memory_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.memory_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.pids_max.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (("commands.O-PYTEST.limits.pids_max.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-PYTEST"),
    (
        ("commands.O-PYTEST.limits.pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.cpu_usage_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.cpu_usage_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.cpu_usage_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.scratch_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.scratch_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.scratch_max_inodes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.scratch_max_inodes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.retained_combined_stdout_stderr_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-PYTEST",
    ),
    (
        (
            "commands.O-PYTEST.limits.retained_combined_stdout_stderr_bytes.value",
            "ENFORCEMENT_WITNESS",
        ),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.wall_limit_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.wall_limit_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-PYTEST",
    ),
    (
        ("commands.O-PYTEST.limits.wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-PYTEST",
    ),
    (("commands.O-PYTEST.timing.start_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "O-PYTEST"),
    (("commands.O-PYTEST.timing.deadline_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "O-PYTEST"),
    (("commands.O-PYTEST.timing.clock_domain", "COMMAND_CLOCK"), ("COMMAND_START",), "O-PYTEST"),
    (
        ("commands.O-H6.cohort_id", "CONSUMED_COMMAND_SOURCE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "O-H6",
    ),
    (("commands.O-H6.boundary.identity_digest", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-H6"),
    (("commands.O-H6.boundary.generation", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-H6"),
    (("commands.O-H6.boundary.clock_domain", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-H6"),
    (
        ("commands.O-H6.limits.memory_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H6",
    ),
    (("commands.O-H6.limits.memory_max_bytes.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-H6"),
    (
        ("commands.O-H6.limits.memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (("commands.O-H6.limits.pids_max.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), "O-H6"),
    (("commands.O-H6.limits.pids_max.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-H6"),
    (
        ("commands.O-H6.limits.pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.cpu_usage_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.cpu_usage_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.cpu_usage_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.scratch_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.scratch_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.scratch_max_inodes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.scratch_max_inodes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.retained_combined_stdout_stderr_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H6",
    ),
    (
        ("commands.O-H6.limits.retained_combined_stdout_stderr_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (("commands.O-H6.limits.wall_limit_ns.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), "O-H6"),
    (("commands.O-H6.limits.wall_limit_ns.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-H6"),
    (
        ("commands.O-H6.limits.wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H6",
    ),
    (("commands.O-H6.timing.start_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "O-H6"),
    (("commands.O-H6.timing.deadline_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "O-H6"),
    (("commands.O-H6.timing.clock_domain", "COMMAND_CLOCK"), ("COMMAND_START",), "O-H6"),
    (
        ("commands.O-H7.cohort_id", "CONSUMED_COMMAND_SOURCE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "O-H7",
    ),
    (("commands.O-H7.boundary.identity_digest", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-H7"),
    (("commands.O-H7.boundary.generation", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-H7"),
    (("commands.O-H7.boundary.clock_domain", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "O-H7"),
    (
        ("commands.O-H7.limits.memory_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H7",
    ),
    (("commands.O-H7.limits.memory_max_bytes.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-H7"),
    (
        ("commands.O-H7.limits.memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (("commands.O-H7.limits.pids_max.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), "O-H7"),
    (("commands.O-H7.limits.pids_max.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-H7"),
    (
        ("commands.O-H7.limits.pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.cpu_usage_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.cpu_usage_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.cpu_usage_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.scratch_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.scratch_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.scratch_max_inodes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.scratch_max_inodes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.retained_combined_stdout_stderr_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "O-H7",
    ),
    (
        ("commands.O-H7.limits.retained_combined_stdout_stderr_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (("commands.O-H7.limits.wall_limit_ns.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), "O-H7"),
    (("commands.O-H7.limits.wall_limit_ns.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "O-H7"),
    (
        ("commands.O-H7.limits.wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "O-H7",
    ),
    (("commands.O-H7.timing.start_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "O-H7"),
    (("commands.O-H7.timing.deadline_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "O-H7"),
    (("commands.O-H7.timing.clock_domain", "COMMAND_CLOCK"), ("COMMAND_START",), "O-H7"),
    (
        ("commands.D-PYTEST.cohort_id", "CONSUMED_COMMAND_SOURCE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.boundary.identity_digest", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "D-PYTEST",
    ),
    (("commands.D-PYTEST.boundary.generation", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "D-PYTEST"),
    (
        ("commands.D-PYTEST.boundary.clock_domain", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.memory_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.memory_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.pids_max.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (("commands.D-PYTEST.limits.pids_max.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "D-PYTEST"),
    (
        ("commands.D-PYTEST.limits.pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.cpu_usage_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.cpu_usage_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.cpu_usage_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.scratch_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.scratch_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.scratch_max_inodes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.scratch_max_inodes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.retained_combined_stdout_stderr_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-PYTEST",
    ),
    (
        (
            "commands.D-PYTEST.limits.retained_combined_stdout_stderr_bytes.value",
            "ENFORCEMENT_WITNESS",
        ),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.wall_limit_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.wall_limit_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-PYTEST",
    ),
    (
        ("commands.D-PYTEST.limits.wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-PYTEST",
    ),
    (("commands.D-PYTEST.timing.start_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "D-PYTEST"),
    (("commands.D-PYTEST.timing.deadline_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "D-PYTEST"),
    (("commands.D-PYTEST.timing.clock_domain", "COMMAND_CLOCK"), ("COMMAND_START",), "D-PYTEST"),
    (
        ("commands.D-H6.cohort_id", "CONSUMED_COMMAND_SOURCE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-H6",
    ),
    (("commands.D-H6.boundary.identity_digest", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "D-H6"),
    (("commands.D-H6.boundary.generation", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "D-H6"),
    (("commands.D-H6.boundary.clock_domain", "OWNED_BOUNDARY"), ("BOUNDARY_READY",), "D-H6"),
    (
        ("commands.D-H6.limits.memory_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-H6",
    ),
    (("commands.D-H6.limits.memory_max_bytes.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "D-H6"),
    (
        ("commands.D-H6.limits.memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (("commands.D-H6.limits.pids_max.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), "D-H6"),
    (("commands.D-H6.limits.pids_max.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "D-H6"),
    (
        ("commands.D-H6.limits.pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.cpu_usage_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.cpu_usage_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.cpu_usage_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.scratch_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.scratch_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.scratch_max_inodes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.scratch_max_inodes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.retained_combined_stdout_stderr_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-H6",
    ),
    (
        ("commands.D-H6.limits.retained_combined_stdout_stderr_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (("commands.D-H6.limits.wall_limit_ns.value", "APPROVED_LIMIT"), ("PREPARED_BINDING",), "D-H6"),
    (("commands.D-H6.limits.wall_limit_ns.value", "APPLIED_LIMIT"), ("LIMITS_APPLIED",), "D-H6"),
    (
        ("commands.D-H6.limits.wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-H6",
    ),
    (("commands.D-H6.timing.start_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "D-H6"),
    (("commands.D-H6.timing.deadline_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "D-H6"),
    (("commands.D-H6.timing.clock_domain", "COMMAND_CLOCK"), ("COMMAND_START",), "D-H6"),
    (
        ("commands.D-COVERAGE.cohort_id", "CONSUMED_COMMAND_SOURCE"),
        ("COMMAND_START", "COMMAND_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.boundary.identity_digest", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.boundary.generation", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.boundary.clock_domain", "OWNED_BOUNDARY"),
        ("BOUNDARY_READY",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.memory_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.memory_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.memory_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.pids_max.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.pids_max.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.pids_max.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.cpu_usage_budget_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.cpu_usage_budget_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.cpu_usage_budget_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.scratch_max_bytes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.scratch_max_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.scratch_max_bytes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.scratch_max_inodes.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.scratch_max_inodes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.scratch_max_inodes.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (
        (
            "commands.D-COVERAGE.limits.retained_combined_stdout_stderr_bytes.value",
            "APPROVED_LIMIT",
        ),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.retained_combined_stdout_stderr_bytes.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        (
            "commands.D-COVERAGE.limits.retained_combined_stdout_stderr_bytes.value",
            "ENFORCEMENT_WITNESS",
        ),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.wall_limit_ns.value", "APPROVED_LIMIT"),
        ("PREPARED_BINDING",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.wall_limit_ns.value", "APPLIED_LIMIT"),
        ("LIMITS_APPLIED",),
        "D-COVERAGE",
    ),
    (
        ("commands.D-COVERAGE.limits.wall_limit_ns.value", "ENFORCEMENT_WITNESS"),
        ("CONTROL_WITNESS", "BATCH_FINISH"),
        "D-COVERAGE",
    ),
    (("commands.D-COVERAGE.timing.start_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "D-COVERAGE"),
    (("commands.D-COVERAGE.timing.deadline_ns", "COMMAND_CLOCK"), ("COMMAND_START",), "D-COVERAGE"),
    (
        ("commands.D-COVERAGE.timing.clock_domain", "COMMAND_CLOCK"),
        ("COMMAND_START",),
        "D-COVERAGE",
    ),
    (("controls.subject_ro_enforced.value", "CONTROL_OBSERVATION"), ("CONTROL_WITNESS",), None),
    (("controls.subject_ro_enforced.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (("controls.network_denial_enforced.value", "CONTROL_OBSERVATION"), ("CONTROL_WITNESS",), None),
    (("controls.network_denial_enforced.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (
        ("controls.batch_boundary_placement_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (
        ("controls.batch_boundary_placement_observed.value", "CONTEXT_BINDING"),
        ("BATCH_FINISH",),
        None,
    ),
    (
        ("controls.pre_payload_gate_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (("controls.pre_payload_gate_observed.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (
        ("controls.bootstrap_outer_boundary_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (
        ("controls.bootstrap_outer_boundary_observed.value", "CONTEXT_BINDING"),
        ("BATCH_FINISH",),
        None,
    ),
    (
        ("controls.aggregate_memory_pids_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (("controls.aggregate_memory_pids_observed.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (
        ("controls.aggregate_scratch_bytes_inodes_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (
        ("controls.aggregate_scratch_bytes_inodes_observed.value", "CONTEXT_BINDING"),
        ("BATCH_FINISH",),
        None,
    ),
    (
        ("controls.stream_output_deadline_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (
        ("controls.stream_output_deadline_observed.value", "CONTEXT_BINDING"),
        ("BATCH_FINISH",),
        None,
    ),
    (("controls.FD_policy_observed.value", "CONTROL_OBSERVATION"), ("CONTROL_WITNESS",), None),
    (("controls.FD_policy_observed.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (("controls.owned_cleanup_observed.value", "CONTROL_OBSERVATION"), ("CONTROL_WITNESS",), None),
    (("controls.owned_cleanup_observed.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (
        ("controls.provider_guard_compatible.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (("controls.provider_guard_compatible.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (
        ("controls.toolchain_closure_reviewed.value", "CONTROL_OBSERVATION"),
        ("PREPARED_BINDING",),
        None,
    ),
    (("controls.toolchain_closure_reviewed.value", "CONTEXT_BINDING"), ("BATCH_FINISH",), None),
    (
        ("controls.expected_inventory_separately_frozen.value", "CONTROL_OBSERVATION"),
        ("PREPARED_BINDING",),
        None,
    ),
    (
        ("controls.expected_inventory_separately_frozen.value", "CONTEXT_BINDING"),
        ("BATCH_FINISH",),
        None,
    ),
    (
        ("controls.consumed_origins_lineage_observed.value", "CONTROL_OBSERVATION"),
        ("CONTROL_WITNESS",),
        None,
    ),
    (
        ("controls.consumed_origins_lineage_observed.value", "CONTEXT_BINDING"),
        ("BATCH_FINISH",),
        None,
    ),
    (("policy_digest", "PREPARED_POLICY"), ("PREPARED_BINDING",), None),
    (("producer_errors", "PRODUCER_STATUS"), ("PRODUCER_STATUS",), None),
    (("producer_unavailable", "PRODUCER_STATUS"), ("PRODUCER_STATUS",), None),
)
ERROR_CODES = (
    "NEGATIVE_CLAIM",
    "PRODUCER_REPORTED_ERROR",
    "EPOCH_MISMATCH",
    "COMMAND_MISMATCH",
    "CONTEXT_CHANGED",
    "BOUNDARY_REUSE",
    "CLOCK_DOMAIN_MISMATCH",
    "SOURCE_EVENT_ALIAS",
    "TIME_ORDER_INVALID",
    "EVENT_OUTSIDE_CAPTURE_WINDOW",
    "STAGE_ORDER_INVALID",
)
UNAVAILABLE_CODES = (
    "EPOCH_UNAVAILABLE",
    "CAPTURE_WINDOW_UNAVAILABLE",
    "WITNESS_MISSING",
    "WITNESS_UNAVAILABLE",
    "CONTEXT_UNAVAILABLE",
    "EVENT_IDENTITY_UNAVAILABLE",
    "CONTENT_REFERENCE_UNAVAILABLE",
)
ISSUE_FIELDS = (
    "epoch",
    "epoch.run_id",
    "epoch.policy_digest",
    "epoch.clock_domain",
    "capture_begin_ns",
    "capture_end_ns",
    "witnesses",
    "outcome",
    "stage",
    "context",
    "context.epoch",
    "context.epoch.run_id",
    "context.epoch.policy_digest",
    "context.epoch.clock_domain",
    "context.command_id",
    "context.attempt",
    "context.boundary_digest",
    "context.boundary_generation",
    "source_id",
    "event_id",
    "sequence",
    "event_time_ns",
    "content_digest",
)
COMMANDS = (
    "O-PYTEST",
    "O-H6",
    "O-H7",
    "D-PYTEST",
    "D-H6",
    "D-COVERAGE",
)
OUTCOMES = (
    "PRESENT_CLAIM",
    "NEGATIVE_CLAIM",
    "UNAVAILABLE_CLAIM",
    "ERROR_CLAIM",
)


KEYS = tuple(key for key, _, _ in CATALOG)


def need(condition: bool) -> None:
    if not condition:
        raise ValueError(ERROR)


def _member(value: Any, choices: Any) -> None:
    need(type(value) is str and value in choices)


def _uint(value: Any) -> None:
    need(value is None or (type(value) is int and 0 <= value <= UINT64_MAX))


def _hex(value: Any, size: int = 64) -> None:
    need(
        value is None
        or (
            type(value) is str
            and len(value) == size
            and all(c in "0123456789abcdef" for c in value)
        )
    )


def _nested(value: Any, cls: type) -> None:
    if value is not None:
        validate(value, cls)


class _Metadata:
    __slots__ = ()

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def mapping_status(self) -> str:
        return "PROVENANCE_METADATA_ONLY"

    @property
    def H_executed(self) -> bool:
        return False

    @property
    def integrated_admission(self) -> bool:
        return False

    @property
    def profile_record(self) -> None:
        return None

    @property
    def content_identity_only(self) -> bool:
        return True

    @property
    def atomicity(self) -> str:
        return "NOT_ESTABLISHED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    def __post_init__(self) -> None:
        for key, value in validate(self, type(self)).items():
            object.__setattr__(self, key, value)


@dataclass(frozen=True, slots=True)
class CaptureEpoch(_Metadata):
    run_id: str | None
    policy_digest: str | None
    clock_domain: str | None


@dataclass(frozen=True, slots=True)
class WitnessContext(_Metadata):
    epoch: CaptureEpoch | None
    command_id: str | None
    attempt: int | None
    boundary_digest: str | None
    boundary_generation: int | None


@dataclass(frozen=True, slots=True)
class CaptureWitness(_Metadata):
    target_path: str
    role: str
    stage: str
    context: WitnessContext | None
    source_id: str | None
    event_id: str | None
    sequence: int | None
    event_time_ns: int | None
    content_digest: str | None
    outcome: str


@dataclass(frozen=True, slots=True)
class CaptureWitnessBundle(_Metadata):
    epoch: CaptureEpoch | None
    capture_begin_ns: int | None
    capture_end_ns: int | None
    witnesses: tuple[CaptureWitness, ...]


@dataclass(frozen=True, slots=True)
class CaptureIssue(_Metadata):
    code: str
    target_path: str
    role: str
    field: str


@dataclass(frozen=True, slots=True)
class CaptureAlignmentDecision(_Metadata):
    errors: tuple[CaptureIssue, ...]
    unavailable: tuple[CaptureIssue, ...]

    @property
    def alignment_status(self) -> str:
        if self.errors:
            return "REJECTED"
        return "UNAVAILABLE" if self.unavailable else "COHORT_METADATA_CONSISTENT"


_TYPES = (
    CaptureEpoch,
    WitnessContext,
    CaptureWitness,
    CaptureWitnessBundle,
    CaptureIssue,
    CaptureAlignmentDecision,
)


def _key(value: Any) -> tuple[str, str]:
    need(type(value.target_path) is str and type(value.role) is str)
    result = value.target_path, value.role
    need(result in KEYS)
    return result


def _issue_key(value: CaptureIssue) -> tuple[str, str, str, str]:
    return value.code, value.target_path, value.role, value.field


def validate(value: Any, expected: type) -> dict[str, Any]:
    need(expected in _TYPES and type(value) is expected)
    try:
        data = {f.name: getattr(value, f.name) for f in fields(expected)}
    except AttributeError:
        data = None
    need(data is not None)
    assert data is not None
    if expected is CaptureEpoch:
        _hex(data["run_id"], 32)
        _hex(data["policy_digest"])
        text = data["clock_domain"]
        need(
            text is None
            or (
                type(text) is str
                and 1 <= len(text) <= 128
                and all(
                    c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
                    for c in text
                )
            )
        )
    elif expected is WitnessContext:
        _nested(data["epoch"], CaptureEpoch)
        if data["command_id"] is not None:
            _member(data["command_id"], COMMANDS)
        _uint(data["attempt"])
        _hex(data["boundary_digest"])
        _uint(data["boundary_generation"])
    elif expected is CaptureWitness:
        key = _key(value)
        stages = CATALOG[KEYS.index(key)][1]
        _member(data["stage"], stages)
        _nested(data["context"], WitnessContext)
        for name in ("source_id", "event_id", "content_digest"):
            _hex(data[name])
        _uint(data["sequence"])
        _uint(data["event_time_ns"])
        _member(data["outcome"], OUTCOMES)
    elif expected is CaptureWitnessBundle:
        _nested(data["epoch"], CaptureEpoch)
        _uint(data["capture_begin_ns"])
        _uint(data["capture_end_ns"])
        witnesses = data["witnesses"]
        need(type(witnesses) is tuple)
        for witness in witnesses:
            validate(witness, CaptureWitness)
        keys = tuple(_key(w) for w in witnesses)
        need(len(set(keys)) == len(keys))
        order = {key: i for i, (key, _, _) in enumerate(CATALOG)}
        data["witnesses"] = tuple(sorted((w for w in witnesses), key=lambda w: order[_key(w)]))
    elif expected is CaptureIssue:
        _member(data["code"], ERROR_CODES + UNAVAILABLE_CODES)
        need(type(data["target_path"]) is str and type(data["role"]) is str)
        if (data["target_path"], data["role"]) != ("@bundle", "BUNDLE"):
            _key(value)
        _member(data["field"], ISSUE_FIELDS)
    else:
        for name, codes in (("errors", ERROR_CODES), ("unavailable", UNAVAILABLE_CODES)):
            issues = data[name]
            need(type(issues) is tuple)
            for issue in issues:
                validate(issue, CaptureIssue)
                need(issue.code in codes)
            data[name] = tuple(sorted(set(issues), key=_issue_key))
    return data
