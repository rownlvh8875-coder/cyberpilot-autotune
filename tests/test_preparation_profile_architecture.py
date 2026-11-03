"""The new comparator cannot obtain a runtime capability or rewrite frozen history."""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.fixtures.preparation_profile import registration
from tests.test_preparation_profile_scope import ADDITIONS, BASE, CHECKPOINT, MODIFICATIONS

ROOT = Path(__file__).resolve().parents[1]


def test_package_imports_only_closed_stdlib_and_exact_siblings():
    allowed = {
        "__init__": {"contracts", "wire", "validation"},
        "contracts": set(),
        "wire": {"contracts"},
        "validation": {"contracts", "wire"},
    }
    package = ROOT / "tests/audit_preparation_profile"
    assert {p.stem for p in package.glob("*.py")} == set(allowed)
    forbidden = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint"}
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(
                    n.name in {"dataclasses", "hashlib", "json", "typing"} for n in node.names
                )
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1 and node.module in allowed[path.stem]
                else:
                    assert node.module in {"dataclasses", "hashlib", "json", "typing"}
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden


def test_fresh_import_decode_and_assessment_have_no_effects_or_runtime_bridge():
    vector = registration()["conformance"]
    code = r"""
import json, os, sys
raw = json.loads(sys.stdin.read())
def audit(event, args):
    forbidden = ("socket.", "subprocess.", "os.system", "os.fork", "os.exec",
                 "os.spawn", "ctypes.", "_thread.")
    if event.startswith(forbidden):
        raise AssertionError(event)
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
    if event == "open" and args[2] & write_flags:
        raise AssertionError("file write")
sys.addaudithook(audit)
from tests.audit_preparation_profile import (
    assess_profile, decode_profile, decode_policy, canonical_profile,
)
record = decode_profile(raw[0].encode())
policy = decode_policy(raw[1].encode())
decision = assess_profile(record, policy)
assert decision.consistency == "STRUCTURAL_PROFILE_MATCH"
assert canonical_profile(record).decode() == raw[0]
assert decision.status == "BLOCKED" and not decision.H_executed
assert len(decision.permissions) == 9 and all(flag is False for _, flag in decision.permissions)
for name in sys.modules:
    forbidden_modules = ("cyberpilot_autotune", "openpilot", "cereal", "tests.audit_compatibility")
    assert not name.startswith(forbidden_modules), name
print("PURE_SUPPLIED_CLAIMS_ONLY_BLOCKED")
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        input=json.dumps([vector["canonical_record_utf8"], vector["canonical_policy_utf8"]]),
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "PURE_SUPPLIED_CLAIMS_ONLY_BLOCKED" and not result.stderr


def test_final_scope_exact_inventory_and_registration_do_not_authorize_execution():
    from tests.test_audit_compatibility_history_architecture import (
        test_all_earlier_files_and_guard_bytes_are_preserved,
    )

    rows = (
        subprocess.check_output(
            [
                "git",
                "diff",
                "--no-renames",
                "--name-status",
                BASE,
                "0ac6e3519ad7191b036eb777b4317174121851bb",
            ],
            cwd=ROOT,
        )
        .decode()
        .splitlines()
    )
    assert sorted(rows) == sorted(
        ["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS]
    )
    current = registration()
    previous = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                CHECKPOINT
                + ":docs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json",
            ],
            cwd=ROOT,
        )
    )
    assert (
        set(current["new_paths"]) == ADDITIONS and set(current["modified_paths"]) == MODIFICATIONS
    )
    assert set(previous["retained_blockers"]) <= set(current["retained_blockers"])
    assert current["permissions"] == previous["permissions"]
    assert not any(current["permissions"].values()) and not current["manifest_is_authority"]
    assert not current["H_executed"] and not current["integrated_admission"]
    assert current["atomicity"] == "NOT_ESTABLISHED" and current["content_identity_only"]
    test_all_earlier_files_and_guard_bytes_are_preserved()


def test_every_old_nonconsumer_function_and_toplevel_setting_is_preserved():
    allowed = {
        "tests/test_audit_compatibility_history_architecture.py": {
            "test_all_earlier_files_and_guard_bytes_are_preserved"
        },
        "tests/test_h1_cancellation_cleanup.py": {
            "test_successor_accepts_only_the_literal_cancellation_repair_inventory"
        },
    }
    for path, exceptions in allowed.items():
        old_text = subprocess.check_output(
            ["git", "show", CHECKPOINT + ":" + path], cwd=ROOT
        ).decode()
        new_text = (ROOT / path).read_text()
        old, new = ast.parse(old_text), ast.parse(new_text)
        functions = {n.name: n for n in new.body if isinstance(n, ast.FunctionDef)}
        old_names = {n.name for n in old.body if isinstance(n, ast.FunctionDef)}
        additions = (
            {"_preparation_profile_changes", "_preparation_profile_composed_changes"}
            if path.endswith("history_architecture.py")
            else set()
        )
        assert set(functions) == old_names | additions
        for node in old.body:
            if isinstance(node, ast.FunctionDef) and node.name not in exceptions:
                assert ast.get_source_segment(old_text, node) == ast.get_source_segment(
                    new_text, functions[node.name]
                ), node.name
        assert [ast.dump(n) for n in old.body if not isinstance(n, ast.FunctionDef)] == [
            ast.dump(n) for n in new.body if not isinstance(n, ast.FunctionDef)
        ]
