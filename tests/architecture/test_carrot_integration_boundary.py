"""Optional dependency imports are localized; core never depends on integration."""

import ast
from pathlib import Path

from tests.fixtures.carrot_adapter import config
from tests.fixtures.carrot_readers import binding, samples

ROOT = Path(__file__).resolve().parents[2] / "src/cyberpilot_autotune"


def test_core_areas_cannot_import_optional_integration():
    for area in ("core", "safety", "runtime", "replay"):
        for path in (ROOT / area).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else []
                )
                assert not any(
                    name.startswith("cyberpilot_autotune.integrations") for name in names
                )


def test_only_fixed_local_dependency_loader_can_import_vehicle_schema():
    forbidden = {
        "socket",
        "threading",
        "subprocess",
        "multiprocessing",
        "pathlib",
        "os",
        "time",
        "cereal",
        "opendbc",
        "selfdrive",
    }
    for path in (ROOT / "integrations/carrot").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in names:
                assert name.split(".")[0] not in forbidden
                if name.startswith("openpilot") or name == "capnp":
                    assert path.name == "availability.py"
                    loader = next(
                        n
                        for n in tree.body
                        if isinstance(n, ast.FunctionDef) and n.name == "require_schema"
                    )
                    assert node in list(ast.walk(loader))
                    assert name in {"openpilot.cereal", "capnp"}
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__"}


def test_adapter_has_no_io_network_thread_process_or_control_side_effect(monkeypatch):
    import builtins
    import socket
    import subprocess
    import threading

    from cyberpilot_autotune.integrations.carrot.adapter import CarrotReadOnlyAdapter

    monkeypatch.setattr("cyberpilot_autotune.integrations.carrot.adapter.require_schema", binding)
    adapter = CarrotReadOnlyAdapter(config())
    cc, cs, co = samples()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("FORBIDDEN_CAPABILITY")

    with monkeypatch.context() as guard:
        guard.setattr(builtins, "open", forbidden)
        guard.setattr(socket.socket, "connect", forbidden)
        guard.setattr(socket, "create_connection", forbidden)
        guard.setattr(subprocess, "Popen", forbidden)
        guard.setattr(threading.Thread, "start", forbidden)
        adapter.ingest_car_control(cc)
        adapter.ingest_car_state(cs)
        result = adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000)
        assert result.snapshot.source_valid and not calls
