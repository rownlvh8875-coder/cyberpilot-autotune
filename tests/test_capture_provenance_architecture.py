"""No source IO,H bridge,capability or scope expansion can hide in metadata checks."""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.fixtures.capture_provenance import document, registration
from tests.test_capture_provenance_scope import ADDITIONS, BASE, MODIFICATIONS

ROOT = Path(__file__).resolve().parents[1]


def test_pure_imports_and_closed_public_surface():
    directory = ROOT / "tests/audit_capture_provenance"
    siblings = {
        "__init__": {"contracts", "validation"},
        "contracts": set(),
        "validation": {"contracts"},
    }
    assert {p.stem for p in directory.glob("*.py")} == set(siblings)
    for path in directory.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(n.name in {"dataclasses", "typing"} for n in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (node.level == 1 and node.module in siblings[path.stem]) or (
                    node.level == 0 and node.module in {"dataclasses", "typing"}
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "open",
                    "exec",
                    "eval",
                    "compile",
                    "__import__",
                    "input",
                    "breakpoint",
                }
    from tests.audit_capture_provenance import __all__

    assert set(__all__) == {
        "CaptureEpoch",
        "WitnessContext",
        "CaptureWitness",
        "CaptureWitnessBundle",
        "CaptureIssue",
        "CaptureAlignmentDecision",
        "assess_capture_bundle",
    }


def test_fresh_import_and_assessment_have_no_effects_or_old_bridge():
    code = r"""
import dataclasses,typing,json,os,sys,time
doc=json.loads(sys.stdin.read())
def forbidden(*args,**kwargs): raise AssertionError("clock read")
for name in ("time","monotonic","monotonic_ns","perf_counter","perf_counter_ns"):
    setattr(time,name,forbidden)
locked=False
def audit(event,args):
    if event.startswith(("socket.","subprocess.","os.system","os.fork","os.exec",
                         "os.spawn","ctypes.","_thread.")):
        raise AssertionError(event)
    writes=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND
    if event=="open" and (locked or args[2]&writes):
        raise AssertionError("source IO")
sys.addaudithook(audit)
from tests.audit_capture_provenance import (CaptureEpoch,WitnessContext,CaptureWitness,
                                          CaptureWitnessBundle,assess_capture_bundle)
locked=True
def epoch(value): return None if value is None else CaptureEpoch(**value)
def context(value):
    return None if value is None else WitnessContext(**{**value,"epoch":epoch(value["epoch"])})
items=tuple(CaptureWitness(**{**w,"context":context(w["context"])}) for w in doc["witnesses"])
bundle=CaptureWitnessBundle(epoch(doc["epoch"]),doc["capture_begin_ns"],doc["capture_end_ns"],items)
result=assess_capture_bundle(bundle)
assert result.alignment_status=="COHORT_METADATA_CONSISTENT"
negative=dataclasses.replace(items[0],outcome="NEGATIVE_CLAIM")
changed=dataclasses.replace(bundle,witnesses=(negative,)+items[1:])
rejected=assess_capture_bundle(changed)
assert rejected.alignment_status=="REJECTED"
for r in (result,rejected):
    assert r.profile_record is None and r.H_executed is False
    assert r.integrated_admission is False and all(v is False for _,v in r.permissions)
assert not any(name.startswith(("cyberpilot_autotune","tests.audit_preparation_profile",
    "tests.audit_preflight_profile_mapping","tests.audit_compatibility",
    "tools.actions_runner_preflight")) for name in sys.modules)
print("PURE_SUPPLIED_METADATA_NO_SOURCE_IO_CLOCK_OR_H_RECEIPT")
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        input=json.dumps(document()),
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "PURE_SUPPLIED_METADATA_NO_SOURCE_IO_CLOCK_OR_H_RECEIPT"
    assert not result.stderr


def test_final_scope_and_embedded_catalog_are_closed_not_authority():
    rows = (
        subprocess.check_output(["git", "diff", "--no-renames", "--name-status", BASE], cwd=ROOT)
        .decode()
        .splitlines()
    )
    rows += [
        "A\t" + p
        for p in subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT
        )
        .decode()
        .splitlines()
    ]
    assert sorted(rows) == sorted(
        ["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS]
    )
    current = registration()
    assert (
        set(current["new_paths"]) == ADDITIONS and set(current["modified_paths"]) == MODIFICATIONS
    )
    previous = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                BASE + ":docs/evidence/audit_compatibility/"
                "preflight-profile-mapping-v1/registration.json",
            ],
            cwd=ROOT,
        )
    )
    assert set(previous["retained_blockers"]) <= set(current["retained_blockers"])
    assert current["permissions"] == previous["permissions"] and not any(
        current["permissions"].values()
    )
    assert current["profile_record"] is None and not current["manifest_is_authority"]
    assert not current["H_executed"] and not current["integrated_admission"]
    from tests.audit_capture_provenance.contracts import CATALOG

    expected = tuple(
        ((row["target_path"], r["role"]), tuple(r["allowed_stages"]), r["expected_command_id"])
        for row in current["catalog"]["rows"]
        for r in row["required_witnesses"]
    )
    assert CATALOG == expected and len(CATALOG) == 273
    assert len({k[0] for k, _, _ in CATALOG}) == 132


def test_all_old_nonconsumer_bytes_and_top_level_AST_preserved():
    changed = {
        "tests/test_audit_compatibility_history_architecture.py": (
            "test_all_earlier_files_and_guard_bytes_are_preserved"
        ),
        "tests/test_preflight_profile_mapping_architecture.py": (
            "test_final_scope_is_exact_and_manifest_cannot_grant_authority"
        ),
    }
    for path, allowed in changed.items():
        old = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT).decode()
        new = (ROOT / path).read_text()
        a, b = ast.parse(old), ast.parse(new)
        af = {n.name: n for n in a.body if isinstance(n, ast.FunctionDef)}
        bf = {n.name: n for n in b.body if isinstance(n, ast.FunctionDef)}
        assert af.keys() == bf.keys()
        for name, node in af.items():
            if name != allowed:
                assert ast.get_source_segment(old, node) == ast.get_source_segment(new, bf[name])
        assert [ast.dump(n) for n in a.body if not isinstance(n, ast.FunctionDef)] == [
            ast.dump(n) for n in b.body if not isinstance(n, ast.FunctionDef)
        ]
