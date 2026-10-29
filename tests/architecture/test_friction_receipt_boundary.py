"""H7 cannot acquire runtime, estimator, IO or application capabilities."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/cyberpilot_autotune"


def test_observability_dependencies_are_neutral_stdlib_and_local_records_only():
    allowed = {"dataclasses", "enum", "hashlib", "json", "math", "re"}
    local = {"types", "contracts", "context", "validation", "schema"}
    forbidden = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "Params",
        "SubMaster",
        "PubMaster",
        "socket",
        "Thread",
        "Process",
        "Popen",
        "run",
        "system",
        "exec",
        "eval",
        "send",
        "put",
        "commit",
        "start",
        "SteeringRequest",
        "AuthorizationGrant",
    }
    for path in (ROOT / "observability").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(n.name.split(".")[0] in allowed for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert (node.level == 1 and node.module in local) or (
                    node.level == 0 and node.module.split(".")[0] in allowed
                )
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in forbidden


def test_no_existing_runtime_estimator_owner_or_application_namespace_consumes_receipts():
    for path in ROOT.rglob("*.py"):
        if "observability" in path.relative_to(ROOT).parts:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                assert "observability" not in (node.module or "").split(".")
            elif isinstance(node, ast.Import):
                assert all("observability" not in n.name.split(".") for n in node.names)
