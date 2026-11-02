"""Immutable capture inputs and diagnostic values;no authority or implicit I/O."""

import json
from dataclasses import dataclass, fields
from hashlib import sha256
from typing import Any

from tests.audit_compatibility.contracts import PERMISSIONS, CompatibilityInputBundle
from tests.audit_compatibility.git_objects import (
    CommitObject,
    GitImage,
    TreeSnapshot,
    oid,
    path_value,
)

PROFILE = "C1_POSIX_RAW_BYTES_V1"
ATTRIBUTE_SHA256 = "3da824d0f37be4082aecb38cef9b01c8f0b9e66ab67d574cfbe3b2e3553db908"
ALLOWED_GIT_ENV = frozenset(
    (
        "GIT_PAGER",
        "GIT_NO_LAZY_FETCH",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OPTIONAL_LOCKS",
        "GIT_TERMINAL_PROMPT",
        "GIT_ALLOW_PROTOCOL",
        "GIT_ATTR_NOSYSTEM",
        "GIT_ASKPASS",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "GIT_SSH_VARIANT",
        "GIT_PROXY_COMMAND",
        "GIT_SSL_CAINFO",
        "GIT_SSL_CAPATH",
        "GIT_SSL_CERT",
        "GIT_SSL_KEY",
        "GIT_SSL_NO_VERIFY",
        "GIT_SSL_CERT_PASSWORD_PROTECTED",
        "GIT_HTTP_USER_AGENT",
        "GIT_HTTP_PROXY_AUTHMETHOD",
        "GIT_HTTP_LOW_SPEED_LIMIT",
        "GIT_HTTP_LOW_SPEED_TIME",
    )
)
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


def records(values: Any, cls: type[Any]) -> None:
    need(type(values) is tuple and all(type(v) is cls for v in values))
    for value in values:
        cls.__post_init__(value)


def hash256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(x in "0123456789abcdef" for x in value)


def expected_attributes(path: str) -> tuple[tuple[str, str], ...]:
    if path.startswith("src/cyberpilot_autotune/diagnostics/"):
        return (("eol", "lf"), ("text", "set"))
    if (
        path.startswith("tests/fixtures/actual_binding/")
        and "/" not in path.removeprefix("tests/fixtures/actual_binding/")
        and path.endswith(".zip")
    ):
        return (("binary", "set"), ("diff", "unset"), ("merge", "unset"), ("text", "unset"))
    return ()


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
        need(hash256(self.raw_sha256))
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

    def __post_init__(self) -> None:
        need(type(self.identities) is tuple)
        need(
            all(
                type(p) is tuple
                and len(p) == 2
                and type(p[0]) is str
                and (p[1] is None or hash256(p[1]))
                for p in self.identities
            )
        )
        need(len({p[0] for p in self.identities}) == len(self.identities))
        reasons(self.errors)
        reasons(self.unavailable)


@dataclass(frozen=True, slots=True)
class ObjectCapture:
    raw_commits: tuple[CommitObject, ...]
    trees: tuple[TreeSnapshot, ...]
    missing_oids: tuple[str, ...]
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        records(self.raw_commits, CommitObject)
        records(self.trees, TreeSnapshot)
        need(len({v.oid for v in self.raw_commits}) == len(self.raw_commits))
        need(len({v.oid for v in self.trees}) == len(self.trees))
        reasons(self.missing_oids)
        need(all(oid(v) for v in self.missing_oids))
        reasons(self.errors)
        reasons(self.unavailable)


@dataclass(frozen=True, slots=True)
class FileCapture:
    path: str
    image: GitImage
    stat_identity: tuple[int, ...]

    def __post_init__(self) -> None:
        need(path_value(self.path) and type(self.image) is GitImage)
        GitImage.__post_init__(self.image)
        need(self.image.mode == "100644" and type(self.stat_identity) is tuple)
        need(len(self.stat_identity) == 7 and all(type(x) is int for x in self.stat_identity))


@dataclass(frozen=True, slots=True)
class WorktreeCapture:
    files: tuple[FileCapture, ...]
    inventory: tuple[str, ...]
    untracked_including_ignored: tuple[str, ...]
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        records(self.files, FileCapture)
        reasons(self.inventory)
        need(all(path_value(x) for x in self.inventory))
        reasons(self.untracked_including_ignored)
        need(all(hash256(x) for x in self.untracked_including_ignored))
        need(len({v.path for v in self.files}) == len(self.files))
        reasons(self.errors)
        reasons(self.unavailable)


@dataclass(frozen=True, slots=True)
class AttributeCapture:
    vectors: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]

    def __post_init__(self) -> None:
        need(type(self.vectors) is tuple)
        for pair in self.vectors:
            need(
                type(pair) is tuple
                and len(pair) == 2
                and path_value(pair[0])
                and type(pair[1]) is tuple
            )
            need(
                all(
                    type(v) is tuple and len(v) == 2 and all(type(x) is str for x in v)
                    for v in pair[1]
                )
            )
            need(len({v[0] for v in pair[1]}) == len(pair[1]))
        need(len({p[0] for p in self.vectors}) == len(self.vectors))


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

    def __post_init__(self) -> None:
        need(self.head_oid is None or oid(self.head_oid))
        records((self.controls,), ControlCapture)
        records((self.objects,), ObjectCapture)
        for value, cls in (
            (self.index, IndexCapture),
            (self.worktree, WorktreeCapture),
            (self.attributes, AttributeCapture),
        ):
            if value is not None:
                records((value,), cls)
        reasons(self.errors)
        reasons(self.unavailable)


@dataclass(frozen=True, slots=True)
class CaptureReport:
    pass_a: CapturePass | None
    pass_b: CapturePass | None
    partial_bundle: CompatibilityInputBundle | None
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.pass_a, self.pass_b):
            if value is not None:
                records((value,), CapturePass)
        if self.partial_bundle is not None:
            records((self.partial_bundle,), CompatibilityInputBundle)
        reasons(self.errors)
        reasons(self.unavailable)

    @property
    def consistency(self) -> str:
        return evaluate_report(self).decision

    @property
    def content_digest(self) -> str:
        CaptureReport.__post_init__(self)

        def encode(value: Any) -> Any:
            if type(value) is bytes:
                return {"bytes_hex": value.hex()}
            if type(value) is tuple:
                return [encode(v) for v in value]
            if value is None or type(value) in (str, int, bool):
                return value
            return {f.name: encode(getattr(value, f.name)) for f in fields(value)}

        return digest(
            json.dumps(
                encode(self), sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        )

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


def evaluate_report(report: CaptureReport) -> CaptureConsistencyDecision:
    need(type(report) is CaptureReport)
    CaptureReport.__post_init__(report)
    errors, missing = set(report.errors), set(report.unavailable)
    for observed in (report.pass_a, report.pass_b):
        if observed is None:
            missing.add("CAPTURE_PASS_MISSING")
            continue
        for part in (observed, observed.controls, observed.objects, observed.worktree):
            if part is not None:
                errors.update(part.errors)
                missing.update(part.unavailable)
        if observed.objects.missing_oids:
            missing.add("OBJECT_MISSING")
        required_controls = {
            *(f"config{i}" for i in range(5)),
            "ambientattrs0",
            "ambientattrs1",
            "attributes0",
            "grafts0",
            "shallow0",
            "alternates0",
            "REPLACE_REFS",
            "PARTIAL_CLONE",
            "objectstore",
            "refstore",
            "packedrefs",
            "HEAD",
        }
        if not required_controls <= dict(observed.controls.identities).keys():
            missing.add("CONTROL_OBSERVATIONS_INCOMPLETE")
        if observed.worktree is not None and observed.worktree.untracked_including_ignored:
            errors.add("UNTRACKED_PATH")
        if (
            observed.head_oid is None
            or observed.index is None
            or observed.worktree is None
            or observed.attributes is None
        ):
            missing.add("CURRENT_COMPONENT_MISSING")
        commits = {v.oid: v for v in observed.objects.raw_commits}
        trees = {v.oid: v for v in observed.objects.trees}
        head = commits.get(observed.head_oid or "")
        tree = trees.get(head.tree) if head is not None else None
        if tree is None:
            missing.add("CURRENT_TREE_MISSING")
        else:
            attribute_source = dict(tree.entries).get(".gitattributes")
            if attribute_source is None or digest(attribute_source.data) != ATTRIBUTE_SHA256:
                errors.add("ATTRIBUTE_POLICY")
            if observed.attributes is not None and observed.attributes.vectors != tuple(
                (p, expected_attributes(p)) for p, _ in tree.entries
            ):
                errors.add("ATTRIBUTE_POLICY")
            if observed.index is not None:
                actual = tuple((v.path, v.mode, v.oid) for v in observed.index.entries)
                if actual != tuple((p, image.mode, image.oid) for p, image in tree.entries):
                    errors.add("INDEX_HEAD_MISMATCH")
            if observed.worktree is not None:
                files = {v.path: v.image for v in observed.worktree.files}
                expected_files = dict(tree.entries)
                inventory = set(observed.worktree.inventory)
                if (
                    not files.keys() <= inventory
                    or not inventory <= expected_files.keys()
                    or (not observed.worktree.unavailable and inventory != expected_files.keys())
                ):
                    errors.add("INVENTORY_HEAD_MISMATCH")
                if any(expected_files.get(p) != image for p, image in files.items()) or (
                    not observed.worktree.unavailable and files != expected_files
                ):
                    errors.add("WORKTREE_HEAD_MISMATCH")
    a, b = report.pass_a, report.pass_b
    if a is not None and b is not None:
        for left, right in (
            (a.head_oid, b.head_oid),
            (a.index, b.index),
            (a.attributes, b.attributes),
        ):
            if left is not None and right is not None and left != right:
                errors.add("COHORT_CHANGED")
        left_controls, right_controls = dict(a.controls.identities), dict(b.controls.identities)
        if any(
            left_controls[p] != right_controls[p]
            for p in left_controls.keys() & right_controls.keys()
        ):
            errors.add("COHORT_CHANGED")
        if a.worktree is not None and b.worktree is not None:
            if (
                not a.worktree.unavailable
                and not b.worktree.unavailable
                and a.worktree != b.worktree
            ):
                errors.add("COHORT_CHANGED")
    return CaptureConsistencyDecision(tuple(sorted(errors)), tuple(sorted(missing)))
