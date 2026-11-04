"""Supplied metadata consistency is not observed capture or runtime authority."""

from dataclasses import FrozenInstanceError, fields, replace
from random import Random

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


@pytest.mark.parametrize("domain", ["same", "missing", "other", "missing_root"])
def test_source_time_order_requires_comparable_domains(domain):
    doc = document()
    w = find(doc)
    w["event_time_ns"] = 80
    if domain == "missing":
        w["context"]["epoch"]["clock_domain"] = None
    if domain == "other":
        w["context"]["epoch"]["clock_domain"] = "other"
    if domain == "missing_root":
        doc["epoch"] = None
    assert ("TIME_ORDER_INVALID" in codes(evaluate(doc))) is (domain in ("same", "missing_root"))


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


def test_reserved_bundle_locator_cannot_bypass_exact_string_type_validation():
    module = api()

    class ForeignText(str):
        pass

    with pytest.raises(ValueError):
        module.CaptureIssue("EPOCH_UNAVAILABLE", ForeignText("@bundle"), "BUNDLE", "epoch")


def test_locator_type_is_rejected_before_foreign_equality_can_execute():
    module = api()

    class ForeignText(str):
        def __eq__(self, other):
            raise AssertionError("foreign equality executed")

    with pytest.raises(ValueError):
        module.CaptureIssue("EPOCH_UNAVAILABLE", ForeignText("@bundle"), "BUNDLE", "epoch")


def test_incomplete_and_foreign_graphs_fail_without_input_bearing_exception_context():
    module = api()
    incomplete = object.__new__(module.CaptureWitnessBundle)
    with pytest.raises(ValueError) as caught:
        module.assess_capture_bundle(incomplete)
    assert caught.value.__context__ is None
    with pytest.raises(ValueError):
        module.assess_capture_bundle(object())

    class ForeignBundle(module.CaptureWitnessBundle):
        pass

    with pytest.raises(ValueError):
        module.assess_capture_bundle(object.__new__(ForeignBundle))
    bundle = materialize(document())
    for cls in (module.CaptureEpoch, module.WitnessContext, module.CaptureWitness):
        forged = object.__new__(cls)
        with pytest.raises(ValueError):
            if cls is module.CaptureEpoch:
                replace(bundle, epoch=forged)
            elif cls is module.WitnessContext:
                replace(bundle.witnesses[0], context=forged)
            else:
                replace(bundle, witnesses=(forged,))


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", ""),
        ("run_id", "A" * 32),
        ("run_id", 1),
        ("policy_digest", True),
        ("clock_domain", ""),
        ("clock_domain", "x" * 129),
        ("clock_domain", "bad domain"),
        ("clock_domain", "비공개"),
        ("clock_domain", 0),
    ],
)
def test_epoch_primitive_grammar_is_strict(field, value):
    doc = document()
    doc["epoch"][field] = value
    with pytest.raises(ValueError):
        evaluate(doc)


@pytest.mark.parametrize(
    "field,value",
    [
        ("command_id", False),
        ("command_id", "UNREGISTERED"),
        ("attempt", True),
        ("attempt", -1),
        ("attempt", 2**64),
        ("boundary_digest", "UPPER"),
        ("boundary_generation", float("inf")),
        ("boundary_generation", -1),
    ],
)
def test_context_primitive_grammar_is_strict(field, value):
    doc = document()
    find(doc)["context"][field] = value
    with pytest.raises(ValueError):
        evaluate(doc)


def test_uint64_max_is_exact_data_not_missing_or_coerced():
    doc = document()
    find(doc)["sequence"] = 2**64 - 1
    bundle = materialize(doc)
    observed = next(
        w
        for w in bundle.witnesses
        if (w.target_path, w.role) == ("artifacts.executor_content.sha256", "PREPARED_CONTENT")
    )
    assert observed.sequence == 2**64 - 1
    facets(api().assess_capture_bundle(bundle))


def test_missing_context_epoch_leaf_and_issue_containers_are_closed():
    doc = document()
    find(doc)["context"]["epoch"]["run_id"] = None
    assert "CONTEXT_UNAVAILABLE" in codes(evaluate(doc), "unavailable")
    module = api()
    with pytest.raises(ValueError):
        module.CaptureAlignmentDecision([], ())
    with pytest.raises(ValueError):
        module.CaptureAlignmentDecision((), [])


@pytest.mark.parametrize("field,value", [("run_id", "5" * 32), ("policy_digest", "5" * 64)])
def test_known_wrong_root_fact_is_not_repaired_from_witnesses(field, value):
    doc = document()
    doc["epoch"][field] = value
    result = evaluate(doc)
    assert "EPOCH_MISMATCH" in codes(result)
    assert any(i.target_path == "@bundle" and i.field == "epoch." + field for i in result.errors)


def test_known_zero_instants_and_inclusive_window_are_not_missing():
    doc = document()
    doc["capture_end_ns"] = 0
    for witness in doc["witnesses"]:
        witness["event_time_ns"] = 0
    assert evaluate(doc).alignment_status == "COHORT_METADATA_CONSISTENT"
    doc = document()
    find(doc)["event_time_ns"] = 100
    renumber(doc["witnesses"])
    assert evaluate(doc).alignment_status == "COHORT_METADATA_CONSISTENT"


def test_issue_order_is_owned_sorted_and_deduplicated():
    module = api()
    a = module.CaptureIssue("WITNESS_MISSING", *KEYS[0], "witnesses")
    b = module.CaptureIssue("WITNESS_MISSING", *KEYS[-1], "witnesses")
    first = module.CaptureAlignmentDecision((), (a, b, a))
    second = module.CaptureAlignmentDecision((), (b, a))
    assert first == second and len(first.unavailable) == 2


@pytest.mark.parametrize("conflict", [False, True])
def test_partial_identity_bridges_cannot_hide_a_proven_event_conflict(conflict):
    doc = document()
    a = find(doc)
    b = find(doc, role="REVIEWED_CONTENT")
    c = find(doc, "artifacts.bootstrap_content.sha256", "PREPARED_CONTENT")
    a["event_id"] = None
    b.update(source_id=a["source_id"], sequence=a["sequence"], event_time_ns=None)
    c.update(
        source_id=None, sequence=None, event_id=b["event_id"], event_time_ns=1 if conflict else 0
    )
    bundle = materialize(doc)
    result = api().assess_capture_bundle(bundle)
    assert ("SOURCE_EVENT_ALIAS" in codes(result)) is conflict
    assert "EVENT_IDENTITY_UNAVAILABLE" in codes(result, "unavailable")
    assert (
        next(
            w
            for w in bundle.witnesses
            if (w.target_path, w.role) == ("artifacts.executor_content.sha256", "PREPARED_CONTENT")
        ).event_id
        is None
    )


@pytest.mark.parametrize("batch_context_missing", [False, True])
def test_known_batch_scope_is_not_unknown_command_scope_for_shared_event(batch_context_missing):
    doc = document()
    a = find(doc)
    b = find(doc, "commands.O-PYTEST.limits.memory_max_bytes.value", "APPROVED_LIMIT")
    for name in ("source_id", "event_id", "sequence", "event_time_ns", "stage", "content_digest"):
        b[name] = a[name]
    for witness in (a, b):
        witness["context"].update(boundary_digest=None, boundary_generation=None)
    if batch_context_missing:
        a["context"] = None
    result = evaluate(doc)
    assert ("SOURCE_EVENT_ALIAS" in codes(result)) is (not batch_context_missing)


@pytest.mark.parametrize("seed", range(10))
def test_time_and_stage_reason_sets_match_independent_pairwise_oracle(seed):
    rng = Random(seed)
    doc = document()
    doc["witnesses"] = [w for w in doc["witnesses"] if w["context"]["command_id"] == "O-PYTEST"][
        :16
    ]
    allowed = {
        (row["target_path"], r["role"]): r["allowed_stages"]
        for row in registration()["catalog"]["rows"]
        for r in row["required_witnesses"]
    }
    for w in doc["witnesses"]:
        w["source_id"] = rng.choice([None, "5" * 64, "6" * 64])
        w["sequence"] = rng.choice([None, 0, 1, 2, 3])
        w["event_time_ns"] = rng.choice([None, 0, 10, 50, 80])
        w["stage"] = rng.choice(allowed[w["target_path"], w["role"]])
        w["context"]["epoch"]["clock_domain"] = rng.choice([None, "synthetic-H-clock-v1", "other"])
    order = [
        "BOUNDARY_READY",
        "LIMITS_APPLIED",
        "PRE_RELEASE",
        "COMMAND_START",
        "COMMAND_FINISH",
        "BATCH_FINISH",
    ]
    expected_time, expected_stage = set(), set()
    for a in doc["witnesses"]:
        for b in doc["witnesses"]:
            ac = a["context"]["epoch"]["clock_domain"]
            bc = b["context"]["epoch"]["clock_domain"]
            if ac is None or ac != bc or a["event_time_ns"] is None or b["event_time_ns"] is None:
                continue
            if (
                a["source_id"] is not None
                and a["source_id"] == b["source_id"]
                and a["sequence"] is not None
                and b["sequence"] is not None
                and a["sequence"] < b["sequence"]
                and a["event_time_ns"] > b["event_time_ns"]
            ):
                expected_time.add((b["target_path"], b["role"], "event_time_ns"))
            if (
                a["stage"] in order
                and b["stage"] in order
                and order.index(a["stage"]) < order.index(b["stage"])
                and a["event_time_ns"] > b["event_time_ns"]
            ):
                expected_stage.add((b["target_path"], b["role"], "event_time_ns"))
    result = evaluate(doc)
    for code, expected in (
        ("TIME_ORDER_INVALID", expected_time),
        ("STAGE_ORDER_INVALID", expected_stage),
    ):
        assert {
            (i.target_path, i.role, i.field) for i in result.errors if i.code == code
        } == expected
