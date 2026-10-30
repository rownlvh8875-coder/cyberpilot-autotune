"""Immutable neutral content identities, explicitly distinct from trusted inputs."""

import re
import stat
from dataclasses import dataclass, field


def relative_path(path: str, *, root: bool = False) -> None:
    if type(path) is not str or not path or len(path) > 4096:
        raise ValueError("invalid relative path")
    if root and path == ".":
        return
    if "\\" in path or any(ord(c) < 32 for c in path):
        raise ValueError("invalid path character")
    if any(p in {"", ".", ".."} for p in path.split("/")):
        raise ValueError("path traversal or alias")


@dataclass(frozen=True, slots=True)
class InputEntry:
    root: str
    path: str
    kind: str
    mode: int
    size: int
    sha256: str | None
    target: str | None

    def __post_init__(self) -> None:
        if type(self.root) is not str or re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", self.root) is None:
            raise ValueError("invalid logical root")
        relative_path(self.path, root=True)
        if type(self.mode) is not int or not 0 <= self.mode <= 0o177777:
            raise ValueError("invalid mode")
        if type(self.size) is not int or not 0 <= self.size <= 2**40:
            raise ValueError("invalid size")
        kinds = {"file": stat.S_IFREG, "directory": stat.S_IFDIR, "symlink": stat.S_IFLNK}
        if type(self.kind) is not str or self.kind not in kinds:
            raise ValueError("unsupported host entry")
        if stat.S_IFMT(self.mode) != kinds[self.kind]:
            raise ValueError("kind/mode mismatch")
        if self.path == "." and self.kind != "directory":
            raise ValueError("root must be a directory")
        if self.kind == "file":
            if type(self.sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
                raise ValueError("missing content identity")
            if self.target is not None:
                raise ValueError("file is not a link")
        elif self.sha256 is not None:
            raise ValueError("nonfile content hash")
        elif self.kind == "directory":
            if self.size != 0 or self.target is not None:
                raise ValueError("invalid directory metadata")
        elif (
            type(self.target) is not str
            or not self.target
            or len(self.target) > 4096
            or any(ord(c) < 32 for c in self.target)
            or self.size != len(self.target.encode())
        ):
            raise ValueError("invalid literal link target")


@dataclass(frozen=True, slots=True)
class InputSnapshot:
    entries: tuple[InputEntry, ...]

    def __post_init__(self) -> None:
        items = tuple(self.entries)
        if len(items) > 50000 or any(type(e) is not InputEntry for e in items):
            raise ValueError("invalid inventory")
        for entry in items:
            entry.__post_init__()
        keys = [(e.root, e.path) for e in items]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate inventory identity")
        object.__setattr__(self, "entries", tuple(sorted(items, key=lambda e: (e.root, e.path))))


@dataclass(frozen=True, slots=True)
class ElfInfo:
    machine: int
    elf_type: int
    interpreter: str | None
    needed: tuple[str, ...]
    soname: str | None
    rpath: str | None
    runpath: str | None
    loader_directives: tuple[int, ...]
    osabi: int = 0
    abi_version: int = 0
    flags: int = 0
    flags_1: int = 0

    def __post_init__(self) -> None:
        if any(type(v) is not int or not 0 <= v <= 65535 for v in (self.machine, self.elf_type)):
            raise ValueError("invalid ELF identity")
        if any(
            type(v) is not int or not 0 <= v <= 255 for v in (self.osabi, self.abi_version)
        ) or any(type(v) is not int or not 0 <= v <= 2**64 - 1 for v in (self.flags, self.flags_1)):
            raise ValueError("invalid ELF ABI or flags")
        names = tuple(self.needed)
        directives = tuple(self.loader_directives)
        for value in (self.interpreter, self.soname, self.rpath, self.runpath, *names):
            if value is not None and (
                type(value) is not str or not value or len(value) > 4096 or "\0" in value
            ):
                raise ValueError("invalid ELF string")
        if (
            any(type(v) is not str for v in names)
            or len(names) != len(set(names))
            or any(type(v) is not int or not 0 <= v <= 2**63 - 1 for v in directives)
        ):
            raise ValueError("invalid dynamic directives")
        object.__setattr__(self, "needed", names)
        object.__setattr__(self, "loader_directives", directives)


@dataclass(frozen=True, slots=True)
class ImageMember:
    path: str
    mode: int
    data: bytes
    major: int = 0
    minor: int = 0

    def __post_init__(self) -> None:
        relative_path(self.path)
        if type(self.mode) is not int or not 0 <= self.mode <= 0o177777:
            raise ValueError("invalid image mode")
        if type(self.data) is not bytes or len(self.data) > 32 * 1024 * 1024:
            raise ValueError("invalid image content")
        if any(type(v) is not int or not 0 <= v <= 2**32 - 1 for v in (self.major, self.minor)):
            raise ValueError("invalid pseudo-node identity")
        kind = stat.S_IFMT(self.mode)
        if self.path in {"dev/console", "dev/null"}:
            expected = (0o020600, 5, 1) if self.path == "dev/console" else (0o020666, 1, 3)
            if (self.mode, self.major, self.minor) != expected or self.data:
                raise ValueError("wrong bootstrap pseudo-node object")
        if kind not in {stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK, stat.S_IFCHR}:
            raise ValueError("unsupported image kind")
        if kind == stat.S_IFDIR and self.data:
            raise ValueError("directory contains data")
        if kind == stat.S_IFLNK:
            try:
                target = self.data.decode("utf-8")
            except UnicodeError as error:
                raise ValueError("invalid link text") from error
            if not target or len(target) > 4096 or any(ord(c) < 32 for c in target):
                raise ValueError("invalid image link")
        if kind == stat.S_IFCHR:
            permitted = {"dev/console": (5, 1, 0o020600), "dev/null": (1, 3, 0o020666)}
            if permitted.get(self.path) != (self.major, self.minor, self.mode) or self.data:
                raise ValueError("unapproved bootstrap pseudo-node metadata")
        elif self.major or self.minor:
            raise ValueError("device identity on nondevice")


MANDATORY_BLOCKERS = (
    "HISTORICAL_BUILD_CONSUMPTION_UNPROVEN",
    "HISTORICAL_EXECUTED_IMAGE_BINDING_UNPROVEN",
    "HOST_COMPILER_CLOSURE_UNQUALIFIED",
    "HOST_PYTHON_CLOSURE_UNQUALIFIED",
    "QEMU_DYNAMIC_INPUTS_UNQUALIFIED",
    "DYNAMIC_LOAD_BEHAVIOR_UNQUALIFIED",
    "EXECUTION_INPUT_IMMUTABILITY_UNPROVEN",
    "COLLECTOR_AUTHENTICITY_UNQUALIFIED",
)


@dataclass(frozen=True, slots=True)
class ClosureReport:
    declared_inputs_match: bool
    guest_elf_dependencies_closed: bool
    entry_count: int
    image_count: int
    image_digests: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str, str], ...]
    issues: tuple[str, ...]
    evidence_kind: str = field(default="UNTRUSTED_CURRENT_CLOSURE_REPORT", init=False)
    overall_status: str = field(default="BLOCKED", init=False)
    blockers: tuple[str, ...] = field(default=MANDATORY_BLOCKERS, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    device_class_qualified: bool = field(default=False, init=False)
    policy_adopted: bool = field(default=False, init=False)
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    owner_proposal_allowed: bool = field(default=False, init=False)
    successful_prohibited_handles: None = field(default=None, init=False)
    successful_prohibited_effects: None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if (
            type(self.declared_inputs_match) is not bool
            or type(self.guest_elf_dependencies_closed) is not bool
        ):
            raise ValueError("invalid fact status")
        if any(
            type(v) is not int or not 0 <= v <= 50000 for v in (self.entry_count, self.image_count)
        ):
            raise ValueError("invalid report count")
        digests, issues = tuple(self.image_digests), tuple(self.issues)
        edges = tuple(tuple(edge) for edge in self.dependency_edges)
        if len(digests) != self.image_count or any(
            type(v) is not str or re.fullmatch(r"[0-9a-f]{64}", v) is None for v in digests
        ):
            raise ValueError("invalid image identities")
        if any(type(v) is not str or not v for v in issues) or any(
            len(e) != 3 or any(type(v) is not str or not v for v in e) for e in edges
        ):
            raise ValueError("invalid report details")
        object.__setattr__(self, "image_digests", digests)
        object.__setattr__(self, "dependency_edges", edges)
        object.__setattr__(self, "issues", issues)
