"""Immutable provided Git objects. No Git invocation, filesystem or trust claim."""

import re
from dataclasses import dataclass
from hashlib import sha1, sha256


def require(value: bool) -> None:
    if not value:
        raise ValueError("invalid supplied Git value")


def oid(value: object) -> bool:
    return type(value) is str and re.fullmatch("[0-9a-f]{40}", value) is not None


def object_id(kind: str, raw: bytes) -> str:
    return sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def path_value(value: object) -> bool:
    if type(value) is not str or not value or any(c in value for c in "\\\0\r\n:*?[]"):
        return False
    try:
        value.encode("utf-8", "strict")
    except UnicodeError:
        return False
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{n}{i}" for n in ("COM", "LPT") for i in range(1, 10)
    }
    return all(
        p not in ("", ".", "..")
        and p.lower() != ".git"
        and p[-1:] not in (".", " ")
        and p.split(".")[0].upper() not in reserved
        for p in value.split("/")
    )


@dataclass(frozen=True, slots=True)
class GitImage:
    mode: str
    data: bytes

    def __post_init__(self) -> None:
        require(type(self.mode) is str and self.mode in ("100644", "100755"))
        require(type(self.data) is bytes)

    @property
    def oid(self) -> str:
        return object_id("blob", self.data)

    @property
    def sha256(self) -> str:
        return sha256(self.data).hexdigest()


type Node = dict[str, GitImage | Node]


def _tree_id(node: Node) -> str:
    rows = []
    for name, value in node.items():
        if isinstance(value, dict):
            mode, digest, key = "40000", _tree_id(value), name.encode() + b"/"
        else:
            mode, digest, key = value.mode, value.oid, name.encode()
        rows.append((key, mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(digest)))
    return object_id("tree", b"".join(raw for _, raw in sorted(rows)))


@dataclass(frozen=True, slots=True)
class TreeSnapshot:
    entries: tuple[tuple[str, GitImage], ...]

    def __post_init__(self) -> None:
        require(type(self.entries) is tuple)
        seen: set[str] = set()
        prefixes: dict[str, str] = {}
        for pair in self.entries:
            require(type(pair) is tuple and len(pair) == 2)
            path, image = pair
            require(path_value(path) and type(image) is GitImage)
            GitImage.__post_init__(image)
            require(path.casefold() not in seen)
            seen.add(path.casefold())
            for i in range(1, len(path.split("/")) + 1):
                prefix = "/".join(path.split("/")[:i])
                require(prefixes.setdefault(prefix.casefold(), prefix) == prefix)
        require(
            not any(
                "/".join(p.split("/")[:i]).casefold() in seen
                for p, _ in self.entries
                for i in range(1, len(p.split("/")))
            )
        )
        object.__setattr__(self, "entries", tuple(sorted(self.entries)))

    @property
    def oid(self) -> str:
        root: Node = {}
        for path, image in self.entries:
            node = root
            parts = path.split("/")
            for part in parts[:-1]:
                child = node.setdefault(part, {})
                assert isinstance(child, dict)
                node = child
            node[parts[-1]] = image
        return _tree_id(root)


def _commit_parts(raw: bytes) -> tuple[str, tuple[str, ...]]:
    require(type(raw) is bytes and b"\n\n" in raw and b"\0" not in raw)
    lines = raw.split(b"\n\n", 1)[0].splitlines()
    require(bool(lines) and lines[0].startswith(b"tree "))
    try:
        tree = lines[0][5:].decode("ascii")
        parents = []
        other_header = False
        for line in lines[1:]:
            require(not line.startswith(b"tree "))
            if line.startswith(b"parent "):
                require(not other_header)
                parents.append(line[7:].decode("ascii"))
            else:
                other_header = True
    except UnicodeError as error:
        raise ValueError("invalid commit header") from error
    require(oid(tree) and all(oid(p) for p in parents) and len(set(parents)) == len(parents))
    return tree, tuple(parents)


@dataclass(frozen=True, slots=True)
class CommitObject:
    raw: bytes

    def __post_init__(self) -> None:
        _commit_parts(self.raw)

    @property
    def oid(self) -> str:
        return object_id("commit", self.raw)

    @property
    def tree(self) -> str:
        return _commit_parts(self.raw)[0]

    @property
    def parents(self) -> tuple[str, ...]:
        return _commit_parts(self.raw)[1]
