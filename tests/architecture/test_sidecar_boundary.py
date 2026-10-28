"""Read-only receive capability only; native SubMaster internals are outside this AST."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/cyberpilot_autotune/integrations/carrot"


def test_entire_integration_has_no_control_persistence_or_extra_runtime_capability():
    forbidden_imports = {
        "socket",
        "subprocess",
        "multiprocessing",
        "threading",
        "sqlite3",
        "pickle",
        "shelve",
        "pathlib",
        "os",
    }
    forbidden_symbols = {
        "AutoTuneEngine",
        "ResidualStatisticsLearner",
        "CarController",
        "Params",
        "PubMaster",
    }
    forbidden_calls = {
        "open",
        "eval",
        "exec",
        "__import__",
        "apply",
        "put",
        "put_bool",
        "remove",
        "send",
        "pub_sock",
        "start",
        "Popen",
    }
    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names]
                modules = names if isinstance(node, ast.Import) else [node.module or ""]
                assert not set(names) & forbidden_symbols
                for module in modules:
                    assert module.split(".")[0] not in forbidden_imports
                    assert not module.startswith(
                        (
                            "cyberpilot_autotune.core",
                            "cyberpilot_autotune.runtime",
                            "common.params",
                            "selfdrive",
                            "cereal",
                            "opendbc",
                        )
                    )
                    if module.startswith("openpilot"):
                        assert (path.name, module, tuple(names)) in {
                            ("availability.py", "openpilot.cereal", ("car", "log")),
                            ("source.py", "openpilot.cereal", ("messaging",)),
                        }
                        function = next(
                            n
                            for n in tree.body
                            if isinstance(n, ast.FunctionDef)
                            and n.name
                            == (
                                "require_schema"
                                if path.name == "availability.py"
                                else "require_live_dependencies"
                            )
                        )
                        assert node in list(ast.walk(function))
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                if name == "put":
                    # The only allowed put is the pre-existing in-memory exact cache.
                    assert path.name == "adapter.py"
                    assert isinstance(node.func, ast.Attribute)
                    assert isinstance(node.func.value, ast.Attribute)
                    assert node.func.value.attr in {"_commands", "_states"}
                else:
                    assert name not in forbidden_calls


def test_scripted_sidecar_receive_path_has_no_extra_io_or_control_side_effect(monkeypatch):
    import builtins
    import socket
    import subprocess
    import threading

    from cyberpilot_autotune.integrations.carrot.sidecar.runner import SidecarRunner
    from cyberpilot_autotune.integrations.carrot.sidecar.source import SubMasterSource
    from tests.fixtures.carrot_adapter import session
    from tests.fixtures.carrot_readers import binding, samples
    from tests.fixtures.sidecar import ScriptedSubMaster, sidecar_config

    monkeypatch.setattr("cyberpilot_autotune.integrations.carrot.adapter.require_schema", binding)
    runner = SidecarRunner(
        sidecar_config(),
        SubMasterSource(ScriptedSubMaster([samples()]), session()),
        clock=lambda: 10_010_000_000,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("EXTRA_RUNTIME_CAPABILITY")

    with monkeypatch.context() as guard:
        guard.setattr(builtins, "open", forbidden)
        guard.setattr(socket, "socket", forbidden)
        guard.setattr(subprocess, "Popen", forbidden)
        guard.setattr(threading.Thread, "start", forbidden)
        assert runner.poll_once()[0].snapshot.source_valid
        assert runner.diagnostics().accepted_mapping_count == 1
        runner.close()
