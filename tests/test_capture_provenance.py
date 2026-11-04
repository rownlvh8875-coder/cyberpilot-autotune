"""Supplied metadata consistency is not observed capture or runtime authority."""

from dataclasses import FrozenInstanceError, fields, replace

import pytest

from tests.fixtures.capture_provenance import (
    api,
    document,
    evaluate,
    find,
    materialize,
    registration,
    renumber,
)

KEYS = [
    (row["target_path"], role["role"])
    for row in registration()["catalog"]["rows"]
    for role in row["required_witnesses"]
]
COMMAND_TARGET = "commands.O-PYTEST.cohort_id"
COMMAND_ROLE = "CONSUMED_COMMAND_SOURCE"


def codes(result, category="errors"):
    return {issue.code for issue in getattr(result, category)}


def facets(value):
    assert value.status == "BLOCKED" and value.mapping_status == "PROVENANCE_METADATA_ONLY"
    assert value.profile_record is None and value.H_executed is False
    assert value.integrated_admission is False and value.content_identity_only is True
    assert value.atomicity == "NOT_ESTABLISHED"
    assert len(value.permissions) == 9 and all(flag is False for _, flag in value.permissions)


def test_complete_fictional_metadata_is_not_capture_or_admission():
    module = api()
    bundle = materialize(document())
    result = module.assess_capture_bundle(bundle)
    assert len(bundle.witnesses) == 273 and len({w.target_path for w in bundle.witnesses}) == 132
    assert result.alignment_status == "COHORT_METADATA_CONSISTENT"
    assert result.errors == result.unavailable == ()
    for obj in (
        bundle,
        bundle.epoch,
        bundle.witnesses[0],
        bundle.witnesses[0].context,
        module.CaptureIssue("WITNESS_MISSING", *KEYS[0], "witnesses"),
        result,
    ):
        facets(obj)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            obj.H_executed = True
        assert obj.H_executed is False


def test_empty_witness_inventory_is_not_success():
    doc = document()
    doc["witnesses"] = []
    result = evaluate(doc)
    assert result.alignment_status == "UNAVAILABLE"
    assert len(result.unavailable) == 273 and codes(result, "unavailable") == {"WITNESS_MISSING"}


@pytest.mark.parametrize("key", KEYS)
def test_each_required_witness_is_independently_required(key):
    doc = document()
    doc["witnesses"] = [w for w in doc["witnesses"] if (w["target_path"], w["role"]) != key]
    result = evaluate(doc)
    assert result.alignment_status == "UNAVAILABLE"
    assert [(i.code, i.target_path, i.role, i.field) for i in result.unavailable] == [
        ("WITNESS_MISSING", *key, "witnesses")
    ]


@pytest.mark.parametrize("field", [None, "run_id", "policy_digest", "clock_domain"])
def test_missing_root_identity_never_borrows_witness_values(field):
    doc = document()
    if field is None:
        doc["epoch"] = None
    else:
        doc["epoch"][field] = None
    result = evaluate(doc)
    assert result.alignment_status == "UNAVAILABLE" and "EPOCH_UNAVAILABLE" in codes(
        result, "unavailable"
    )


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("run_id", "5" * 32, "EPOCH_MISMATCH"),
        ("policy_digest", "5" * 64, "EPOCH_MISMATCH"),
        ("clock_domain", "synthetic-other-clock", "CLOCK_DOMAIN_MISMATCH"),
    ],
)
@pytest.mark.parametrize("root_missing", [False, True])
def test_known_peer_epoch_conflict_survives_missing_root(field, value, code, root_missing):
    doc = document()
    if root_missing:
        doc["epoch"] = None
    find(doc)["context"]["epoch"][field] = value
    result = evaluate(doc)
    assert result.alignment_status == "REJECTED" and code in codes(result)
    marked = [i for i in result.errors if i.code == code]
    assert {(i.target_path, i.role) for i in marked if i.target_path != "@bundle"} == set(KEYS)
    if root_missing:
        assert "EPOCH_UNAVAILABLE" in codes(result, "unavailable")


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("command_id", "D-PYTEST", "COMMAND_MISMATCH"),
        ("attempt", 1, "CONTEXT_CHANGED"),
        ("boundary_digest", "5" * 64, "CONTEXT_CHANGED"),
        ("boundary_generation", 1, "CONTEXT_CHANGED"),
    ],
)
def test_command_context_changes_are_not_pooled(field, value, code):
    doc = document()
    find(doc, COMMAND_TARGET, COMMAND_ROLE)["context"][field] = value
    assert code in codes(evaluate(doc))


@pytest.mark.parametrize(
    "field", ["command_id", "attempt", "boundary_digest", "boundary_generation", "epoch"]
)
def test_each_missing_command_context_fact_is_unavailable(field):
    doc = document()
    find(doc, COMMAND_TARGET, COMMAND_ROLE)["context"][field] = None
    assert "CONTEXT_UNAVAILABLE" in codes(evaluate(doc), "unavailable")


def test_batch_command_metadata_is_not_a_missing_command():
    doc = document()
    w = find(doc)
    w["context"].update(command_id="O-PYTEST", attempt=0)
    assert "COMMAND_MISMATCH" in codes(evaluate(doc))


def test_batch_boundary_cannot_be_reused_for_command():
    doc = document()
    batch = find(doc)["context"]["boundary_digest"]
    for w in doc["witnesses"]:
        if w["context"]["command_id"] == "O-PYTEST":
            w["context"]["boundary_digest"] = batch
    assert "BOUNDARY_REUSE" in codes(evaluate(doc))


@pytest.mark.parametrize(
    "field", ["source_id", "event_id", "sequence", "event_time_ns", "content_digest", "context"]
)
def test_missing_event_identity_content_or_context_is_not_a_default(field):
    doc = document()
    find(doc)[field] = None
    result = evaluate(doc)
    expected = (
        "CONTENT_REFERENCE_UNAVAILABLE"
        if field == "content_digest"
        else ("CONTEXT_UNAVAILABLE" if field == "context" else "EVENT_IDENTITY_UNAVAILABLE")
    )
    assert expected in codes(result, "unavailable") and result.alignment_status == "UNAVAILABLE"


def test_legitimate_shared_event_is_not_a_duplicate_witness_key():
    doc = document()
    a = find(doc)
    b = find(doc, role="REVIEWED_CONTENT")
    b.update({k: v for k, v in a.items() if k not in ("target_path", "role")})
    assert evaluate(doc).alignment_status == "COHORT_METADATA_CONSISTENT"


@pytest.mark.parametrize(
    "mode", ["source_pair", "partial_source", "partial_sequence", "partial_content"]
)
def test_partial_event_identity_never_hides_known_alias(mode):
    doc = document()
    a = find(doc)
    b = find(doc, role="REVIEWED_CONTENT")
    if mode == "source_pair":
        b["sequence"] = a["sequence"]
        b["event_time_ns"] = None
    else:
        b["event_id"] = a["event_id"]
        if mode == "partial_source":
            b.update(source_id="5" * 64, sequence=None)
        if mode == "partial_sequence":
            b.update(source_id=None, sequence=a["sequence"] + 1)
        if mode == "partial_content":
            b.update(source_id=None, sequence=None, content_digest="5" * 64)
    result = evaluate(doc)
    assert "SOURCE_EVENT_ALIAS" in codes(result)
    assert "EVENT_IDENTITY_UNAVAILABLE" in codes(result, "unavailable")


@pytest.mark.parametrize("domain", ["same", "missing", "other", "missing_root"])
def test_window_comparison_requires_known_equal_domains(domain):
    doc = document()
    w = find(doc)
    w["event_time_ns"] = 200
    renumber(doc["witnesses"])
    if domain == "missing":
        w["context"]["epoch"]["clock_domain"] = None
    if domain == "other":
        w["context"]["epoch"]["clock_domain"] = "other"
    if domain == "missing_root":
        doc["epoch"]["clock_domain"] = None
    result = evaluate(doc)
    assert ("EVENT_OUTSIDE_CAPTURE_WINDOW" in codes(result)) is (domain == "same")
    if domain == "other":
        assert "CLOCK_DOMAIN_MISMATCH" in codes(result)


@pytest.mark.parametrize("domain", ["same", "missing", "other"])
def test_source_time_order_requires_comparable_domains(domain):
    doc = document()
    w = find(doc)
    w["event_time_ns"] = 80
    if domain == "missing":
        w["context"]["epoch"]["clock_domain"] = None
    if domain == "other":
        w["context"]["epoch"]["clock_domain"] = "other"
    assert ("TIME_ORDER_INVALID" in codes(evaluate(doc))) is (domain == "same")


@pytest.mark.parametrize("domain", ["same", "missing", "other", "missing_root"])
def test_stage_order_is_independent_of_source_order_and_root_availability(domain):
    doc = document()
    finish = find(doc, "cohorts.O.revision", "CONSUMED_SOURCE:O-PYTEST")
    finish.update(stage="COMMAND_FINISH", event_time_ns=50)
    for w in doc["witnesses"]:
        if w["context"]["command_id"] == "O-PYTEST" and w["stage"] == "COMMAND_START":
            w["event_time_ns"] = 60
    renumber(doc["witnesses"])
    if domain == "missing":
        finish["context"]["epoch"]["clock_domain"] = None
    if domain == "other":
        finish["context"]["epoch"]["clock_domain"] = "other"
    if domain == "missing_root":
        doc["epoch"] = None
    assert ("STAGE_ORDER_INVALID" in codes(evaluate(doc))) is (domain in ("same", "missing_root"))


def test_reversed_root_window_is_invalid_even_with_no_named_domain():
    doc = document()
    doc["epoch"] = None
    doc.update(capture_begin_ns=100, capture_end_ns=0)
    result = evaluate(doc)
    assert "TIME_ORDER_INVALID" in codes(result) and "EPOCH_UNAVAILABLE" in codes(
        result, "unavailable"
    )


@pytest.mark.parametrize("field", ["capture_begin_ns", "capture_end_ns"])
def test_missing_capture_window_is_unavailable(field):
    doc = document()
    doc[field] = None
    assert "CAPTURE_WINDOW_UNAVAILABLE" in codes(evaluate(doc), "unavailable")


@pytest.mark.parametrize(
    "outcome,code,category",
    [
        ("NEGATIVE_CLAIM", "NEGATIVE_CLAIM", "errors"),
        ("ERROR_CLAIM", "PRODUCER_REPORTED_ERROR", "errors"),
        ("UNAVAILABLE_CLAIM", "WITNESS_UNAVAILABLE", "unavailable"),
    ],
)
def test_known_outcome_survives_missing_epoch(outcome, code, category):
    doc = document()
    doc["epoch"] = None
    find(doc)["outcome"] = outcome
    result = evaluate(doc)
    assert code in codes(result, category) and "EPOCH_UNAVAILABLE" in codes(result, "unavailable")


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_path", "PRIVATE_CANARY"),
        ("role", "PRIVATE_CANARY"),
        ("stage", "COMMAND_FINISH"),
        ("outcome", "PRIVATE_CANARY"),
        ("source_id", "PRIVATE_CANARY"),
        ("event_id", "F" * 64),
        ("sequence", True),
        ("sequence", -1),
        ("sequence", 2**64),
        ("event_time_ns", 1.0),
        ("event_time_ns", float("nan")),
        ("event_time_ns", float("inf")),
    ],
)
def test_malformed_witnesses_raise_constant_no_echo(field, value):
    doc = document()
    find(doc)[field] = value
    with pytest.raises(ValueError) as caught:
        evaluate(doc)
    assert "PRIVATE_CANARY" not in str(caught.value)


def test_duplicate_target_role_is_structural_even_for_identical_event():
    doc = document()
    doc["witnesses"].append(dict(doc["witnesses"][0]))
    with pytest.raises(ValueError):
        evaluate(doc)


def test_owned_tuple_order_and_forged_graph_revalidation():
    module = api()
    bundle = materialize(document())
    reversed_bundle = replace(bundle, witnesses=tuple(reversed(bundle.witnesses)))
    assert reversed_bundle == bundle and reversed_bundle.witnesses is not bundle.witnesses
    with pytest.raises(ValueError):
        replace(bundle, witnesses=list(bundle.witnesses))
    witness = bundle.witnesses[0]
    with pytest.raises(FrozenInstanceError):
        witness.sequence = 3
    object.__setattr__(witness, "event_id", "PRIVATE_CANARY")
    with pytest.raises(ValueError):
        module.assess_capture_bundle(bundle)


def test_decision_issues_are_closed_and_category_separated():
    module = api()
    item = module.CaptureIssue("WITNESS_MISSING", *KEYS[0], "witnesses")
    decision = module.CaptureAlignmentDecision((), (item, item))
    assert len(decision.unavailable) == 1
    with pytest.raises(ValueError):
        module.CaptureAlignmentDecision((item,), ())
    with pytest.raises(ValueError):
        module.CaptureIssue("UNKNOWN", *KEYS[0], "witnesses")
    with pytest.raises(ValueError):
        module.CaptureIssue("WITNESS_MISSING", "UNKNOWN", "UNKNOWN", "witnesses")
    with pytest.raises(ValueError):
        module.CaptureIssue("WITNESS_MISSING", *KEYS[0], "UNKNOWN")
    assert {f.name for f in fields(decision)} == {"errors", "unavailable"}
