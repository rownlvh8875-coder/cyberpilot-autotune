"""Immutable evidence shapes, not proof producers or promotion capabilities."""

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

MAX_ITEMS = 50000
UINT64_MAX = 2**64 - 1
CLOCK_DOMAIN = "GUEST_TRACER_OBSERVATION_MONOTONIC_NS"


class MaterialRole(StrEnum):
    SOURCE = "SOURCE"
    TOOLCHAIN = "TOOLCHAIN"
    CONFIG = "CONFIG"
    GENERATED = "GENERATED"


class UseKind(StrEnum):
    READ_BYTES = "READ_BYTES"
    MMAP_BOUND = "MMAP_BOUND"
    EXEC_BOUND = "EXEC_BOUND"
    METADATA_ONLY = "METADATA_ONLY"


class ExitKind(StrEnum):
    EXITED = "EXITED"
    SIGNALLED = "SIGNALLED"


class EvidenceKind(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    OBSERVED_UNTRUSTED = "OBSERVED_UNTRUSTED"


def uint(value: int | None, *, optional: bool = False, positive: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not int or not (1 if positive else 0) <= value <= UINT64_MAX:
        raise ValueError("invalid UInt64 observation")


def sha(value: str | None, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("invalid SHA256 identity")


def opaque(value: str) -> None:
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}", value) is None:
        raise ValueError("invalid opaque identity")


def path(value: str) -> None:
    if type(value) is not str or not value or len(value) > 4096:
        raise ValueError("invalid logical path")
    if (
        "\\" in value
        or any(ord(c) < 32 for c in value)
        or any(p in {"", ".", ".."} for p in value.split("/"))
    ):
        raise ValueError("path traversal or alias")
    try:
        value.encode("utf-8")
    except UnicodeError as error:
        raise ValueError("invalid path encoding") from error


class _Record(Protocol):
    def __post_init__(self) -> None: ...


def records[T: _Record](values: Any, cls: type[T], keys: tuple[str, ...] = ()) -> tuple[T, ...]:
    result: list[T] = []
    try:
        for value in values:
            if len(result) >= MAX_ITEMS or type(value) is not cls:
                raise ValueError("invalid or oversized record collection")
            value.__post_init__()
            result.append(value)
    except TypeError as error:
        raise ValueError("invalid record collection") from error
    if keys:
        identities = [tuple(getattr(value, name) for name in keys) for value in result]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate record identity")
        result.sort(key=lambda value: tuple(getattr(value, name) for name in keys))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class BuildIdentity:
    session_id: str
    attempt_id: str
    source_digest: str | None
    toolchain_digest: str | None
    recipe_digest: str | None
    environment_digest: str | None
    observer_digest: str | None
    clock_domain: str

    def __post_init__(self) -> None:
        opaque(self.session_id)
        opaque(self.attempt_id)
        for value in (
            self.source_digest,
            self.toolchain_digest,
            self.recipe_digest,
            self.environment_digest,
            self.observer_digest,
        ):
            sha(value, optional=True)
        if (
            type(self.clock_domain) is not str
            or not self.clock_domain
            or len(self.clock_domain) > 128
            or any(ord(c) < 32 for c in self.clock_domain)
        ):
            raise ValueError("invalid clock domain")


@dataclass(frozen=True, slots=True)
class BuildMaterial:
    material_id: str
    generation: int
    role: MaterialRole
    logical_path: str
    size: int
    sha256: str
    cohort_digest: str
    origin_digest: str | None = None

    def __post_init__(self) -> None:
        opaque(self.material_id)
        uint(self.generation)
        uint(self.size)
        if type(self.role) is not MaterialRole:
            raise ValueError("unknown material role")
        path(self.logical_path)
        sha(self.sha256)
        sha(self.cohort_digest)
        sha(self.origin_digest, optional=True)


@dataclass(frozen=True, slots=True)
class TaskImage:
    task_generation: int
    exec_generation: int
    parent_generation: int | None
    image_id: str
    image_generation: int
    start_ns: int
    finish_ns: int

    def __post_init__(self) -> None:
        uint(self.task_generation, positive=True)
        uint(self.exec_generation)
        uint(self.parent_generation, optional=True, positive=True)
        opaque(self.image_id)
        for value in (self.image_generation, self.start_ns, self.finish_ns):
            uint(value)


@dataclass(frozen=True, slots=True)
class InputUse:
    sequence: int
    context_digest: str
    task_generation: int
    exec_generation: int
    material_id: str
    material_generation: int
    kind: UseKind
    time_ns: int
    offset: int | None
    length: int | None
    range_digest: str | None

    def __post_init__(self) -> None:
        uint(self.sequence, positive=True)
        uint(self.task_generation, positive=True)
        for value in (self.exec_generation, self.material_generation, self.time_ns):
            uint(value)
        uint(self.offset, optional=True)
        uint(self.length, optional=True)
        sha(self.context_digest)
        sha(self.range_digest, optional=True)
        opaque(self.material_id)
        if type(self.kind) is not UseKind:
            raise ValueError("unsupported consumed-source stage")


@dataclass(frozen=True, slots=True)
class BuildOutput:
    output_id: str
    generation: int
    logical_path: str
    size: int
    sha256: str
    last_write_ns: int | None
    writer_task_generation: int
    writer_exec_generation: int

    def __post_init__(self) -> None:
        opaque(self.output_id)
        path(self.logical_path)
        for value in (self.generation, self.size, self.writer_exec_generation):
            uint(value)
        uint(self.writer_task_generation, positive=True)
        uint(self.last_write_ns, optional=True)
        sha(self.sha256)


@dataclass(frozen=True, slots=True)
class BuildCompletion:
    exit_kind: ExitKind | None
    exit_code: int | None
    term_signal: int | None
    sequence_complete: bool | None
    dropped_events: int | None
    input_seal_digest: str | None
    task_trace_digest: str | None
    input_trace_digest: str | None
    writer_trace_digest: str | None

    def __post_init__(self) -> None:
        if self.exit_kind is not None and type(self.exit_kind) is not ExitKind:
            raise ValueError("unsupported exit identity")
        uint(self.exit_code, optional=True)
        uint(self.term_signal, optional=True, positive=True)
        if (self.exit_code is not None and self.exit_code > 255) or (
            self.term_signal is not None and self.term_signal > 64
        ):
            raise ValueError("invalid process exit observation")
        if self.exit_kind is None and (self.exit_code is not None or self.term_signal is not None):
            raise ValueError("unknown exit is not zero/signal")
        if self.exit_kind is ExitKind.EXITED and self.term_signal is not None:
            raise ValueError("normal exit cannot supply a terminating signal")
        if self.exit_kind is ExitKind.SIGNALLED and self.exit_code is not None:
            raise ValueError("signal termination is not a normal exit code")
        if self.sequence_complete is not None and type(self.sequence_complete) is not bool:
            raise ValueError("invalid trace availability")
        uint(self.dropped_events, optional=True)
        for value in (
            self.input_seal_digest,
            self.task_trace_digest,
            self.input_trace_digest,
            self.writer_trace_digest,
        ):
            sha(value, optional=True)


@dataclass(frozen=True, slots=True)
class BuildReceipt:
    identity: BuildIdentity
    materials: tuple[BuildMaterial, ...]
    images: tuple[TaskImage, ...]
    uses: tuple[InputUse, ...]
    outputs: tuple[BuildOutput, ...]
    start_ns: int | None
    finish_ns: int | None
    completion: BuildCompletion
    evidence_kind: EvidenceKind

    def __post_init__(self) -> None:
        if type(self.identity) is not BuildIdentity or type(self.completion) is not BuildCompletion:
            raise ValueError("invalid build context/completion")
        self.identity.__post_init__()
        self.completion.__post_init__()
        if type(self.evidence_kind) is not EvidenceKind:
            raise ValueError("unknown evidence kind")
        uint(self.start_ns, optional=True)
        uint(self.finish_ns, optional=True)
        object.__setattr__(
            self, "materials", records(self.materials, BuildMaterial, ("material_id", "generation"))
        )
        object.__setattr__(
            self, "images", records(self.images, TaskImage, ("task_generation", "exec_generation"))
        )
        object.__setattr__(self, "uses", records(self.uses, InputUse))
        object.__setattr__(
            self, "outputs", records(self.outputs, BuildOutput, ("output_id", "generation"))
        )


@dataclass(frozen=True, slots=True)
class PromotionReceipt:
    context_digest: str
    build_digest: str
    output_id: str
    output_generation: int
    output_sha256: str
    staged_sha256: str | None
    sealed_sha256: str | None
    source_namespace_digest: str | None
    destination_namespace_digest: str | None
    quiesced_ns: int | None
    sealed_ns: int | None
    verified_ns: int | None
    promoted_ns: int | None
    quiescence_digest: str | None
    seal_digest: str | None
    verification_digest: str | None

    def __post_init__(self) -> None:
        opaque(self.output_id)
        uint(self.output_generation)
        for required_digest in (self.context_digest, self.build_digest, self.output_sha256):
            sha(required_digest)
        for optional_digest in (
            self.staged_sha256,
            self.sealed_sha256,
            self.source_namespace_digest,
            self.destination_namespace_digest,
            self.quiescence_digest,
            self.seal_digest,
            self.verification_digest,
        ):
            sha(optional_digest, optional=True)
        for observation_time in (
            self.quiesced_ns,
            self.sealed_ns,
            self.verified_ns,
            self.promoted_ns,
        ):
            uint(observation_time, optional=True)
