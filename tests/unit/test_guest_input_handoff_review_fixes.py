"""I1: a controlled inherited handoff needs an explicit observed cohort transition."""

import copy

import pytest

from tests.audit.guest_input_handoff_examples import complete, event
from tests.audit.guest_input_handoff_model import evaluate


def renumber(graph):
    for i, row in enumerate(graph["events"]):
        row.update(seq=i, time_ns=i + 10)


def test_missing_controlled_exec_transition_cannot_pass():
    graph = complete()
    graph["events"] = [e for e in graph["events"] if e["kind"] != "EXEC_TRANSITION"]
    renumber(graph)
    assert evaluate(graph)["status"] == "REJECTED"


def test_previous_uncontrolled_v1_cannot_silently_fallback():
    graph = complete()
    graph["schema"] = "guest-input-handoff-design-v1"
    assert evaluate(graph)["reasons"] == ["SCHEMA_INVALID"]


@pytest.mark.parametrize(
    "side,field,value",
    [
        ("predecessor", "exec_generation", 8),
        ("predecessor", "image_digest", "f" * 64),
        ("successor", "fd_table_generation", 8),
        ("successor", "task_generation", 8),
    ],
)
def test_controlled_exec_must_match_both_actual_cohorts(side, field, value):
    graph = complete()
    transitions = [e for e in graph["events"] if e["kind"] == "EXEC_TRANSITION"]
    assert len(transitions) == 1, "controlled exec must be represented"
    transitions[0]["data"][side][field] = value
    assert evaluate(graph)["reasons"] == ["COHORT_MISMATCH"]


@pytest.mark.parametrize("kind", ["BIND", "READY", "PREAD_FULL", "CLOSE", "FINISH"])
def test_post_exec_stages_cannot_reuse_bootstrap_cohort(kind):
    graph = complete()
    assert "bootstrap_cohort" in graph["context"], "pre-exec actual identity must be explicit"
    event(graph, kind)["data"]["cohort"] = copy.deepcopy(graph["context"]["bootstrap_cohort"])
    assert evaluate(graph)["reasons"] == ["COHORT_MISMATCH"]


@pytest.mark.parametrize(
    "field,value", [("consumer_task_generation", 9), ("consumer_exec_generation", 3)]
)
def test_header_cannot_join_unrelated_task_or_skip_controlled_exec(field, value):
    graph = complete()
    graph["context"][field] = value
    assert evaluate(graph)["reasons"] == ["COHORT_TRANSITION_INVALID"]


@pytest.mark.parametrize("value", [True, 1.0, None])
def test_actual_cohort_integer_fields_do_not_coerce(value):
    graph = complete()
    assert "cohort" in event(graph, "BIND")["data"]
    event(graph, "BIND")["data"]["cohort"]["fd_table_generation"] = value
    assert evaluate(graph)["reasons"] == ["SCHEMA_INVALID"]
