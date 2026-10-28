"""AST constraints plus isolated, guarded imports and OFF/SHADOW execution."""

import ast
import inspect
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from cyberpilot_autotune.adapters.base import ObservationAdapter

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "cyberpilot_autotune"
FORBIDDEN = {"openpilot", "cereal", "selfdrive", "common.params", "opendbc"}
CAPABILITIES = {"CarInterface", "CarInterfaceBase", "SubMaster"}


def test_dependency_boundaries_use_ast():
    for area in ("contracts", "core", "safety", "runtime", "adapters", "telemetry", "replay"):
        for path in (PACKAGE / area).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                    assert not CAPABILITIES.intersection(alias.name for alias in node.names), path
                else:
                    continue
                for module in modules:
                    assert not any(
                        module == bad or module.startswith(bad + ".") for bad in FORBIDDEN
                    ), (path, module)
            # Disallow dynamic imports and code execution that could bypass static imports.
            calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
            for call in calls:
                if isinstance(call.func, ast.Name):
                    assert call.func.id not in {"__import__", "eval", "exec", "open"}, path
                if isinstance(call.func, ast.Attribute):
                    is_cli = path == PACKAGE / "replay" / "cli.py"
                    if call.func.attr == "write":
                        assert is_cli and ast.unparse(call.func.value) in {
                            "sys.stdout.buffer",
                            "sys.stderr.buffer",
                        }, path
                        continue
                    if call.func.attr in {"open", "read_bytes", "read_text"}:
                        assert is_cli, path
                        assert call.func.attr == "open" and len(call.args) == 1, path
                        assert isinstance(call.args[0], ast.Constant), path
                        assert call.args[0].value == "rb", path
                    assert call.func.attr not in {
                        "import_module",
                        "write",
                        "write_text",
                        "write_bytes",
                        "start_new_thread",
                    }, path


def test_adapter_exposes_only_readonly_conversion():
    public_methods = {
        name
        for name, value in inspect.getmembers(ObservationAdapter)
        if not name.startswith("_") and callable(value)
    }
    assert public_methods == {"to_observation"}
    assert inspect.signature(ObservationAdapter.to_observation).return_annotation.__name__ == (
        "ObservationSnapshot"
    )


@pytest.mark.parametrize(
    "first_module",
    [
        "core",
        "core.residual",
        "safety",
        "runtime",
        "telemetry.events",
        "adapters.base",
        "contracts",
        "replay",
        "replay.runner",
        "replay.cli",
    ],
)
def test_import_and_modes_have_no_io_network_threads_or_optional_dependencies(
    first_module, tmp_path
):
    script = textwrap.dedent("""
        import sys, os, importlib, pkgutil, socket, threading, _thread
        sys.dont_write_bytecode = True
        def forbidden(*args, **kwargs):
            raise AssertionError('Forbidden side effect')
        class NoVehicleImports:
            def find_spec(self, fullname, *args):
                if fullname.split('.')[0] in {'openpilot', 'cereal', 'selfdrive', 'opendbc'}:
                    raise AssertionError('Forbidden optional dependency')
        def audit(event, args):
            if event == 'open':
                flags = args[2]
                if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                    forbidden()
            if event.startswith('socket.') or event in {
                'os.mkdir', 'os.remove', 'os.rename', 'subprocess.Popen', 'os.system'
            }:
                forbidden()
        sys.meta_path.insert(0, NoVehicleImports())
        threading.Thread.start = forbidden
        _thread.start_new_thread = forbidden
        sys.addaudithook(audit)
        package = importlib.import_module('cyberpilot_autotune.' + sys.argv[1])
        import cyberpilot_autotune
        for module in pkgutil.walk_packages(cyberpilot_autotune.__path__, 'cyberpilot_autotune.'):
            importlib.import_module(module.name)
        from cyberpilot_autotune.core.no_op import NoOpLearner
        from cyberpilot_autotune.core.residual import (
            ResidualStatisticsConfig, ResidualStatisticsLearner,
        )
        from cyberpilot_autotune.contracts import ObservationSnapshot, ParameterSpec
        from cyberpilot_autotune.runtime.engine import AutoTuneEngine
        from cyberpilot_autotune.runtime.mode import RuntimeMode
        from cyberpilot_autotune.safety.gate import GateConfig, SafetyGate
        class Clock:
            def now_s(self): return 10.0
        baseline = {'synthetic.test_only': 10.0}
        spec = ParameterSpec('synthetic.test_only', 'test_unit', 0, 20, 2, 1,
                             'Test only; not for vehicle use', False)
        gate = SafetyGate({spec.parameter_id: spec}, GateConfig(1, 2, .8, minimum_speed_mps=1))
        config = ResidualStatisticsConfig(.5, 2, 8, 1, 2, 10, 1, .5, .01, 2, minimum_speed_mps=1)
        for mode in RuntimeMode:
            for learner in (NoOpLearner(), ResidualStatisticsLearner(spec, config)):
                engine = AutoTuneEngine(mode=mode, baseline_parameters=baseline,
                                       learner=learner, gate=gate, clock=Clock())
                for sequence in range(2):
                    snapshot = ObservationSnapshot(
                        9 + sequence, sequence, 0, 'test', True, 2, .25, 0, None,
                        False, False, baseline, control_active=True)
                    result = engine.step(snapshot)
                    assert result.effective_parameters == baseline
                    assert not any(event.reason.value == 'INTERNAL_ERROR'
                                   for event in result.events)
                if isinstance(learner, ResidualStatisticsLearner) and mode is RuntimeMode.SHADOW:
                    assert result.gate_decisions[0].eligible
                    engine.step(None)
                    assert learner.statistics is None
        from dataclasses import replace
        from cyberpilot_autotune.replay import ReplayEvent, ReplayScenario, run_replay
        from cyberpilot_autotune.replay.schema import CANONICAL_UNITS
        frames = tuple(ReplayEvent(9 + i, 9 + i, replace(
            snapshot, timestamp_s=9 + i, sequence=i, context_key='synthetic/guarded'
        )) for i in range(2))
        scenario = ReplayScenario(1, 'SYNTHETIC_TEST_ONLY', 'residual-ewma-v1',
            'synthetic.monotonic.v1', 0, CANONICAL_UNITS, baseline, spec,
            GateConfig(1, 2, .8, minimum_speed_mps=1), config, frames)
        ticks = iter(range(100))
        report = run_replay(scenario, timer_ns=lambda: next(ticks))
        assert report.software_checks_passed and report.summary.eligible_count == 1
        assert len(report.digest) == 64
        if sys.argv[1] == 'replay.cli':
            assert package.main(['verify-all', sys.argv[2]]) == 0
        assert not any(name.split('.')[0] in {'openpilot', 'cereal', 'selfdrive', 'opendbc'}
                       for name in sys.modules)
    """)
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, first_module, str(ROOT / "tests/fixtures/replay")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert list(tmp_path.iterdir()) == []
