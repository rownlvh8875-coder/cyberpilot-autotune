"""Linux anchored no-follow snapshots. Not hostile-host or execution-time sealing."""

import hashlib
import os
import stat
import sys
from pathlib import Path
from typing import BinaryIO

from .contracts import InputEntry, InputSnapshot, relative_path

MAX_ENTRIES = 50000
MAX_DEPTH = 64
MAX_FILE_BYTES = 1024 * 1024 * 1024


class _BoundedReader:
    def __init__(self, stream: BinaryIO, limit: int):
        self.stream = stream
        self.remaining = limit

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray) -> int:
        data = self.stream.read(min(len(buffer), self.remaining + 1))
        count = len(data)
        if count > self.remaining:
            raise ValueError("input changed beyond initial size during hash")
        buffer[:count] = data
        self.remaining -= count
        return count


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _root(root: Path) -> int:
    if sys.platform != "linux" or not root.is_absolute() or ".." in root.parts:
        raise ValueError("Linux absolute fixed root required")
    return os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)


def _parent(root_fd: int, path: str) -> tuple[int, str]:
    relative_path(path)
    parts = path.split("/")
    descriptor = os.dup(root_fd)
    try:
        for name in parts[:-1]:
            child = os.open(
                name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = child
        return descriptor, parts[-1]
    except BaseException:
        os.close(descriptor)
        raise


def _entry(root_id: str, path: str, parent: int, name: str, before: os.stat_result) -> InputEntry:
    mode = before.st_mode
    if stat.S_ISREG(mode):
        if before.st_size > MAX_FILE_BYTES:
            raise ValueError("file size exceeds input bound")
        descriptor = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent
        )
        with os.fdopen(descriptor, "rb") as stream:
            if _identity(os.fstat(stream.fileno())) != _identity(before):
                raise ValueError("input changed before read")
            digest = hashlib.file_digest(
                _BoundedReader(stream, before.st_size), "sha256"
            ).hexdigest()
            after = os.fstat(stream.fileno())
        result = InputEntry(root_id, path, "file", mode, before.st_size, digest, None)
    elif stat.S_ISLNK(mode):
        target = os.readlink(name, dir_fd=parent)
        result = InputEntry(root_id, path, "symlink", mode, len(target.encode()), None, target)
        after = os.stat(name, dir_fd=parent, follow_symlinks=False)
    elif stat.S_ISDIR(mode):
        result = InputEntry(root_id, path, "directory", mode, 0, None, None)
        after = os.stat(name, dir_fd=parent, follow_symlinks=False)
    else:
        raise ValueError("special host input is not readable code/data")
    if _identity(before) != _identity(after) or _identity(before) != _identity(
        os.stat(name, dir_fd=parent, follow_symlinks=False)
    ):
        raise ValueError("input changed during observation")
    return result


def scan_tree(root_id: str, root: Path) -> tuple[InputEntry, ...]:
    descriptor = _root(root)
    entries: list[InputEntry] = []
    try:
        root_before = os.fstat(descriptor)
        entries.append(InputEntry(root_id, ".", "directory", root_before.st_mode, 0, None, None))

        def walk(parent: int, prefix: str, depth: int) -> None:
            if depth > MAX_DEPTH:
                raise ValueError("tree depth exceeds bound")
            before = os.fstat(parent)
            with os.scandir(parent) as listing:
                names: list[str] = []
                for entry in listing:
                    if len(names) + len(entries) >= MAX_ENTRIES:
                        raise ValueError("tree entry bound exceeded")
                    names.append(entry.name)
                names.sort()
            for name in names:
                if len(entries) >= MAX_ENTRIES:
                    raise ValueError("tree entry bound exceeded")
                path = prefix + name
                info = os.stat(name, dir_fd=parent, follow_symlinks=False)
                entries.append(_entry(root_id, path, parent, name, info))
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(
                        name,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=parent,
                    )
                    try:
                        if _identity(os.fstat(child)) != _identity(info):
                            raise ValueError("directory changed before traversal")
                        walk(child, path + "/", depth + 1)
                    finally:
                        os.close(child)
                    if _identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != _identity(
                        info
                    ):
                        raise ValueError("directory changed during traversal")
            if _identity(os.fstat(parent)) != _identity(before):
                raise ValueError("directory changed during observation")

        walk(descriptor, "", 0)
        if _identity(root.lstat()) != _identity(root_before):
            raise ValueError("root changed during observation")
        return InputSnapshot(tuple(entries)).entries
    finally:
        os.close(descriptor)


def scan_selected(root_id: str, root: Path, paths: tuple[str, ...]) -> tuple[InputEntry, ...]:
    paths = tuple(paths)
    if len(paths) > MAX_ENTRIES or len(paths) != len(set(paths)):
        raise ValueError("invalid selected paths")
    for path in paths:
        relative_path(path)
    descriptor = _root(root)
    try:
        before = os.fstat(descriptor)
        entries = [InputEntry(root_id, ".", "directory", before.st_mode, 0, None, None)]
        for path in paths:
            parent, name = _parent(descriptor, path)
            try:
                info = os.stat(name, dir_fd=parent, follow_symlinks=False)
                entries.append(_entry(root_id, path, parent, name, info))
            finally:
                os.close(parent)
        if _identity(root.lstat()) != _identity(before):
            raise ValueError("selected root changed during observation")
        return InputSnapshot(tuple(entries)).entries
    finally:
        os.close(descriptor)


def read_regular(root: Path, path: str, limit: int) -> bytes:
    if type(limit) is not int or not 0 < limit <= MAX_FILE_BYTES:
        raise ValueError("invalid read limit")
    descriptor = _root(root)
    try:
        parent, name = _parent(descriptor, path)
        try:
            before = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                raise ValueError("regular bounded input required")
            opened = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent
            )
            with os.fdopen(opened, "rb") as stream:
                data = stream.read(limit + 1)
                if _identity(before) != _identity(os.fstat(stream.fileno())):
                    raise ValueError("input changed during bounded read")
            if len(data) != before.st_size or _identity(before) != _identity(
                os.stat(name, dir_fd=parent, follow_symlinks=False)
            ):
                raise ValueError("input changed during bounded read")
            return data
        finally:
            os.close(parent)
    finally:
        os.close(descriptor)
