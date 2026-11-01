"""Synthetic external-asset fixtures; not build or acquisition evidence."""

import copy
import hashlib
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.guest_closure import elf_bytes


def api():
    assert importlib.util.find_spec("tests.deny_fd_v2_harness") is not None, "harness required"
    return importlib.import_module("tests.deny_fd_v2_harness.assets")


def synthetic_assets(monkeypatch):
    """Bind controlled unit-test assets; no real VM/probe is substituted on disk."""
    a = api()
    profile = copy.deepcopy(a.PROFILE)
    probe = elf_bytes(elf_type=2) + b"synthetic-probe"
    busybox = elf_bytes(elf_type=2) + b"synthetic-busybox"
    for key, raw in (("probe", probe), ("busybox", busybox)):
        profile[key] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    record = {
        "schema": "deny-fd-v2-compile-record-v1",
        "source_revision": profile["source_revision"],
        "source_manifest_digest": profile["source_manifest_digest"],
        "compiler_version": "synthetic compiler; never invoked",
        "command": ["/usr/bin/cc", "synthetic compile-only provenance"],
        "binary": {"path": "deny-fd-v2-probe", **profile["probe"]},
        "runtime_qualified": False,
        "build_input_closure_qualified": False,
        "permissions": dict(a.PERMISSIONS),
    }
    raw_record = json.dumps(record, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    profile["build_record_sha256"] = hashlib.sha256(raw_record).hexdigest()
    monkeypatch.setattr(a, "PROFILE", profile)
    files = {"deny-fd-v2-probe": probe, "build-record.json": raw_record}

    def read(root, path, limit):
        if root == a.ROOT and path == a.MANIFEST:
            return json.dumps(profile, sort_keys=True).encode()
        assert root == a.PROBE_ROOT and path in files and 0 < limit <= 4 * 1024 * 1024
        return files[path]

    monkeypatch.setattr(a, "read_regular", read)
    monkeypatch.setattr(a, "_vm_busybox", lambda: busybox)
    monkeypatch.setattr(
        a,
        "_producer_identity",
        lambda: (
            profile["source_revision"],
            profile["source_manifest_digest"],
        ),
    )
    return a, files, record


def test_fixed_preflight_preserves_relocated_historical_record(monkeypatch):
    a, files, _ = synthetic_assets(monkeypatch)
    before = files["build-record.json"]
    bundle = a.preflight()
    assert bundle.probe == files["deny-fd-v2-probe"]
    assert bundle.source_revision == "2481b84405beda95a394d1ca0248d7c9d632d28b"
    assert files["build-record.json"] == before
    assert all(value is False for _, value in bundle.permissions)
    with pytest.raises(FrozenInstanceError):
        bundle.probe = b"other"


@pytest.mark.parametrize("name", ("deny-fd-v2-probe", "build-record.json"))
def test_missing_or_changed_asset_fails_closed(monkeypatch, name):
    a, files, _ = synthetic_assets(monkeypatch)
    files[name] += b"changed"
    with pytest.raises(ValueError):
        a.preflight()


@pytest.mark.parametrize("failure", (OSError("missing asset"), ValueError("VM tree drift")))
def test_complete_vm_tree_failure_is_not_downgraded(monkeypatch, failure):
    a, _, _ = synthetic_assets(monkeypatch)

    def fail():
        raise failure

    monkeypatch.setattr(a, "_vm_busybox", fail)
    with pytest.raises(ValueError):
        a.preflight()


@pytest.mark.parametrize("mutation", ("extra", "true", "number", "duplicate", "nonfinite"))
def test_manifest_cannot_change_the_fixed_profile(monkeypatch, mutation):
    a, _, _ = synthetic_assets(monkeypatch)
    data = copy.deepcopy(a.PROFILE)
    if mutation == "extra":
        data["extra"] = "not permitted"
    elif mutation == "true":
        data["runtime_qualified"] = True
    elif mutation == "number":
        data["runtime_qualified"] = 0
    raw = json.dumps(data).encode()
    if mutation == "duplicate":
        raw = b'{"schema":"duplicate",' + raw[1:]
    if mutation == "nonfinite":
        raw = b'{"bad":NaN}'
    original = a.read_regular
    monkeypatch.setattr(
        a, "read_regular", lambda r, p, n: raw if r == a.ROOT else original(r, p, n)
    )
    with pytest.raises(ValueError):
        a.preflight()


@pytest.mark.parametrize("value", (b"", bytearray(b"x"), None, 0, False))
def test_bundle_does_not_coerce_unknown_or_mutable_payload(monkeypatch, value):
    a, _, _ = synthetic_assets(monkeypatch)
    with pytest.raises(ValueError):
        replace(a.preflight(), probe=value)


def test_tampered_source_identity_blocks_preparation(monkeypatch):
    a, _, _ = synthetic_assets(monkeypatch)
    monkeypatch.setattr(a, "_producer_identity", lambda: ("0" * 40, "0" * 64))
    with pytest.raises(ValueError):
        a.preflight()


@pytest.mark.parametrize("key", ("runtime_qualified", "build_input_closure_qualified"))
def test_compile_record_cannot_grant_runtime_or_closure(monkeypatch, key):
    a, files, record = synthetic_assets(monkeypatch)
    record[key] = True
    files["build-record.json"] = json.dumps(record).encode()
    # Bind the synthetic unit profile to reach the semantic guard, not authenticity.
    a.PROFILE["build_record_sha256"] = hashlib.sha256(files["build-record.json"]).hexdigest()
    with pytest.raises(ValueError):
        a.preflight()
