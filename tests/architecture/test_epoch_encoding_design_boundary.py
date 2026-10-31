"""Keep the representation design pure and every previous blob unchanged."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "72362dcf235f91cbce30501aeeb72b66ee6c124c"


def test_existing_source_test_evidence_workflow_blobs_are_preserved():
    scope = ["src", "compatibility", ".github", "tests", "docs/evidence"]
    prior = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE, "--", *scope],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *scope],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    assert not prior & changed


def test_model_and_audit_have_no_producer_or_actual_record_capability():
    allowed = {
        "__init__.py": set(),
        "model.py": {"hashlib", "re", "dataclasses", "tests.audit.fd_ofd_lifetime_model"},
        "audit.py": {
            "argparse",
            "json",
            "dataclasses",
            "pathlib",
            "typing",
            "tests.audit.fd_ofd_lifetime_model",
            "tests.bootstrap_tag_audit.audit",
            "tests.copy_reference_audit.audit",
            "model",
        },
    }
    for filename, modules in allowed.items():
        for node in ast.walk(
            ast.parse((ROOT / "tests/epoch_encoding_design" / filename).read_bytes())
        ):
            if isinstance(node, ast.Import):
                assert all(alias.name in modules for alias in node.names)
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
                    "open",
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
