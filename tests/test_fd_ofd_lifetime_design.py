"""Breaks caught: guessed generations, alias/cohort drift, lost coverage and false authority."""

import copy

import pytest

from tests.audit.fd_ofd_lifetime_examples import catalog, complete
from tests.audit.fd_ofd_lifetime_model import context_digest, evaluate


def first(graph, kind):
    return next(e for e in graph["events"] if e["kind"] == kind)


@pytest.mark.parametrize(
    "scenario,tables,ofds",
    [
        ("basic", 1, 1),
        ("share", 1, 1),
        ("fork", 2, 1),
        ("unshare", 2, 1),
        ("exec_copy", 2, 1),
        ("unshare_same", 1, 1),
        ("reuse", 1, 2),
    ],
)
def test_synthetic_consistency_never_qualifies(scenario, tables, ofds):
    result = evaluate(complete(scenario))
    assert result.model_consistent is True
    assert result.synthetic_tables == tables
    assert result.synthetic_ofds == ofds
    assert result.status == "BLOCKED"
    assert result.actual_dropped_events is None
    assert result.global_prohibited_counts is None
    assert len(result.permissions) == 9 and all(v is False for _, v in result.permissions)


@pytest.mark.parametrize(
    "scenario,mutate",
    [
        ("basic", lambda g: first(g, "INSTALL")["data"].__setitem__(4, 1)),
        ("basic", lambda g: first(g, "DUP")["data"].__setitem__(4, 1)),
        ("basic", lambda g: first(g, "DUP")["data"].__setitem__(7, "DUP2")),
        ("basic", lambda g: first(g, "EXEC")["data"].__setitem__(6, [])),
        ("basic", lambda g: first(g, "EXEC")["data"].__setitem__(5, 2)),
        ("basic", lambda g: first(g, "CLOSE")["data"].__setitem__(5, [2, 0])),
        ("basic", lambda g: first(g, "INVENTORY")["data"].__setitem__(4, [[0, 0, [1, 0], False]])),
        ("fork", lambda g: first(g, "FORK")["data"].__setitem__(4, [1, 0])),
        ("share", lambda g: first(g, "FORK")["data"].__setitem__(4, [2, 0])),
        ("exec_copy", lambda g: first(g, "EXEC")["data"].__setitem__(3, [1, 0])),
        (
            "reuse",
            lambda g: [e for e in g["events"] if e["kind"] == "OFD_NEW"][1]["data"].__setitem__(
                2, [1, 0]
            ),
        ),
        (
            "reuse",
            lambda g: [e for e in g["events"] if e["kind"] == "INSTALL"][1]["data"].__setitem__(
                4, 0
            ),
        ),
        ("basic", lambda g: first(g, "TABLE_FREE")["data"].__setitem__(1, 3)),
        ("basic", lambda g: first(g, "REAP").__setitem__("kind", "TABLE_NEW")),
        ("basic", lambda g: first(g, "OFD_FREE")["data"].__setitem__(0, [1, 1])),
    ],
)
def test_detectable_lifetime_contradictions_reject(scenario, mutate):
    graph = complete(scenario)
    mutate(graph)
    assert evaluate(graph).model_consistent is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda g: g.__setitem__("evidence_class", "OBSERVED"),
        lambda g: g["coverage"]["cpus"][0].__setitem__("dropped", None),
        lambda g: g["coverage"]["cpus"][0].__setitem__("dropped", 1),
        lambda g: g["coverage"]["cpus"][1].__setitem__("drained", False),
        lambda g: g["coverage"]["cpus"].pop(),
        lambda g: g["coverage"]["cpus"][0].__setitem__("emitted", 0),
        lambda g: g["coverage"]["cpus"][0].__setitem__("last_source_seq", 0),
        lambda g: g["events"][3].__setitem__("cpu_seq", 99),
        lambda g: g["events"][3].__setitem__("seq", 99),
        lambda g: g["events"][3].__setitem__("context_digest", "d" * 64),
        lambda g: g["context"].__setitem__("clock_domain", "WALL_CLOCK"),
        lambda g: g["events"][3].__setitem__("kind", "SCM_RIGHTS_UNKNOWN"),
        lambda g: g["events"][3].__setitem__("time_ns", float("nan")),
        lambda g: g["events"][3].__setitem__("seq", True),
        lambda g: g["events"].reverse(),
    ],
)
def test_loss_context_and_scalar_claims_cannot_be_repaired(mutate):
    graph = complete()
    mutate(graph)
    result = evaluate(graph)
    assert result.model_consistent is False
    assert result.status == "BLOCKED"


def test_digest_is_content_identity_only_and_input_unchanged():
    graph = complete()
    saved = copy.deepcopy(graph)
    a = evaluate(graph)
    b = evaluate(dict(reversed(list(graph.items()))))
    assert a.digest == b.digest and graph == saved
    changed = copy.deepcopy(graph)
    changed["context"]["source_revision"] = "f" * 40
    digest = context_digest(changed["context"])
    for e in changed["events"]:
        e["context_digest"] = digest
    assert evaluate(changed).digest != a.digest


@pytest.mark.parametrize("case", catalog(), ids=lambda r: r["case_id"] + "_" + r["name"])
def test_hand_specified_published_counterexamples(case):
    result = evaluate(case["graph"])
    assert result.model_consistent is case["expected_consistent"]
    assert result.actual_dropped_events is None
    assert result.global_prohibited_counts is None


@pytest.mark.parametrize("value", [None, False, True, 0.0, float("inf"), [], {}, object()])
def test_exact_fd_scalar_rejects_unavailable_bool_float_and_custom(value):
    graph = complete()
    first(graph, "INSTALL")["data"][3] = value
    result = evaluate(graph)
    assert result.model_consistent is False
