"""H6 evidence rejects mutation, misbinding and post-comparison policy selection."""

import copy
import json
import subprocess
from pathlib import Path

import pytest

from tests.audit import validate_friction_model as audit

ROOT = Path(__file__).resolve().parents[2]


def test_frozen_sources_policy_history_and_results_are_reproducible():
    source = json.loads((ROOT / audit.SOURCE_PATH).read_text())
    audit.validate_sources(source)
    audit.verify_history()
    audit.validate_results(json.loads((ROOT / audit.RESULT_PATH).read_text()))


@pytest.mark.parametrize(
    "mutation", ["pin", "hash", "range", "file_set", "authority", "freeze", "absence", "dynamic"]
)
def test_source_manifest_rejects_wrong_pin_hash_ranges_and_authority(mutation):
    source = json.loads((ROOT / audit.SOURCE_PATH).read_text())
    if mutation == "pin":
        source["files"][0]["revision"] = "main"
    elif mutation == "hash":
        source["files"][0]["sha256"] = "bad"
    elif mutation == "range":
        source["files"][0]["ranges"][0]["start"] = 0
    elif mutation == "file_set":
        source["files"].pop()
    elif mutation == "authority":
        source["application_authorized"] = True
    elif mutation == "freeze":
        source["policy_freeze_commit"] = source["base"]
    elif mutation == "absence":
        source["static_runtime_dynamic_geometry_absent"] = False
    else:
        source["current_dynamic_geometry_path_present"] = False
    with pytest.raises(ValueError):
        audit.validate_sources(source)


def test_results_reject_scientific_and_numeric_mutations():
    result = json.loads((ROOT / audit.RESULT_PATH).read_text())
    for mode in ("authority", "selected_model", "coefficient", "scenario", "hash", "geometry"):
        mutated = copy.deepcopy(result)
        if mode == "authority":
            mutated["authority"]["application_authorized"] = True
        elif mode == "selected_model":
            mutated["selected_model"] = "controller"
        elif mode == "coefficient":
            mutated["scenarios"][0]["models"]["controller"]["estimate"] = 0.8
        elif mode == "scenario":
            mutated["scenarios"].pop()
        elif mode == "hash":
            mutated["scenarios"][0]["input_sha256"] = "0" * 64
        else:
            mutated["geometry"]["comparisons"][1]["ratio"] = 0.6
        with pytest.raises(ValueError):
            audit.validate_results(mutated)


def test_coverage_requires_separate_statement_and_branch_floors():
    for statements, branches, expected in ((98, 95, True), (97, 99, False), (100, 94, False)):
        report = {
            "files": {
                "src/research/friction_model/candidates.py": {
                    "summary": {
                        "num_statements": 100,
                        "covered_lines": statements,
                        "num_branches": 100,
                        "covered_branches": branches,
                    }
                }
            }
        }
        if expected:
            audit.check_coverage(report)
        else:
            with pytest.raises(ValueError, match="COVERAGE"):
                audit.check_coverage(report)


def test_pr_virtual_merge_still_orders_topic_preregistration_first(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)

    def git(*args, data=None):
        return (
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(tmp_path),
                    "-c",
                    "user.name=H6 test",
                    "-c",
                    "user.email=h6@example.invalid",
                    *args,
                ],
                input=data,
            )
            .decode()
            .strip()
        )

    tree = git("hash-object", "-t", "tree", "-w", "--stdin", data=b"")
    base = git("commit-tree", tree, "-m", "base")
    freeze = git("commit-tree", tree, "-p", base, "-m", "topic freeze")
    result = git("commit-tree", tree, "-p", freeze, "-m", "topic result")
    merge = git("commit-tree", tree, "-p", base, "-p", result, "-m", "PR virtual merge")
    assert audit.history_order(tmp_path, base, merge) == [freeze, result, merge]
