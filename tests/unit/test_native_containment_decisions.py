"""Synthetic model outcomes cannot qualify or authorize a real run."""

import importlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from compatibility.native_containment.contracts import canonical_digest, parse_synthetic_case
from tests.fixtures.native_containment import synthetic_case


def api():
    assert importlib.util.find_spec("compatibility.native_containment.validation") is not None
    return importlib.import_module("compatibility.native_containment.validation")


def decide(
    raw=None, *, mode="CAPABILITY_CLOSED_DISCOVERY_PROPOSAL", adopted=True, expected="a" * 64
):
    validation = api()
    case = parse_synthetic_case(json.dumps(synthetic_case() if raw is None else raw))
    return validation.evaluate_synthetic(
        case, validation.SyntheticPolicyContext(mode, adopted, expected)
    )


def test_strict_and_unadopted_proposal_are_rejected_with_same_case_digest():
    strict = decide(mode="STRICT_NO_DEVICE_ATTEMPT")
    unadopted = decide(adopted=False)
    diagnostic = decide()
    assert strict.status == "REJECTED"
    assert strict.reasons == ("DEVICE_ATTEMPT_STRICT",)
    assert unadopted.reasons == ("POLICY_NOT_ADOPTED",)
    assert diagnostic.status == "DIAGNOSTIC_EXPECTED_DENIAL_ONLY"
    assert diagnostic.reasons == ()
    expected = canonical_digest(parse_synthetic_case(json.dumps(synthetic_case())))
    assert strict.case_digest == unadopted.case_digest == diagnostic.case_digest == expected
    for decision in (strict, unadopted, diagnostic):
        assert decision.evidence_kind == "SYNTHETIC"
        assert decision.runtime_qualified is False
        assert decision.candidate_generation_allowed is False
        assert decision.application_authorized is False
        assert decision.runtime_accepted is False
        assert decision.owner_proposal_allowed is False
        with pytest.raises(FrozenInstanceError):
            decision.status = "ACCEPTED"


@pytest.mark.parametrize(
    "proof,reason",
    [
        ("input_closure_complete", "INPUT_CLOSURE_INCOMPLETE"),
        ("enforcement_observed_active", "ENFORCEMENT_UNQUALIFIED"),
        ("source_loader_immutable", "MUTABLE_LOADER_INPUT"),
        ("process_stage_bound", "PROCESS_PROVENANCE_UNKNOWN"),
        ("resource_resolution_bound", "RESOURCE_RESOLUTION_UNKNOWN"),
        ("capture_guard_bound", "ENFORCEMENT_UNQUALIFIED"),
        ("trace_complete", "TRACE_INCOMPLETE"),
        ("observer_intact", "OBSERVER_OR_POLICY_TAMPERED"),
    ],
)
@pytest.mark.parametrize("value", [False, None])
def test_each_missing_or_false_modeled_proof_rejects(proof, reason, value):
    raw = synthetic_case()
    raw["modeled_proofs"][proof] = value
    result = decide(raw)
    assert result.status == "REJECTED"
    assert result.reasons == (reason,)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("resolution_bound", None, "RESOURCE_RESOLUTION_UNKNOWN"),
        ("resolution_bound", False, "RESOURCE_RESOLUTION_UNKNOWN"),
        ("resolved_kind", None, "RESOURCE_RESOLUTION_UNKNOWN"),
        ("resolved_kind", "UNKNOWN", "RESOURCE_RESOLUTION_UNKNOWN"),
        ("result_known", None, "RESULT_UNKNOWN"),
        ("result_known", False, "RESULT_UNKNOWN"),
        ("fd_created_or_imported", None, "RESULT_UNKNOWN"),
        ("effect_observed", None, "RESULT_UNKNOWN"),
        ("actor_id", "reused-pid", "PROCESS_PROVENANCE_UNKNOWN"),
        ("process_generation", 9, "PROCESS_PROVENANCE_UNKNOWN"),
        ("exec_generation", 9, "PROCESS_PROVENANCE_UNKNOWN"),
        ("clock_domain", "guest-clock", "CLOCK_DOMAIN_UNBOUND"),
        ("resolved_kind", "PROHIBITED_HARDWARE", "ENFORCEMENT_UNQUALIFIED"),
    ],
)
def test_incomplete_or_unbound_events_cannot_pass(field, value, reason):
    raw = synthetic_case()
    raw["events"][0][field] = value
    result = decide(raw)
    assert result.status == "REJECTED"
    assert reason in result.reasons


@pytest.mark.parametrize(
    "field", ["successful_prohibited_handles", "successful_prohibited_effects"]
)
@pytest.mark.parametrize(
    "value,reason", [(None, "RESULT_UNKNOWN"), (1, "PROHIBITED_CAPABILITY_ACQUIRED")]
)
def test_unknown_counts_are_not_zero(field, value, reason):
    raw = synthetic_case()
    raw[field] = value
    assert decide(raw).reasons == (reason,)


def test_cpu_or_errno_cannot_substitute_for_proof_or_cohort():
    raw = synthetic_case()
    raw["modeled_proofs"]["capture_guard_bound"] = None
    raw["cpu_backend"] = None
    result = decide(raw, expected="b" * 64)
    assert result.reasons == (
        "ENFORCEMENT_UNQUALIFIED",
        "SOURCE_COHORT_MISMATCH",
        "CPU_BACKEND_UNCONFIRMED",
    )


@pytest.mark.parametrize(
    "operation,reason",
    [
        ("CONTROL", "CONTROL_OPERATION_ATTEMPTED"),
        ("IOCTL", "CONTROL_OPERATION_ATTEMPTED"),
        ("MMAP", "CONTROL_OPERATION_ATTEMPTED"),
        ("PRIVILEGE_OR_POLICY", "CONTROL_OPERATION_ATTEMPTED"),
        ("ASYNC_IO", "CONTROL_OPERATION_ATTEMPTED"),
        ("NETWORK", "NETWORK_OR_FD_PASS_ATTEMPTED"),
        ("FD_PASS", "NETWORK_OR_FD_PASS_ATTEMPTED"),
    ],
)
def test_fatal_second_event_is_not_hidden_by_plausible_first_denial(operation, reason):
    raw = synthetic_case()
    second = dict(raw["events"][0], sequence=2, operation_class=operation)
    raw["events"].append(second)
    result = decide(raw)
    assert result.status == "REJECTED"
    assert reason in result.reasons


@pytest.mark.parametrize("field", ["fd_created_or_imported", "effect_observed"])
def test_successful_capability_or_effect_rejects_even_with_denial_errno(field):
    raw = synthetic_case()
    raw["events"][0][field] = True
    assert "PROHIBITED_CAPABILITY_ACQUIRED" in decide(raw).reasons


@pytest.mark.parametrize(
    "values",
    [
        ("unknown", True, "a" * 64),
        ("STRICT_NO_DEVICE_ATTEMPT", 1, "a" * 64),
        ("STRICT_NO_DEVICE_ATTEMPT", False, "bad"),
    ],
)
def test_context_rejects_invalid_mode_bool_or_digest(values):
    with pytest.raises(ValueError):
        api().SyntheticPolicyContext(*values)


def test_decision_context_is_immutable_and_does_not_adopt_actual_policy():
    validation = api()
    context = validation.SyntheticPolicyContext("STRICT_NO_DEVICE_ATTEMPT", False, "a" * 64)
    with pytest.raises(FrozenInstanceError):
        context.mode = "CAPABILITY_CLOSED_DISCOVERY_PROPOSAL"
    case = parse_synthetic_case(json.dumps(synthetic_case()))
    # Re-evaluation is stateless; simulated adoption never changes the original context.
    validation.evaluate_synthetic(
        case,
        replace(
            context,
            mode="CAPABILITY_CLOSED_DISCOVERY_PROPOSAL",
            hypothetical_adoption_for_test=True,
        ),
    )
    assert validation.evaluate_synthetic(case, context).reasons == ("DEVICE_ATTEMPT_STRICT",)
