"""Fixed semantic profile; no permission or execution capability."""

VERSION = "actual-diagnostic-receipt-v1"
PRE_VERSION = "actual-diagnostic-prelaunch-reference-v1"
POST_VERSION = "actual-diagnostic-capture-reference-v1"
MODE = "ACTUAL_DIAGNOSTIC_REPORTED_UNTRUSTED"
ORIGIN = "PROSPECTIVE_CAPTURE_REPORTED_UNTRUSTED"
DOCUMENT_ROLES = ("baseline", "command", "preflight", "intent", "exit", "snapshot")
RAW_ROLES = (
    "telemetry",
    "console",
    "cli_stdout",
    "cli_stderr",
    "record_json",
    "initrd",
    "exit_receipt",
)
HEADER_KEYS = (
    "contract_version",
    "role",
    "mode",
    "origin",
    "synthetic",
    "workflow_run_id",
    "workflow_attempt_id",
    "case",
    "producer_implementation_revision",
    "producer_source_revision",
    "capture_implementation_sha256",
    "host_clock_context",
    "status",
    "permissions",
)
BODY_KEYS = (
    (
        "baseline",
        (
            "expected_assets",
            "declared_case_profile",
            "producer_record_schema",
            "policy_reference_sha256",
        ),
    ),
    (
        "command",
        (
            "host_cli_argv",
            "host_cli_cwd",
            "interpreter_sha256",
            "environment_scope",
            "environment",
            "planned_destination",
            "expected_qemu_argv",
        ),
    ),
    (
        "preflight",
        (
            "baseline_sha256",
            "command_sha256",
            "observed_assets",
            "observation_kind",
            "asset_checks",
            "mono_ns",
            "event_ordinal",
        ),
    ),
    (
        "intent",
        (
            "baseline_sha256",
            "command_sha256",
            "preflight_sha256",
            "pre_reference_content_sha256",
            "mono_ns",
            "event_ordinal",
        ),
    ),
    (
        "exit",
        (
            "intent_sha256",
            "reported_source_ids",
            "host_cli_argv_observed",
            "cli_observation",
            "qemu_observation",
            "launch_before_ns",
            "launch_after_ns",
            "exit_observed_ns",
            "mono_ns",
            "event_ordinal",
            "raw_close_states",
            "capture_outcome",
            "failure_stage",
            "host_interpreter_sha256_observed",
            "host_environment_observed",
            "host_context_observation_kind",
        ),
    ),
    (
        "snapshot",
        (
            "baseline_sha256",
            "command_sha256",
            "preflight_sha256",
            "intent_sha256",
            "exit_sha256",
            "raw_descriptors",
            "reported_source_ids",
            "original_case_directory",
            "mono_ns",
            "event_ordinal",
        ),
    ),
)
ASSET_KEYS = ("probe", "vm", "kernel", "kernel_config", "transport_profile", "init", "image")
ENV_KEYS = ("LANG", "LC_ALL", "PATH", "PYTHONDONTWRITEBYTECODE")
SHARED_IDENTITIES = (
    "workflow_run_id",
    "workflow_attempt_id",
    "case",
    "producer_implementation_revision",
    "producer_source_revision",
    "capture_implementation_sha256",
)
PERMISSIONS = (
    ("build_execution_allowed", False),
    ("promotion_authorized", False),
    ("runtime_qualified", False),
    ("device_class_qualified", False),
    ("policy_adopted", False),
    ("candidate_generation_allowed", False),
    ("application_authorized", False),
    ("runtime_accepted", False),
    ("owner_proposal_allowed", False),
)
REASON_ORDER = (
    "INPUT_LIMIT",
    "PARSE_INVALID",
    "ROLE_SET_INVALID",
    "DOCUMENT_SHAPE_INVALID",
    "UNSUPPORTED_VERSION",
    "WRONG_ORIGIN",
    "CONTEXT_MISMATCH",
    "PERMISSION_ESCALATION",
    "HASH_MISMATCH",
    "RAW_DESCRIPTOR_MISMATCH",
    "REPORTED_ID_MISMATCH",
    "COMMAND_MISMATCH",
    "INTERPRETER_MISMATCH",
    "ENVIRONMENT_MISMATCH",
    "PROCESS_STATE_CONFLICT",
    "CAPTURE_STATE_CONFLICT",
    "TIME_REVERSED",
    "MISSING_DOCUMENT",
    "MISSING_RAW",
    "MISSING_PRE_REFERENCE",
    "MISSING_POST_REFERENCE",
    "MISSING_CONTEXT",
    "CLOCK_CONTEXT_UNAVAILABLE",
    "CLOCK_CONTEXT_CHANGED",
)
REJECT_REASONS = REASON_ORDER[:17]
INCOMPLETE_REASONS = REASON_ORDER[17:23]
STATUSES = (
    "REJECTED",
    "INCOMPLETE",
    "REPORTED_TIME_ORDER_UNCOMPARABLE",
    "REPORTED_BINDING_CONSISTENT",
)
CHECK_GROUP_ORDER = (
    "container_bounds",
    "document:baseline",
    "document:command",
    "document:preflight",
    "document:intent",
    "document:exit",
    "document:snapshot",
    "headers",
    "assets",
    "pre_reference",
    "document_links",
    "raw_binding",
    "reported_ids",
    "command_context",
    "process_state",
    "clocks",
    "completeness",
    "post_reference",
)
CASES = ("DFD01", "DFD02", "DFD03", "DFD04", "DFD05", "DFD06")
DOCUMENT_CAP = 65536
JSON_RAW_CAP = 65536
STREAM_CAP = 1048576
IMAGE_CAP = 4194304
TOTAL_CAP = 5898240
