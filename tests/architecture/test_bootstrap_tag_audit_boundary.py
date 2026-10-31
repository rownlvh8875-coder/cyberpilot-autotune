"""New source-only audit cannot mutate/import producers or alter prior artifacts."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "37c0e614f01e13b5e6078178b3712c0ec6ba4495"


def test_source_audit_has_no_writer_process_network_runtime_or_admission_import():
    for name, allowed in (
        ("model.py", {"dataclasses", "typing", "tests.audit.fd_ofd_lifetime_model"}),
        (
            "audit.py",
            {
                "argparse",
                "base64",
                "hashlib",
                "json",
                "re",
                "dataclasses",
                "pathlib",
                "typing",
                "tests.audit.fd_ofd_lifetime_model",
                "tests.audit.validate_kernel_lifetime_feasibility",
                "model",
            },
        ),
    ):
        tree = ast.parse((ROOT / "tests/bootstrap_tag_audit" / name).read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(item.name in allowed for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module in allowed
            elif isinstance(node, ast.Call):
                call = node.func
                leaf = (
                    call.id
                    if isinstance(call, ast.Name)
                    else (call.attr if isinstance(call, ast.Attribute) else "")
                )
                assert leaf not in {
                    "write",
                    "write_bytes",
                    "write_text",
                    "exec",
                    "eval",
                    "compile",
                    "__import__",
                    "run",
                    "Popen",
                    "system",
                    "connect",
                    "Thread",
                    "evaluate",
                    "capture",
                }
                if leaf == "open":
                    assert len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
                    assert node.args[0].value == "rb"


def test_all_preexisting_runtime_source_test_and_evidence_blobs_are_unchanged():
    scopes = ["src", "compatibility", ".github", "tests", "docs/evidence"]
    before = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE, "--", *scopes], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *scopes], cwd=ROOT, text=True
        ).splitlines()
    )
    assert not before & changed
