"""Immutable capture inputs and diagnostic values;no authority or implicit I/O."""

from dataclasses import dataclass
from hashlib import sha256

from tests.audit_compatibility.contracts import PERMISSIONS, CompatibilityInputBundle
from tests.audit_compatibility.git_objects import (
    CommitObject,
    GitImage,
    TreeSnapshot,
    oid,
    path_value,
)

PROFILE = "C1_POSIX_RAW_BYTES_V1"
BLOCKERS = (
    "ACTUAL_Q_I",
    "ENTRY_GUARD_INTEGRATION",
    "EXACT_I_CI",
    "HISTORICAL_REPLAY",
    "SOURCE_CAPTURE_ATOMICITY",
    "STACK_ADOPTION",
)


def need(value: bool) -> None:
    if not value:
        raise ValueError("invalid capture value")


def reasons(value: tuple[str, ...]) -> None:
    need(type(value) is tuple and all(type(x) is str and bool(x) for x in value))
    need(value == tuple(sorted(set(value))))


def absolute(value: str) -> bool:
    return (
        type(value) is str
        and value.startswith("/")
        and "\\" not in value
        and "\0" not in value
        and all(p not in (".", "..", "") for p in value.split("/")[1:])
    )


class CaptureFault(Exception):
    def __init__(self, reason: str, unavailable: bool = False):
        super().__init__(reason)
        self.reason, self.unavailable = reason, unavailable


def require(value: bool, reason: str, *, unavailable: bool = False) -> None:
    if not value:
        raise CaptureFault(reason, unavailable)


@dataclass(frozen=True, slots=True)
class CaptureBudget:
    maximum_output_bytes: int
    maximum_total_read_bytes: int
    maximum_entries: int
    subprocess_timeout_ns: int

    def __post_init__(self) -> None:
        need(
            all(
                type(v) is int and 0 < v <= 2**63 - 1
                for v in (
                    self.maximum_output_bytes,
                    self.maximum_total_read_bytes,
                    self.maximum_entries,
                    self.subprocess_timeout_ns,
                )
            )
        )


class ReadBudget:
    """Per-call private accounting,never global state or a report claim."""

    def __init__(self, limits: CaptureBudget):
        CaptureBudget.__post_init__(limits)
        self.limits, self.bytes, self.entries = limits, 0, 0

    def consume(self, count: int, entries: int = 0) -> None:
        self.bytes += count
        self.entries += entries
        require(
            self.bytes <= self.limits.maximum_total_read_bytes
            and self.entries <= self.limits.maximum_entries,
            "RESOURCE_LIMIT",
            unavailable=True,
        )


@dataclass(frozen=True, slots=True)
class RepoLayout:
    worktree_root: str
    git_dir: str
    common_dir: str
    control_roots: tuple[str, ...]

    def __post_init__(self) -> None:
        need(all(absolute(x) for x in (self.worktree_root, self.git_dir, self.common_dir)))
        need(type(self.control_roots) is tuple and all(absolute(x) for x in self.control_roots))
        need(len(set(self.control_roots)) == len(self.control_roots))


@dataclass(frozen=True, slots=True)
class CaptureRequest:
    candidate_head: str
    validation_head: str
    declared_base: str | None
    source_oids: tuple[str, ...]
    layout: RepoLayout
    budget: CaptureBudget
    profile: str = PROFILE

    def __post_init__(self) -> None:
        need(oid(self.candidate_head) and oid(self.validation_head))
        need(self.declared_base is None or oid(self.declared_base))
        need(type(self.source_oids) is tuple and all(oid(x) for x in self.source_oids))
        need(len(set(self.source_oids)) == len(self.source_oids))
        need(type(self.layout) is RepoLayout and type(self.budget) is CaptureBudget)
        RepoLayout.__post_init__(self.layout)
        CaptureBudget.__post_init__(self.budget)
        need(type(self.profile) is str and self.profile == PROFILE)


@dataclass(frozen=True, slots=True)
class CaptureConsistencyDecision:
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        reasons(self.errors)
        reasons(self.unavailable)

    @property
    def decision(self) -> str:
        return (
            "REJECTED" if self.errors else "UNAVAILABLE" if self.unavailable else "OBSERVED_STABLE"
        )

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def atomicity(self) -> str:
        return "NOT_ESTABLISHED"

    @property
    def integrated_admission(self) -> bool:
        return False

    @property
    def content_identity_only(self) -> bool:
        return True

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    @property
    def remaining_blockers(self) -> tuple[str, ...]:
        return BLOCKERS


@dataclass(frozen=True, slots=True)
class IndexEntry:
    path: str
    mode: str
    oid: str
    flags: int

    def __post_init__(self) -> None:
        need(path_value(self.path) and self.mode == "100644" and oid(self.oid))
        need(type(self.flags) is int and 0 <= self.flags <= 4095)


@dataclass(frozen=True, slots=True)
class IndexCapture:
    raw_sha256: str
    version: int
    entries: tuple[IndexEntry, ...]
    extensions: tuple[tuple[str, bytes], ...]

    def __post_init__(self) -> None:
        need(type(self.version) is int and self.version == 2)
        need(type(self.entries) is tuple and all(type(x) is IndexEntry for x in self.entries))
        for x in self.entries:
            IndexEntry.__post_init__(x)
        TreeSnapshot(tuple((x.path, GitImage(x.mode, b"")) for x in self.entries))
        need(type(self.extensions) is tuple)
        need(
            all(
                type(x) is tuple and len(x) == 2 and x[0] == "TREE" and type(x[1]) is bytes
                for x in self.extensions
            )
        )


@dataclass(frozen=True, slots=True)
class ControlCapture:
    identities: tuple[tuple[str, str | None], ...]
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObjectCapture:
    raw_commits: tuple[CommitObject, ...]
    trees: tuple[TreeSnapshot, ...]
    missing_oids: tuple[str, ...]
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FileCapture:
    path: str
    image: GitImage
    stat_identity: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class WorktreeCapture:
    files: tuple[FileCapture, ...]
    inventory: tuple[str, ...]
    untracked_including_ignored: tuple[str, ...]
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AttributeCapture:
    vectors: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]


@dataclass(frozen=True, slots=True)
class CapturePass:
    head_oid: str | None
    controls: ControlCapture
    objects: ObjectCapture
    index: IndexCapture | None
    worktree: WorktreeCapture | None
    attributes: AttributeCapture | None
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CaptureReport:
    pass_a: CapturePass | None
    pass_b: CapturePass | None
    partial_bundle: CompatibilityInputBundle | None
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    @property
    def consistency(self) -> str:
        return CaptureConsistencyDecision(self.errors, self.unavailable).decision

    @property
    def atomicity(self) -> str:
        return "NOT_ESTABLISHED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def integrated_admission(self) -> bool:
        return False


def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()
