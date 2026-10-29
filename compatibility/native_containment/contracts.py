"""Strict immutable synthetic cases. Digests identify content, not authenticity."""

import json
import re
from dataclasses import asdict, dataclass, fields
from enum import StrEnum
from hashlib import sha256
from typing import Any


class OperationClass(StrEnum):
    OPEN = "OPEN"
    CONTROL = "CONTROL"
    IOCTL = "IOCTL"
    MMAP = "MMAP"
    NETWORK = "NETWORK"
    FD_PASS = "FD_PASS"
    PRIVILEGE_OR_POLICY = "PRIVILEGE_OR_POLICY"
    ASYNC_IO = "ASYNC_IO"
    OTHER = "OTHER"


class ResolvedKind(StrEnum):
    PRIVATE_NAMESPACE_ABSENCE = "PRIVATE_NAMESPACE_ABSENCE"
    POLICY_DENIED_NO_OBJECT = "POLICY_DENIED_NO_OBJECT"
    PROHIBITED_HARDWARE = "PROHIBITED_HARDWARE"
    EXACT_PSEUDO = "EXACT_PSEUDO"
    REGULAR_BUILD_FILE = "REGULAR_BUILD_FILE"
    UNKNOWN = "UNKNOWN"


def _uint(value: object) -> None:
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError("expected UInt64 (not bool)")


def _text(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("expected nonempty string")


def _optional_bool(value: object) -> None:
    if value is not None and type(value) is not bool:
        raise ValueError("expected bool or null")


def _digest(value: object) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("expected lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class ModeledProofs:
    """Caller-authored test claims only, never actual enforcement evidence."""

    input_closure_complete: bool | None
    enforcement_observed_active: bool | None
    source_loader_immutable: bool | None
    process_stage_bound: bool | None
    resource_resolution_bound: bool | None
    capture_guard_bound: bool | None
    trace_complete: bool | None
    observer_intact: bool | None

    def __post_init__(self) -> None:
        for field in fields(self):
            _optional_bool(getattr(self, field.name))


@dataclass(frozen=True, slots=True)
class SyntheticSecurityEvent:
    sequence: int
    mono_time_ns: int
    actor_id: str
    process_generation: int
    exec_generation: int
    clock_domain: str
    operation_class: OperationClass
    requested_endpoint: str | None
    flags: tuple[str, ...] | None
    resolved_kind: ResolvedKind | None
    resolution_bound: bool | None
    result_known: bool | None
    errno_name: str | None
    fd_created_or_imported: bool | None
    effect_observed: bool | None

    def __post_init__(self) -> None:
        for value in (
            self.sequence,
            self.mono_time_ns,
            self.process_generation,
            self.exec_generation,
        ):
            _uint(value)
        _text(self.actor_id)
        _text(self.clock_domain)
        for label in (self.requested_endpoint, self.errno_name):
            if label is not None:
                _text(label)
        for status in (
            self.resolution_bound,
            self.result_known,
            self.fd_created_or_imported,
            self.effect_observed,
        ):
            _optional_bool(status)
        if not isinstance(self.operation_class, str):
            raise ValueError("expected operation enum")
        object.__setattr__(self, "operation_class", OperationClass(self.operation_class))
        if self.resolved_kind is not None:
            if not isinstance(self.resolved_kind, str):
                raise ValueError("expected resolution enum or null")
            object.__setattr__(self, "resolved_kind", ResolvedKind(self.resolved_kind))
        if self.flags is not None:
            if type(self.flags) not in (tuple, list):
                raise ValueError("flags must be an array or null")
            for flag in self.flags:
                _text(flag)
            if len(set(self.flags)) != len(self.flags):
                raise ValueError("duplicate flags")
            object.__setattr__(self, "flags", tuple(sorted(self.flags)))


@dataclass(frozen=True, slots=True)
class SyntheticContainmentCase:
    schema_version: str
    evidence_kind: str
    source_cohort_digest: str
    actor_id: str
    process_generation: int
    exec_generation: int
    clock_domain: str
    modeled_proofs: ModeledProofs
    cpu_backend: str | None
    successful_prohibited_handles: int | None
    successful_prohibited_effects: int | None
    events: tuple[SyntheticSecurityEvent, ...]
    candidate_generation_allowed: bool
    application_authorized: bool
    runtime_accepted: bool
    owner_proposal_allowed: bool

    def __post_init__(self) -> None:
        if self.schema_version != "synthetic-native-containment-case-v1":
            raise ValueError("unsupported synthetic schema")
        if self.evidence_kind != "SYNTHETIC":
            raise ValueError("only SYNTHETIC cases; no OBSERVED trust binding exists")
        _digest(self.source_cohort_digest)
        _text(self.actor_id)
        _uint(self.process_generation)
        _uint(self.exec_generation)
        if self.clock_domain != "synthetic-monotonic-ns-v1":
            raise ValueError("unsupported synthetic clock")
        if type(self.modeled_proofs) is not ModeledProofs:
            raise ValueError("expected immutable modeled proofs")
        self.modeled_proofs.__post_init__()
        if self.cpu_backend is not None and self.cpu_backend != "CPU:LLVM":
            raise ValueError("unsupported backend label")
        for value in (self.successful_prohibited_handles, self.successful_prohibited_effects):
            if value is not None:
                _uint(value)
        if type(self.events) not in (tuple, list) or not self.events:
            raise ValueError("nonempty event array required")
        for event in self.events:
            if type(event) is not SyntheticSecurityEvent:
                raise ValueError("expected immutable event")
            event.__post_init__()
        object.__setattr__(self, "events", tuple(self.events))
        for value in (
            self.candidate_generation_allowed,
            self.application_authorized,
            self.runtime_accepted,
            self.owner_proposal_allowed,
        ):
            if value is not False:
                raise ValueError("real permissions are fixed false")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> Any:
    raise ValueError("nonfinite JSON value: " + value)


def _exact(value: Any, cls: type[Any]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {field.name for field in fields(cls)}:
        raise ValueError("missing/unknown keys or wrong object shape")
    return value


def parse_synthetic_case(raw: str) -> SyntheticContainmentCase:
    """Parse data only. No observed verifier, policy loader or external input access."""
    if type(raw) is not str:
        raise ValueError("expected JSON string")
    data = _exact(
        json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite),
        SyntheticContainmentCase,
    )
    data["modeled_proofs"] = ModeledProofs(**_exact(data["modeled_proofs"], ModeledProofs))
    if type(data["events"]) is not list:
        raise ValueError("expected event array")
    data["events"] = tuple(
        SyntheticSecurityEvent(**_exact(event, SyntheticSecurityEvent)) for event in data["events"]
    )
    return SyntheticContainmentCase(**data)


def canonical_digest(case: SyntheticContainmentCase) -> str:
    """Case content only; policy mode is external, and no authority is conveyed."""
    if type(case) is not SyntheticContainmentCase:
        raise ValueError("expected synthetic case")
    case.__post_init__()
    encoded = json.dumps(
        asdict(case), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return sha256(encoded.encode("utf-8")).hexdigest()
