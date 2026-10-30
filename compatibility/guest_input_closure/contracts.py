"""Immutable neutral content identities, explicitly distinct from trusted inputs."""

import re
import stat
from dataclasses import dataclass


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

    def __post_init__(self) -> None:
        if any(type(v) is not int or not 0 <= v <= 65535 for v in (self.machine, self.elf_type)):
            raise ValueError("invalid ELF identity")
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
