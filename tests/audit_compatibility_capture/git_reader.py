"""Explicit bounded,allowlisted local Git plumbing. Never a writer or executor bridge."""

import os
import selectors
import subprocess
import time

from tests.audit_compatibility.git_objects import (
    CommitObject,
    GitImage,
    TreeSnapshot,
    object_id,
    oid,
)

from .contracts import (
    AttributeCapture,
    CaptureFault,
    CaptureRequest,
    ObjectCapture,
    ReadBudget,
    digest,
    require,
)
from .worktree_reader import preflight, read_file

ATTR_NAMES = ("text", "eol", "filter", "ident", "working-tree-encoding", "merge", "diff", "binary")


def _allowed(args: tuple[str, ...]) -> bool:
    fixed = {
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--absolute-git-dir"),
        ("rev-parse", "--path-format=absolute", "--git-common-dir"),
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("cat-file", "--batch"),
        ("ls-files", "--stage", "-z"),
        ("ls-files", "--others", "-z"),
    }
    attrs = {
        ("check-attr", *cached, "-z", *tail)
        for cached in ((), ("--cached",))
        for tail in (("--all", "--stdin"), ("--stdin", *ATTR_NAMES))
    }
    return args in fixed | attrs or (
        len(args) == 4 and args[:3] == ("ls-tree", "-rz", "--full-tree") and oid(args[3])
    )


class GitReader:
    def __init__(self, request: CaptureRequest, budget: ReadBudget):
        require(type(request) is CaptureRequest, "REQUEST_TYPE")
        CaptureRequest.__post_init__(request)
        self.request, self.budget = request, budget
        self.controls = preflight(request, budget)
        self.cache: dict[str, tuple[str, bytes]] = {}
        self.missing: set[str] = set()

    def run(self, args: tuple[str, ...], raw: bytes = b"") -> bytes:
        require(
            type(args) is tuple and all(type(x) is str for x in args) and _allowed(args),
            "COMMAND_FORBIDDEN",
        )
        require(type(raw) is bytes, "INPUT_TYPE")
        require(
            not self.controls.errors and not self.controls.unavailable,
            "PREFLIGHT_BLOCKED",
            unavailable=True,
        )
        layout = self.request.layout
        env = dict(os.environ)
        env.update(
            GIT_NO_LAZY_FETCH="1",
            GIT_NO_REPLACE_OBJECTS="1",
            GIT_OPTIONAL_LOCKS="0",
            GIT_TERMINAL_PROMPT="0",
            GIT_ALLOW_PROTOCOL="",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_SYSTEM=os.devnull,
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_ATTR_NOSYSTEM="1",
        )
        command = [
            "/usr/bin/git",
            "--no-pager",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.attributesFile=" + os.devnull,
            "--git-dir=" + layout.git_dir,
            "--work-tree=" + layout.worktree_root,
            *args,
        ]
        deadline = time.monotonic_ns() + self.budget.limits.subprocess_timeout_ns
        process = None
        try:
            process = subprocess.Popen(
                command,
                cwd=layout.worktree_root,
                env=env,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert (
                process.stdin is not None
                and process.stdout is not None
                and process.stderr is not None
            )
            output: list[bytes] = []
            offset, total = 0, 0
            with selectors.DefaultSelector() as selector:
                for stream, name in ((process.stdout, "out"), (process.stderr, "err")):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, name)
                if raw:
                    os.set_blocking(process.stdin.fileno(), False)
                    selector.register(process.stdin, selectors.EVENT_WRITE, "in")
                else:
                    process.stdin.close()
                while selector.get_map():
                    remaining = deadline - time.monotonic_ns()
                    require(remaining > 0, "GIT_RESOURCE_LIMIT", unavailable=True)
                    for key, _ in selector.select(remaining / 1_000_000_000):
                        if key.data == "in":
                            offset += os.write(key.fd, raw[offset : offset + 65536])
                            if offset == len(raw):
                                selector.unregister(key.fileobj)
                                process.stdin.close()
                        else:
                            data = os.read(key.fd, 65536)
                            if not data:
                                selector.unregister(key.fileobj)
                                continue
                            total += len(data)
                            self.budget.consume(len(data))
                            require(
                                total <= self.budget.limits.maximum_output_bytes,
                                "GIT_RESOURCE_LIMIT",
                                unavailable=True,
                            )
                            if key.data == "out":
                                output.append(data)
            remaining = deadline - time.monotonic_ns()
            require(remaining > 0, "GIT_RESOURCE_LIMIT", unavailable=True)
            code = process.wait(timeout=remaining / 1_000_000_000)
            require(code == 0, "GIT_COMMAND_UNAVAILABLE", unavailable=True)
            return b"".join(output)
        except (OSError, subprocess.SubprocessError) as error:
            raise CaptureFault("GIT_IO", True) from error
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait()
                for closing in (process.stdin, process.stdout, process.stderr):
                    if closing is not None:
                        closing.close()

    def object(self, identity: str, expected: str) -> bytes:
        require(oid(identity), "OBJECT_ID")
        if identity not in self.cache:
            self.budget.consume(0, 1)
            result = self.run(("cat-file", "--batch"), identity.encode() + b"\n")
            header, sep, tail = result.partition(b"\n")
            require(bool(sep), "OBJECT_FRAME")
            if header == identity.encode() + b" missing":
                self.missing.add(identity)
                raise CaptureFault("OBJECT_MISSING", True)
            fields = header.split(b" ")
            require(
                len(fields) == 3 and fields[0] == identity.encode() and fields[2].isdigit(),
                "OBJECT_FRAME",
            )
            kind, size = fields[1].decode("ascii"), int(fields[2])
            require(
                kind in ("blob", "tree", "commit", "tag")
                and len(tail) == size + 1
                and tail[-1:] == b"\n",
                "OBJECT_FRAME",
            )
            value = tail[:-1]
            require(object_id(kind, value) == identity, "OBJECT_HASH")
            self.cache[identity] = (kind, value)
        kind, value = self.cache[identity]
        require(kind == expected, "OBJECT_TYPE")
        return value

    def tree(self, identity: str) -> TreeSnapshot:
        rows: list[tuple[str, GitImage]] = []

        def walk(tree: str, prefix: str) -> None:
            raw = self.object(tree, "tree")
            pos = 0
            while pos < len(raw):
                self.budget.consume(0, 1)
                end = raw.index(b"\0", pos)
                header = raw[pos:end].split(b" ")
                require(len(header) == 2 and b"/" not in header[1], "TREE_FRAME")
                mode, name = header[0], header[1].decode("utf-8", "strict")
                require(end + 21 <= len(raw), "TREE_FRAME")
                child = raw[end + 1 : end + 21].hex()
                pos = end + 21
                if mode == b"40000":
                    walk(child, prefix + name + "/")
                else:
                    require(mode == b"100644", "OBJECT_MODE")
                    rows.append((prefix + name, GitImage("100644", self.object(child, "blob"))))

        walk(identity, "")
        result = TreeSnapshot(tuple(rows))
        require(result.oid == identity, "TREE_HASH")
        listing = self.run(("ls-tree", "-rz", "--full-tree", identity))
        observed = []
        for row in listing.split(b"\0")[:-1]:
            header, name = row.split(b"\t", 1)
            mode, kind, obj = header.split(b" ")
            require(kind == b"blob", "TREE_FRAME")
            observed.append((name.decode("utf-8"), mode.decode(), obj.decode()))
        require(not listing or listing.endswith(b"\0"), "TREE_FRAME")
        require(
            sorted(observed) == [(p, image.mode, image.oid) for p, image in result.entries],
            "TREE_INVENTORY",
        )
        return result


def read_objects_with(reader: GitReader, identities: tuple[str, ...]) -> ObjectCapture:
    commits: dict[str, CommitObject] = {}
    trees: dict[str, TreeSnapshot] = {}
    errors, missing = set(reader.controls.errors), set(reader.controls.unavailable)
    if errors or missing:
        return ObjectCapture((), (), (), tuple(sorted(errors)), tuple(sorted(missing)))
    try:
        layout = reader.request.layout
        for args, wanted in (
            (("rev-parse", "--show-toplevel"), layout.worktree_root),
            (("rev-parse", "--absolute-git-dir"), layout.git_dir),
            (("rev-parse", "--path-format=absolute", "--git-common-dir"), layout.common_dir),
        ):
            require(reader.run(args).decode("utf-8").removesuffix("\n") == wanted, "GIT_LAYOUT")
    except CaptureFault as error:
        (missing if error.unavailable else errors).add(error.reason)
        return ObjectCapture((), (), (), tuple(sorted(errors)), tuple(sorted(missing)))
    pending, seen = list(identities), set()
    while pending:
        identity = pending.pop()
        if identity in seen:
            continue
        seen.add(identity)
        try:
            commit = CommitObject(reader.object(identity, "commit"))
            commits[identity] = commit
            pending.extend(commit.parents)
        except CaptureFault as error:
            (missing if error.unavailable else errors).add(error.reason)
        except ValueError:
            errors.add("COMMIT_FORMAT")
    for identity in identities:
        if identity not in commits:
            continue
        try:
            tree = reader.tree(commits[identity].tree)
            trees[tree.oid] = tree
        except CaptureFault as error:
            (missing if error.unavailable else errors).add(error.reason)
        except (ValueError, RecursionError):
            errors.add("TREE_FORMAT")
    return ObjectCapture(
        tuple(commits[k] for k in sorted(commits)),
        tuple(trees[k] for k in sorted(trees)),
        tuple(sorted(reader.missing)),
        tuple(sorted(errors)),
        tuple(sorted(missing)),
    )


def read_objects(request: CaptureRequest) -> ObjectCapture:
    reader = GitReader(request, ReadBudget(request.budget))
    ids = tuple(
        dict.fromkeys(
            (
                request.candidate_head,
                request.validation_head,
                *((request.declared_base,) if request.declared_base is not None else ()),
                *request.source_oids,
            )
        )
    )
    return read_objects_with(reader, ids)


def _expected_attributes(path: str) -> tuple[tuple[str, str], ...]:
    if path.startswith("src/cyberpilot_autotune/diagnostics/"):
        return (("eol", "lf"), ("text", "set"))
    if (
        path.startswith("tests/fixtures/actual_binding/")
        and "/" not in path.removeprefix("tests/fixtures/actual_binding/")
        and path.endswith(".zip")
    ):
        return (("binary", "set"), ("diff", "unset"), ("merge", "unset"), ("text", "unset"))
    return ()


def read_attributes(reader: GitReader, tree: TreeSnapshot) -> AttributeCapture:
    entries = dict(tree.entries)
    image = entries.get(".gitattributes")
    require(
        image is not None
        and digest(image.data)
        == "3da824d0f37be4082aecb38cef9b01c8f0b9e66ab67d574cfbe3b2e3553db908",
        "ATTRIBUTE_POLICY",
    )
    require(not any(p.endswith("/.gitattributes") for p in entries), "ATTRIBUTE_OVERRIDE")
    actual, _ = read_file(reader.request.layout.worktree_root + "/.gitattributes", reader.budget)
    require(image is not None and actual == image.data, "ATTRIBUTE_POLICY")
    names = tuple(entries)
    raw = b"".join(p.encode() + b"\0" for p in names)
    expected = {p: _expected_attributes(p) for p in names}
    for cached in ((), ("--cached",)):
        for all_values in (True, False):
            tail = ("--all", "--stdin") if all_values else ("--stdin", *ATTR_NAMES)
            result = reader.run(("check-attr", *cached, "-z", *tail), raw)
            require(not result or result.endswith(b"\0"), "ATTRIBUTE_FRAME")
            values = result.split(b"\0")[:-1]
            require(len(values) % 3 == 0, "ATTRIBUTE_FRAME")
            rows: dict[str, dict[str, str]] = {p: {} for p in names}
            for i in range(0, len(values), 3):
                path, attribute, value = (x.decode("utf-8", "strict") for x in values[i : i + 3])
                require(path in rows and attribute not in rows[path], "ATTRIBUTE_FRAME")
                rows[path][attribute] = value
            for p in names:
                wanted = (
                    dict(expected[p])
                    if all_values
                    else {n: dict(expected[p]).get(n, "unspecified") for n in ATTR_NAMES}
                )
                require(rows[p] == wanted, "ATTRIBUTE_OVERRIDE")
    return AttributeCapture(tuple(sorted(expected.items())))
