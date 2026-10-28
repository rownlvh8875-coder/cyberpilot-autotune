"""CLI errors are stable/redacted; success output has canonical portable bytes."""

import json
import shutil
import subprocess
import sys
from dataclasses import replace
from importlib import import_module
from pathlib import Path

import pytest

from cyberpilot_autotune.replay.canonical import canonical_bytes
from tests.fixtures.replay_data import replay_document

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/replay"


def invoke(*args):
    return subprocess.run(
        [sys.executable, "-I", "-m", "cyberpilot_autotune.replay.cli", *map(str, args)],
        capture_output=True,
        timeout=30,
    )


def write_document(tmp_path, document):
    path = tmp_path / "PRIVATE_INPUT.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_run_exit_zero_and_canonical_stdout(tmp_path):
    result = invoke("run", write_document(tmp_path, replay_document()))
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    output = json.loads(result.stdout)
    assert canonical_bytes(output) + b"\n" == result.stdout
    assert output["event_count"] == 3
    assert output["proposal_count"] == output["eligible_count"] == 1
    assert output["events"][0]["sample_count"] == 1
    assert "latency" not in result.stdout.decode()
    assert output["sha256"] == output["result_sha256"]


@pytest.mark.parametrize("raw", ['{"PRIVATE":', '{"x":1,"x":2}', '{"x":NaN}', "{}"])
def test_schema_error_exit_two_without_raw_input(tmp_path, raw):
    path = tmp_path / "PRIVATE_PATH.json"
    path.write_text(raw, encoding="utf-8")
    result = invoke("run", path)
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr == b"SCHEMA_INPUT_ERROR: Invalid replay input\n"
    assert b"PRIVATE" not in result.stderr


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 99),
        ("learner_version", "unknown"),
        ("scope", "VEHICLE"),
        ("time_domain", "utc"),
    ],
)
def test_unsupported_configuration_exit_five(tmp_path, field, value):
    document = replay_document()
    document[field] = value
    result = invoke("run", write_document(tmp_path, document))
    assert result.returncode == 5
    assert result.stderr == b"UNSUPPORTED_CONFIGURATION: Unsupported replay configuration\n"


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("scope", []),
        ("learner_version", False),
        ("time_domain", 3),
    ],
)
def test_invalid_metadata_types_are_input_errors_not_unsupported(tmp_path, field, value):
    document = replay_document()
    document[field] = value
    assert invoke("run", write_document(tmp_path, document)).returncode == 2


def test_verify_checks_metrics_as_well_as_digest_and_one_byte_mutation(tmp_path):
    scenario = FIXTURES / "golden_v1.json"
    expected = FIXTURES / "golden_v1.expected.json"
    assert invoke("verify", scenario, expected).returncode == 0
    raw = expected.read_bytes()
    changed = raw.replace(b'"event_count": 21', b'"event_count": 22', 1)
    assert sum(a != b for a, b in zip(raw, changed, strict=True)) == 1
    mutated = tmp_path / "expected.json"
    mutated.write_bytes(changed)
    result = invoke("verify", scenario, mutated)
    assert result.returncode == 3
    assert result.stdout == b""
    assert result.stderr == b"GOLDEN_MISMATCH: Replay expectations differ\n"


@pytest.mark.parametrize(
    "field,value",
    [
        ("event_count", 21.0),
        ("eligible_count", True),
        ("unknown", "ignored?"),
        ("rejection_counts", {}),
        ("sha256", "0" * 64),
    ],
)
def test_expected_types_unknown_fields_reasons_and_hash_cannot_silently_pass(
    tmp_path, field, value
):
    expected = json.loads((FIXTURES / "golden_v1.expected.json").read_text())
    expected[field] = value
    path = tmp_path / "expected.json"
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert invoke("verify", FIXTURES / "golden_v1.json", path).returncode == 3


def test_verify_all_sorts_fixtures_and_never_reads_expected_as_scenario(tmp_path):
    for name in ("z", "a", "m"):
        shutil.copyfile(FIXTURES / "golden_v1.json", tmp_path / f"{name}_v1.json")
        shutil.copyfile(FIXTURES / "golden_v1.expected.json", tmp_path / f"{name}_v1.expected.json")
    (tmp_path / "ignored_v1.expected.json").write_text("INVALID")
    (tmp_path / "ignored.json").write_text("INVALID")
    result = invoke("verify-all", tmp_path)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert [item["fixture"] for item in output["verified"]] == [
        "a_v1.json",
        "m_v1.json",
        "z_v1.json",
    ]
    assert canonical_bytes(output) + b"\n" == result.stdout


def test_invariant_failure_exit_four_and_unexpected_error_redacted(tmp_path, capfd, monkeypatch):
    cli = import_module("cyberpilot_autotune.replay.cli")
    real = cli.characterize_replay

    def violation(scenario):
        report, counts = real(scenario)
        return replace(report, summary=replace(report.summary, invariant_violations=1)), counts

    monkeypatch.setattr(cli, "characterize_replay", violation)
    assert cli.main(["run", str(write_document(tmp_path, replay_document()))]) == 4
    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == "REPLAY_INVARIANT_VIOLATION: Replay software checks failed\n"

    def broken(scenario):
        raise RuntimeError("PRIVATE_EXCEPTION_TOKEN")

    monkeypatch.setattr(cli, "characterize_replay", broken)
    assert cli.main(["run", str(tmp_path / "PRIVATE_INPUT.json")]) == 4
    assert "PRIVATE" not in capfd.readouterr().err


def test_missing_inputs_empty_directory_and_update_flag_return_two(tmp_path):
    for args in [
        ("run",),
        ("run", tmp_path / "PRIVATE_MISSING"),
        ("verify-all", tmp_path),
        ("run", "--update-golden", "PRIVATE"),
    ]:
        result = invoke(*args)
        assert result.returncode == 2
        assert b"PRIVATE" not in result.stderr


@pytest.mark.parametrize(
    "case",
    [
        "run",
        "verify",
        "verify-all",
        "schema",
        "unsupported",
        "mismatch",
        "missing",
        "invalid_args",
        "bad_expected",
        "oversized",
        "unicode",
        "bad_directory",
        "empty",
    ],
)
def test_direct_entry_and_fresh_process_have_identical_safe_behavior(tmp_path, capfd, case):
    cli = import_module("cyberpilot_autotune.replay.cli")
    path = write_document(tmp_path, replay_document())
    args = ["run", str(path)]
    if case == "verify":
        args = [
            "verify",
            str(FIXTURES / "golden_v1.json"),
            str(FIXTURES / "golden_v1.expected.json"),
        ]
    elif case == "verify-all":
        args = ["verify-all", str(FIXTURES)]
    elif case == "schema":
        path.write_text("PRIVATE_INVALID")
    elif case == "unsupported":
        document = replay_document()
        document["schema_version"] = 99
        path.write_text(json.dumps(document))
    elif case in ("mismatch", "bad_expected"):
        expected = tmp_path / "expected.json"
        expected.write_text("{}" if case == "mismatch" else '{"x":1,"x":2}')
        args = ["verify", str(path), str(expected)]
    elif case == "missing":
        args = ["run", str(tmp_path / "PRIVATE_MISSING")]
    elif case == "invalid_args":
        args = ["run", "--update-golden", "PRIVATE"]
    elif case == "oversized":
        path.write_bytes(b" " * (256 * 1024 + 1))
    elif case == "unicode":
        path.write_bytes(b"\xff")
    elif case == "bad_directory":
        args = ["verify-all", str(tmp_path / "PRIVATE_MISSING")]
    elif case == "empty":
        args = ["verify-all", str(tmp_path)]
    direct_code = cli.main(args)
    direct = capfd.readouterr()
    fresh = invoke(*args)
    assert direct_code == fresh.returncode
    assert direct.out.encode() == fresh.stdout
    assert direct.err.encode() == fresh.stderr
