"""Independent digest domains and compatibility with the historical result hash."""

import json
import re
from dataclasses import replace
from importlib import import_module

from cyberpilot_autotune.replay import load_replay, run_replay
from cyberpilot_autotune.replay.canonical import canonical_bytes
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from cyberpilot_autotune.telemetry.events import DiagnosticEvent
from tests.fixtures.replay_data import ordering_document, replay_document
from tests.integration.test_replay_runner import Timer


def hashes(report):
    return report.scenario_sha256, report.configuration_sha256, report.result_sha256


def test_three_hash_domains_are_lowercase_sha256_and_timer_independent():
    scenario = load_replay(json.dumps(replay_document()))
    a, b = run_replay(scenario, timer_ns=Timer()), run_replay(scenario, timer_ns=Timer(100))
    assert hashes(a) == hashes(b)
    assert all(re.fullmatch("[0-9a-f]{64}", value) for value in hashes(a))
    assert a.digest == a.result_sha256
    assert b"result_sha256" not in a.deterministic_bytes()
    assert b"latency" not in a.deterministic_bytes()
    import hashlib

    assert a.scenario_sha256 == hashlib.sha256(canonical_bytes(scenario)).hexdigest()
    config = {
        key: getattr(scenario, key)
        for key in (
            "scope",
            "learner_version",
            "time_domain",
            "baseline_parameters",
            "parameter_spec",
            "gate_config",
            "learner_config",
        )
    }
    assert a.configuration_sha256 == hashlib.sha256(canonical_bytes(config)).hexdigest()
    assert a.result_sha256 == hashlib.sha256(a.deterministic_bytes()).hexdigest()


def test_formatting_policy_input_and_output_changes_have_separate_hash_effects():
    document = replay_document()
    a = run_replay(load_replay(json.dumps(document)))
    b = run_replay(load_replay(json.dumps(document, sort_keys=True, indent=4)))
    assert hashes(a) == hashes(b)
    document["events"][0]["observation"]["speed_mps"] = 3.0
    changed_input = run_replay(load_replay(json.dumps(document)))
    assert changed_input.scenario_sha256 != a.scenario_sha256
    assert changed_input.configuration_sha256 == a.configuration_sha256
    document["learner_config"]["alpha"] = 0.25
    changed_policy = run_replay(load_replay(json.dumps(document)))
    assert changed_policy.configuration_sha256 != a.configuration_sha256
    mutated = replace(
        a,
        shadow_results=(
            replace(a.shadow_results[0], events=(DiagnosticEvent(R.LOW_CONFIDENCE, "Synthetic"),)),
            *a.shadow_results[1:],
        ),
    )
    assert mutated.scenario_sha256 == a.scenario_sha256
    assert mutated.configuration_sha256 == a.configuration_sha256
    assert mutated.result_sha256 != a.result_sha256


def test_characterization_observes_sample_counts_from_same_real_learner_run():
    api = import_module("cyberpilot_autotune.replay")
    scenario = load_replay(json.dumps(ordering_document()))
    report, counts = api.characterize_replay(scenario, timer_ns=Timer())
    assert counts == (1, 2, None, None, None, None, 1, None, None, 1, None, None, 1, 2, 3, 4)
    assert report.digest == run_replay(scenario, timer_ns=Timer(10)).digest
    assert isinstance(counts, tuple)
