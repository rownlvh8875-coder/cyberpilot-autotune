"""Static audit must not acquire producer,record-admission or installed powers."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "5581049957088b348498eb5ef0b1061f76d19b7c"


def test_all_prior_source_tests_evidence_and_workflows_remain_byte_identical():
    scope = ["src", "compatibility", ".github", "tests", "docs/evidence"]
    prior = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE, "--", *scope], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *scope], cwd=ROOT, text=True
        ).splitlines()
    )
    assert not prior & changed


def test_pure_model_and_readonly_audit_have_no_runtime_or_actual_record_dependency():
    allowed = {
        "model.py": {"dataclasses", "typing", "tests.audit.fd_ofd_lifetime_model"},
        "audit.py": {
            "argparse",
            "hashlib",
            "json",
            "dataclasses",
            "pathlib",
            "typing",
            "tests.audit.fd_ofd_lifetime_model",
            "tests.bootstrap_tag_audit.audit",
            "model",
        },
    }
    for filename, modules in allowed.items():
        tree = ast.parse((ROOT / "tests/copy_reference_audit" / filename).read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(item.name in modules for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module in modules
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in {
                    "write",
                    "write_bytes",
                    "write_text",
                    "run",
                    "Popen",
                    "system",
                    "Thread",
                    "connect",
                    "capture",
                    "parse_serial",
                    "exec",
                    "eval",
                    "compile",
                    "__import__",
                }
                if name == "open":
                    assert filename == "audit.py" and len(node.args) == 1
                    assert isinstance(node.args[0], ast.Constant) and node.args[0].value == "rb"
