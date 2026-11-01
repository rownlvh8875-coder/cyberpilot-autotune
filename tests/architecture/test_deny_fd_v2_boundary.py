"""Pure diagnostic boundary and source-only build capability separation."""

import ast
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def violations(raw):
    allowed = {"re", "dataclasses", "typing", "json", "hashlib"}
    forbidden = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "getattr",
        "globals",
        "write_bytes",
        "write_text",
        "read_bytes",
        "read_text",
        "run",
        "Popen",
        "connect",
        "Thread",
        "Process",
        "Params",
        "start",
        "system",
        "print",
    }
    result = []
    for node in ast.walk(ast.parse(raw)):
        if isinstance(node, ast.Import):
            if any(n.name not in allowed for n in node.names):
                result.append("import")
        elif isinstance(node, ast.ImportFrom):
            if not (
                (node.level == 1 and node.module == "contracts")
                or (node.level == 0 and node.module in allowed)
            ):
                result.append("import")
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            )
            if name in forbidden:
                result.append("call")
            if name == "__setattr__" and not (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "object"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "self"
            ):
                result.append("mutation")
    return result


def test_build_boundary_must_exist_before_source_is_accepted():
    assert importlib.util.find_spec("tests.deny_fd_v2.build") is not None
    assert (ROOT / "tests/deny_fd_v2/guest/probe.c").is_file()


def test_pure_modules_have_no_acquisition_io_or_admission_bridge():
    for filename in ("__init__.py", "contracts.py", "wire.py", "validation.py"):
        assert violations((ROOT / "tests/deny_fd_v2" / filename).read_bytes()) == []
    for path in (ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_bytes())):
            names = (
                [n.name for n in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            assert all("deny_fd_v2" not in n for n in names)


@pytest.mark.parametrize(
    "source",
    [
        "import socket",
        "from subprocess import run",
        "from cereal import messaging",
        "from cyberpilot_autotune.application import AuthorizationGrant",
        "from tests.deny_fd_provenance.validation import evaluate",
        "from tests.experiments.guest_data_fd_handoff.model import parse_serial",
        "open('capture','w')",
        "value.write_bytes(b'x')",
        "object.__setattr__(other, 'runtime_accepted', True)",
    ],
)
def test_guard_detects_operational_or_promotion_capabilities(source):
    assert violations(source)


def test_final_head_contains_exact_approved_delta_and_preserves_old_images(tmp_path):
    from tests.history_transition.deny_fd_v2_harness_successor import (
        replay_original_scope,
        validate_harness_successor,
    )

    if validate_harness_successor(ROOT):
        replay_original_scope(ROOT, tmp_path)
        return

    from tests.history_transition.deny_fd_v2_successor import (
        BASE,
        MODIFIED,
        NEW_PATHS,
        validate_v2_successor,
    )

    changed = set(
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", BASE, "HEAD"], cwd=ROOT, text=True
        ).splitlines()
    )
    assert changed == set(NEW_PATHS) | {MODIFIED}
    assert len(changed) == 19 and len(validate_v2_successor(ROOT)) == 18


def test_source_manifest_is_raw_git_bound_without_a_self_hash_cycle():
    from tests.deny_fd_v2.build import SOURCES, describe_sources
    from tests.history_transition.deny_fd_v2_successor import PREREGISTRATION

    manifest = json.loads((ROOT / "docs/evidence/deny_fd_v2_sources.json").read_text())
    source = manifest["source_revision"]
    assert manifest == describe_sources(source)
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREREGISTRATION, source], cwd=ROOT, check=True
    )
    subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=ROOT, check=True)
    assert "docs/evidence/deny_fd_v2_sources.json" not in SOURCES
    for path in SOURCES:
        assert subprocess.check_output(["git", "show", source + ":" + path], cwd=ROOT) == (
            subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT)
        )
