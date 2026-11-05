"""Read-only snapshot byte check; no provenance/authority or execution grant."""

import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "CLOUD_SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
assert manifest["schema"] == 1 and manifest["source_file_count"] == 135
assert manifest["source_revision"] == "f9490bb7d3d1b605f309cde5441ca3f561969325"
assert len(manifest["files"]) == 135
for name, expected in manifest["files"].items():
    rel = PurePosixPath(name)
    assert not rel.is_absolute() and all(part not in {".", ".."} for part in rel.parts)
    assert str(rel) == name and "\\" not in name
    path = ROOT
    for part in rel.parts:
        path = path / part
        assert not path.is_symlink(), name
    assert path.is_file() and path.stat().st_size <= 1_000_000, name
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected["sha256"], name
    blob = b"blob " + str(len(raw)).encode() + b"\0" + raw
    assert hashlib.sha1(blob).hexdigest() == expected["git_blob_sha1"], name
latest = json.loads((ROOT / "evidence_factory_intent.json").read_text(encoding="utf-8"))
assert len(latest["flags"]) == 14 and all(v is False for v in latest["flags"].values())
assert latest["provider_registration"] == "UNBOUND"
assert latest["qualification_required"] == 16 and latest["qualification_available"] == 0
print(
    json.dumps(
        {
            "status": "SOURCE_BYTES_MATCH_NOT_QUALIFICATION",
            "source_files_verified": 135,
            "source_revision": manifest["source_revision"],
            "provider_registration": "UNBOUND",
            "qualification_available": 0,
        }
    )
)
