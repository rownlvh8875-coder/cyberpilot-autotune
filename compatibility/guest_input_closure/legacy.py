"""Read frozen legacy receipts through scoped, bounded no-follow observations."""

import hashlib
import json
import stat
from pathlib import Path
from typing import Any

from .contracts import InputEntry, InputSnapshot, relative_path
from .filesystem import read_regular, scan_selected
from .inventory import unique_object

BASE_PATH = "compatibility/containment_backend_harmless/host/build_manifest.json"
COLLECTOR_PATH = "compatibility/containment_guest_collector/guest/build_manifest.json"
BASE_SHA = "ccabaa75fede7b5d704301fad185a0c9efc306c8757426ea28d9bd05a7136e4e"
COLLECTOR_SHA = "1ce218b6b82dc36a6f347b8e744c90da08380dc1ec8a43bd51133a7532f9170a"
VM_DIGEST = "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c"


class _Verifier:
    def __init__(self, snapshot: InputSnapshot, roots: dict[str, Path]):
        self.observed = {(entry.root, entry.path): entry for entry in snapshot.entries}
        self.roots = dict(roots)

    def scoped(self, value: str) -> tuple[str, Path, str]:
        if type(value) is not str or not value or len(value) > 4096:
            raise ValueError("invalid legacy input path")
        candidate = Path(value)
        if not candidate.is_absolute():
            relative_path(value)
            return "repo_selected", self.roots["repo_selected"], value
        if ".." in candidate.parts:
            raise ValueError("legacy path traversal")
        for role, root in sorted(
            self.roots.items(), key=lambda row: len(row[1].parts), reverse=True
        ):
            if candidate.is_relative_to(root):
                relative = str(candidate.relative_to(root))
                relative_path(relative)
                if role == "host_gcc_selected" and (role, relative) not in self.observed:
                    continue
                return role, root, relative
        for role, root in (
            ("legacy_backend", self.roots["fixture_selected"].parent),
            ("legacy_vm", self.roots["vm_exact_tree"].parent),
        ):
            if candidate.is_relative_to(root):
                relative = str(candidate.relative_to(root))
                relative_path(relative)
                return role, root, relative
        raise ValueError("legacy path outside declared fixed roots")

    def check(self, record: dict[str, Any]) -> None:
        value = record.get("path", record.get("archive"))
        if type(value) is not str:
            raise ValueError("legacy record path unavailable")
        role, root, path = self.scoped(value)
        entry = self.observed.get((role, path))
        if entry is None:
            entry = next(e for e in scan_selected(role, root, (path,)) if e.path == path)
        if (
            entry.kind != "file"
            or entry.sha256 != record["sha256"]
            or ("bytes" in record and entry.size != record["bytes"])
        ):
            raise ValueError("legacy input content/kind mismatch: " + value)

    def bytes(self, record: dict[str, Any]) -> bytes:
        role, root, path = self.scoped(record["path"])
        self.check(record)
        data = read_regular(root, path, 32 * 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != record["sha256"] or len(data) != record["bytes"]:
            raise ValueError("consumed legacy asset differs from observed content")
        return data


def _manifest(root: Path, path: str, digest: str) -> dict[str, Any]:
    raw = read_regular(root, path, 32 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("legacy manifest content pin mismatch")
    result: dict[str, Any] = json.loads(raw, object_pairs_hook=unique_object)
    if type(result) is not dict:
        raise ValueError("legacy manifest is not an object")
    return result


def _verify_vm(checker: _Verifier) -> None:
    root = checker.roots["vm_exact_tree"].parent
    raw = read_regular(root, "cohort.json", 32 * 1024 * 1024)
    data = json.loads(raw, object_pairs_hook=unique_object)
    if type(data) is not dict or data.pop("content_digest", None) != VM_DIGEST:
        raise ValueError("legacy VM cohort identity mismatch")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != VM_DIGEST:
        raise ValueError("legacy VM cohort content mismatch")
    rows: dict[str, InputEntry] = {
        path: entry
        for (role, path), entry in checker.observed.items()
        if role == "vm_exact_tree" and path != "."
    }
    expected = {
        record["path"].removeprefix("sysroot/"): record for record in data["extracted_tree"]
    }
    if rows.keys() != expected.keys():
        raise ValueError("legacy VM tree membership mismatch")
    for path, record in expected.items():
        entry = rows[path]
        if entry.kind != record["kind"] or stat.S_IMODE(entry.mode) != record["mode"]:
            raise ValueError("legacy VM mode/kind mismatch")
        if entry.kind == "file" and (
            entry.sha256 != record["sha256"] or entry.size != record["bytes"]
        ):
            raise ValueError("legacy VM file mismatch")
        if entry.kind == "symlink" and entry.target != record["target"]:
            raise ValueError("legacy VM symlink mismatch")
    for record in data["packages"] + data["assets"] + data["signed_release_metadata"]:
        path = record.get("path", record.get("archive"))
        relative_path(path)
        checker.check({**record, "path": str(root / path)})


def load_checked_assets(
    snapshot: InputSnapshot, roots: dict[str, Path]
) -> tuple[dict[str, tuple[int, bytes]], bytes]:
    from compatibility.containment_backend_harmless.guest_image import GUEST_FILES

    checker = _Verifier(snapshot, roots)
    repo = roots["repo_selected"]
    base = _manifest(repo, BASE_PATH, BASE_SHA)
    collector = _manifest(repo, COLLECTOR_PATH, COLLECTOR_SHA)
    if collector["base_manifest_sha256"] != BASE_SHA:
        raise ValueError("legacy manifest linkage mismatch")
    for record in base["inputs"] + collector["inputs"]:
        checker.check(record)
    _verify_vm(checker)
    records = {record["path"]: record for record in base["inputs"]}
    files: dict[str, tuple[int, bytes]] = {}
    for record in base["guest_files"]:
        name = record["guest_path"]
        mode = 0o100444 if name == "guard.bpf.o" else 0o100755
        if name in files or name not in GUEST_FILES or record["mode"] != mode:
            raise ValueError("legacy guest asset identity mismatch")
        files[name] = (mode, checker.bytes(records[record["path"]]))
    if files.keys() != GUEST_FILES:
        raise ValueError("legacy guest asset missing")
    binary = next(
        record for record in collector["inputs"] if record["path"] == collector["collector_path"]
    )
    return files, checker.bytes(binary)
