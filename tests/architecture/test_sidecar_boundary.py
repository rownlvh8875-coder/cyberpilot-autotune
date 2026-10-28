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
