"""Mutually linked claims can be diagnostic, never build/promotion authority."""

import importlib
from dataclasses import asdict, replace

import pytest

from tests.fixtures.guest_build_receipt import EMPTY_SHA, SHA_A, SHA_B, build, models, promotion


def evaluate(receipt=None, promotions=None):
    models()
    assert importlib.util.find_spec("compatibility.guest_build_receipt.evaluation") is not None
    value = build() if receipt is None else receipt
    claims = (promotion(value),) if promotions is None else promotions
    return importlib.import_module(
        "compatibility.guest_build_receipt.evaluation"
    ).evaluate_receipts(value, claims)


def changed_use(b, index, **changes):
    rows = list(b.uses)
    rows[index] = replace(rows[index], **changes)
    return replace(b, uses=rows)


def test_full_synthetic_chain_has_separate_counts_and_no_operational_permission():
    decision = evaluate()
    assert decision.status == "DIAGNOSTIC_CHAIN_CONSISTENT" and decision.reasons == ()
    assert (
        decision.read_events,
        decision.map_bindings,
        decision.exec_bindings,
        decision.metadata_events,
        decision.promotions_checked,
    ) == (1, 1, 1, 1, 1)
    assert decision.overall_status == "BLOCKED"
    for key in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert asdict(decision)[key] is False
    assert (
        decision.successful_prohibited_handles is None
        and decision.successful_prohibited_effects is None
    )
    m = models()
    observed = evaluate(replace(build(), evidence_kind=m.EvidenceKind.OBSERVED_UNTRUSTED))
    assert (
        observed.status == "DIAGNOSTIC_CHAIN_CONSISTENT"
        and observed.build_execution_allowed is False
    )


@pytest.mark.parametrize(
    "field,reason",
    [
        ("source_digest", "MISSING_SOURCE_COHORT"),
        ("toolchain_digest", "MISSING_TOOLCHAIN_COHORT"),
        ("recipe_digest", "MISSING_RECIPE_COHORT"),
        ("environment_digest", "MISSING_ENVIRONMENT_COHORT"),
        ("observer_digest", "MISSING_OBSERVER_COHORT"),
    ],
)
def test_missing_cohort_is_not_a_default_digest_or_a_latest_seen_source(field, reason):
    b = build()
    result = evaluate(replace(b, identity=replace(b.identity, **{field: None})))
    assert reason in result.reasons and result.status == "REJECTED"


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"clock_domain": "HOST_MONOTONIC_NS"}, "WRONG_CLOCK_DOMAIN"),
        ({"source_digest": "a" * 64}, "MATERIAL_COHORT_MISMATCH"),
    ],
)
def test_clock_or_source_context_cannot_be_mixed_by_matching_filenames(changes, reason):
    b = build()
    assert reason in evaluate(replace(b, identity=replace(b.identity, **changes))).reasons


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("sequence", 9, "SEQUENCE_INVALID"),
        ("context_digest", "f" * 64, "USE_CONTEXT_MISMATCH"),
        ("material_generation", 1, "MATERIAL_UNKNOWN"),
        ("task_generation", 9, "TASK_IMAGE_UNKNOWN"),
        ("exec_generation", 1, "TASK_IMAGE_UNKNOWN"),
        ("time_ns", 101, "USE_OUTSIDE_IMAGE"),
        ("time_ns", 5, "USE_OUTSIDE_BUILD"),
        ("offset", None, "MISSING_READ_RANGE"),
        ("length", None, "MISSING_READ_RANGE"),
        ("range_digest", None, "MISSING_READ_DIGEST"),
        ("length", 2, "READ_OUTSIDE_MATERIAL"),
        ("range_digest", SHA_B, "FULL_READ_HASH_MISMATCH"),
        ("offset", 2**64 - 1, "RANGE_OVERFLOW"),
    ],
)
def test_use_stage_and_actual_consumed_object_must_match_exactly(field, value, reason):
    b = changed_use(build(), 1, **{field: value})
    assert reason in evaluate(b).reasons


def test_unknown_is_not_an_actual_zero_length_read_and_never_derives_its_hash():
    b = changed_use(build(), 1, length=0, range_digest=EMPTY_SHA)
    assert evaluate(b).status == "DIAGNOSTIC_CHAIN_CONSISTENT"
    assert "MISSING_READ_RANGE" in evaluate(changed_use(b, 1, length=None)).reasons
    assert "MISSING_READ_DIGEST" in evaluate(changed_use(b, 1, range_digest=None)).reasons
    assert "EMPTY_READ_HASH_MISMATCH" in evaluate(changed_use(b, 1, range_digest=SHA_A)).reasons


def test_metadata_or_mmap_cannot_substitute_for_observed_read_bytes():
    m = models()
    b = changed_use(
        build(), 1, kind=m.UseKind.METADATA_ONLY, offset=None, length=None, range_digest=None
    )
    d = evaluate(b)
    assert d.read_events == 0 and d.metadata_events == 2
    assert (
        "METADATA_HAS_BYTE_CLAIM"
        in evaluate(changed_use(build(), 2, offset=0, length=1, range_digest=SHA_A)).reasons
    )
    assert "MMAP_HAS_READ_HASH" in evaluate(changed_use(build(), 3, range_digest=SHA_A)).reasons
    assert (
        evaluate(changed_use(build(), 3, offset=10000, length=4096)).status
        == "DIAGNOSTIC_CHAIN_CONSISTENT"
    )
    assert "INVALID_MAP_EXTENT" in evaluate(changed_use(build(), 3, length=0)).reasons


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"image_id": "source"}, "IMAGE_ROLE_INVALID"),
        ({"image_generation": 1}, "IMAGE_MATERIAL_UNKNOWN"),
        ({"exec_generation": 2}, "EXEC_GENERATION_GAP"),
        ({"parent_generation": 1}, "TASK_LINEAGE_CYCLE"),
        ({"parent_generation": 9}, "TASK_PARENT_UNKNOWN"),
        ({"start_ns": 101}, "IMAGE_TIME_INVALID"),
    ],
)
def test_task_and_image_generations_are_not_pid_or_time_heuristics(changes, reason):
    b = build()
    assert reason in evaluate(replace(b, images=(replace(b.images[0], **changes),))).reasons


def test_image_intervals_and_child_birth_require_one_rooted_lineage():
    b = build()
    second = replace(b.images[0], exec_generation=1, start_ns=50)
    assert "IMAGE_INTERVAL_OVERLAP" in evaluate(replace(b, images=(*b.images, second))).reasons
    child = replace(b.images[0], task_generation=2, parent_generation=1, start_ns=50, finish_ns=90)
    assert evaluate(replace(b, images=(*b.images, child))).status == "DIAGNOSTIC_CHAIN_CONSISTENT"
    assert (
        "MULTIPLE_TASK_ROOTS"
        in evaluate(replace(b, images=(*b.images, replace(child, parent_generation=None)))).reasons
    )
    assert (
        "CHILD_BIRTH_OUTSIDE_PARENT_IMAGE"
        in evaluate(replace(b, images=(*b.images, replace(child, start_ns=5)))).reasons
    )


def test_generated_inputs_need_a_real_causal_extension_not_a_digest_shaped_origin():
    m = models()
    b = build()
    material = replace(b.materials[1], role=m.MaterialRole.GENERATED, origin_digest="a" * 64)
    assert (
        "GENERATED_INPUT_CHAIN_UNSUPPORTED"
        in evaluate(replace(b, materials=(b.materials[0], material))).reasons
    )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("sequence_complete", None, "TRACE_SEQUENCE_UNAVAILABLE"),
        ("sequence_complete", False, "DECLARED_TRACE_INCOMPLETE"),
        ("dropped_events", None, "MISSING_DROP_COUNT"),
        ("dropped_events", 1, "TRACE_DROPPED"),
        ("input_seal_digest", None, "MISSING_INPUT_SEAL_WITNESS"),
        ("task_trace_digest", None, "MISSING_TASK_TRACE_WITNESS"),
        ("input_trace_digest", None, "MISSING_CONSUMPTION_TRACE_WITNESS"),
        ("writer_trace_digest", None, "MISSING_WRITER_TRACE_WITNESS"),
        ("exit_code", 1, "BUILD_NOT_SUCCESSFUL"),
        ("exit_code", None, "MISSING_EXIT_STATUS"),
    ],
)
def test_incomplete_trace_or_failed_build_cannot_become_a_promotion_candidate(field, value, reason):
    b = build()
    assert (
        reason in evaluate(replace(b, completion=replace(b.completion, **{field: value}))).reasons
    )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("context_digest", "f" * 64, "PROMOTION_CONTEXT_MISMATCH"),
        ("build_digest", "f" * 64, "PROMOTION_BUILD_MISMATCH"),
        ("output_generation", 1, "UNKNOWN_PROMOTED_OUTPUT"),
        ("output_sha256", SHA_A, "PROMOTED_OUTPUT_HASH_MISMATCH"),
        ("staged_sha256", None, "MISSING_PROMOTION_HASH"),
        ("sealed_sha256", SHA_A, "OUTPUT_MUTATED"),
        ("quiesced_ns", None, "MISSING_PROMOTION_TIMING"),
        ("sealed_ns", 99, "PROMOTION_TIME_ORDER_INVALID"),
        ("source_namespace_digest", None, "MISSING_NAMESPACE_BINDING"),
        ("source_namespace_digest", "b" * 64, "NAMESPACE_ALIAS"),
        ("quiescence_digest", None, "MISSING_QUIESCENCE_WITNESS"),
        ("seal_digest", None, "MISSING_OUTPUT_SEAL_WITNESS"),
        ("verification_digest", None, "MISSING_INDEPENDENT_VERIFICATION"),
    ],
)
def test_promotion_is_an_exact_causal_chain_not_a_matching_output_hash(field, value, reason):
    assert reason in evaluate(promotions=(replace(promotion(), **{field: value}),)).reasons


def test_zero_length_eof_read_beyond_file_end_is_not_invented_byte_consumption():
    b = changed_use(build(), 1, offset=10000, length=0, range_digest=EMPTY_SHA)
    assert evaluate(b).status == "DIAGNOSTIC_CHAIN_CONSISTENT"


def test_missing_duplicate_or_written_after_finish_outputs_are_not_promoted():
    b = build()
    assert "MISSING_PROMOTION" in evaluate(promotions=()).reasons
    assert "DUPLICATE_PROMOTION" in evaluate(promotions=(promotion(), promotion())).reasons
    assert (
        "OUTPUT_WRITE_OUTSIDE_BUILD"
        in evaluate(replace(b, outputs=(replace(b.outputs[0], last_write_ns=101),))).reasons
    )
    assert (
        "OUTPUT_ALIASES_INPUT"
        in evaluate(replace(b, outputs=(replace(b.outputs[0], output_id="source"),))).reasons
    )
