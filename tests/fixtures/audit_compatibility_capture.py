"""Test-only prepared repositories and hand-framed Git index vectors."""

import importlib
import importlib.util
import os
import struct
import subprocess
from hashlib import sha1
from pathlib import Path


def api(name):
    assert importlib.util.find_spec("tests.audit_compatibility_capture") is not None, (
        "reader absent"
    )
    return importlib.import_module("tests.audit_compatibility_capture." + name)


def index_bytes(
    rows=(("a", 0o100644, "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", 0),),
    *,
    version=2,
    extension=b"",
):
    entries = []
    for path, mode, oid, flags in rows:
        name = path.encode()
        row = struct.pack(">10I", 0, 0, 0, 0, 0, 0, mode, 0, 0, 0) + bytes.fromhex(oid)
        row += struct.pack(">H", flags | min(len(name), 4095)) + name + b"\0"
        row += b"\0" * (-len(row) % 8)
        entries.append(row)
    raw = b"DIRC" + struct.pack(">II", version, len(entries)) + b"".join(entries) + extension
    return raw + sha1(raw).digest()


ATTRIBUTES = (
    b"# Keep the relocated frozen runtime's exact LF byte identities on every platform.\n"
    b"src/cyberpilot_autotune/diagnostics/** text eol=lf\n"
    b"# Historical source fixture, never a platform-normalized active source tree.\n"
    b"tests/fixtures/actual_binding/*.zip binary\n"
)


def git(root, *args, input=None):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], input=input, stderr=subprocess.PIPE
    )


def prepared(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "--quiet")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "core.autocrlf", "false")
    (root / ".gitattributes").write_bytes(ATTRIBUTES)
    (root / "a").write_bytes(b"hello\n")
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "TEST_ONLY")
    return root


def request(root, **changes):
    c = api("contracts")
    gitdir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    common = Path(
        git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip()
    )
    head = git(root, "rev-parse", "HEAD").decode().strip()
    configs = (
        "/etc/gitconfig",
        str(Path(os.environ["HOME"]) / ".gitconfig"),
        str(
            Path(os.environ.get("XDG_CONFIG_HOME", str(Path(os.environ["HOME"]) / ".config")))
            / "git/config"
        ),
    )
    layout = c.RepoLayout(str(root), str(gitdir), str(common), configs)
    values = dict(
        candidate_head=head,
        validation_head=head,
        declared_base=None,
        source_oids=(head,),
        layout=layout,
        budget=c.CaptureBudget(8_000_000, 64_000_000, 50_000, 5_000_000_000),
    )
    values.update(changes)
    return c.CaptureRequest(**values)
