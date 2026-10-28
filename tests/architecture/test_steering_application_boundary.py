"""Application capability is isolated; no longitudinal or hidden runtime owner."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/cyberpilot_autotune"


def test_existing_layers_do_not_acquire_application_capability():
    for name in ("core", "safety", "runtime", "replay", "integrations"):
        for path in (ROOT / name).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    assert "application" not in (node.module or "").split(".")
                if isinstance(node, ast.Import):
                    assert all("application" not in n.name.split(".") for n in node.names)


def test_application_contains_no_openpilot_params_io_network_or_process_api():
    forbidden = {
        "openpilot",
        "cereal",
        "opendbc",
        "capnp",
        "numpy",
        "os",
        "socket",
        "subprocess",
        "threading",
        "multiprocessing",
        "pathlib",
        "sqlite3",
        "pickle",
        "shelve",
    }
    for path in (ROOT / "application").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert all(m.split(".")[0] not in forbidden for m in modules)
                assert all(
                    a.name
                    not in {
                        "AutoTuneEngine",
                        "ResidualStatisticsLearner",
                        "Params",
                        "CarController",
                        "PubMaster",
                        "SubMaster",
                    }
                    for a in node.names
                )
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                if name == "remove":
                    assert path.name == "coordinator.py"
                    assert isinstance(node.func, ast.Attribute)
                    assert isinstance(node.func.value, ast.Attribute)
                    assert isinstance(node.func.value.value, ast.Name)
                    assert node.func.value.value.id == "self"
                    assert node.func.value.attr == "_consumed"  # bounded in-memory ID set only
                    continue
                assert name not in {
                    "open",
                    "write_text",
                    "write_bytes",
                    "put",
                    "put_bool",
                    "remove",
                    "eval",
                    "exec",
                    "__import__",
                    "Popen",
                    "start",
                    "send",
                    "apply",
                }


def test_explicit_synthetic_target_path_adds_no_io_or_threads(monkeypatch):
    import builtins
    import socket
    import subprocess
    import threading

    from cyberpilot_autotune.application.coordinator import BoundedSteeringApplicator
    from tests.fixtures.steering_application import (
        Authority,
        Clock,
        MemoryTarget,
        baseline,
        policy,
        request,
    )

    p, clock = policy(), Clock()
    target = MemoryTarget(clock, baseline(p))

    def forbidden(*args, **kwargs):
        raise AssertionError("UNEXPECTED_RUNTIME_CAPABILITY")

    with monkeypatch.context() as guard:
        guard.setattr(builtins, "open", forbidden)
        guard.setattr(socket, "socket", forbidden)
        guard.setattr(subprocess, "Popen", forbidden)
        guard.setattr(threading.Thread, "start", forbidden)
        app = BoundedSteeringApplicator(p, baseline(p), target, Authority(), clock)
        assert app.process(request(p)).effective_parameters["lat_accel_factor"] == 11.0
        assert app.disarm().effective_parameters == baseline(p).values
