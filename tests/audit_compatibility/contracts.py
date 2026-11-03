"""Neutral core inputs and permanently unqualified,immutable diagnostics."""

from dataclasses import dataclass

from .git_objects import CommitObject, TreeSnapshot, oid, path_value, require

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
IO_UNAVAILABLE = (
    "CURRENT_INDEX_WORKTREE",
    "EFFECTIVE_ATTRIBUTES",
    "HISTORICAL_REPLAY",
    "SOURCE_CAPTURE_ATOMICITY",
)


def paths(value: tuple[str, ...]) -> None:
    require(type(value) is tuple and all(path_value(p) for p in value))
    require(len({p.casefold() for p in value}) == len(value))


@dataclass(frozen=True, slots=True)
class PinnedCompatibilityManifest:
    r: str
    m: str
    d: str
    o: str
    semantic_path: str
    semantic_paths: tuple[str, ...]
    active_paths: tuple[str, ...]
    manifest_path: str
    inert_root: str

    def __post_init__(self) -> None:
        require(all(oid(x) for x in (self.r, self.m, self.d, self.o)))
        paths(self.semantic_paths)
        paths(self.active_paths)
        require(path_value(self.semantic_path) and self.semantic_path in self.semantic_paths)
        require(path_value(self.manifest_path) and path_value(self.inert_root))
        require(not set(self.semantic_paths) & set(self.active_paths))
        reserved = (*self.semantic_paths, self.manifest_path, self.inert_root)
        require(len({p.casefold() for p in reserved}) == len(reserved))
        require(
            not any(
                p == q or p.startswith(q + "/") or q.startswith(p + "/")
                for p in self.active_paths
                for q in reserved
            )
        )


@dataclass(frozen=True, slots=True)
class CompatibilityInputBundle:
    commits: tuple[CommitObject, ...]
    trees: tuple[TreeSnapshot, ...]
    candidate_head: str | None
    validation_head: str | None
    declared_base: str | None

    def __post_init__(self) -> None:
        require(type(self.commits) is tuple and type(self.trees) is tuple)
        for c in self.commits:
            require(type(c) is CommitObject)
            CommitObject.__post_init__(c)
        for t in self.trees:
            require(type(t) is TreeSnapshot)
            TreeSnapshot.__post_init__(t)
        require(len({c.oid for c in self.commits}) == len(self.commits))
        require(len({t.oid for t in self.trees}) == len(self.trees))
        require(
            all(
                x is None or oid(x)
                for x in (self.candidate_head, self.validation_head, self.declared_base)
            )
        )


@dataclass(frozen=True, slots=True)
class AuditCompatibilityDecision:
    errors: tuple[str, ...]
    unavailable_checks: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.errors, self.unavailable_checks):
            require(type(value) is tuple and all(type(x) is str and bool(x) for x in value))
            require(value == tuple(sorted(set(value))))
        require(set(IO_UNAVAILABLE) <= set(self.unavailable_checks))

    @property
    def decision(self) -> str:
        return "REJECTED" if self.errors else "UNAVAILABLE"

    @property
    def structural_content_status(self) -> str:
        if self.errors:
            return "REJECTED"
        return (
            "UNAVAILABLE" if set(self.unavailable_checks) - set(IO_UNAVAILABLE) else "CONTENT_MATCH"
        )

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def integrated_admission(self) -> bool:
        return False

    @property
    def content_identity_only(self) -> bool:
        return True

    @property
    def scientific_qualified(self) -> bool:
        return False

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS
