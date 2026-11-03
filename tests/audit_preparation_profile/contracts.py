"""Closed immutable supplied claims. Never an observation producer or authority."""

from dataclasses import dataclass
from typing import Any

PROFILE = "H_PREPARATION_PROFILE_V1"
WIRE_SCHEMA = "preparation-profile-claims-v1"
UINT64_MAX = 2**64 - 1
PERMISSIONS = tuple(
    (name, False)
    for name in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    )
)
ARTIFACTS = (
    "executor_content",
    "bootstrap_content",
    "provider_implementation",
    "syscall_policy",
    "collection_policy",
    "toolchain_inventory",
    "dependency_inventory",
    "private_snapshot_manifest",
    "full_expected_node_inventory",
    "materialized_command_manifest",
    "scope_record",
)
BATCH_LIMITS = (
    ("batch_memory_max_bytes", "byte"),
    ("batch_pids_max", "process_or_thread_count"),
    ("cpu_bandwidth_quota_us", "microsecond"),
    ("cpu_bandwidth_period_us", "microsecond"),
    ("cpu_usage_accounting_budget_ns", "nanosecond"),
    ("cpu_accounting_latency_bound_ns", "nanosecond"),
    ("scratch_max_bytes", "byte"),
    ("scratch_max_inodes", "inode_count"),
    ("retained_combined_stdout_stderr_bytes", "byte"),
    ("batch_wall_limit_ns", "nanosecond_duration"),
    ("command_wall_limit_ns", "nanosecond_duration"),
    ("stop_and_cleanup_limit_ns", "nanosecond_duration"),
)
COMMAND_LIMITS = (
    ("memory_max_bytes", "byte", "batch_memory_max_bytes"),
    ("pids_max", "process_or_thread_count", "batch_pids_max"),
    ("cpu_usage_budget_ns", "nanosecond", "cpu_usage_accounting_budget_ns"),
    ("scratch_max_bytes", "byte", "scratch_max_bytes"),
    ("scratch_max_inodes", "inode_count", "scratch_max_inodes"),
    ("retained_combined_stdout_stderr_bytes", "byte", "retained_combined_stdout_stderr_bytes"),
    ("wall_limit_ns", "nanosecond_duration", "command_wall_limit_ns"),
)
CONTROLS = (
    "subject_ro_enforced",
    "network_denial_enforced",
    "batch_boundary_placement_observed",
    "pre_payload_gate_observed",
    "bootstrap_outer_boundary_observed",
    "aggregate_memory_pids_observed",
    "aggregate_scratch_bytes_inodes_observed",
    "stream_output_deadline_observed",
    "FD_policy_observed",
    "owned_cleanup_observed",
    "provider_guard_compatible",
    "toolchain_closure_reviewed",
    "expected_inventory_separately_frozen",
    "consumed_origins_lineage_observed",
)
COMMANDS = (
    ("O-PYTEST", "O"),
    ("O-H6", "O"),
    ("O-H7", "O"),
    ("D-PYTEST", "D"),
    ("D-H6", "D"),
    ("D-COVERAGE", "D"),
)
COHORTS = (
    ("O", "5357d5d555d49b258affa237d83b8491b8a8c6ce", "18e63fc8e03077684cd14c1ed33e2c7a8ceb89a5"),
    ("D", "75e00280a09323ad4a3fc82453383f220c92f6c6", "d0dd929f3bb46d1a33d8bb00f29e7638b48d9483"),
)
ERROR_CODES = (
    "PROFILE_ID_MISMATCH",
    "PRODUCER_FAILURE",
    "TABLE_INVENTORY_MISMATCH",
    "COHORT_PIN_MISMATCH",
    "COMMAND_CONTEXT_MISMATCH",
    "LIMIT_NONPOSITIVE",
    "LIMIT_UNBOUNDED",
    "LIMIT_SCOPE_INCONSISTENT",
    "CONTROL_CLAIM_FALSE",
    "BOUNDARY_REUSE",
    "CLOCK_DOMAIN_MISMATCH",
    "TIME_ORDER_INVALID",
    "TIME_OVERFLOW",
    "DEADLINE_MISMATCH",
    "POLICY_RECORD_MISMATCH",
    "POLICY_DIGEST_MISMATCH",
)
UNAVAILABLE_CODES = (
    "POLICY_UNAVAILABLE",
    "TABLE_UNAVAILABLE",
    "VALUE_UNAVAILABLE",
    "PRODUCER_UNAVAILABLE",
)


class _Claim:
    __slots__ = ()

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

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

    def __post_init__(self) -> None:
        for name, value in normalized_fields(self, type(self)).items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class ArtifactPin(_Claim):
    role: str
    sha256: str | None


@dataclass(frozen=True, slots=True)
class LimitValue(_Claim):
    name: str
    unit: str
    value: int | str | None


@dataclass(frozen=True, slots=True)
class ControlClaim(_Claim):
    name: str
    value: bool | None


@dataclass(frozen=True, slots=True)
class CohortPin(_Claim):
    cohort_id: str
    revision: str | None
    tree: str | None


@dataclass(frozen=True, slots=True)
class BoundaryRef(_Claim):
    identity_digest: str | None
    generation: int | None
    clock_domain: str | None


@dataclass(frozen=True, slots=True)
class TimingClaim(_Claim):
    start_ns: int | None
    deadline_ns: int | None
    clock_domain: str | None


@dataclass(frozen=True, slots=True)
class CommandProfile(_Claim):
    command_id: str
    cohort_id: str
    boundary: BoundaryRef | None
    limits: tuple[LimitValue, ...] | None
    timing: TimingClaim | None


@dataclass(frozen=True, slots=True)
class PreparationProfilePolicy(_Claim):
    profile_id: str
    run_id: str | None
    artifacts: tuple[ArtifactPin, ...] | None
    cohorts: tuple[CohortPin, ...] | None
    batch_boundary: BoundaryRef | None
    batch_limits: tuple[LimitValue, ...] | None
    commands: tuple[CommandProfile, ...] | None
    controls: tuple[ControlClaim, ...] | None


@dataclass(frozen=True, slots=True)
class PreparationProfileRecord(_Claim):
    profile_id: str
    run_id: str | None
    policy_digest: str | None
    artifacts: tuple[ArtifactPin, ...] | None
    cohorts: tuple[CohortPin, ...] | None
    batch_boundary: BoundaryRef | None
    batch_limits: tuple[LimitValue, ...] | None
    commands: tuple[CommandProfile, ...] | None
    controls: tuple[ControlClaim, ...] | None
    producer_errors: tuple[str, ...]
    producer_unavailable: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProfileReason(_Claim):
    code: str
    subject: str


@dataclass(frozen=True, slots=True)
class PreparationProfileDecision(_Claim):
    errors: tuple[ProfileReason, ...]
    unavailable: tuple[ProfileReason, ...]

    @property
    def consistency(self) -> str:
        if self.errors:
            return "REJECTED"
        return "UNAVAILABLE" if self.unavailable else "STRUCTURAL_PROFILE_MATCH"


def need(condition: bool) -> None:
    if not condition:
        raise ValueError("malformed preparation-profile claim")


def _subjects() -> frozenset[str]:
    subjects = {"policy", "record.producer", "record.policy_digest"}
    boundary = ("identity_digest", "generation", "clock_domain")
    for side in ("record", "policy"):
        root = side + "."
        subjects.update(
            root + f
            for f in (
                "profile_id",
                "run_id",
                "artifacts",
                "cohorts",
                "batch_boundary",
                "batch_limits",
                "commands",
                "controls",
            )
        )
        subjects.update(root + "artifacts." + k + ".sha256" for k in ARTIFACTS)
        subjects.update(
            root + "cohorts." + k + "." + f for k, _, _ in COHORTS for f in ("revision", "tree")
        )
        subjects.update(root + "batch_boundary." + f for f in boundary)
        subjects.update(root + "batch_limits." + k + ".value" for k, _ in BATCH_LIMITS)
        subjects.update(root + "controls." + k + ".value" for k in CONTROLS)
        for command, _ in COMMANDS:
            prefix = root + "commands." + command
            subjects.update(
                (
                    prefix,
                    prefix + ".cohort_id",
                    prefix + ".boundary",
                    prefix + ".limits",
                    prefix + ".timing",
                )
            )
            subjects.update(prefix + ".boundary." + f for f in boundary)
            subjects.update(prefix + ".limits." + k + ".value" for k, _, _ in COMMAND_LIMITS)
            subjects.update(
                prefix + ".timing." + f for f in ("start_ns", "deadline_ns", "clock_domain")
            )
    return frozenset(subjects)


SUBJECTS = _subjects()
# Descriptors encode only the closed value graph, never user-selected constructors.
_HEX64 = ("nullable", ("hex", 64))
_HEX40 = ("nullable", ("hex", 40))
_UINT = ("nullable", ("uint",))
_TEXT = ("nullable", ("text",))
_COHORT_ID = ("id", tuple(k for k, _, _ in COHORTS))
_COMMON = (
    ("profile_id", ("text",)),
    ("run_id", ("nullable", ("hex", 32))),
    ("artifacts", ("table", ArtifactPin, "role", ARTIFACTS)),
    ("cohorts", ("table", CohortPin, "cohort_id", tuple(k for k, _, _ in COHORTS))),
    ("batch_boundary", ("nullable", ("dto", BoundaryRef))),
    ("batch_limits", ("table", LimitValue, "name", tuple(k for k, _ in BATCH_LIMITS))),
    ("commands", ("table", CommandProfile, "command_id", tuple(k for k, _ in COMMANDS))),
    ("controls", ("table", ControlClaim, "name", CONTROLS)),
)
SPECS: dict[type, tuple[tuple[str, tuple[Any, ...]], ...]] = {
    ArtifactPin: (("role", ("id", ARTIFACTS)), ("sha256", _HEX64)),
    LimitValue: (
        ("name", ("id", tuple(dict(BATCH_LIMITS + tuple((k, u) for k, u, _ in COMMAND_LIMITS))))),
        ("unit", ("unit",)),
        ("value", ("limit",)),
    ),
    ControlClaim: (("name", ("id", CONTROLS)), ("value", ("nullable", ("bool",)))),
    CohortPin: (("cohort_id", _COHORT_ID), ("revision", _HEX40), ("tree", _HEX40)),
    BoundaryRef: (("identity_digest", _HEX64), ("generation", _UINT), ("clock_domain", _TEXT)),
    TimingClaim: (("start_ns", _UINT), ("deadline_ns", _UINT), ("clock_domain", _TEXT)),
    CommandProfile: (
        ("command_id", ("id", tuple(k for k, _ in COMMANDS))),
        ("cohort_id", _COHORT_ID),
        ("boundary", ("nullable", ("dto", BoundaryRef))),
        ("limits", ("table", LimitValue, "name", tuple(k for k, _, _ in COMMAND_LIMITS))),
        ("timing", ("nullable", ("dto", TimingClaim))),
    ),
    PreparationProfilePolicy: _COMMON,
    PreparationProfileRecord: _COMMON[:2]
    + (("policy_digest", _HEX64),)
    + _COMMON[2:]
    + (
        ("producer_errors", ("codes", ("PRODUCER_REPORTED_FAILURE",))),
        ("producer_unavailable", ("codes", ("PRODUCER_REPORTED_UNAVAILABLE",))),
    ),
    ProfileReason: (
        ("code", ("id", ERROR_CODES + UNAVAILABLE_CODES)),
        ("subject", ("id", SUBJECTS)),
    ),
    PreparationProfileDecision: (
        ("errors", ("reasons", ERROR_CODES)),
        ("unavailable", ("reasons", UNAVAILABLE_CODES)),
    ),
}


def normalized_fields(value: Any, expected: type) -> dict[str, Any]:
    need(expected in SPECS and type(value) is expected)
    try:
        result = {name: _normalize(getattr(value, name), spec) for name, spec in SPECS[expected]}
    except AttributeError as exc:
        raise ValueError("incomplete preparation-profile object") from exc
    if expected is LimitValue:
        units = dict(BATCH_LIMITS + tuple((k, u) for k, u, _ in COMMAND_LIMITS))
        need(result["unit"] == units[result["name"]])
    return result


def _normalize(value: Any, spec: tuple[Any, ...]) -> Any:
    tag = spec[0]
    if tag == "nullable":
        return None if value is None else _normalize(value, spec[1])
    if tag == "dto":
        normalized_fields(value, spec[1])
    elif tag == "id":
        need(type(value) is str and value in spec[1])
    elif tag == "hex":
        need(
            type(value) is str
            and len(value) == spec[1]
            and all(c in "0123456789abcdef" for c in value)
        )
    elif tag == "uint":
        need(type(value) is int and 0 <= value <= UINT64_MAX)
    elif tag == "text":
        need(
            type(value) is str
            and 1 <= len(value) <= 128
            and all(
                c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
                for c in value
            )
        )
    elif tag == "bool":
        need(type(value) is bool)
    elif tag == "unit":
        need(type(value) is str)
    elif tag == "limit":
        if value is not None and not (type(value) is str and value == "UNBOUNDED"):
            _normalize(value, ("uint",))
    elif tag == "table":
        if value is None:
            return None
        need(type(value) is tuple)
        for item in value:
            normalized_fields(item, spec[1])
        keys = tuple(getattr(item, spec[2]) for item in value)
        need(len(set(keys)) == len(keys) and set(keys) <= set(spec[3]))
        return tuple(sorted(value, key=lambda item: spec[3].index(getattr(item, spec[2]))))
    elif tag == "codes":
        need(type(value) is tuple)
        for item in value:
            _normalize(item, ("id", spec[1]))
        need(len(set(value)) == len(value))
        return tuple(sorted(value))
    else:  # Closed decision-reason tuple; not a generic user-defined descriptor.
        need(tag == "reasons" and type(value) is tuple)
        for item in value:
            normalized_fields(item, ProfileReason)
            need(item.code in spec[1])
        return tuple(sorted(set(value), key=lambda item: (item.code, item.subject)))
    return value
