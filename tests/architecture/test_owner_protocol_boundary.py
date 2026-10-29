"""The reference owner cannot acquire runtime, vehicle or IO capabilities."""

import ast
import inspect
from pathlib import Path

from cyberpilot_autotune import owner_protocol

ROOT = Path(__file__).resolve().parents[2]


def test_reference_package_imports_only_explicit_pure_standard_library_and_itself():
    allowed = {"hashlib", "json", "math", "re", "dataclasses", "enum", "typing"}
    forbidden_calls = {
        "open",
        "eval",
        "exec",
        "__import__",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "send",
        "publish",
        "put",
        "put_int",
        "put_bool",
        "Popen",
        "start",
        "connect",
        "monotonic",
        "time",
    }
    for path in (ROOT / "src/cyberpilot_autotune/owner_protocol").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(a.name.split(".")[0] in allowed for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert node.module.split(".")[0] in allowed
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in forbidden_calls


def test_reference_constructor_has_no_implicit_clock_baseline_authority_or_policy():
    signature = inspect.signature(owner_protocol.ReferenceTorqueParameterOwner)
    assert set(signature.parameters) == {
        "identity",
        "baseline",
        "policy",
        "clock",
        "authority",
        "port",
    }
    assert all(p.default is inspect.Parameter.empty for p in signature.parameters.values())


def test_h4_keeps_h3_unit_evidence_unpromoted_and_pr9_source_reference_unchanged():
    import json

    sources = json.loads((ROOT / "docs/evidence/carrot_writer_ownership_sources.json").read_text())
    matrix = json.loads((ROOT / "docs/evidence/carrot_writer_unit_matrix.json").read_text())
    assert sources["preserved_prs"]["9"] == "6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5"
    assert {p["global_status"] for p in matrix["parameters"]} == {
        "FACTOR_UNIT_EQUIVALENCE_UNRESOLVED",
        "FRICTION_UNIT_EQUIVALENCE_UNRESOLVED",
        "OFFSET_SEMANTICS_PROVEN",
    }
    # The future target facade has not been added to production application/integration code.
    assert not (ROOT / "src/cyberpilot_autotune/application").exists()
    for name in ("core", "safety", "runtime", "replay", "integrations", "knowledge"):
        for path in (ROOT / "src/cyberpilot_autotune" / name).rglob("*.py"):
            assert "owner_protocol" not in path.read_text()
