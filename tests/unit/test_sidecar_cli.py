"""Qualify-only CLI, stdin boundary and sanitized stable exits; no native IPC."""

import io
import json
from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.errors import (
    CarrotDependencyUnavailable,
    CarrotSchemaIncompatible,
)
from cyberpilot_autotune.integrations.carrot.sidecar import cli
from cyberpilot_autotune.integrations.carrot.sidecar.config import SidecarError, SidecarReason
from cyberpilot_autotune.integrations.carrot.sidecar.runner import SidecarRunner
from cyberpilot_autotune.integrations.carrot.sidecar.source import SubMasterSource
from tests.fixtures.carrot_readers import binding, samples
from tests.fixtures.sidecar import ScriptedSubMaster, config_stdin, sidecar_config


def argv(cfg):
    return [
        "qualify",
        *sum(
            (
                ["--" + name.replace("_", "-"), str(getattr(cfg, name))]
                for name in (
                    "expected_platform",
                    "runtime_platform",
                    "source_revision",
                    "integration_revision",
                    "contract_basis",
                    "schema_revision",
                    "poll_timeout_ms",
                    "maximum_updates",
                )
            ),
            [],
        ),
    ]


@pytest.fixture
def configured(monkeypatch):
    cfg = sidecar_config()
    monkeypatch.setattr("cyberpilot_autotune.integrations.carrot.adapter.require_schema", binding)
    monkeypatch.setattr(
        cli, "SidecarRunner", lambda c, s: SidecarRunner(c, s, clock=lambda: 10_010_000_000)
    )
    monkeypatch.setattr(
        cli,
        "open_live_source",
        lambda token: SubMasterSource(ScriptedSubMaster([samples()]), token),
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(config_stdin(cfg))))
    return cfg


def test_qualify_emits_only_sanitized_canonical_summaries(configured, capsys):
    assert cli.main(argv(configured)) == 0
    out = capsys.readouterr()
    records = [json.loads(line) for line in out.out.splitlines()]
    assert records[-1]["accepted_mapping_count"] == 1
    assert records[-1]["session_state"] == "closed"
    assert not out.err and "baseline" not in out.out and "actuator" not in out.out
    assert all(
        line == json.dumps(json.loads(line), sort_keys=True, separators=(",", ":"))
        for line in out.out.splitlines()
    )


@pytest.mark.parametrize(
    "text", ["{", '{"SECRET-VIN":NaN}', '{"x":1,"x":2}', "[]", '"' + "x" * 65537 + '"']
)
def test_invalid_stdin_is_exit_two_without_raw_input(configured, monkeypatch, capsys, text):
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    assert cli.main(argv(configured)) == 2
    out = capsys.readouterr()
    assert "INVALID_CONFIG" in out.err and "SECRET" not in out.err and not out.out


@pytest.mark.parametrize(
    "case", ["unknown_field", "missing_field", "context", "baseline", "token", "capability"]
)
def test_config_semantics_reject_before_subscription(configured, monkeypatch, capsys, case):
    data = config_stdin(configured)
    code = 2
    if case == "unknown_field":
        data["unknown"] = "SECRET"
    if case == "missing_field":
        data.pop("baseline_parameters")
    if case == "context":
        data["static_context_digest"] = "0" * 64
        code = 4
    if case == "baseline":
        data["baseline_epoch"] = 2
        code = 4
    if case == "token":
        data["session"] = None
        code = 4
    if case == "capability":
        data["steering_pressed_capability"] = None
        code = 4
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(data)))

    def forbidden(token):
        raise AssertionError("subscription before config validation")

    monkeypatch.setattr(cli, "open_live_source", forbidden)
    assert cli.main(argv(configured)) == code
    assert "SECRET" not in capsys.readouterr().err


def test_platform_and_pin_failure_do_not_read_stdin(configured, monkeypatch, capsys):
    class NoRead:
        def read(self, *args):
            raise AssertionError("must not read stdin")

    monkeypatch.setattr("sys.stdin", NoRead())
    args = argv(configured)
    args[args.index("--runtime-platform") + 1] = "other"
    assert cli.main(args) == 4
    assert "RUNTIME_PLATFORM_MISMATCH" in capsys.readouterr().err


@pytest.mark.parametrize(
    "failure,code",
    [
        (CarrotDependencyUnavailable(), 3),
        (CarrotSchemaIncompatible(), 3),
        (SidecarError(SidecarReason.UNSUPPORTED_ENVIRONMENT), 6),
        (RuntimeError("SECRET-RAW"), 5),
        (KeyboardInterrupt(), 0),
    ],
)
def test_live_dependency_and_runtime_errors_are_sanitized(
    configured, monkeypatch, capsys, failure, code
):
    def failed(token):
        raise failure

    monkeypatch.setattr(cli, "open_live_source", failed)
    assert cli.main(argv(configured)) == code
    out = capsys.readouterr()
    assert "SECRET" not in out.err and "Traceback" not in out.err


@pytest.mark.parametrize("command", ["apply", "learn", "tune", "persist", "write", "install"])
def test_unimplemented_commands_are_rejected_without_echo(command, capsys):
    assert cli.main([command, "SECRET-VIN"]) == 2
    out = capsys.readouterr()
    assert "SECRET" not in out.err and "INVALID_CONFIG" in out.err


def test_help_is_parked_only_and_never_opens_dependencies(capsys):
    assert cli.main(["--help"]) == 0
    assert "parked" in capsys.readouterr().out.lower()


def test_stdin_read_failure_is_invalid_input_without_raw_error(configured, monkeypatch, capsys):
    class BrokenInput:
        def read(self, size):
            raise OSError("SECRET-STDIN")

    monkeypatch.setattr("sys.stdin", BrokenInput())
    assert cli.main(argv(configured)) == 2
    assert "SECRET" not in capsys.readouterr().err


def test_runtime_fault_summary_is_sanitized_and_requires_restart(configured, monkeypatch, capsys):
    cc, cs, co = samples()
    co = replace(co, reader=None)
    monkeypatch.setattr(
        cli,
        "open_live_source",
        lambda token: SubMasterSource(ScriptedSubMaster([(cc, cs, co)]), token),
    )
    assert cli.main(argv(configured)) == 4
    result = capsys.readouterr()
    assert "SESSION_REQUIRED" in result.err
    assert json.loads(result.out.splitlines()[-1])["latest_snapshot_available"] is False


def test_broken_terminal_never_produces_a_raw_traceback(configured, monkeypatch):
    class BrokenOutput:
        def write(self, value):
            raise OSError("SECRET-OUTPUT")

    monkeypatch.setattr("sys.stdout", BrokenOutput())
    monkeypatch.setattr("sys.stderr", BrokenOutput())
    assert cli.main(argv(configured)) == 5
