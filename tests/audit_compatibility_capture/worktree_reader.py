"""Closed index decoding and explicit safe filesystem observation (no Git imports)."""

import errno
import os
import posixpath
import re
import stat
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha1

from tests.audit_compatibility.git_objects import GitImage, TreeSnapshot, oid, path_value

from .contracts import (
    CaptureFault,
    CaptureRequest,
    ControlCapture,
    FileCapture,
    IndexCapture,
    IndexEntry,
    ReadBudget,
    RepoLayout,
    WorktreeCapture,
    absolute,
    digest,
    require,
)


def capable() -> bool:
    return os.name == "posix" and hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


@contextmanager
def directory(path: str) -> Iterator[int]:
    require(capable(), "PLATFORM_SAFE_OPEN", unavailable=True)
    require(absolute(path) or path == "/", "UNSAFE_PATH")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.split("/")[1:]:
            if part:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
        yield fd
    finally:
        os.close(fd)


def read_file(
    path: str, budget: ReadBudget, *, missing_ok: bool = False
) -> tuple[bytes | None, tuple[int, ...]]:
    require(absolute(path), "UNSAFE_PATH")
    parent, name = posixpath.split(path)
    try:
        with directory(parent) as root:
            root_identity = _identity(os.fstat(root))[:2]
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "FILE_TYPE")
                chunks = []
                while chunk := os.read(fd, 65536):
                    budget.consume(len(chunk))
                    chunks.append(chunk)
                after = os.fstat(fd)
                require(_identity(before) == _identity(after), "FILE_CHANGED")
                require(
                    _identity(after)
                    == _identity(os.stat(name, dir_fd=root, follow_symlinks=False)),
                    "FILE_CHANGED",
                )
                with directory(parent) as current:
                    require(_identity(os.fstat(current))[:2] == root_identity, "ROOT_CHANGED")
                return b"".join(chunks), _identity(after)
            finally:
                os.close(fd)
    except OSError as error:
        if error.errno == errno.ENOENT and missing_ok:
            return None, ()
        unsafe = error.errno in (errno.ELOOP, errno.ENOTDIR)
        raise CaptureFault("UNSAFE_PATH" if unsafe else "FILE_IO", not unsafe) from error


def config_candidates(layout: RepoLayout) -> tuple[str, ...]:
    user = os.environ.get("HOME")
    require(user is not None and absolute(user), "CONFIG_SCOPE", unavailable=True)
    assert user is not None
    xdg = os.environ.get("XDG_CONFIG_HOME", user + "/.config")
    require(absolute(xdg), "CONFIG_SCOPE", unavailable=True)
    return ("/etc/gitconfig", user + "/.gitconfig", xdg + "/git/config")


def _value(raw: str) -> str:
    output, quoted, escaped = [], False, False
    for char in raw.strip():
        if escaped:
            require(char in '\\"ntb', "CONFIG_SYNTAX", unavailable=True)
            output.append({"n": "\n", "t": "\t", "b": "\b"}.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char in "#;" and not quoted:
            break
        else:
            output.append(char)
    require(not quoted and not escaped, "CONFIG_SYNTAX", unavailable=True)
    return "".join(output).strip()


def inspect_config(raw: bytes, errors: set[str], missing: set[str], layout: RepoLayout) -> None:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError:
        missing.add("CONFIG_SYNTAX")
        return
    section, subsection = "", ""
    inert_core = {
        "repositoryformatversion",
        "filemode",
        "logallrefupdates",
        "ignorecase",
        "precomposeunicode",
        "autocrlf",
        "eol",
        "quotepath",
        "symlinks",
        "editor",
        "pager",
        "protecthfs",
        "protectntfs",
        "compression",
        "excludesfile",
    }
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            match = re.fullmatch(r'\[([A-Za-z][A-Za-z0-9-]*)(?: "([^"\\]*)")?\]', line)
            if match is None:
                missing.add("CONFIG_SYNTAX")
                section, subsection = "", ""
            else:
                section, subsection = match[1].lower(), match[2] or ""
            continue
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*)(?:\s*=\s*(.*))?", line)
        if match is None or not section:
            missing.add("CONFIG_SYNTAX")
            continue
        key = match[1].lower()
        if section in ("include", "includeif"):
            missing.add("CONFIG_INCLUDE")
            continue
        if section == "filter" or (
            section in ("diff", "merge") and key in ("command", "driver", "textconv")
        ):
            errors.add("CUSTOM_HELPER")
            continue
        try:
            original = _value(match[2] if match[2] is not None else "true")
            value = original.lower()
        except CaptureFault:
            missing.add("CONFIG_SYNTAX")
            continue
        if section == "core":
            if subsection:
                missing.add("CONFIG_SYNTAX")
            elif (
                key == "worktree"
                and posixpath.normpath(posixpath.join(layout.git_dir, original))
                != layout.worktree_root
            ):
                errors.add("WRONG_LAYOUT")
            elif key == "attributesfile" and value:
                errors.add("ATTRIBUTE_OVERRIDE")
            elif key == "fsmonitor" and value not in ("false", "no", "off", "0"):
                errors.add("CUSTOM_HELPER")
            elif key in ("sparsecheckout", "splitindex", "untrackedcache") and value not in (
                "false",
                "no",
                "off",
                "0",
            ):
                missing.add("CONFIG_FEATURE")
            elif key == "bare" and value not in ("false", "no", "off", "0"):
                errors.add("WRONG_LAYOUT")
            elif key not in inert_core | {
                "attributesfile",
                "fsmonitor",
                "sparsecheckout",
                "splitindex",
                "untrackedcache",
                "bare",
                "worktree",
            }:
                missing.add("CONFIG_SYNTAX")
        elif section == "extensions":
            if key == "objectformat" and value != "sha1":
                missing.add("OBJECT_FORMAT")
            elif key not in ("objectformat", "worktreeconfig"):
                missing.add("CONFIG_FEATURE")
        elif section not in (
            "user",
            "remote",
            "branch",
            "credential",
            "http",
            "url",
            "safe",
            "init",
            "alias",
            "gc",
            "pack",
            "fetch",
            "push",
        ):
            missing.add("CONFIG_SYNTAX")


def verify_layout(request: CaptureRequest, budget: ReadBudget) -> None:
    layout = request.layout
    try:
        for path in (layout.worktree_root, layout.git_dir, layout.common_dir):
            with directory(path):
                pass
        marker = layout.worktree_root + "/.git"
        with directory(layout.worktree_root) as root:
            info = os.stat(".git", dir_fd=root, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            require(marker == layout.git_dir == layout.common_dir, "WRONG_LAYOUT")
        else:
            raw, _ = read_file(marker, budget)
            require(
                raw is not None and raw.startswith(b"gitdir: ") and b"\r" not in raw, "WRONG_LAYOUT"
            )
            assert raw is not None
            value = raw[8:].decode("utf-8").removesuffix("\n")
            require(
                "\n" not in value
                and posixpath.normpath(posixpath.join(layout.worktree_root, value))
                == layout.git_dir,
                "WRONG_LAYOUT",
            )
        raw, _ = read_file(layout.git_dir + "/commondir", budget, missing_ok=True)
        if raw is None:
            require(layout.common_dir == layout.git_dir, "WRONG_LAYOUT")
        else:
            value = raw.decode("utf-8").removesuffix("\n")
            require(
                posixpath.normpath(posixpath.join(layout.git_dir, value)) == layout.common_dir,
                "WRONG_LAYOUT",
            )
    except (OSError, UnicodeError) as error:
        raise CaptureFault("LAYOUT_IO", True) from error


def preflight(request: CaptureRequest, budget: ReadBudget) -> ControlCapture:
    errors: set[str] = set()
    missing: set[str] = set()
    identities: list[tuple[str, str | None]] = []

    def fault(error: CaptureFault) -> None:
        (missing if error.unavailable else errors).add(error.reason)

    try:
        verify_layout(request, budget)
    except CaptureFault as error:
        fault(error)
    for key, value in os.environ.items():
        if value and (
            key.startswith("GIT_CONFIG")
            or key
            in {
                "GIT_DIR",
                "GIT_WORK_TREE",
                "GIT_INDEX_FILE",
                "GIT_COMMON_DIR",
                "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                "GIT_NAMESPACE",
                "GIT_ATTR_SOURCE",
                "GIT_REPLACE_REF_BASE",
                "GIT_GRAFT_FILE",
                "GIT_SHALLOW_FILE",
            }
        ):
            errors.add("ENV_REDIRECT")
    try:
        candidates = config_candidates(request.layout)
        require(
            set(candidates) == set(request.layout.control_roots), "CONFIG_SCOPE", unavailable=True
        )
    except CaptureFault as error:
        fault(error)
        candidates = ()
    config_files = (
        *candidates,
        request.layout.common_dir + "/config",
        request.layout.git_dir + "/config.worktree",
    )
    for i, path in enumerate(config_files):
        try:
            raw, _ = read_file(path, budget, missing_ok=True)
            identities.append((f"config{i}", None if raw is None else digest(raw)))
            if raw is not None:
                inspect_config(raw, errors, missing, request.layout)
        except CaptureFault as error:
            fault(error)
    controls = (
        ("attributes", "info/attributes", True),
        ("grafts", "info/grafts", True),
        ("shallow", "shallow", False),
        ("alternates", "objects/info/alternates", False),
    )
    for n, path in enumerate(
        ("/etc/gitattributes", *(p.removesuffix("config") + "attributes" for p in candidates[-1:]))
    ):
        try:
            raw, _ = read_file(path, budget, missing_ok=True)
            identities.append((f"ambientattrs{n}", None if raw is None else digest(raw)))
            if raw:
                errors.add("ATTRIBUTE_OVERRIDE")
        except CaptureFault as error:
            fault(error)
    for label, relative, forbidden in controls:
        for n, base in enumerate(
            dict.fromkeys((request.layout.git_dir, request.layout.common_dir))
        ):
            try:
                raw, _ = read_file(base + "/" + relative, budget, missing_ok=True)
                identities.append((f"{label}{n}", None if raw is None else digest(raw)))
                if raw:
                    (errors if forbidden else missing).add(
                        "ATTRIBUTE_OVERRIDE" if label == "attributes" else label.upper()
                    )
            except CaptureFault as error:
                fault(error)
    for relative, code in (("refs/replace", "REPLACE_REFS"), ("objects/pack", "PARTIAL_CLONE")):
        try:
            with directory(request.layout.common_dir + "/" + relative) as fd:
                names = sorted(os.listdir(fd))
                if names if code == "REPLACE_REFS" else any(n.endswith(".promisor") for n in names):
                    (errors if code == "REPLACE_REFS" else missing).add(code)
                identities.append(
                    (code, digest("\0".join(names).encode("utf-8", "surrogateescape")))
                )
        except FileNotFoundError:
            identities.append((code, None))
        except CaptureFault as error:
            fault(error)
        except OSError:
            missing.add("CONTROL_IO")
    try:
        raw, _ = read_file(request.layout.common_dir + "/packed-refs", budget, missing_ok=True)
        identities.append(("packedrefs", None if raw is None else digest(raw)))
        if raw is not None and any(b" refs/replace/" in line for line in raw.split(b"\n")):
            errors.add("REPLACE_REFS")
    except CaptureFault as error:
        fault(error)
    return ControlCapture(tuple(sorted(identities)), tuple(sorted(errors)), tuple(sorted(missing)))


def read_head(
    request: CaptureRequest, budget: ReadBudget
) -> tuple[str | None, tuple[tuple[str, str | None], ...]]:
    raw, _ = read_file(request.layout.git_dir + "/HEAD", budget)
    assert raw is not None
    identities: list[tuple[str, str | None]] = [("HEAD", digest(raw))]
    if raw.startswith(b"ref: "):
        name = raw[5:].decode("utf-8").removesuffix("\n")
        require(
            path_value(name) and name.startswith("refs/") and not name.startswith("refs/replace/"),
            "HEAD_FORMAT",
        )
        direct, _ = read_file(request.layout.common_dir + "/" + name, budget, missing_ok=True)
        identities.append(("HEADref", None if direct is None else digest(direct)))
        if direct is None:
            packed, _ = read_file(
                request.layout.common_dir + "/packed-refs", budget, missing_ok=True
            )
            matches = (
                []
                if packed is None
                else [
                    line.split(b" ")[0]
                    for line in packed.split(b"\n")
                    if line.endswith(b" " + name.encode())
                ]
            )
            require(len(matches) == 1, "HEAD_UNAVAILABLE", unavailable=True)
            raw = matches[0]
        else:
            raw = direct
    value = raw.decode("ascii").removesuffix("\n")
    require(oid(value), "HEAD_FORMAT")
    return value, tuple(identities)


def read_worktree(
    request: CaptureRequest, tracked: tuple[tuple[str, bytes], ...], budget: ReadBudget
) -> WorktreeCapture:
    errors: set[str] = set()
    missing: set[str] = set()
    files: list[FileCapture] = []
    observed: set[str] = set()
    expected = dict(tracked)
    unknown: set[str] = set()

    def walk(fd: int, prefix: str) -> None:
        for name in sorted(os.listdir(fd)):
            budget.consume(0, 1)
            if not prefix and name == ".git":
                continue
            path = prefix + name
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if name == ".git":
                errors.add("NESTED_REPOSITORY")
                continue
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY, dir_fd=fd)
                try:
                    walk(child, path + "/")
                finally:
                    os.close(child)
            else:
                if path in observed:
                    errors.add("DUPLICATE_PATH")
                observed.add(path)
                if not stat.S_ISREG(info.st_mode):
                    errors.add("FILE_TYPE")
                if path not in expected:
                    unknown.add(digest(path.encode("utf-8", "surrogateescape")))

    try:
        verify_layout(request, budget)
        with directory(request.layout.worktree_root) as fd:
            walk(fd, "")
        try:
            TreeSnapshot(tuple((p, GitImage("100644", b"")) for p in observed))
        except ValueError:
            errors.add("UNSAFE_PATH")
        if unknown:
            errors.add("UNTRACKED_PATH")
        for path, raw in tracked:
            try:
                require(path_value(path), "UNSAFE_PATH")
                if path not in observed:
                    errors.add("TRACKED_MISSING")
                    continue
                value, identity = read_file(request.layout.worktree_root + "/" + path, budget)
                assert value is not None
                require(not identity[2] & 0o111, "FILE_MODE")
                if value != raw:
                    errors.add("RAW_BYTES_CHANGED")
                files.append(FileCapture(path, GitImage("100644", value), identity))
            except CaptureFault as error:
                (missing if error.unavailable else errors).add(error.reason)
    except CaptureFault as error:
        (missing if error.unavailable else errors).add(error.reason)
    except OSError:
        missing.add("WORKTREE_IO")
    return WorktreeCapture(
        tuple(files),
        tuple(sorted(observed & expected.keys())),
        tuple(sorted(unknown)),
        tuple(sorted(errors)),
        tuple(sorted(missing)),
    )


def _cache_tree(raw: bytes) -> None:
    def node(pos: int) -> int:
        zero = raw.index(b"\0", pos)
        name = raw[pos:zero]
        require(b"/" not in name and b"\n" not in name, "INDEX_TREE")
        end = raw.index(b"\n", zero)
        count, children = raw[zero + 1 : end].split(b" ")
        require(count == b"-1" or count.isdigit(), "INDEX_TREE")
        require(children.isdigit(), "INDEX_TREE")
        pos = end + 1 + (20 if int(count) >= 0 else 0)
        require(pos <= len(raw), "INDEX_TREE")
        for _ in range(int(children)):
            pos = node(pos)
        return pos

    require(node(0) == len(raw), "INDEX_TREE")


def parse_index(raw: bytes) -> IndexCapture:
    try:
        require(type(raw) is bytes and len(raw) >= 32 and raw[:4] == b"DIRC", "INDEX_FORMAT")
        require(sha1(raw[:-20]).digest() == raw[-20:], "INDEX_CHECKSUM")
        version, count = struct.unpack(">II", raw[4:12])
        require(version in (2, 3), "INDEX_VERSION", unavailable=True)
        pos, rows = 12, []
        for _ in range(count):
            start = pos
            require(pos + 62 <= len(raw) - 20, "INDEX_ENTRY")
            mode = struct.unpack(">I", raw[pos + 24 : pos + 28])[0]
            obj = raw[pos + 40 : pos + 60].hex()
            flags = struct.unpack(">H", raw[pos + 60 : pos + 62])[0]
            require(not flags & 0xF000, "INDEX_FLAGS")
            end = raw.index(b"\0", pos + 62, len(raw) - 20)
            name = raw[pos + 62 : end].decode("utf-8", "strict")
            require(flags & 4095 == min(len(raw[pos + 62 : end]), 4095), "INDEX_NAME")
            pos = start + ((end + 1 - start + 7) // 8) * 8
            require(pos <= len(raw) - 20 and not any(raw[end:pos]), "INDEX_PADDING")
            require(mode == 0o100644, "INDEX_MODE")
            rows.append(IndexEntry(name, "100644", obj, flags))
        # Validate the complete set before an unsupported extension/version can hide errors.
        TreeSnapshot(tuple((r.path, GitImage(r.mode, b"")) for r in rows))
        require([r.path for r in rows] == sorted(r.path for r in rows), "INDEX_ORDER")
        extensions: list[tuple[str, bytes]] = []
        unsupported = version != 2
        while pos < len(raw) - 20:
            require(pos + 8 <= len(raw) - 20, "INDEX_EXTENSION")
            signature, size = raw[pos : pos + 4], struct.unpack(">I", raw[pos + 4 : pos + 8])[0]
            pos += 8
            require(pos + size <= len(raw) - 20, "INDEX_EXTENSION")
            value = raw[pos : pos + size]
            pos += size
            if signature == b"TREE":
                require(not extensions, "INDEX_EXTENSION_DUPLICATE")
                _cache_tree(value)
                extensions.append(("TREE", value))
            else:
                unsupported = True
        require(not unsupported, "INDEX_FEATURE", unavailable=True)
        return IndexCapture(digest(raw), version, tuple(rows), tuple(extensions))
    except (ValueError, struct.error, RecursionError) as error:
        raise CaptureFault("INDEX_FORMAT") from error
