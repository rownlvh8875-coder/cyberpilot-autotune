"""Published current-state inventory is reproducible text, not a historical seal."""

import gzip
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from compatibility.guest_input_closure.contracts import MANDATORY_BLOCKERS
from compatibility.guest_input_closure.inventory import parse_snapshot, snapshot_digest

ROOT = Path(__file__).resolve().parents[2]


def evidence():
    path = ROOT / "docs/evidence/guest_input_closure_result.json"
    assert path.is_file(), "current closure evidence missing"
    return json.loads(path.read_text())


def test_published_current_snapshot_is_exactly_hash_bound_and_not_a_history_receipt():
    data = evidence()
    record = data["snapshot"]
    compressed = (ROOT / record["path"]).read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == record["sha256"]
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == record["uncompressed_sha256"]
    snapshot = parse_snapshot(raw.decode())
    assert snapshot_digest(snapshot) == record["content_digest"]
    assert len(snapshot.entries) == 11351 == data["report"]["entry_count"]
    assert data["provenance"] == "CURRENT_RECONSTRUCTION_NOT_HISTORICAL_CONSUMPTION"
    assert data["actual_vm_or_target_execution"] is False


def test_current_matching_inputs_do_not_clear_any_qualification_blocker():
    report = evidence()["report"]
    assert (
        report["declared_inputs_match"] is True and report["guest_elf_dependencies_closed"] is True
    )
    assert report["overall_status"] == "BLOCKED" and report["issues"] == []
    assert set(report["blockers"]) == set(MANDATORY_BLOCKERS)
    for key in (
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert report[key] is False
    assert report["successful_prohibited_handles"] is None
    assert report["successful_prohibited_effects"] is None


def test_exact_tree_and_selected_inputs_are_not_conflated_with_whole_host_closure():
    roots = {r["root"]: r for r in evidence()["root_scopes"]}
    assert roots["toolchain_exact_tree"]["coverage"] == "EXACT_TREE"
    assert roots["vm_exact_tree"]["coverage"] == "EXACT_TREE"
    assert roots["host_gcc_selected"]["coverage"] == "SELECTED_FILES_NOT_SEARCH_CLOSURE"
    assert roots["repo_selected"]["coverage"] == "SELECTED_FILES_NOT_SEARCH_CLOSURE"
    assert len(roots) == 7


def test_all_24_current_images_have_the_recorded_graph_without_redistributing_binaries():
    data = evidence()
    assert [row["fixture_id"] for row in data["images"]] == [f"HF{i:02d}" for i in range(1, 25)]
    assert [row["sha256"] for row in data["images"]] == data["report"]["image_digests"]
    assert all(row["member_count"] == 32 for row in data["images"])
    assert len(data["report"]["dependency_edges"]) == 15
    assert ["harmless-fixtures", "NEEDED:libbpf.so.1", "lib/x86_64-linux-gnu/libbpf.so.1"] in data[
        "report"
    ]["dependency_edges"]
    assert len(data["elf_objects"]) == 11
    assert data["raw_binaries_published"] is False


def test_published_verifier_source_hashes_are_exact_current_bytes():
    for row in evidence()["verifier_sources"]:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]


@pytest.mark.parametrize(
    "path",
    [
        "docs/evidence/guest_input_closure_result.json",
        "compatibility/guest_input_closure/evidence/current-snapshot.json.gz",
        "compatibility/guest_input_closure/elf.py",
    ],
)
def test_new_hash_bound_artifacts_and_sources_survive_autocrlf_checkout(path):
    assert (
        subprocess.check_output(
            ["git", "check-attr", "text", "--", path], cwd=ROOT, text=True
        ).strip()
        == f"{path}: text: unset"
    )
