"""Catch object/hash substitution, lifetime joins, incomplete sets and authority escalation."""

import copy
import json

import pytest

from tests.audit.guest_input_handoff_examples import CASES, complete, event, example
from tests.audit.guest_input_handoff_model import evaluate, graph_digest


@pytest.mark.parametrize("case,status,reason", CASES)
def test_literal_synthetic_acceptance(case, status, reason):
    graph = example(case)
    original = copy.deepcopy(graph)
    decision = evaluate(graph)
    assert decision["status"] == status
    assert decision["reasons"] == ([] if reason is None else [reason])
    assert decision["overall"] == "BLOCKED"
    assert len(decision["permissions"]) == 9
    assert all(v is False for v in decision["permissions"].values())
    assert decision["successful_prohibited_handles"] is None
    assert decision["successful_prohibited_effects"] is None
    assert graph == original


def test_digest_set_order_is_not_event_order():
    graph = complete(2)
    original = graph_digest(graph)
    graph["manifest"].reverse()
    assert graph_digest(graph) == original
    graph["events"][0], graph["events"][1] = graph["events"][1], graph["events"][0]
    assert graph_digest(graph) != original
    assert evaluate(graph)["status"] == "REJECTED"


def test_digest_field_order_does_not_change_identity():
    graph = complete()
    reordered = json.loads(json.dumps(graph, sort_keys=True))
    assert graph_digest(graph) == graph_digest(reordered)
    graph["context"]["source_revision"] = "e" * 40
    assert graph_digest(graph) != graph_digest(reordered)


@pytest.mark.parametrize("value", [None, False, 0, [], {}, "caller says ready"])
def test_malformed_root_cannot_authorize(value):
    decision = evaluate(value)
    assert decision["status"] == "REJECTED"
    assert all(v is False for v in decision["permissions"].values())


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, None, -1, 2**64])
def test_nonfinite_coercions_or_unknown_time_reject(value):
    graph = complete()
    event(graph, "READY")["time_ns"] = value
    assert evaluate(graph)["status"] == "REJECTED"


def test_permissions_in_input_are_not_an_authority_channel():
    graph = complete()
    graph["application_authorized"] = True
    decision = evaluate(graph)
    assert decision["status"] == "REJECTED"
    assert all(v is False for v in decision["permissions"].values())


def test_none_and_real_zero_have_different_content_identity():
    graph = complete()
    zero = graph_digest(graph)
    event(graph, "STOPPED")["data"]["extra_fd_count"] = None
    assert graph_digest(graph) != zero
    assert evaluate(graph)["status"] == "REJECTED"


@pytest.mark.parametrize("kind", ["PIN", "SEAL", "BIND"])
@pytest.mark.parametrize("field,value", [("dev", True), ("dev", 1.0), ("ino", 10.0)])
def test_object_binding_does_not_coerce_kernel_identity(kind, field, value):
    graph = complete()
    event(graph, kind)["data"][field] = value
    assert evaluate(graph)["reasons"] == ["SCHEMA_INVALID"]
