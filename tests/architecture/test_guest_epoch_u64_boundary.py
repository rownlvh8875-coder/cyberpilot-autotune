"""Preserve history; keep bounded tooling out of runtime/qualification bridges."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "1d9207723ac63c90d8a2173bd401e3115abe2edf"


def test_all_prior_blobs_except_additive_attributes_are_unchanged():
    prior = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
    )
    assert not (prior & changed) - {".gitattributes"}
    original = subprocess.check_output(["git", "show", BASE + ":.gitattributes"], cwd=ROOT)
    assert (ROOT / ".gitattributes").read_text().encode().startswith(original)


def test_wire_and_audit_never_use_old_parser_models_or_runtime_capabilities():
    allowed = {
        "contracts.py": {"dataclasses", "tests.audit.fd_ofd_lifetime_model"},
        "wire.py": {
            "re",
            "tests.guest_raw_lifetime.model",
            "tests.guest_tag_snapshot.contracts",
            "tests.guest_tag_snapshot.wire",
            "contracts",
        },
        "audit.py": {
            "argparse",
            "hashlib",
            "json",
            "pathlib",
            "typing",
            "tests.audit.fd_ofd_lifetime_model",
            "tests.bootstrap_tag_audit.audit",
            "tests.copy_reference_audit.audit",
            "cohort",
        },
    }
    for name, imports in allowed.items():
        tree = ast.parse((ROOT / "tests/guest_epoch_u64" / name).read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name in imports for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module in imports
                if node.module == "tests.guest_tag_snapshot.wire":
                    assert all(alias.name in {"ENUMS", "FIELDS", "RESULTS"} for alias in node.names)
                if node.module == "tests.guest_tag_snapshot.contracts":
                    assert [alias.name for alias in node.names] == ["CASES"]
            elif isinstance(node, ast.Call):
                called = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert called not in {
                    "write",
                    "write_bytes",
                    "write_text",
                    "open",
                    "run",
                    "Popen",
                    "system",
                    "exec",
                    "eval",
                    "__import__",
                    "Thread",
                    "connect",
                    "probe",
                    "capture",
                    "classify",
                    "assess",
                }
    assert not (ROOT / "tests/guest_epoch_u64/runner.py").exists()
