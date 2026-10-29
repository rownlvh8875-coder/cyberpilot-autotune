"""Model adversarial claims, not actual kernel/device behavior or collector trust."""

import json
from dataclasses import replace
from itertools import product

import pytest

from compatibility.native_containment.contracts import canonical_digest, parse_synthetic_case
from compatibility.native_containment.validation import (
    SyntheticContainmentDecision,
    SyntheticPolicyContext,
    evaluate_synthetic,
)
from tests.fixtures.native_containment import synthetic_case


def decision(raw):
    return evaluate_synthetic(
        parse_synthetic_case(json.dumps(raw)),
        SyntheticPolicyContext("CAPABILITY_CLOSED_DISCOVERY_PROPOSAL", True, "a" * 64),
    )


@pytest.mark.parametrize(
    "endpoint,flags,errno,kind",
    list(
        product(
            ["/dev/kfd", "/dev/nvidiactl", "/dev/nvidia-uvm", "/dev/kgsl-3d0"],
            [["O_RDWR"], ["O_RDWR", "O_CLOEXEC"]],
            ["ENOENT", "EACCES", "EPERM"],
            ["PRIVATE_NAMESPACE_ABSENCE", "POLICY_DENIED_NO_OBJECT"],
        )
    ),
)
def test_exact_candidates_remain_diagnostic_only(endpoint, flags, errno, kind):
    raw = synthetic_case()
    raw["events"][0].update(
        requested_endpoint=endpoint, flags=flags, errno_name=errno, resolved_kind=kind
    )
    result = decision(raw)
    assert result.status == "DIAGNOSTIC_EXPECTED_DENIAL_ONLY"
    assert result.runtime_qualified is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_endpoint", None),
        ("requested_endpoint", "/dev/dri/renderD128"),
        ("requested_endpoint", "/dev/nvidia0"),
        ("requested_endpoint", "/dev/vfio/1"),
        ("requested_endpoint", "/dev/kvm"),
        ("requested_endpoint", "/dev/sda"),
        ("requested_endpoint", "/dev/gpiochip0"),
        ("requested_endpoint", "/dev/video0"),
        ("requested_endpoint", "/dev/bus/usb/001/001"),
        ("requested_endpoint", "can0"),
        ("requested_endpoint", "/proc/self/fd/4"),
        ("requested_endpoint", "kfd"),
        ("requested_endpoint", "/alias/hardlink"),
        ("requested_endpoint", "/alias/symlink"),
        ("requested_endpoint", "/dev/kfd/../kfd"),
        ("requested_endpoint", "/dev/kfd2"),
        ("flags", None),
        ("flags", []),
        ("flags", ["O_PATH"]),
        ("flags", ["O_RDWR", "O_CREAT"]),
        ("flags", ["O_RDWR", "O_TRUNC"]),
        ("flags", ["O_RDWR", "O_APPEND"]),
        ("flags", ["O_RDONLY"]),
        ("errno_name", None),
        ("errno_name", "EIO"),
        ("operation_class", "OTHER"),
        ("resolved_kind", "REGULAR_BUILD_FILE"),
        ("resolved_kind", "EXACT_PSEUDO"),
    ],
)
def test_labels_and_errno_cannot_expand_proposed_candidate_set(field, value):
    raw = synthetic_case()
    raw["events"][0][field] = value
    assert "UNEXPECTED_DISCOVERY_OPERATION" in decision(raw).reasons


@pytest.mark.parametrize("leaf", ["enable", "unbind", "driver_override", "drivers_probe"])
def test_denied_sysfs_open_is_still_a_fatal_control_attempt(leaf):
    raw = synthetic_case()
    raw["events"][0]["requested_endpoint"] = "/sys/bus/pci/devices/synthetic/" + leaf
    assert decision(raw).reasons == (
        "UNEXPECTED_DISCOVERY_OPERATION",
        "CONTROL_OPERATION_ATTEMPTED",
    )


@pytest.mark.parametrize("sequence,time", [(1, 101), (0, 101), (2, 99)])
def test_duplicate_reordered_or_backward_time_is_rejected(sequence, time):
    raw = synthetic_case()
    raw["events"].append(dict(raw["events"][0], sequence=sequence, mono_time_ns=time))
    assert decision(raw).reasons == ("TRACE_SEQUENCE_INVALID",)


def test_sequence_gaps_are_not_guessed_drop_counts_but_coverage_unknown_rejects():
    raw = synthetic_case()
    raw["events"].append(dict(raw["events"][0], sequence=9))
    assert decision(raw).status == "DIAGNOSTIC_EXPECTED_DENIAL_ONLY"
    raw["modeled_proofs"]["trace_complete"] = None
    assert decision(raw).reasons == ("TRACE_INCOMPLETE",)


@pytest.mark.parametrize(
    "proof,reason",
    [
        ("source_loader_immutable", "MUTABLE_LOADER_INPUT"),
        ("process_stage_bound", "PROCESS_PROVENANCE_UNKNOWN"),
        ("trace_complete", "TRACE_INCOMPLETE"),
        ("observer_intact", "OBSERVER_OR_POLICY_TAMPERED"),
        ("resource_resolution_bound", "RESOURCE_RESOLUTION_UNKNOWN"),
    ],
)
def test_unknown_loader_lineage_coverage_observer_or_resolution_claims_reject(proof, reason):
    # pyc/preload shadowing, unmatched child/clone, capture loss, alias resolution
    # cannot be detected by this model: their corresponding modeled proof must fail.
    raw = synthetic_case()
    raw["modeled_proofs"][proof] = None
    assert decision(raw).reasons == (reason,)


def test_source_drift_cannot_be_hidden_by_same_cpu_or_request_label():
    raw = synthetic_case()
    old_digest = canonical_digest(parse_synthetic_case(json.dumps(raw)))
    raw["source_cohort_digest"] = "b" * 64
    assert decision(raw).reasons == ("SOURCE_COHORT_MISMATCH",)
    assert decision(raw).case_digest != old_digest


def test_all_reasons_are_ordered_and_deduplicated_without_erasing_fatal_events():
    raw = synthetic_case()
    raw["modeled_proofs"]["capture_guard_bound"] = False
    raw["modeled_proofs"]["enforcement_observed_active"] = False
    raw["events"][0].update(operation_class="FD_PASS", fd_created_or_imported=True)
    raw["events"].append(dict(raw["events"][0], sequence=2, operation_class="IOCTL"))
    result = evaluate_synthetic(
        parse_synthetic_case(json.dumps(raw)),
        SyntheticPolicyContext("STRICT_NO_DEVICE_ATTEMPT", False, "b" * 64),
    )
    assert result.reasons == (
        "ENFORCEMENT_UNQUALIFIED",
        "SOURCE_COHORT_MISMATCH",
        "DEVICE_ATTEMPT_STRICT",
        "UNEXPECTED_DISCOVERY_OPERATION",
        "PROHIBITED_CAPABILITY_ACQUIRED",
        "CONTROL_OPERATION_ATTEMPTED",
        "NETWORK_OR_FD_PASS_ATTEMPTED",
    )


def test_direct_decision_defensively_copies_and_orders_reasons():
    reasons = ["RESULT_UNKNOWN", "ENFORCEMENT_UNQUALIFIED"]
    result = SyntheticContainmentDecision("REJECTED", reasons, "a" * 64, "STRICT_NO_DEVICE_ATTEMPT")
    reasons.clear()
    assert result.reasons == ("ENFORCEMENT_UNQUALIFIED", "RESULT_UNKNOWN")


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "ACCEPTED"},
        {"status": "DIAGNOSTIC_EXPECTED_DENIAL_ONLY"},
        {"reasons": []},
        {"reasons": ["NOT_A_REASON"]},
        {"reasons": "RESULT_UNKNOWN"},
        {"mode": "POLICY_ADOPTED"},
        {"case_digest": "bad"},
    ],
)
def test_direct_decision_cannot_fabricate_accepted_or_inconsistent_outcome(changes):
    original = decision({**synthetic_case(), "cpu_backend": None})
    with pytest.raises(ValueError):
        replace(original, **changes)


def test_public_functions_reject_wrong_objects_and_forged_nested_values():
    policy = SyntheticPolicyContext("STRICT_NO_DEVICE_ATTEMPT", False, "a" * 64)
    with pytest.raises(ValueError):
        canonical_digest({})
    with pytest.raises(ValueError):
        parse_synthetic_case(None)
    case = parse_synthetic_case(json.dumps(synthetic_case()))
    with pytest.raises(ValueError):
        evaluate_synthetic(case, {})
    object.__setattr__(case.modeled_proofs, "observer_intact", 1)
    with pytest.raises(ValueError):
        evaluate_synthetic(case, policy)


@pytest.mark.parametrize("field,value", [("operation_class", 0), ("resolved_kind", 0)])
def test_wrong_enum_scalar_cannot_be_coerced(field, value):
    raw = synthetic_case()
    raw["events"][0][field] = value
    with pytest.raises(ValueError):
        parse_synthetic_case(json.dumps(raw))


def test_direct_case_cannot_contain_mutable_event_dictionary():
    raw = synthetic_case()
    case = parse_synthetic_case(json.dumps(raw))
    with pytest.raises(ValueError):
        replace(case, events=[raw["events"][0]])


def test_wrong_context_and_decision_scalar_types_reject_without_coercion():
    with pytest.raises(ValueError):
        SyntheticPolicyContext(None, False, "a" * 64)
    result = decision({**synthetic_case(), "cpu_backend": None})
    with pytest.raises(ValueError):
        replace(result, status=None)
    with pytest.raises(ValueError):
        replace(result, reasons=[0])


def test_direct_decision_cannot_claim_strict_mode_diagnostic_success():
    result = decision(synthetic_case())
    with pytest.raises(ValueError):
        replace(result, mode="STRICT_NO_DEVICE_ATTEMPT")
