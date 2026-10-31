"""Design-only module cannot grow a producer/writer/actual-evidence bridge."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "e01cdc127bbb17073aa47967b926b68088f57ded"


def test_design_model_is_pure_and_audit_has_no_writer_or_runtime_dependency():
    for filename, modules in (
        ("model.py", {"re", "dataclasses", "typing", "tests.audit.fd_ofd_lifetime_model"}),
        (
            "audit.py",
            {
                "argparse",
                "hashlib",
                "json",
                "pathlib",
                "typing",
                "model",
                "tests.audit.fd_ofd_lifetime_model",
                "tests.audit.validate_kernel_lifetime_feasibility",
                "tests.bootstrap_tag_audit.audit",
            },
        ),
    ):
        tree = ast.parse((ROOT / "tests/tag_read_protocol" / filename).read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(item.name in modules for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module in modules
                if node.module == "tests.audit.fd_ofd_lifetime_model":
                    assert all(item.name in {"PERMISSIONS", "need", "shape"} for item in node.names)
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                )
                assert name not in {
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
                    "capture",
                    "parse_serial",
                }
                if name == "open":
                    assert filename == "audit.py" and len(node.args) == 1
                    assert isinstance(node.args[0], ast.Constant) and node.args[0].value == "rb"


def test_every_old_source_runtime_test_evidence_and_workflow_blob_is_preserved():
    scope = ["src", "compatibility", ".github", "tests", "docs/evidence"]
    old = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE, "--", *scope], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *scope], cwd=ROOT, text=True
        ).splitlines()
    )
    assert not old & changed
