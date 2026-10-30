"""Operational tooling never becomes an installed/controller/application dependency."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "compatibility/containment_guest_collector"


def test_pure_capture_contract_and_evaluation_have_no_operational_imports():
    for name in ("contracts.py", "validation.py", "evaluation.py"):
        for node in ast.walk(ast.parse((PACKAGE / name).read_text())):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(
                name.split(".")[0]
                in {
                    "os",
                    "subprocess",
                    "socket",
                    "ctypes",
                    "threading",
                    "multiprocessing",
                    "cereal",
                    "openpilot",
                    "cyberpilot_autotune",
                }
                for name in names
            )


def test_runner_has_only_a_fixed_qemu_subprocess_boundary():
    tree = ast.parse((PACKAGE / "vm_runner.py").read_text())
    runs = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
    ]
    assert len(runs) == 1
    assert isinstance(runs[0].args[0], ast.Call)
    assert isinstance(runs[0].args[0].func, ast.Name)
    assert runs[0].args[0].func.id == "qemu_arguments"
    assert not any(k.arg == "shell" for k in runs[0].keywords)


def test_prior_fixture_package_installed_source_and_ci_are_unchanged():
    paths = [
        "compatibility/containment_backend_harmless",
        "src",
        ".github",
        "docs/evidence/containment_backend_harmless_results.json",
        "docs/evidence/containment_backend_guest_sources.json",
    ]
    result = subprocess.check_output(
        ["git", "diff", "--name-only", "1b2ff21ac83a8ea9d7c04850c8e2f7e92d06425d", "--", *paths],
        cwd=ROOT,
        text=True,
    )
    assert result.strip() == ""


def test_installed_module_graph_has_no_collector_dependency():
    for path in (ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(
                    "compatibility.containment_guest_collector"
                )
            elif isinstance(node, ast.Import):
                assert not any(
                    a.name.startswith("compatibility.containment_guest_collector")
                    for a in node.names
                )
