"""Immutable supplied diagnostics;never a source reader or H receipt."""

import re
from dataclasses import dataclass, fields
from typing import Any

ERROR = "invalid preflight diagnostic value"
UINT64_MAX = 2**64 - 1
REDACTED = "[REDACTED_UNREGISTERED_SOURCE_TEXT]"

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

BINDING_FIELDS = (
    "repository",
    "run_id",
    "attempt",
    "job_id",
    "source_revision",
    "workflow_sha256",
    "collector_sha256",
    "observation_sha256",
)

PROFILES = (
    (
        "REGISTERED_PREFLIGHT_R0",
        (
            ("repository", "rownlvh8875-coder/cyberpilot-autotune"),
            ("run_id", 41653951704),
            ("attempt", 1),
            ("job_id", 125979186623),
            ("source_revision", "4b77b31dd23010f2d2b394466d88b04a4a2720e2"),
            ("workflow_sha256", "40781c65ecb75467cdcd1204902e72869249ad018c7c4bc51e11996830572b1d"),
            (
                "collector_sha256",
                "3b3b99e4fb1dab67b2972c06cc432ed80f6b38c3f48c3aa69a4d13517750429e",
            ),
            (
                "observation_sha256",
                "4b6aa465bacb157eee17852fdacc5f4da69d7e9401d027f6db3cafa741929597",
            ),
        ),
    ),
    (
        "SYNTHETIC_MAPPING_S0",
        (
            ("repository", "rownlvh8875-coder/cyberpilot-autotune"),
            ("run_id", 1),
            ("attempt", 1),
            ("job_id", 1),
            ("source_revision", "1111111111111111111111111111111111111111"),
            ("workflow_sha256", "40781c65ecb75467cdcd1204902e72869249ad018c7c4bc51e11996830572b1d"),
            (
                "collector_sha256",
                "3b3b99e4fb1dab67b2972c06cc432ed80f6b38c3f48c3aa69a4d13517750429e",
            ),
            (
                "observation_sha256",
                "5d813832979c34b7efc5c15c5312d83c266a14ce63144e3f4bb9fe9ca027040d",
            ),
        ),
    ),
)

EVIDENCE_KINDS = (
    ("REGISTERED_PREFLIGHT_R0", "REGISTERED_SOURCE_CONTEXT_ONLY_NOT_H"),
    ("SYNTHETIC_MAPPING_S0", "SYNTHETIC_NOT_OBSERVED_OR_H_BUDGET"),
)

SOURCE_OBJECT_KEYS = (
    (
        "",
        (
            "H_executed",
            "aggregate_resource_boundary_qualified",
            "atomic",
            "cgroup",
            "content_identity_only",
            "execution_context",
            "execution_verdict",
            "global_status",
            "host",
            "limitations",
            "native_apis",
            "permissions",
            "schema",
            "security",
            "status",
            "tools",
        ),
    ),
    (
        "/cgroup",
        (
            "atomic",
            "controls",
            "directory",
            "membership_confirmed",
            "status",
            "write_delegation_verified",
        ),
    ),
    (
        "/cgroup/controls",
        (
            "cgroup.controllers",
            "cgroup.max.depth",
            "cgroup.max.descendants",
            "cgroup.subtree_control",
            "cgroup.type",
            "cpu.max",
            "memory.max",
            "pids.max",
        ),
    ),
    ("/cgroup/controls/cgroup.controllers", ("metadata", "value")),
    (
        "/cgroup/controls/cgroup.controllers/metadata",
        ("effective_write_access", "gid", "mode", "uid"),
    ),
    ("/cgroup/controls/cgroup.max.depth", ("metadata", "value")),
    (
        "/cgroup/controls/cgroup.max.depth/metadata",
        ("effective_write_access", "gid", "mode", "uid"),
    ),
    ("/cgroup/controls/cgroup.max.descendants", ("metadata", "value")),
    (
        "/cgroup/controls/cgroup.max.descendants/metadata",
        ("effective_write_access", "gid", "mode", "uid"),
    ),
    ("/cgroup/controls/cgroup.subtree_control", ("metadata", "value")),
    (
        "/cgroup/controls/cgroup.subtree_control/metadata",
        ("effective_write_access", "gid", "mode", "uid"),
    ),
    ("/cgroup/controls/cgroup.type", ("metadata", "value")),
    ("/cgroup/controls/cgroup.type/metadata", ("effective_write_access", "gid", "mode", "uid")),
    ("/cgroup/controls/cpu.max", ("metadata", "value")),
    ("/cgroup/controls/cpu.max/metadata", ("effective_write_access", "gid", "mode", "uid")),
    ("/cgroup/controls/memory.max", ("metadata", "value")),
    ("/cgroup/controls/memory.max/metadata", ("effective_write_access", "gid", "mode", "uid")),
    ("/cgroup/controls/pids.max", ("metadata", "value")),
    ("/cgroup/controls/pids.max/metadata", ("effective_write_access", "gid", "mode", "uid")),
    ("/cgroup/directory", ("effective_write_access", "gid", "mode", "uid")),
    ("/execution_context", ("actions", "repository", "run_attempt", "run_id", "sha", "trust")),
    ("/host", ("egid", "euid", "gid", "machine", "python_version", "system", "uid")),
    ("/native_apis", ("fcntl", "os", "resource")),
    ("/native_apis/fcntl", ("module_available", "required_apis_present")),
    (
        "/native_apis/os",
        ("MFD_ALLOW_SEALING", "MFD_CLOEXEC", "P_PIDFD", "memfd_create", "pidfd_open"),
    ),
    ("/native_apis/resource", ("module_available", "required_apis_present")),
    (
        "/permissions",
        (
            "application_authorized",
            "build_execution_allowed",
            "candidate_generation_allowed",
            "device_class_qualified",
            "owner_proposal_allowed",
            "policy_adopted",
            "promotion_authorized",
            "runtime_accepted",
            "runtime_qualified",
        ),
    ),
    ("/security", ("CapEff", "NoNewPrivs", "Seccomp")),
    (
        "/tools",
        (
            "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12",
            "/usr/bin/bwrap",
            "/usr/bin/setpriv",
        ),
    ),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12",
        ("expected_sha256", "pin_matches", "sha256"),
    ),
    ("/tools/~1usr~1bin~1bwrap", ("expected_sha256", "pin_matches", "sha256")),
    ("/tools/~1usr~1bin~1setpriv", ("expected_sha256", "pin_matches", "sha256")),
)

SOURCE_ARRAY_LENGTHS = (
    ("/host/python_version", 3),
    ("/limitations", 4),
)

NULLABLE_CONTAINERS = (
    "/cgroup/controls",
    "/cgroup/controls/cgroup.controllers/metadata",
    "/cgroup/controls/cgroup.max.depth/metadata",
    "/cgroup/controls/cgroup.max.descendants/metadata",
    "/cgroup/controls/cgroup.subtree_control/metadata",
    "/cgroup/controls/cgroup.type/metadata",
    "/cgroup/controls/cpu.max/metadata",
    "/cgroup/controls/memory.max/metadata",
    "/cgroup/controls/pids.max/metadata",
    "/cgroup/directory",
)

SOURCE_LEAF_RULES = (
    ("/H_executed", "bool"),
    ("/aggregate_resource_boundary_qualified", "bool"),
    ("/atomic", "bool"),
    ("/cgroup/atomic", "bool"),
    ("/cgroup/controls/cgroup.controllers/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/cgroup.controllers/metadata/gid", "uint"),
    ("/cgroup/controls/cgroup.controllers/metadata/mode", "mode"),
    ("/cgroup/controls/cgroup.controllers/metadata/uid", "uint"),
    ("/cgroup/controls/cgroup.controllers/value", "optional:control:cgroup.controllers"),
    ("/cgroup/controls/cgroup.max.depth/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/cgroup.max.depth/metadata/gid", "uint"),
    ("/cgroup/controls/cgroup.max.depth/metadata/mode", "mode"),
    ("/cgroup/controls/cgroup.max.depth/metadata/uid", "uint"),
    ("/cgroup/controls/cgroup.max.depth/value", "optional:control:cgroup.max.depth"),
    ("/cgroup/controls/cgroup.max.descendants/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/cgroup.max.descendants/metadata/gid", "uint"),
    ("/cgroup/controls/cgroup.max.descendants/metadata/mode", "mode"),
    ("/cgroup/controls/cgroup.max.descendants/metadata/uid", "uint"),
    ("/cgroup/controls/cgroup.max.descendants/value", "optional:control:cgroup.max.descendants"),
    ("/cgroup/controls/cgroup.subtree_control/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/cgroup.subtree_control/metadata/gid", "uint"),
    ("/cgroup/controls/cgroup.subtree_control/metadata/mode", "mode"),
    ("/cgroup/controls/cgroup.subtree_control/metadata/uid", "uint"),
    ("/cgroup/controls/cgroup.subtree_control/value", "optional:control:cgroup.subtree_control"),
    ("/cgroup/controls/cgroup.type/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/cgroup.type/metadata/gid", "uint"),
    ("/cgroup/controls/cgroup.type/metadata/mode", "mode"),
    ("/cgroup/controls/cgroup.type/metadata/uid", "uint"),
    ("/cgroup/controls/cgroup.type/value", "optional:control:cgroup.type"),
    ("/cgroup/controls/cpu.max/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/cpu.max/metadata/gid", "uint"),
    ("/cgroup/controls/cpu.max/metadata/mode", "mode"),
    ("/cgroup/controls/cpu.max/metadata/uid", "uint"),
    ("/cgroup/controls/cpu.max/value", "optional:control:cpu.max"),
    ("/cgroup/controls/memory.max/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/memory.max/metadata/gid", "uint"),
    ("/cgroup/controls/memory.max/metadata/mode", "mode"),
    ("/cgroup/controls/memory.max/metadata/uid", "uint"),
    ("/cgroup/controls/memory.max/value", "optional:control:memory.max"),
    ("/cgroup/controls/pids.max/metadata/effective_write_access", "optional:bool"),
    ("/cgroup/controls/pids.max/metadata/gid", "uint"),
    ("/cgroup/controls/pids.max/metadata/mode", "mode"),
    ("/cgroup/controls/pids.max/metadata/uid", "uint"),
    ("/cgroup/controls/pids.max/value", "optional:control:pids.max"),
    ("/cgroup/directory/effective_write_access", "optional:bool"),
    ("/cgroup/directory/gid", "uint"),
    ("/cgroup/directory/mode", "mode"),
    ("/cgroup/directory/uid", "uint"),
    ("/cgroup/membership_confirmed", "optional:bool"),
    ("/cgroup/status", "cgroup_status"),
    ("/cgroup/write_delegation_verified", "bool"),
    ("/content_identity_only", "bool"),
    ("/execution_context/actions", "optional:bool"),
    ("/execution_context/repository", "optional:repo"),
    ("/execution_context/run_attempt", "optional:decimal8"),
    ("/execution_context/run_id", "optional:decimal20"),
    ("/execution_context/sha", "optional:hex40"),
    ("/execution_context/trust", "ascii128"),
    ("/execution_verdict", "ascii128"),
    ("/global_status", "ascii128"),
    ("/host/egid", "optional:uint"),
    ("/host/euid", "optional:uint"),
    ("/host/gid", "optional:uint"),
    ("/host/machine", "optional:machine"),
    ("/host/python_version/0", "uint"),
    ("/host/python_version/1", "uint"),
    ("/host/python_version/2", "uint"),
    ("/host/system", "optional:linux"),
    ("/host/uid", "optional:uint"),
    ("/limitations/0", "ascii128"),
    ("/limitations/1", "ascii128"),
    ("/limitations/2", "ascii128"),
    ("/limitations/3", "ascii128"),
    ("/native_apis/fcntl/module_available", "bool"),
    ("/native_apis/fcntl/required_apis_present", "bool"),
    ("/native_apis/os/MFD_ALLOW_SEALING", "bool"),
    ("/native_apis/os/MFD_CLOEXEC", "bool"),
    ("/native_apis/os/P_PIDFD", "bool"),
    ("/native_apis/os/memfd_create", "bool"),
    ("/native_apis/os/pidfd_open", "bool"),
    ("/native_apis/resource/module_available", "bool"),
    ("/native_apis/resource/required_apis_present", "bool"),
    ("/permissions/application_authorized", "bool"),
    ("/permissions/build_execution_allowed", "bool"),
    ("/permissions/candidate_generation_allowed", "bool"),
    ("/permissions/device_class_qualified", "bool"),
    ("/permissions/owner_proposal_allowed", "bool"),
    ("/permissions/policy_adopted", "bool"),
    ("/permissions/promotion_authorized", "bool"),
    ("/permissions/runtime_accepted", "bool"),
    ("/permissions/runtime_qualified", "bool"),
    ("/schema", "schema"),
    ("/security/CapEff", "optional:caphex"),
    ("/security/NoNewPrivs", "optional:security1"),
    ("/security/Seccomp", "optional:security2"),
    ("/status", "ascii128"),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/expected_sha256",
        "hex64",
    ),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/pin_matches",
        "optional:bool",
    ),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/sha256",
        "optional:hex64",
    ),
    ("/tools/~1usr~1bin~1bwrap/expected_sha256", "hex64"),
    ("/tools/~1usr~1bin~1bwrap/pin_matches", "optional:bool"),
    ("/tools/~1usr~1bin~1bwrap/sha256", "optional:hex64"),
    ("/tools/~1usr~1bin~1setpriv/expected_sha256", "hex64"),
    ("/tools/~1usr~1bin~1setpriv/pin_matches", "optional:bool"),
    ("/tools/~1usr~1bin~1setpriv/sha256", "optional:hex64"),
)

DIAGNOSTIC_RULES = (
    ("/H_executed", "bool", False),
    ("/aggregate_resource_boundary_qualified", "bool", False),
    ("/atomic", "bool", False),
    ("/cgroup/atomic", "bool", False),
    ("/cgroup/controls/cgroup.controllers/metadata/effective_write_access", "optional:bool", True),
    ("/cgroup/controls/cgroup.controllers/metadata/mode", "mode", True),
    ("/cgroup/controls/cgroup.controllers/value", "optional:control:cgroup.controllers", True),
    ("/cgroup/controls/cgroup.max.depth/metadata/effective_write_access", "optional:bool", True),
    ("/cgroup/controls/cgroup.max.depth/metadata/mode", "mode", True),
    ("/cgroup/controls/cgroup.max.depth/value", "optional:control:cgroup.max.depth", True),
    (
        "/cgroup/controls/cgroup.max.descendants/metadata/effective_write_access",
        "optional:bool",
        True,
    ),
    ("/cgroup/controls/cgroup.max.descendants/metadata/mode", "mode", True),
    (
        "/cgroup/controls/cgroup.max.descendants/value",
        "optional:control:cgroup.max.descendants",
        True,
    ),
    (
        "/cgroup/controls/cgroup.subtree_control/metadata/effective_write_access",
        "optional:bool",
        True,
    ),
    ("/cgroup/controls/cgroup.subtree_control/metadata/mode", "mode", True),
    (
        "/cgroup/controls/cgroup.subtree_control/value",
        "optional:control:cgroup.subtree_control",
        True,
    ),
    ("/cgroup/controls/cgroup.type/metadata/effective_write_access", "optional:bool", True),
    ("/cgroup/controls/cgroup.type/metadata/mode", "mode", True),
    ("/cgroup/controls/cgroup.type/value", "optional:control:cgroup.type", True),
    ("/cgroup/controls/cpu.max/metadata/effective_write_access", "optional:bool", True),
    ("/cgroup/controls/cpu.max/metadata/mode", "mode", True),
    ("/cgroup/controls/cpu.max/value", "optional:control:cpu.max", True),
    ("/cgroup/controls/memory.max/metadata/effective_write_access", "optional:bool", True),
    ("/cgroup/controls/memory.max/metadata/mode", "mode", True),
    ("/cgroup/controls/memory.max/value", "optional:control:memory.max", True),
    ("/cgroup/controls/pids.max/metadata/effective_write_access", "optional:bool", True),
    ("/cgroup/controls/pids.max/metadata/mode", "mode", True),
    ("/cgroup/controls/pids.max/value", "optional:control:pids.max", True),
    ("/cgroup/directory/effective_write_access", "optional:bool", True),
    ("/cgroup/directory/mode", "mode", True),
    ("/cgroup/membership_confirmed", "optional:bool", True),
    ("/cgroup/status", "cgroup_status", False),
    ("/cgroup/write_delegation_verified", "bool", False),
    ("/content_identity_only", "bool", False),
    ("/execution_context/actions", "optional:bool", True),
    ("/execution_context/repository", "optional:repo", True),
    ("/execution_context/run_attempt", "optional:decimal8", True),
    ("/execution_context/run_id", "optional:decimal20", True),
    ("/execution_context/sha", "optional:hex40", True),
    ("/execution_context/trust", "ascii128", False),
    ("/execution_verdict", "ascii128", False),
    ("/global_status", "ascii128", False),
    ("/host/machine", "optional:machine", True),
    ("/host/python_version/0", "uint", False),
    ("/host/python_version/1", "uint", False),
    ("/host/python_version/2", "uint", False),
    ("/host/system", "optional:linux", True),
    ("/limitations/0", "ascii128", False),
    ("/limitations/1", "ascii128", False),
    ("/limitations/2", "ascii128", False),
    ("/limitations/3", "ascii128", False),
    ("/native_apis/fcntl/module_available", "bool", False),
    ("/native_apis/fcntl/required_apis_present", "bool", False),
    ("/native_apis/os/MFD_ALLOW_SEALING", "bool", False),
    ("/native_apis/os/MFD_CLOEXEC", "bool", False),
    ("/native_apis/os/P_PIDFD", "bool", False),
    ("/native_apis/os/memfd_create", "bool", False),
    ("/native_apis/os/pidfd_open", "bool", False),
    ("/native_apis/resource/module_available", "bool", False),
    ("/native_apis/resource/required_apis_present", "bool", False),
    ("/permissions/application_authorized", "bool", False),
    ("/permissions/build_execution_allowed", "bool", False),
    ("/permissions/candidate_generation_allowed", "bool", False),
    ("/permissions/device_class_qualified", "bool", False),
    ("/permissions/owner_proposal_allowed", "bool", False),
    ("/permissions/policy_adopted", "bool", False),
    ("/permissions/promotion_authorized", "bool", False),
    ("/permissions/runtime_accepted", "bool", False),
    ("/permissions/runtime_qualified", "bool", False),
    ("/schema", "schema", False),
    ("/security/CapEff", "optional:caphex", True),
    ("/security/NoNewPrivs", "optional:security1", True),
    ("/security/Seccomp", "optional:security2", True),
    ("/status", "ascii128", False),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/expected_sha256",
        "hex64",
        False,
    ),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/pin_matches",
        "optional:bool",
        True,
    ),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/sha256",
        "optional:hex64",
        True,
    ),
    ("/tools/~1usr~1bin~1bwrap/expected_sha256", "hex64", False),
    ("/tools/~1usr~1bin~1bwrap/pin_matches", "optional:bool", True),
    ("/tools/~1usr~1bin~1bwrap/sha256", "optional:hex64", True),
    ("/tools/~1usr~1bin~1setpriv/expected_sha256", "hex64", False),
    ("/tools/~1usr~1bin~1setpriv/pin_matches", "optional:bool", True),
    ("/tools/~1usr~1bin~1setpriv/sha256", "optional:hex64", True),
)

STRING_VALUES = (
    ("/cgroup/controls/cgroup.controllers/metadata/mode", ("0444",)),
    ("/cgroup/controls/cgroup.controllers/value", ("cpuset cpu io memory pids",)),
    ("/cgroup/controls/cgroup.max.depth/metadata/mode", ("0644",)),
    ("/cgroup/controls/cgroup.max.depth/value", ("max",)),
    ("/cgroup/controls/cgroup.max.descendants/metadata/mode", ("0644",)),
    ("/cgroup/controls/cgroup.max.descendants/value", ("max",)),
    ("/cgroup/controls/cgroup.subtree_control/metadata/mode", ("0644",)),
    ("/cgroup/controls/cgroup.subtree_control/value", ("",)),
    ("/cgroup/controls/cgroup.type/metadata/mode", ("0644",)),
    ("/cgroup/controls/cgroup.type/value", ("domain",)),
    ("/cgroup/controls/cpu.max/metadata/mode", ("0644",)),
    ("/cgroup/controls/cpu.max/value", ("max 100000",)),
    ("/cgroup/controls/memory.max/metadata/mode", ("0644",)),
    ("/cgroup/controls/memory.max/value", ("max",)),
    ("/cgroup/controls/pids.max/metadata/mode", ("0644",)),
    ("/cgroup/controls/pids.max/value", ("1", "17441")),
    ("/cgroup/directory/mode", ("0755",)),
    ("/cgroup/status", ("MEMBERSHIP_OBSERVED_NOT_DELEGATION",)),
    ("/execution_context/repository", ("rownlvh8875-coder/cyberpilot-autotune",)),
    ("/execution_context/run_attempt", ("1",)),
    ("/execution_context/run_id", ("1", "41653951704")),
    (
        "/execution_context/sha",
        ("1111111111111111111111111111111111111111", "4b77b31dd23010f2d2b394466d88b04a4a2720e2"),
    ),
    ("/execution_context/trust", ("UNVERIFIED_CALLER_METADATA",)),
    ("/execution_verdict", ("NOT_EVALUATED",)),
    ("/global_status", ("BLOCKED",)),
    ("/host/machine", ("synthetic", "x86_64")),
    ("/host/system", ("Linux",)),
    ("/limitations/0", ("NO_EXECUTION_OR_WRITE_PROBE",)),
    ("/limitations/1", ("NO_PRIVATE_BUDGET_OR_DELEGATION_PROOF",)),
    ("/limitations/2", ("NO_ATOMICITY_OR_AUTHENTICITY",)),
    ("/limitations/3", ("NO_RUNTIME_QUALIFICATION",)),
    ("/schema", ("actions-runner-preflight-v1",)),
    ("/security/CapEff", ("0000000000000000",)),
    ("/status", ("READ_ONLY_OBSERVATION_NOT_QUALIFICATION",)),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/expected_sha256",
        ("fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7",),
    ),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/sha256",
        (),
    ),
    (
        "/tools/~1usr~1bin~1bwrap/expected_sha256",
        ("573236e5328ac2ebb08f59ae3a9805b4f8d12bdef14be8af4450d5463294985f",),
    ),
    ("/tools/~1usr~1bin~1bwrap/sha256", ()),
    (
        "/tools/~1usr~1bin~1setpriv/expected_sha256",
        ("f7cedc63bbc1df7912b343a1240a77d16db7633563d69897ec8ad2a99c24024b",),
    ),
    (
        "/tools/~1usr~1bin~1setpriv/sha256",
        (
            "2222222222222222222222222222222222222222222222222222222222222222",
            "62ec0120791f3afcfb689fed52384ec2b0accc6e118a6b9a1d6fcfa7450aaf37",
        ),
    ),
)

GAP_PAIRS = (
    ("run_id", "NO_H_BATCH_OR_POLICY_BINDING"),
    ("artifacts.executor_content.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.bootstrap_content.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.provider_implementation.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.syscall_policy.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.collection_policy.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.toolchain_inventory.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.dependency_inventory.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.private_snapshot_manifest.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.full_expected_node_inventory.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.materialized_command_manifest.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("artifacts.scope_record.sha256", "NO_FULL_REVIEWED_H_ARTIFACT"),
    ("cohorts.O.revision", "NO_CONSUMED_O_D_COHORT"),
    ("cohorts.O.tree", "NO_CONSUMED_O_D_COHORT"),
    ("cohorts.D.revision", "NO_CONSUMED_O_D_COHORT"),
    ("cohorts.D.tree", "NO_CONSUMED_O_D_COHORT"),
    ("batch_boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("batch_boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("batch_boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("batch_limits.batch_memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.batch_pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.cpu_bandwidth_quota_us.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.cpu_bandwidth_period_us.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.cpu_usage_accounting_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.cpu_accounting_latency_bound_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.retained_combined_stdout_stderr_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.batch_wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.command_wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("batch_limits.stop_and_cleanup_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-PYTEST.cohort_id", "NO_CONSUMED_O_D_COHORT"),
    ("commands.O-PYTEST.boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-PYTEST.boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-PYTEST.boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-PYTEST.limits.memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-PYTEST.limits.pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-PYTEST.limits.cpu_usage_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-PYTEST.limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-PYTEST.limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    (
        "commands.O-PYTEST.limits.retained_combined_stdout_stderr_bytes.value",
        "WRONG_SCOPE_NOT_H_BUDGET",
    ),
    ("commands.O-PYTEST.limits.wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-PYTEST.timing.start_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-PYTEST.timing.deadline_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-PYTEST.timing.clock_domain", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-H6.cohort_id", "NO_CONSUMED_O_D_COHORT"),
    ("commands.O-H6.boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-H6.boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-H6.boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-H6.limits.memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H6.limits.pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H6.limits.cpu_usage_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H6.limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H6.limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    (
        "commands.O-H6.limits.retained_combined_stdout_stderr_bytes.value",
        "WRONG_SCOPE_NOT_H_BUDGET",
    ),
    ("commands.O-H6.limits.wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H6.timing.start_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-H6.timing.deadline_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-H6.timing.clock_domain", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-H7.cohort_id", "NO_CONSUMED_O_D_COHORT"),
    ("commands.O-H7.boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-H7.boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-H7.boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.O-H7.limits.memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H7.limits.pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H7.limits.cpu_usage_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H7.limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H7.limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    (
        "commands.O-H7.limits.retained_combined_stdout_stderr_bytes.value",
        "WRONG_SCOPE_NOT_H_BUDGET",
    ),
    ("commands.O-H7.limits.wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.O-H7.timing.start_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-H7.timing.deadline_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.O-H7.timing.clock_domain", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-PYTEST.cohort_id", "NO_CONSUMED_O_D_COHORT"),
    ("commands.D-PYTEST.boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-PYTEST.boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-PYTEST.boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-PYTEST.limits.memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-PYTEST.limits.pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-PYTEST.limits.cpu_usage_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-PYTEST.limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-PYTEST.limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    (
        "commands.D-PYTEST.limits.retained_combined_stdout_stderr_bytes.value",
        "WRONG_SCOPE_NOT_H_BUDGET",
    ),
    ("commands.D-PYTEST.limits.wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-PYTEST.timing.start_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-PYTEST.timing.deadline_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-PYTEST.timing.clock_domain", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-H6.cohort_id", "NO_CONSUMED_O_D_COHORT"),
    ("commands.D-H6.boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-H6.boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-H6.boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-H6.limits.memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-H6.limits.pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-H6.limits.cpu_usage_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-H6.limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-H6.limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    (
        "commands.D-H6.limits.retained_combined_stdout_stderr_bytes.value",
        "WRONG_SCOPE_NOT_H_BUDGET",
    ),
    ("commands.D-H6.limits.wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-H6.timing.start_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-H6.timing.deadline_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-H6.timing.clock_domain", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-COVERAGE.cohort_id", "NO_CONSUMED_O_D_COHORT"),
    ("commands.D-COVERAGE.boundary.identity_digest", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-COVERAGE.boundary.generation", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-COVERAGE.boundary.clock_domain", "NO_OWNED_H_BOUNDARY_IDENTITY"),
    ("commands.D-COVERAGE.limits.memory_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-COVERAGE.limits.pids_max.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-COVERAGE.limits.cpu_usage_budget_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-COVERAGE.limits.scratch_max_bytes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-COVERAGE.limits.scratch_max_inodes.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    (
        "commands.D-COVERAGE.limits.retained_combined_stdout_stderr_bytes.value",
        "WRONG_SCOPE_NOT_H_BUDGET",
    ),
    ("commands.D-COVERAGE.limits.wall_limit_ns.value", "WRONG_SCOPE_NOT_H_BUDGET"),
    ("commands.D-COVERAGE.timing.start_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-COVERAGE.timing.deadline_ns", "NO_H_MONOTONIC_TIMING"),
    ("commands.D-COVERAGE.timing.clock_domain", "NO_H_MONOTONIC_TIMING"),
    ("controls.subject_ro_enforced.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.network_denial_enforced.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.batch_boundary_placement_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.pre_payload_gate_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.bootstrap_outer_boundary_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.aggregate_memory_pids_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.aggregate_scratch_bytes_inodes_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.stream_output_deadline_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.FD_policy_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.owned_cleanup_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.provider_guard_compatible.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.toolchain_closure_reviewed.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.expected_inventory_separately_frozen.value", "NO_H_CONTROL_EXERCISE"),
    ("controls.consumed_origins_lineage_observed.value", "NO_H_CONTROL_EXERCISE"),
    ("policy_digest", "NO_H_BATCH_OR_POLICY_BINDING"),
    ("producer_errors", "NO_H_PRODUCER_STREAM"),
    ("producer_unavailable", "NO_H_PRODUCER_STREAM"),
)

MEANINGS = (
    "NON_AUTHORITY_DECLARATION",
    "CALLER_METADATA_ONLY",
    "HOST_PROCESS_CONTEXT_ONLY",
    "CGROUP_MEMBERSHIP_NOT_OWNERSHIP",
    "CGROUP_CONTROL_NOT_H_BUDGET",
    "W_OK_NOT_DELEGATION",
    "DECLARED_NOT_VERIFIED",
    "LEGACY_TOOL_CONTENT_ONLY",
    "LEGACY_TOOL_PIN_MISMATCH",
    "NATIVE_API_PRESENCE_ONLY",
    "SOURCE_VALUE_UNAVAILABLE",
    "SOURCE_STATIC_LIMITATION",
    "SOURCE_TEXT_REDACTED",
)

ERROR_CODES = (
    "REGISTERED_SNAPSHOT_CONTENT_MISMATCH",
    "SOURCE_DECLARATION_CONTRADICTION",
    "SOURCE_CONTEXT_MISMATCH",
    "SOURCE_TOOL_RELATION_INCONSISTENT",
    "BINDING_VALUE_MISMATCH",
)

UNAVAILABLE_CODES = (
    "BINDING_UNAVAILABLE",
    "BINDING_VALUE_UNAVAILABLE",
    "CALLER_CONTEXT_UNAVAILABLE",
)

DECLARATIONS = (
    ("/status", "READ_ONLY_OBSERVATION_NOT_QUALIFICATION"),
    ("/global_status", "BLOCKED"),
    ("/execution_verdict", "NOT_EVALUATED"),
    ("/atomic", False),
    ("/aggregate_resource_boundary_qualified", False),
    ("/H_executed", False),
    ("/content_identity_only", True),
    ("/permissions/application_authorized", False),
    ("/permissions/build_execution_allowed", False),
    ("/permissions/candidate_generation_allowed", False),
    ("/permissions/device_class_qualified", False),
    ("/permissions/owner_proposal_allowed", False),
    ("/permissions/policy_adopted", False),
    ("/permissions/promotion_authorized", False),
    ("/permissions/runtime_accepted", False),
    ("/permissions/runtime_qualified", False),
    ("/cgroup/atomic", False),
    ("/cgroup/write_delegation_verified", False),
    ("/execution_context/trust", "UNVERIFIED_CALLER_METADATA"),
    ("/limitations/0", "NO_EXECUTION_OR_WRITE_PROBE"),
    ("/limitations/1", "NO_PRIVATE_BUDGET_OR_DELEGATION_PROOF"),
    ("/limitations/2", "NO_ATOMICITY_OR_AUTHENTICITY"),
    ("/limitations/3", "NO_RUNTIME_QUALIFICATION"),
    (
        "/tools/~1opt~1codex~1runtimes~1codex-primary-runtime~1dependencies~1python~1bin~1python3.12/expected_sha256",
        "fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7",
    ),
    (
        "/tools/~1usr~1bin~1bwrap/expected_sha256",
        "573236e5328ac2ebb08f59ae3a9805b4f8d12bdef14be8af4450d5463294985f",
    ),
    (
        "/tools/~1usr~1bin~1setpriv/expected_sha256",
        "f7cedc63bbc1df7912b343a1240a77d16db7633563d69897ec8ad2a99c24024b",
    ),
)

REASON_SUBJECTS = (
    frozenset(("source", "binding"))
    | frozenset("binding." + n for n in BINDING_FIELDS)
    | frozenset("source:" + p for p, _ in SOURCE_LEAF_RULES)
)

_PATTERNS = (
    ("hex64", r"[0-9a-f]{64}"),
    ("hex40", r"[0-9a-f]{40}"),
    ("caphex", r"[0-9a-fA-F]{1,32}"),
    ("machine", r"[A-Za-z0-9_.-]{1,64}"),
    ("mode", r"[0-7]{4}"),
    ("decimal20", r"[0-9]{1,20}"),
    ("decimal8", r"[0-9]{1,8}"),
    ("repo", r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}"),
)
_CGROUP_STATUSES = (
    "UNAVAILABLE_MAPPING",
    "UNAVAILABLE_MEMBERSHIP",
    "UNAVAILABLE_COHORT_DRIFT",
    "MEMBERSHIP_OBSERVED_NOT_DELEGATION",
)


def need(condition: bool) -> None:
    if not condition:
        raise ValueError(ERROR)


def check_leaf(value: Any, tag: str) -> None:
    if tag.startswith("optional:"):
        if value is None:
            return
        tag = tag[len("optional:") :]
    if tag == "bool":
        need(type(value) is bool)
    elif tag in ("uint", "security1", "security2"):
        need(type(value) is int and 0 <= value <= UINT64_MAX)
        if tag != "uint":
            need(value <= (1 if tag == "security1" else 2))
    else:
        need(type(value) is str)
        if tag in dict(_PATTERNS):
            need(re.fullmatch(dict(_PATTERNS)[tag], value) is not None)
        elif tag == "ascii128":
            need(1 <= len(value) <= 128 and value.isascii())
        elif tag == "schema":
            need(value == "actions-runner-preflight-v1")
        elif tag == "linux":
            need(value == "Linux")
        elif tag == "cgroup_status":
            need(value in _CGROUP_STATUSES)
        else:
            need(tag.startswith("control:") and len(value) <= 1024 and value.isascii())
            name = tag[len("control:") :]
            if name == "cpu.max":
                need(re.fullmatch(r"(?:max|[1-9][0-9]*) [1-9][0-9]*", value) is not None)
            elif name in ("memory.max", "pids.max", "cgroup.max.depth", "cgroup.max.descendants"):
                need(re.fullmatch(r"(?:max|0|[1-9][0-9]*)", value) is not None)
            elif name == "cgroup.type":
                need(value in ("domain", "domain threaded", "domain invalid", "threaded"))
            else:
                need(name in ("cgroup.controllers", "cgroup.subtree_control"))
                words = value.split(" ")
                need(
                    value == ""
                    or (
                        len(words) == len(set(words))
                        and set(words)
                        <= {
                            "cpuset",
                            "cpu",
                            "io",
                            "memory",
                            "hugetlb",
                            "pids",
                            "rdma",
                            "misc",
                            "dmem",
                        }
                    )
                )


def default_meaning(pointer: str) -> str:
    if pointer.startswith("/tools/"):
        return "LEGACY_TOOL_CONTENT_ONLY"
    if pointer.startswith("/execution_context/"):
        return "CALLER_METADATA_ONLY"
    if pointer.startswith("/native_apis/"):
        return "NATIVE_API_PRESENCE_ONLY"
    if pointer.startswith(("/host/", "/security/")):
        return "HOST_PROCESS_CONTEXT_ONLY"
    if pointer.endswith("/effective_write_access"):
        return "W_OK_NOT_DELEGATION"
    if pointer in ("/cgroup/atomic", "/cgroup/write_delegation_verified"):
        return "DECLARED_NOT_VERIFIED"
    if pointer.startswith("/cgroup/controls/"):
        return "CGROUP_CONTROL_NOT_H_BUDGET"
    if pointer.startswith("/cgroup/"):
        return "CGROUP_MEMBERSHIP_NOT_OWNERSHIP"
    if pointer.startswith("/limitations/"):
        return "SOURCE_STATIC_LIMITATION"
    return "NON_AUTHORITY_DECLARATION"


class _DiagnosticClaim:
    __slots__ = ()

    @property
    def mapping_status(self) -> str:
        return "DIAGNOSTIC_ONLY"

    @property
    def profile_record(self) -> None:
        return None

    @property
    def H_executed(self) -> bool:
        return False

    @property
    def integrated_admission(self) -> bool:
        return False

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
        for name, value in validate_dto(self, type(self)).items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class PreflightRunBinding(_DiagnosticClaim):
    repository: str | None
    run_id: int | None
    attempt: int | None
    job_id: int | None
    source_revision: str | None
    workflow_sha256: str | None
    collector_sha256: str | None
    observation_sha256: str | None


@dataclass(frozen=True, slots=True)
class SourceDiagnostic(_DiagnosticClaim):
    source_pointer: str
    value: bool | int | str | None
    meaning: str

    @property
    def availability(self) -> str:
        return "UNAVAILABLE" if self.value is None else "AVAILABLE"


@dataclass(frozen=True, slots=True)
class TargetGap(_DiagnosticClaim):
    target_path: str
    reason: str


@dataclass(frozen=True, slots=True)
class MappingReason(_DiagnosticClaim):
    code: str
    subject: str


@dataclass(frozen=True, slots=True)
class PreflightMappingDecision(_DiagnosticClaim):
    source_profile_id: str
    source_sha256: str
    diagnostics: tuple[SourceDiagnostic, ...]
    target_gaps: tuple[TargetGap, ...]
    errors: tuple[MappingReason, ...]
    unavailable: tuple[MappingReason, ...]

    @property
    def source_consistency(self) -> str:
        if self.errors:
            return "REGISTERED_SNAPSHOT_MISMATCH"
        return "UNAVAILABLE_BINDING" if self.unavailable else "REGISTERED_SNAPSHOT_MATCH"

    @property
    def evidence_kind(self) -> str:
        return dict(EVIDENCE_KINDS)[self.source_profile_id]


_TYPES = (PreflightRunBinding, SourceDiagnostic, TargetGap, MappingReason, PreflightMappingDecision)


def _member(value: Any, choices: Any) -> None:
    need(type(value) is str and value in choices)


def _owned(values: Any, cls: type, key: str, inventory: Any) -> tuple[Any, ...]:
    need(type(values) is tuple)
    for item in values:
        validate_dto(item, cls)
    keys = tuple(getattr(item, key) for item in values)
    need(len(keys) == len(set(keys)) and set(keys) == set(inventory))
    return tuple(sorted(values, key=lambda item: getattr(item, key)))


def _reasons(values: Any, codes: tuple[str, ...]) -> tuple[MappingReason, ...]:
    need(type(values) is tuple)
    for item in values:
        validate_dto(item, MappingReason)
        need(item.code in codes)
    return tuple(sorted(set(values), key=lambda item: (item.code, item.subject)))


def validate_dto(value: Any, expected: type) -> dict[str, Any]:
    need(expected in _TYPES and type(value) is expected)
    try:
        data = {field.name: getattr(value, field.name) for field in fields(expected)}
    except AttributeError:
        raise ValueError(ERROR) from None
    if expected is PreflightRunBinding:
        for name, item in data.items():
            tag = (
                "repo"
                if name == "repository"
                else "uint"
                if name in ("run_id", "attempt", "job_id")
                else "hex40"
                if name == "source_revision"
                else "hex64"
            )
            check_leaf(item, "optional:" + tag)
    elif expected is SourceDiagnostic:
        pointer, item, meaning = data["source_pointer"], data["value"], data["meaning"]
        rules = {p: (tag, nullable) for p, tag, nullable in DIAGNOSTIC_RULES}
        _member(pointer, rules)
        _member(meaning, MEANINGS)
        tag, nullable = rules[pointer]
        if type(item) is str and item == REDACTED:
            need(pointer in dict(STRING_VALUES) and meaning == "SOURCE_TEXT_REDACTED")
        elif item is None:
            need(nullable and meaning == "SOURCE_VALUE_UNAVAILABLE")
        else:
            check_leaf(item, tag)
            if type(item) is str:
                need(item in dict(STRING_VALUES).get(pointer, ()))
            allowed = {default_meaning(pointer)}
            if pointer.startswith("/tools/") and pointer.endswith("/pin_matches") and item is False:
                allowed.add("LEGACY_TOOL_PIN_MISMATCH")
            need(meaning in allowed)
    elif expected is TargetGap:
        _member(data["target_path"], dict(GAP_PAIRS))
        _member(data["reason"], (dict(GAP_PAIRS)[data["target_path"]],))
    elif expected is MappingReason:
        _member(data["code"], ERROR_CODES + UNAVAILABLE_CODES)
        _member(data["subject"], REASON_SUBJECTS)
    else:
        _member(data["source_profile_id"], dict(PROFILES))
        check_leaf(data["source_sha256"], "hex64")
        data["diagnostics"] = _owned(
            data["diagnostics"],
            SourceDiagnostic,
            "source_pointer",
            (p for p, _, _ in DIAGNOSTIC_RULES),
        )
        data["target_gaps"] = _owned(data["target_gaps"], TargetGap, "target_path", dict(GAP_PAIRS))
        data["errors"] = _reasons(data["errors"], ERROR_CODES)
        data["unavailable"] = _reasons(data["unavailable"], UNAVAILABLE_CODES)
    return data
