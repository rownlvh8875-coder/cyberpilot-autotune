"""Knowledge stays descriptive and independent of runtime/control capabilities."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/cyberpilot_autotune"


def test_existing_runtime_layers_never_import_knowledge():
    for name in ("core", "safety", "runtime", "replay", "integrations", "application"):
        for path in (ROOT / name).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    assert "knowledge" not in (node.module or "").split(".")
                if isinstance(node, ast.Import):
                    assert all("knowledge" not in x.name.split(".") for x in node.names)


def test_knowledge_has_no_application_runtime_or_io_imports_or_calls():
    forbidden = {
        "openpilot",
        "cereal",
        "opendbc",
        "selfdrive",
        "capnp",
        "os",
        "socket",
        "subprocess",
        "multiprocessing",
        "threading",
        "time",
        "sqlite3",
        "pickle",
        "shelve",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "importlib",
    }
    forbidden_symbols = {
        "Params",
        "SubMaster",
        "AutoTuneEngine",
        "ResidualStatisticsLearner",
        "SteeringRequest",
        "AuthorizationGrant",
        "ApplicationAuthority",
        "SteeringPolicy",
        "ParameterSpec",
        "TargetSnapshot",
        "SteeringEvidence",
        "CarController",
    }
    forbidden_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "put",
        "put_bool",
        "put_int",
        "remove",
        "apply",
        "commit",
        "authorize",
        "observe",
        "step",
        "Popen",
        "start",
        "send",
        "eval",
        "exec",
        "__import__",
        "time",
        "monotonic",
    }
    for path in (ROOT / "knowledge").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert not any(m.split(".")[0] in forbidden for m in modules)
                assert not any(
                    "application" in m.split(".") or "runtime" in m.split(".") for m in modules
                )
                assert not any(x.name in forbidden_symbols for x in node.names)
                if isinstance(node, ast.ImportFrom) and node.module == "pathlib":
                    assert [x.name for x in node.names] == ["PurePosixPath"]
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in forbidden_calls


def test_import_catalog_and_digests_have_no_added_side_effects(monkeypatch):
    import builtins
    import importlib
    import io
    import socket
    import subprocess
    import threading
    import time

    import cyberpilot_autotune.knowledge._catalog_data as data
    from cyberpilot_autotune.knowledge.steering import get_registry

    def deny(*args, **kwargs):
        raise AssertionError("KNOWLEDGE_SIDE_EFFECT")

    with monkeypatch.context() as guard:
        for obj, name in (
            (builtins, "open"),
            (io, "open"),
            (socket, "socket"),
            (subprocess, "Popen"),
            (threading.Thread, "start"),
            (time, "time"),
            (time, "monotonic"),
        ):
            guard.setattr(obj, name, deny)
        importlib.reload(data)
        for registry in data.CATALOGS:
            assert get_registry(registry.source_revision) == registry
            assert all(len(p.digest) == 64 for p in registry.parameters)


def test_new_namespaces_are_only_knowledge_and_isolated_reference_protocol():
    import json

    base = ROOT.parents[1]
    frozen = json.loads((base / "docs/evidence/hoya_c3_atune_sources.json").read_text())
    original = {p for p in frozen["preserved_files"] if p.startswith("src/")}
    current = {
        p.relative_to(base).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert original <= current
    assert all(
        p.startswith(
            (
                "src/cyberpilot_autotune/knowledge/",
                "src/cyberpilot_autotune/owner_protocol/",
                "src/cyberpilot_autotune/research/",
                "src/cyberpilot_autotune/observability/",
            )
        )
        for p in current - original
    )
