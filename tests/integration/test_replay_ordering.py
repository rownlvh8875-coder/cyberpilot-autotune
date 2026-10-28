"""Observe the unchanged engine's conservative sequence/time maxima policy."""

import json

from cyberpilot_autotune.replay import load_replay, run_replay
from cyberpilot_autotune.safety.reasons import ReasonCode as R
from tests.fixtures.replay_data import ordering_document


def test_anomalies_reach_engine_and_retain_baseline_without_internal_errors():
    report = run_replay(load_replay(json.dumps(ordering_document())))
    reasons = [
        [item.reason for item in (*result.events, *result.gate_decisions)]
        for result in report.shadow_results
    ]
    assert reasons == [
        [],
        [],
        [R.OUT_OF_ORDER],
        [R.OUT_OF_ORDER],
        [R.OUT_OF_ORDER],
        [R.FUTURE_TIMESTAMP],
        [],
        [R.CONTROL_INACTIVE],
        [R.OUT_OF_ORDER],
        [],
        [R.OUT_OF_ORDER],
        [R.OUT_OF_ORDER],
        [],
        [],
        [R.ACCEPTED_FOR_SHADOW],
        [R.ACCEPTED_FOR_SHADOW],
    ]
    assert [r.observation_sequence for r in report.shadow_results] == [
        10,
        11,
        11,
        9,
        12,
        13,
        14,
        15,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
    ]
    assert report.summary.rejection_counts == {
        R.OUT_OF_ORDER: 6,
        R.FUTURE_TIMESTAMP: 1,
        R.CONTROL_INACTIVE: 1,
    }
    assert report.summary.proposal_count == report.summary.eligible_count == 2
    assert report.summary.internal_error_count == 0
    assert report.software_checks_passed
    assert all(
        result.effective_parameters == report.scenario.baseline_parameters
        for result in (*report.off_results, *report.shadow_results)
    )
