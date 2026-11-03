"""No mapper result or import obtains a receipt,IO capability,or wider phase scope."""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.fixtures.preflight_profile_mapping import registration, source_bytes
from tests.test_preflight_profile_mapping_scope import ADDITIONS, BASE, MODIFICATIONS

ROOT = Path(__file__).resolve().parents[1]


def test_pure_package_imports_only_stdlib_and_exact_siblings():
    package = ROOT / "tests/audit_preflight_profile_mapping"
    allowed = {"__init__": {"contracts", "mapping"}, "contracts": set(), "mapping": {"contracts"}}
    assert {p.stem for p in package.glob("*.py")} == set(allowed)
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(
                    n.name in {"dataclasses", "hashlib", "json", "re", "typing"} for n in node.names
                )
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1 and node.module in allowed[path.stem]
                else:
                    assert node.module in {"dataclasses", "hashlib", "json", "re", "typing"}
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "open",
                    "eval",
                    "exec",
                    "compile",
                    "__import__",
                    "input",
                    "breakpoint",
                }


def test_fresh_import_call_and_redaction_have_no_effects_or_old_bridge():
    code = r"""
import json,os,sys
data=json.loads(sys.stdin.read())
def audit(event,args):
    forbidden=("socket.","subprocess.","os.system","os.fork","os.exec","os.spawn",
               "ctypes.","_thread.")
    if event.startswith(forbidden):
        raise AssertionError(event)
    writes=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND
    if event=="open" and args[2]&writes:
        raise AssertionError("file write")
sys.addaudithook(audit)
from tests.audit_preflight_profile_mapping import map_registered_preflight,PreflightRunBinding
binding=PreflightRunBinding(**data["binding"])
result=map_registered_preflight(data["source"].encode(),binding,
                              source_profile_id="SYNTHETIC_MAPPING_S0")
assert result.source_consistency=="REGISTERED_SNAPSHOT_MATCH"
assert result.profile_record is None and not result.H_executed
assert not result.integrated_admission and all(v is False for _,v in result.permissions)
assert len(result.diagnostics)==83 and len(result.target_gaps)==132
source=json.loads(data["source"])
source["status"]="FICTIONAL_PRIVATE_CANARY"
changed=map_registered_preflight(json.dumps(source).encode(),binding,
                               source_profile_id="SYNTHETIC_MAPPING_S0")
assert "FICTIONAL_PRIVATE_CANARY" not in repr(changed)
for name in sys.modules:
    assert not name.startswith(("cyberpilot_autotune","tools.actions_runner_preflight",
                                "tests.audit_compatibility","tests.audit_preparation_profile"))
print("PURE_DIAGNOSTICS_REDACTED_NO_H_RECORD")
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        input=json.dumps(
            {
                "source": source_bytes().decode(),
                "binding": registration()["acceptance"]["baseline_binding"],
            }
        ),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "PURE_DIAGNOSTICS_REDACTED_NO_H_RECORD" and not result.stderr


def test_final_scope_is_exact_and_manifest_cannot_grant_authority():
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
    previous = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                BASE
                + ":docs/evidence/audit_compatibility/preparation-profile-v1/registration.json",
            ],
            cwd=ROOT,
        )
    )
    assert (
        set(current["new_paths"]) == ADDITIONS and set(current["modified_paths"]) == MODIFICATIONS
    )
    assert current["permissions"] == previous["permissions"] and not any(
        current["permissions"].values()
    )
    assert set(previous["retained_blockers"]) <= set(current["retained_blockers"])
    assert current["profile_record"] is None and not current["manifest_is_authority"]
    assert not current["H_executed"] and not current["integrated_admission"]


def test_every_old_nonconsumer_byte_and_top_level_AST_is_preserved():
    changes = {
        "tests/test_audit_compatibility_history_architecture.py": (
            "test_all_earlier_files_and_guard_bytes_are_preserved"
        ),
        "tests/test_preparation_profile_architecture.py": (
            "test_final_scope_exact_inventory_and_registration_do_not_authorize_execution"
        ),
    }
    for path, exception in changes.items():
        old_text = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT).decode()
        new_text = (ROOT / path).read_text()
        old, new = ast.parse(old_text), ast.parse(new_text)
        old_funcs = {n.name: n for n in old.body if isinstance(n, ast.FunctionDef)}
        new_funcs = {n.name: n for n in new.body if isinstance(n, ast.FunctionDef)}
        assert set(old_funcs) == set(new_funcs)
        for name, node in old_funcs.items():
            if name != exception:
                assert ast.get_source_segment(old_text, node) == ast.get_source_segment(
                    new_text, new_funcs[name]
                ), name
        assert [ast.dump(n) for n in old.body if not isinstance(n, ast.FunctionDef)] == [
            ast.dump(n) for n in new.body if not isinstance(n, ast.FunctionDef)
        ]
