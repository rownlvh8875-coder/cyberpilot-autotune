"""Immutable descriptions; a proven description is not a safe setting or policy."""

import re
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import PurePosixPath

from cyberpilot_autotune.contracts.validation import (
    ValidationError,
    count,
    finite,
    strings,
    text,
    typed_tuple,
)

from .canonical import canonical_digest


class Confidence(Enum):
    PROVEN = "PROVEN"
    CONDITIONAL = "CONDITIONAL"
    HEURISTIC = "HEURISTIC"
    UNRESOLVED = "UNRESOLVED"
    REJECTED = "REJECTED"


class Classification(Enum):
    TUNING_CANDIDATE = "TUNING_CANDIDATE"
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"
    MODE_SELECTOR = "MODE_SELECTOR"
    COUPLED_PRESERVED_STATE = "COUPLED_PRESERVED_STATE"
    USER_PREFERENCE = "USER_PREFERENCE"
    PLATFORM_SELECTOR = "PLATFORM_SELECTOR"
    SAFETY_SENSITIVE = "SAFETY_SENSITIVE"
    NOT_SUITABLE = "NOT_SUITABLE"
    UNRESOLVED = "UNRESOLVED"


class StorageType(Enum):
    INTEGER_TEXT = "INTEGER_TEXT"
    MESSAGE_FLOAT32 = "MESSAGE_FLOAT32"


class OwnerRole(Enum):
    UI_SETTINGS_WRITER = "UI_SETTINGS_WRITER"
    TORQUED_PRODUCER = "TORQUED_PRODUCER"
    CONTROLSD_CONSUMER = "CONTROLSD_CONSUMER"
    CUSTOM_TORQUE_OVERRIDE = "CUSTOM_TORQUE_OVERRIDE"
    NN_ALTERNATIVE = "NN_ALTERNATIVE"
    VEHICLE_MODEL_CONSUMER = "VEHICLE_MODEL_CONSUMER"


class OwnershipStatus(Enum):
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"
    CONFLICT_UNRESOLVED = "OWNERSHIP_CONFLICT_UNRESOLVED"


def exact_hash(value: str, length: int) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value) is None:
        raise ValidationError("exact lowercase source identity required")


def _version(value: int) -> None:
    if type(value) is not int or value != 1:
        raise ValidationError("unsupported knowledge schema version")


def _texts(value: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(strings(value))))


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceKnowledgeDescriptor:
    schema_version: int
    claim_id: str
    parameter_ids: tuple[str, ...]
    repository: str
    exact_revision: str
    path: str
    symbol: str
    range_start: int
    range_end: int
    git_blob_sha: str
    source_range_sha256: str
    semantic_claim: str
    conditions: tuple[str, ...]
    confidence: Confidence
    schema_revision: str
    supersedes_claim_id: str | None

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for value in (
            self.claim_id,
            self.repository,
            self.path,
            self.symbol,
            self.semantic_claim,
            self.schema_revision,
        ):
            text(value, "source claim text")
        path = PurePosixPath(self.path)
        if path.is_absolute() or ".." in path.parts or "\\" in self.path or ":" in self.path:
            raise ValidationError("repository-relative source path required")
        for value, size in (
            (self.exact_revision, 40),
            (self.git_blob_sha, 40),
            (self.source_range_sha256, 64),
        ):
            exact_hash(value, size)
        count(self.range_start, "range start")
        count(self.range_end, "range end")
        if not 1 <= self.range_start <= self.range_end:
            raise ValidationError("invalid source range")
        if type(self.confidence) is not Confidence:
            raise ValidationError("typed source confidence required")
        for name in ("conditions", "parameter_ids"):
            copied = _texts(getattr(self, name))
            if not copied:
                raise ValidationError("explicit source conditions and related parameters required")
            object.__setattr__(self, name, copied)
        if self.supersedes_claim_id is not None:
            text(self.supersedes_claim_id, "superseded claim")
            if self.supersedes_claim_id == self.claim_id:
                raise ValidationError("claim cannot supersede itself")

    @property
    def digest(self) -> str:
        return canonical_digest(self)

    def matches_source(
        self, *, exact_revision: str, git_blob_sha: str, source_range_sha256: str
    ) -> bool:
        """Compare explicit identities only; no IO, signature or authenticity check."""
        return (
            self.exact_revision == exact_revision
            and self.git_blob_sha == git_blob_sha
            and self.source_range_sha256 == source_range_sha256
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ParameterDescriptor:
    schema_version: int
    parameter_id: str
    storage_key: str | None
    display_name: str
    domain: str
    family: str
    classification: Classification
    semantic_description: str
    storage_type: StorageType
    storage_unit: str
    storage_scale: float | None
    canonical_unit: str | None
    consumer_unit: str | None
    consumer_transform_description: str
    ui_unit_description: str | None
    consumer_claim_ids: tuple[str, ...]
    mode_conditions: tuple[str, ...] | None
    ui_default: int | float | None
    ui_catalog_min: int | float | None
    ui_catalog_max: int | float | None
    storage_registry_default: int | float | None
    default_sources: tuple[str, ...]
    consumer_value_source: str
    runtime_field: str
    descriptive_owner: tuple[OwnerRole, ...]
    ownership_status: OwnershipStatus
    source_revision: str
    evidence_status: Confidence
    evidence_gaps: tuple[str, ...]

    def __post_init__(self) -> None:
        _version(self.schema_version)
        for name in (
            "parameter_id",
            "display_name",
            "domain",
            "family",
            "semantic_description",
            "storage_unit",
            "consumer_transform_description",
            "consumer_value_source",
            "runtime_field",
        ):
            text(getattr(self, name), name)
        if self.domain != "steering":
            raise ValidationError("steering knowledge only")
        for value in (
            self.storage_key,
            self.canonical_unit,
            self.consumer_unit,
            self.ui_unit_description,
        ):
            if value is not None:
                text(value, "optional descriptive text")
        for enum_value, kind in (
            (self.classification, Classification),
            (self.storage_type, StorageType),
            (self.evidence_status, Confidence),
            (self.ownership_status, OwnershipStatus),
        ):
            if type(enum_value) is not kind:
                raise ValidationError("typed descriptive classification required")
        exact_hash(self.source_revision, 40)
        for name in (
            "storage_scale",
            "ui_default",
            "ui_catalog_min",
            "ui_catalog_max",
            "storage_registry_default",
        ):
            value = getattr(self, name)
            if value is not None:
                finite(value, name)
        if self.storage_scale is not None and self.storage_scale <= 0:
            raise ValidationError("known storage scale must be positive")
        if self.ui_catalog_min is not None and self.ui_catalog_max is not None:
            if self.ui_catalog_min > self.ui_catalog_max:
                raise ValidationError("inverted descriptive UI range")
        for name in ("consumer_claim_ids", "default_sources", "evidence_gaps"):
            object.__setattr__(self, name, _texts(getattr(self, name)))
        if not self.consumer_claim_ids:
            raise ValidationError("explicit consumer source claims required")
        if self.mode_conditions is not None:
            modes = _texts(self.mode_conditions)
            if not modes:
                raise ValidationError("unknown modes must remain unavailable")
            object.__setattr__(self, "mode_conditions", modes)
        roles = typed_tuple(self.descriptive_owner, OwnerRole)
        if not roles:
            raise ValidationError("explicit descriptive roles required")
        object.__setattr__(
            self, "descriptive_owner", tuple(sorted(set(roles), key=lambda x: x.value))
        )
        if self.evidence_status is Confidence.PROVEN:
            if any(
                value is None
                for value in (
                    self.storage_scale,
                    self.canonical_unit,
                    self.consumer_unit,
                    self.mode_conditions,
                )
            ):
                raise ValidationError("unresolved unit/scale/mode cannot be PROVEN")
        elif not self.evidence_gaps:
            raise ValidationError("non-proven descriptions require explicit evidence gaps")

    @property
    def digest(self) -> str:
        return canonical_digest(self)


STEERING_IDS = frozenset(
    (
        "LateralTorqueAccelFactor",
        "LateralTorqueFriction",
        "LateralTorqueKpV",
        "LateralTorqueKiV",
        "LateralTorqueKf",
        "LateralTorqueCustom",
        "SteerRatioRate",
        "SteerActuatorDelay",
        "liveTorqueParameters.latAccelOffset",
    )
)


@dataclass(frozen=True, slots=True)
class KnowledgeRegistry:
    source_revision: str
    parameters: tuple[ParameterDescriptor, ...]
    claims: tuple[SourceKnowledgeDescriptor, ...]

    def __post_init__(self) -> None:
        exact_hash(self.source_revision, 40)
        ps = tuple(replace(p) for p in typed_tuple(self.parameters, ParameterDescriptor))
        cs = tuple(replace(c) for c in typed_tuple(self.claims, SourceKnowledgeDescriptor))
        if len({p.parameter_id for p in ps}) != len(ps) or len({c.claim_id for c in cs}) != len(cs):
            raise ValidationError("duplicate descriptor/claim identity")
        keys = [p.storage_key for p in ps if p.storage_key is not None]
        if len(keys) != len(set(keys)):
            raise ValidationError("unproven storage alias collision")
        by_id = {c.claim_id: c for c in cs}
        if any(c.exact_revision != self.source_revision for c in cs):
            raise ValidationError("cross-revision claim")
        for p in ps:
            if p.source_revision != self.source_revision or p.parameter_id not in STEERING_IDS:
                raise ValidationError("descriptor outside steering source scope")
            if p.parameter_id == "liveTorqueParameters.latAccelOffset":
                if (
                    p.storage_key is not None
                    or p.classification is not Classification.COUPLED_PRESERVED_STATE
                ):
                    raise ValidationError("offset is preserved message state, never a tuning key")
            elif p.storage_key != p.parameter_id:
                raise ValidationError("unproved storage-key alias")
            if (
                p.parameter_id == "LateralTorqueCustom"
                and p.classification is not Classification.MODE_SELECTOR
            ):
                raise ValidationError("custom torque is a mode selector")
            for identity in p.consumer_claim_ids:
                c = by_id.get(identity)
                if c is None or p.parameter_id not in c.parameter_ids:
                    raise ValidationError("missing or unrelated consumer claim")
                if p.evidence_status is Confidence.PROVEN and c.confidence is not Confidence.PROVEN:
                    raise ValidationError("unproved claim cannot support proven metadata")
        object.__setattr__(self, "parameters", tuple(sorted(ps, key=lambda x: x.parameter_id)))
        object.__setattr__(self, "claims", tuple(sorted(cs, key=lambda x: x.claim_id)))

    def get_any(self, parameter_id: str) -> ParameterDescriptor | None:
        """Diagnostic description only; no applicability or application approval."""
        return next((p for p in self.parameters if p.parameter_id == parameter_id), None)

    def get_proven(self, parameter_id: str) -> ParameterDescriptor | None:
        """Source-proven description only, excluding conditional/unresolved entries."""
        p = self.get_any(parameter_id)
        return p if p is not None and p.evidence_status is Confidence.PROVEN else None
