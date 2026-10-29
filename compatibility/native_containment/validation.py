"""Pure synthetic decision matrix; no actual adoption or runtime qualification."""

from dataclasses import dataclass, field
from enum import StrEnum

from .contracts import SyntheticContainmentCase, _digest, canonical_digest


class PolicyMode(StrEnum):
    STRICT_NO_DEVICE_ATTEMPT = "STRICT_NO_DEVICE_ATTEMPT"
    CAPABILITY_CLOSED_DISCOVERY_PROPOSAL = "CAPABILITY_CLOSED_DISCOVERY_PROPOSAL"


class SyntheticStatus(StrEnum):
    REJECTED = "REJECTED"
    DIAGNOSTIC_EXPECTED_DENIAL_ONLY = "DIAGNOSTIC_EXPECTED_DENIAL_ONLY"


class RejectionReason(StrEnum):
    POLICY_NOT_ADOPTED = "POLICY_NOT_ADOPTED"
    ENFORCEMENT_UNQUALIFIED = "ENFORCEMENT_UNQUALIFIED"
    SOURCE_COHORT_MISMATCH = "SOURCE_COHORT_MISMATCH"
    INPUT_CLOSURE_INCOMPLETE = "INPUT_CLOSURE_INCOMPLETE"
    MUTABLE_LOADER_INPUT = "MUTABLE_LOADER_INPUT"
    PROCESS_PROVENANCE_UNKNOWN = "PROCESS_PROVENANCE_UNKNOWN"
    CLOCK_DOMAIN_UNBOUND = "CLOCK_DOMAIN_UNBOUND"
    TRACE_INCOMPLETE = "TRACE_INCOMPLETE"
    TRACE_SEQUENCE_INVALID = "TRACE_SEQUENCE_INVALID"
    RESOURCE_RESOLUTION_UNKNOWN = "RESOURCE_RESOLUTION_UNKNOWN"
    RESULT_UNKNOWN = "RESULT_UNKNOWN"
    DEVICE_ATTEMPT_STRICT = "DEVICE_ATTEMPT_STRICT"
    UNEXPECTED_DISCOVERY_OPERATION = "UNEXPECTED_DISCOVERY_OPERATION"
    PROHIBITED_CAPABILITY_ACQUIRED = "PROHIBITED_CAPABILITY_ACQUIRED"
    CONTROL_OPERATION_ATTEMPTED = "CONTROL_OPERATION_ATTEMPTED"
    NETWORK_OR_FD_PASS_ATTEMPTED = "NETWORK_OR_FD_PASS_ATTEMPTED"
    OBSERVER_OR_POLICY_TAMPERED = "OBSERVER_OR_POLICY_TAMPERED"
    CPU_BACKEND_UNCONFIRMED = "CPU_BACKEND_UNCONFIRMED"


@dataclass(frozen=True, slots=True)
class SyntheticPolicyContext:
    """Test simulation only; a true hypothetical flag is NOT real policy adoption."""

    mode: PolicyMode
    hypothetical_adoption_for_test: bool
    expected_source_cohort_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.mode, str):
            raise ValueError("expected policy mode")
        object.__setattr__(self, "mode", PolicyMode(self.mode))
        if type(self.hypothetical_adoption_for_test) is not bool:
            raise ValueError("expected hypothetical bool")
        _digest(self.expected_source_cohort_digest)


@dataclass(frozen=True, slots=True)
class SyntheticContainmentDecision:
    """Diagnostic result only. Its digest/status cannot convey real authority."""

    status: SyntheticStatus
    reasons: tuple[RejectionReason, ...]
    case_digest: str
    mode: PolicyMode
    evidence_kind: str = field(default="SYNTHETIC", init=False)
    runtime_qualified: bool = field(default=False, init=False)
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    owner_proposal_allowed: bool = field(default=False, init=False)


def evaluate_synthetic(
    case: SyntheticContainmentCase, policy: SyntheticPolicyContext
) -> SyntheticContainmentDecision:
    """Classify one synthetic security-event case, never a whole observed run."""
    case_digest = canonical_digest(case)  # Revalidate even direct constructors.
    if type(policy) is not SyntheticPolicyContext:
        raise ValueError("expected synthetic policy context")
    policy.__post_init__()
    reasons: set[RejectionReason] = set()
    r = RejectionReason
    if policy.mode == PolicyMode.STRICT_NO_DEVICE_ATTEMPT:
        # This is a nonempty security/discovery case, not an ordinary build IO log.
        reasons.add(r.DEVICE_ATTEMPT_STRICT)
    elif not policy.hypothetical_adoption_for_test:
        reasons.add(r.POLICY_NOT_ADOPTED)
    if case.source_cohort_digest != policy.expected_source_cohort_digest:
        reasons.add(r.SOURCE_COHORT_MISMATCH)
    proof_reasons = (
        (case.modeled_proofs.input_closure_complete, r.INPUT_CLOSURE_INCOMPLETE),
        (case.modeled_proofs.enforcement_observed_active, r.ENFORCEMENT_UNQUALIFIED),
        (case.modeled_proofs.source_loader_immutable, r.MUTABLE_LOADER_INPUT),
        (case.modeled_proofs.process_stage_bound, r.PROCESS_PROVENANCE_UNKNOWN),
        (case.modeled_proofs.resource_resolution_bound, r.RESOURCE_RESOLUTION_UNKNOWN),
        (case.modeled_proofs.capture_guard_bound, r.ENFORCEMENT_UNQUALIFIED),
        (case.modeled_proofs.trace_complete, r.TRACE_INCOMPLETE),
        (case.modeled_proofs.observer_intact, r.OBSERVER_OR_POLICY_TAMPERED),
    )
    for proof, reason in proof_reasons:
        if proof is not True:
            reasons.add(reason)
    if case.cpu_backend != "CPU:LLVM":
        reasons.add(r.CPU_BACKEND_UNCONFIRMED)
    for count in (case.successful_prohibited_handles, case.successful_prohibited_effects):
        if count is None:
            reasons.add(r.RESULT_UNKNOWN)
        elif count != 0:
            reasons.add(r.PROHIBITED_CAPABILITY_ACQUIRED)

    previous_sequence = previous_time = -1
    for event in case.events:
        if (event.actor_id, event.process_generation, event.exec_generation) != (
            case.actor_id,
            case.process_generation,
            case.exec_generation,
        ):
            reasons.add(r.PROCESS_PROVENANCE_UNKNOWN)
        if event.clock_domain != case.clock_domain:
            reasons.add(r.CLOCK_DOMAIN_UNBOUND)
        if event.sequence <= previous_sequence or event.mono_time_ns < previous_time:
            reasons.add(r.TRACE_SEQUENCE_INVALID)
        previous_sequence, previous_time = event.sequence, event.mono_time_ns
        if event.resolution_bound is not True or event.resolved_kind in (None, "UNKNOWN"):
            reasons.add(r.RESOURCE_RESOLUTION_UNKNOWN)
        if event.resolved_kind == "PROHIBITED_HARDWARE":
            reasons.add(r.ENFORCEMENT_UNQUALIFIED)
        if event.result_known is not True or None in (
            event.fd_created_or_imported,
            event.effect_observed,
        ):
            reasons.add(r.RESULT_UNKNOWN)
        if event.fd_created_or_imported is True or event.effect_observed is True:
            reasons.add(r.PROHIBITED_CAPABILITY_ACQUIRED)
        if event.operation_class in ("CONTROL", "IOCTL", "MMAP", "PRIVILEGE_OR_POLICY", "ASYNC_IO"):
            reasons.add(r.CONTROL_OPERATION_ATTEMPTED)
        if event.operation_class in ("NETWORK", "FD_PASS"):
            reasons.add(r.NETWORK_OR_FD_PASS_ATTEMPTED)
        # Labels may add a rejection reason, but can never prove resolution/admission.
        if (event.requested_endpoint or "").startswith("/sys/") and (
            event.requested_endpoint or ""
        ).rsplit("/", 1)[-1] in ("enable", "unbind", "driver_override", "drivers_probe"):
            reasons.add(r.CONTROL_OPERATION_ATTEMPTED)
        if not (
            event.operation_class == "OPEN"
            and event.requested_endpoint
            in ("/dev/kfd", "/dev/nvidiactl", "/dev/nvidia-uvm", "/dev/kgsl-3d0")
            and event.flags in (("O_RDWR",), ("O_CLOEXEC", "O_RDWR"))
            and event.errno_name in ("ENOENT", "EACCES", "EPERM")
            and event.resolved_kind in ("PRIVATE_NAMESPACE_ABSENCE", "POLICY_DENIED_NO_OBJECT")
        ):
            reasons.add(r.UNEXPECTED_DISCOVERY_OPERATION)

    ordered = tuple(reason for reason in RejectionReason if reason in reasons)
    return SyntheticContainmentDecision(
        SyntheticStatus.REJECTED if ordered else SyntheticStatus.DIAGNOSTIC_EXPECTED_DENIAL_ONLY,
        ordered,
        case_digest,
        policy.mode,
    )
