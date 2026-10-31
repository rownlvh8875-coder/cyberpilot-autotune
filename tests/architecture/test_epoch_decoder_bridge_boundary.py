"""No frozen-history weakening or runtime/application bridge from an integration test."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "4371dfe5e69878665abcb9133cc20d5e0451949d"


def test_every_prior_tracked_blob_is_preserved_except_additive_attributes():
    before = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
    )
    assert not (before & changed) - {".gitattributes"}
    attrs = subprocess.check_output(["git", "show", BASE + ":.gitattributes"], cwd=ROOT)
    assert (ROOT / ".gitattributes").read_text().encode().startswith(attrs)


def test_only_full_v2_decoder_and_frozen_source_constants_are_imported():
    allowed = {
        "native.py": {
            "base64",
            "hashlib",
            "json",
            "subprocess",
            "pathlib",
            "tests.guest_epoch_u64.native_probe",
        },
        "validation.py": {"tests.guest_epoch_u64.contracts", "tests.guest_epoch_u64.wire"},
    }
    for name, imports in allowed.items():
        for node in ast.walk(ast.parse((ROOT / "tests/epoch_decoder_bridge" / name).read_bytes())):
            if isinstance(node, ast.Import):
                assert all(item.name in imports for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module in imports
                if node.module == "tests.guest_epoch_u64.native_probe":
                    assert {item.name for item in node.names} == {"INPUTS", "INPUT_SHA"}
                elif node.module == "tests.guest_epoch_u64.wire":
                    assert [item.name for item in node.names] == ["parse_serial"]
            elif isinstance(node, ast.Call):
                called = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert called not in {
                    "eval",
                    "exec",
                    "compile",
                    "__import__",
                    "Popen",
                    "system",
                    "Thread",
                    "connect",
                    "probe",
                    "capture",
                    "findall",
                    "search",
                }
                if called in {"open", "write", "run"}:
                    assert name == "native.py"
    assert not (ROOT / "tests/epoch_decoder_bridge/runner.py").exists()
