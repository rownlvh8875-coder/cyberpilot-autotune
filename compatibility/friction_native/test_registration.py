"""Real exact-source Git reconstruction; mandatory source job, no services."""

import hashlib
import importlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from compatibility.friction_native import bundle


def registration():
    path = bundle.ROOT / "compatibility/friction_native/registration.py"
    assert path.is_file(), "OFFLINE_REGISTRATION_MISSING"
    return importlib.import_module("compatibility.friction_native.registration")


def snapshot(reference):
    return {
        str(p.relative_to(reference)): (p.stat().st_size, p.stat().st_mtime_ns)
        for p in reference.rglob("*")
        if p.is_file()
    }


@pytest.fixture(scope="module")
def source():
    return Path(os.environ["FRICTION_NATIVE_REFERENCE"])


def test_registration_is_reproducible_and_never_writes_reference(source, monkeypatch):
    module = registration()
    before = snapshot(source)
    # Ambient Git selectors must not redirect writes or select replace refs.
    monkeypatch.setenv("GIT_DIR", "/does/not/exist")
    monkeypatch.setenv("GIT_WORK_TREE", "/does/not/exist")
    monkeypatch.setenv("GIT_INDEX_FILE", "/does/not/exist/index")
    first = module.prepare(source)
    second = module.prepare(source)
    assert first == second
    assert snapshot(source) == before
    assert first["native_parent"] == bundle.PIN
    assert first["native_base_tree"] == "ffb213d9fdc0f9618264822bd2a4e26263abfe74"
    assert first["offline_candidate_revision"] not in {
        bundle.PIN,
        "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
    }
    module.verify(json.loads(module.RECORD.read_text()), source)


def test_complete_applied_tree_matches_independent_index_reconstruction(source, tmp_path):
    module = registration()
    record = module.prepare(source)
    # Independent path: git read-tree/update-index/write-tree, NOT the builder's
    # recursive mktree algorithm. Writes only a temporary object DB and index.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    command = ["git", "--no-replace-objects", "-C", str(source)]
    objects = (
        subprocess.check_output(
            command + ["rev-parse", "--path-format=absolute", "--git-path", "objects"], env=env
        )
        .decode()
        .strip()
    )
    (tmp_path / "objects").mkdir()
    env.update(
        GIT_OBJECT_DIRECTORY=str(tmp_path / "objects"),
        GIT_ALTERNATE_OBJECT_DIRECTORIES=objects,
        GIT_INDEX_FILE=str(tmp_path / "index"),
        GIT_NO_LAZY_FETCH="1",
        GIT_ALLOW_PROTOCOL="",
    )

    def git(*args, data=None):
        return subprocess.check_output(command + list(args), env=env, input=data)

    git("read-tree", bundle.PIN)
    revised = bundle.instrument(bundle.originals(source))
    for path, raw in revised.items():
        oid = git("hash-object", "-w", "--stdin", data=raw).decode().strip()
        git("update-index", "--add", "--cacheinfo", f"100644,{oid},{path}")
    assert git("write-tree", "--missing-ok").decode().strip() == record["native_applied_tree"]
    payload = record["synthetic_commit_payload"].encode()
    revision = git("hash-object", "-t", "commit", "-w", "--stdin", data=payload).decode().strip()
    assert revision == record["offline_candidate_revision"]
    assert payload.splitlines()[1] == b"parent " + bundle.PIN.encode()
    assert (
        hashlib.sha1(b"commit " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        == revision
    )
    changed = (
        git("diff-tree", "--no-commit-id", "--name-status", "-r", bundle.PIN, revision)
        .decode()
        .splitlines()
    )
    assert {line.split("\t")[1] for line in changed} == set(bundle.EDIT_PATHS)
    assert sum(line.startswith("A\t") for line in changed) == 1
    assert sum(line.startswith("M\t") for line in changed) == 6


def test_schema_root_digest_is_not_confused_with_transitive_schema_closure(source):
    module = registration()
    record = module.prepare(source)
    after = bundle.instrument(bundle.originals(source))
    assert (
        record["source_schema_digest"]
        == hashlib.sha256(after["openpilot/cereal/log.capnp"]).hexdigest()
    )
    assert (
        record["source_schema_digest"]
        == "00ca3b61347659b2515d36efe26cedff57965ca9610e15fe6b2cafdeaefe3b77"
    )
    assert {entry["path"] for entry in record["schema_closure"]} == {
        "openpilot/cereal/custom.capnp",
        "openpilot/cereal/log.capnp",
        "openpilot/cereal/deprecated.capnp",
        "openpilot/cereal/include/c++.capnp",
        "opendbc_repo/opendbc/car/car.capnp",
    }
    assert record["schema_closure_digest"] != record["source_schema_digest"]


def test_altered_record_is_rejected_even_with_valid_parent_or_digest(source):
    module = registration()
    record = module.prepare(source)
    record["runtime_accepted"] = True
    with pytest.raises(ValueError, match="REGISTRATION_CONTENT_MISMATCH"):
        module.verify(record, source)


def test_missing_base_never_fetches_or_creates_reference(tmp_path):
    module = registration()
    source = tmp_path / "empty.git"
    subprocess.run(["git", "init", "--bare", "--quiet", str(source)], check=True)
    before = snapshot(source)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        module.prepare(source)
    assert snapshot(source) == before


def test_sha256_repository_does_not_get_misread_as_pinned_sha1_native(tmp_path):
    module = registration()
    subprocess.run(
        ["git", "init", "--bare", "--object-format=sha256", "--quiet", str(tmp_path)],
        check=True,
    )
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="SHA1_NATIVE_REFERENCE_REQUIRED"):
        module.prepare(tmp_path)
    assert snapshot(tmp_path) == before


def test_cli_checks_evidence_and_prints_only_offline_content(source, capsys, monkeypatch, tmp_path):
    module = registration()
    args = ["--reference-checkout", str(source)]
    assert module.main(args) == 0
    assert "no runtime/empirical/application approval" in capsys.readouterr().out
    assert module.main(args + ["--print-record"]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["registration_scope"] == "OFFLINE_CONTENT_ONLY"
    record["native_parent"] = record["offline_candidate_revision"]
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(record))
    monkeypatch.setattr(module, "RECORD", path)
    assert module.main(args) == 1
    assert "OFFLINE_REGISTRATION_REJECTED" in capsys.readouterr().err


def test_every_previous_committed_file_is_preserved_exactly():
    module = registration()
    changed = (
        subprocess.check_output(
            ["git", "-C", str(bundle.ROOT), "diff", "--name-status", module.BASE, "--"]
        )
        .decode()
        .splitlines()
    )
    assert all(line.startswith("A\t") for line in changed), changed
