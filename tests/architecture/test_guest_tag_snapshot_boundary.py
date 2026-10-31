"""New guest experiment cannot mutate prior evidence or installed architecture."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "eba2e74759cefa65a941ebce09ce2a4cfa33ec21"


def test_every_prior_source_test_evidence_workflow_and_installed_blob_preserved():
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


def test_no_empirical_synthetic_or_application_adapter_and_only_opt_in_execution():
    prohibited = (
        "cyberpilot_autotune",
        "openpilot",
        "cereal",
        "tests.tag_read_protocol",
        "tests.guest_bootstrap.wire",
        "tests.guest_bootstrap.model",
    )
    for path in (ROOT / "tests/guest_tag_snapshot").glob("*.py"):
        tree = ast.parse(path.read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(n.name.startswith(prohibited) for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(prohibited)
            elif isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name in {"run", "write_bytes", "write_text"}:
                    assert path.name in {"runner.py", "native_probe.py"}
                assert name not in {"Popen", "Thread", "connect", "system"}
