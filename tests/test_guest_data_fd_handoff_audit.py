"""Breaks caught: replayed diagnostic bytes detached from fixed source/build cohort."""

import base64
import hashlib

import pytest

from tests.experiments.guest_data_fd_handoff import audit
from tests.test_guest_data_fd_handoff import PROGRAM, negative_rows, rows, serial


def manifest():
    return {
        "schema": "guest-data-fd-handoff-build-v1",
        "base_revision": "74e3fdc67c2695a48035bf51758721f48bd5ae05",
        "vm_cohort_digest": "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c",
        "binary": {"path": "data-fd-handoff-probe", "bytes": 800000, "sha256": PROGRAM},
        "sources": [{"path": p, "bytes": 10, "sha256": "b" * 64} for p in audit.SOURCES],
        "build_command": "cc fixed harmless static C only",
        "permissions": dict(audit.PERMISSIONS),
        "build_input_closure_qualified": False,
    }


def evidence(m, raw):
    captures = []
    for case in audit.CASES:
        text = serial(rows(case) if case in ("HH01", "HH07") else negative_rows(case))
        captures.append(
            {
                "case": case,
                "bytes": len(text),
                "sha256": hashlib.sha256(text).hexdigest(),
                "serial_base64": base64.b64encode(text).decode(),
                "image_sha256": "c" * 64,
            }
        )
    return {
        "schema": "guest-data-fd-handoff-actual-v1",
        "binary": m["binary"],
        "capture_source_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "captures": captures,
        "runtime_qualified": False,
    }


def test_fixed_capture_replays_are_diagnostics_only():
    m = manifest()
    audit.validate_build(m)
    result = audit.validate_evidence(evidence(m, b"manifest"), m, b"manifest")
    assert result == (7, 2)


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_qualified", True),
        ("capture_source_manifest_sha256", "d" * 64),
        ("captures", []),
        ("schema", "guest-input-handoff-v2"),
    ],
)
def test_evidence_never_promotes_unqualified_or_relabels_synthetic(field, value):
    m = manifest()
    e = evidence(m, b"manifest")
    e[field] = value
    with pytest.raises(ValueError):
        audit.validate_evidence(e, m, b"manifest")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["binary"].__setitem__("path", "/arbitrary/program"),
        lambda d: d["binary"].__setitem__("bytes", 800000.0),
        lambda d: d["sources"].append(d["sources"][0]),
        lambda d: d["permissions"].__setitem__("runtime_accepted", 0),
        lambda d: d.__setitem__("build_input_closure_qualified", True),
        lambda d: d.__setitem__("base_revision", "a" * 40),
    ],
)
def test_cannot_execute_unbound_or_qualified_build_manifest(mutate):
    m = manifest()
    mutate(m)
    with pytest.raises(ValueError):
        audit.validate_build(m)


def test_source_range_binds_full_original_blob_and_selected_bytes():
    raw = b"first\nsecond\nthird\n"
    row = {
        "path": "fs/proc/fd.c",
        "bytes": 19,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "git_blob_sha1": hashlib.sha1(b"blob 19\0" + raw).hexdigest(),
        "ranges": [
            {
                "claim": "target_flags",
                "start": 2,
                "end": 2,
                "sha256": hashlib.sha256(b"second\n").hexdigest(),
            }
        ],
    }
    audit.validate_kernel_record(row, raw)
    with pytest.raises(ValueError):
        audit.validate_kernel_record(row, raw.replace(b"second", b"SECOND"))
    row["ranges"][0]["start"] = 0
    with pytest.raises(ValueError):
        audit.validate_kernel_record(row, raw)


def test_published_original_actual_captures_match_current_bound_sources():
    import gzip
    import json

    m, raw = audit.load_build()
    data = json.loads(
        (audit.ROOT / audit.EVIDENCE).read_bytes()
        if not audit.EVIDENCE.endswith(".gz")
        else gzip.decompress((audit.ROOT / audit.EVIDENCE).read_bytes())
    )
    assert audit.validate_evidence(data, m, raw) == (7, 2)
    assert audit.validate_kernel(None) == (8, 12)


def test_offline_replay_does_not_require_linux_anchored_runtime_reader(monkeypatch):
    def unavailable(*args, **kwargs):
        raise ValueError("Linux anchored runtime reader unavailable")

    monkeypatch.setattr(audit, "read_regular", unavailable)
    m, _ = audit.load_build()
    assert m["schema"] == "guest-data-fd-handoff-build-v1"
    with pytest.raises(ValueError, match="Linux anchored runtime reader unavailable"):
        audit.load_build(anchored=True)
