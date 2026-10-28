"""Caller-created public replay contracts also reject malformed nested values."""

import json
from dataclasses import replace
from fractions import Fraction

import pytest

from cyberpilot_autotune.contracts import ValidationError
from cyberpilot_autotune.replay import ReplayLatency, load_replay, run_replay
from tests.fixtures.replay_data import replay_document
from tests.integration.test_replay_runner import Timer


def scenario():
    return load_replay(json.dumps(replay_document()))


@pytest.mark.parametrize(
    "changes",
    [
        {"parameter_spec": None},
        {"gate_config": None},
        {"learner_config": None},
        {"baseline_parameters": {"synthetic.test_only": 21}},
    ],
)
def test_direct_scenario_rejects_invalid_configurations(changes):
    with pytest.raises(ValidationError):
        replace(scenario(), **changes)


def test_direct_event_and_loader_reject_incorrect_types():
    with pytest.raises(ValidationError):
        replace(scenario().events[0], observation=None)
    with pytest.raises(ValidationError):
        load_replay(b"{}")
    with pytest.raises(ValidationError):
        run_replay(None)


@pytest.mark.parametrize(
    "changes",
    [
        {"event_count": -1},
        {"maximum_proposed_delta": -Fraction(1)},
        {"maximum_proposed_delta": 0.5},
        {"rejection_counts": []},
        {"rejection_counts": {"INTERNAL_ERROR": 1}},
    ],
)
def test_summary_rejects_invalid_metrics_or_untyped_reason_counts(changes):
    report = run_replay(scenario(), timer_ns=Timer())
    with pytest.raises(ValidationError):
        replace(report.summary, **changes)


def test_report_requires_matching_trace_measurement_and_event_counts():
    report = run_replay(scenario(), timer_ns=Timer())
    for changes in (
        {"scenario": None},
        {"off_results": ()},
        {"latency": ReplayLatency((), ())},
        {"summary": replace(report.summary, event_count=0)},
    ):
        with pytest.raises(ValidationError):
            replace(report, **changes)
    for invalid in [(-1,), (True,), (1.5,)]:
        with pytest.raises(ValidationError):
            ReplayLatency(invalid, (0,))


def test_latency_timer_regression_never_produces_an_accepted_report():
    ticks = iter((10, 9))
    with pytest.raises(ValidationError, match="timer regressed"):
        run_replay(scenario(), timer_ns=lambda: next(ticks))
