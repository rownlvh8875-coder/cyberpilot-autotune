"""Generated synthetic streams retain baseline and deterministic evidence."""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.contracts import ValidationError
from cyberpilot_autotune.replay import load_replay, run_replay
from tests.fixtures.replay_data import replay_document, replay_event
from tests.integration.test_replay_runner import Timer


@settings(max_examples=50, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from([None, False, True]),
            st.booleans(),
            st.booleans(),
            st.sampled_from([0.0, 0.5, 1.0, 2.0]),
            st.sampled_from([-0.75, -0.25, 0.0, 0.25, 0.75]),
        ),
        min_size=1,
        max_size=25,
    )
)
def test_generated_streams_have_fresh_state_stable_hash_and_baseline_identity(frames):
    document = replay_document()
    document["events"] = [
        replay_event(
            i,
            residual=residual,
            control_active=active,
            driver_override=override,
            controller_saturated=saturated,
            speed_mps=speed,
        )
        for i, (active, override, saturated, speed, residual) in enumerate(frames)
    ]
    scenario = load_replay(json.dumps(document))
    first = run_replay(scenario, timer_ns=Timer(1))
    second = run_replay(scenario, timer_ns=Timer(100))
    assert first.digest == second.digest
    assert first.software_checks_passed
    assert first.summary.event_count == len(frames)
    for result in (*first.off_results, *first.shadow_results):
        assert result.effective_parameters == scenario.baseline_parameters


@settings(max_examples=75, deadline=None)
@given(st.text(max_size=300))
def test_arbitrary_non_schema_text_is_rejected_as_typed_error(raw):
    with pytest.raises(ValidationError):
        load_replay(raw)


@given(st.integers(min_value=0, max_value=1))
def test_reordered_evaluation_clocks_never_enter_runner(index):
    document = replay_document()
    document["events"][index], document["events"][index + 1] = (
        document["events"][index + 1],
        document["events"][index],
    )
    with pytest.raises(ValidationError):
        load_replay(json.dumps(document))


@settings(max_examples=50, deadline=None)
@given(st.lists(st.tuples(st.integers(0, 30), st.integers(0, 200)), min_size=1, max_size=25))
def test_arbitrary_observation_order_remains_fail_closed_with_monotonic_clocks(frames):
    document = replay_document()
    document["events"] = []
    for i, (sequence, capture) in enumerate(frames):
        event = replay_event(i, sequence=sequence, timestamp_s=capture)
        event["clock_before_s"] = event["clock_after_s"] = 100 + i
        document["events"].append(event)
    report = run_replay(load_replay(json.dumps(document)), timer_ns=Timer())
    assert report.software_checks_passed
    assert all(
        result.effective_parameters == document["baseline_parameters"]
        for result in report.shadow_results
    )
