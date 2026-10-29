"""Neutral semantic inventory / wire proposal, not a cereal schema or producer."""

from dataclasses import MISSING, fields

from .context import (
    AppliedGeometryContext,
    DelayContext,
    FrictionObservationContext,
    GainSnapshot,
    InstalledParameters,
)
from .contracts import (
    ConsumedSourceIdentity,
    ControllerCallbackSignals,
    ControllerStageDecomposition,
    CycleIdentity,
    DownstreamStageIdentity,
    LateralTorqueIdentificationReceipt,
    LimitState,
    ScalarObservation,
)
from .types import (
    VERSION,
    AlignmentMethod,
    CallbackFamily,
    CallbackFunction,
    CallbackSite,
    CallbackStage,
    ClockDomain,
    ControllerMode,
    DelaySource,
    GeometryOrigin,
    OffsetSource,
    Precision,
    ScalarOrigin,
    Signal,
    SourceOrigin,
    SourceRole,
    Stage,
    require,
)
from .validation import (
    EligibilityStatus,
    ObservationEligibilityDecision,
    ObservationPolicy,
    ObservationReason,
)

CONTRACT_TYPES = (
    CycleIdentity,
    ConsumedSourceIdentity,
    ScalarObservation,
    ControllerCallbackSignals,
    ControllerStageDecomposition,
    DownstreamStageIdentity,
    LimitState,
    InstalledParameters,
    GainSnapshot,
    AppliedGeometryContext,
    DelayContext,
    FrictionObservationContext,
    LateralTorqueIdentificationReceipt,
    ObservationPolicy,
    ObservationEligibilityDecision,
)


def _unit(name: str) -> str:
    units = dict(
        (
            ("value", "signal-dependent; see Signal field semantics"),
            ("desired_lateral_accel", "m/s^2"),
            ("actual_lateral_accel", "m/s^2"),
            ("roll", "rad"),
            ("roll_compensation", "m/s^2"),
            ("callback_acceleration", "m/s^2"),
            ("friction_input", "m/s^2"),
            ("friction_deadzone", "m/s^2"),
            ("friction_threshold", "m/s^2"),
            ("q_observed", "1"),
            ("callback_output_raw", "normalized torque, internal callback sign"),
            ("pid_p", "normalized torque"),
            ("pid_i", "normalized torque"),
            ("pid_d", "normalized torque"),
            ("pid_f", "normalized torque"),
            ("pid_sum", "normalized torque"),
            ("post_pid_output", "normalized torque, internal PID sign"),
            ("requested_torque", "normalized torque, negated internal PID sign"),
            ("host_output", "normalized torque, external stage sign"),
            ("applied_torque", "normalized torque, applied stage sign"),
            ("factor_installed", "m/s^2 per normalized torque"),
            ("friction_installed", "normalized torque"),
            ("offset_installed", "m/s^2"),
            ("k_p", "1"),
            ("k_i", "1/s"),
            ("k_d", "s"),
            ("k_f", "1"),
            ("wheelbase", "m"),
            ("center_to_front", "m"),
            ("center_to_front_ratio", "1"),
            ("stiffness_factor", "1"),
            ("effective_steer_ratio", "1"),
            ("steer_ratio_rate_raw", "percent"),
            ("steer_ratio_rate_effective", "multiplier"),
            ("custom_sr_raw", "tenths of steer ratio"),
            ("custom_sr_effective", "scaled custom override; 0 disabled, NOT effective VM ratio"),
            ("requested_center_to_front_percent", "percent intent; 0 vehicle default"),
            ("paramsd_target_ratio", "1, candidate only"),
            ("live_parameters_ratio", "1, candidate only"),
            ("effective_delay_s", "s"),
            ("source_revision", "Git commit SHA-1"),
        )
    )
    if name.endswith("_ns"):
        return "ns, explicit monotonic domain"
    if (
        "digest" in name
        or name.endswith("_event_id")
        or name
        in {
            "session_id",
            "source_identity",
            "applied_vm_context_id",
            "sample_pair_id",
            "downstream_cycle_id",
        }
    ):
        return "SHA-256 opaque content identity, NOT authenticity"
    return units.get(name, "dimensionless identity/status/structure")


def _stage(record: str, name: str) -> str:
    stages = {
        Signal.CALLBACK_OUTPUT.value: Stage.RAW_CALLBACK.value,
        Signal.Q_OBSERVED.value: Stage.HELPER_Q.value,
        Signal.PID_P.value: Stage.PID_P.value,
        Signal.PID_I.value: Stage.PID_I.value,
        Signal.PID_D.value: Stage.PID_D.value,
        Signal.PID_F.value: Stage.PID_F.value,
        Signal.PID_SUM.value: Stage.PID_SUM.value,
        Signal.PID_OUTPUT.value: Stage.PID_CLIPPED.value,
        Signal.REQUESTED_TORQUE.value: Stage.REQUESTED_TORQUE.value,
        Signal.HOST_OUTPUT.value: Stage.HOST_OUTPUT.value,
        Signal.APPLIED_TORQUE.value: Stage.APPLIED_TORQUE.value,
    }
    if name in stages:
        return stages[name]
    if record == "ControllerCallbackSignals":
        return Stage.CALLBACK_INPUT.value
    if record in {
        "InstalledParameters",
        "GainSnapshot",
        "AppliedGeometryContext",
        "DelayContext",
        "FrictionObservationContext",
    }:
        return "ACTUALLY_LATCHED_OR_APPLIED_CONTEXT"
    if record == "LimitState":
        return "SAME_CYCLE_LIMIT_STATE"
    return "CAUSAL_IDENTITY_OR_METADATA"


def _source(record: str, name: str) -> tuple[str, str]:
    if record in {"ObservationPolicy", "ObservationEligibilityDecision"}:
        return "neutral local evaluator only", "LOCAL_ONLY_NOT_WIRE_PRODUCER"
    if record == "ControllerCallbackSignals" or name == "callback_output_raw":
        if name == "q_observed":
            return (
                "future instrumented actual helper state; NOT reconstructed/C-derived",
                "NOT_PUBLISHED_CURRENT_HELPER_HAS_NO_Q_OUTPUT",
            )
        availability = (
            "EXISTING_FLOAT32_ONLY_NOT_EXACT_RAW"
            if name in {"desired_lateral_accel", "actual_lateral_accel"}
            else "PROPOSED_LOCAL_CAPTURE_NOT_PUBLISHED"
        )
        return (
            "R/C LatControlTorque.update executed feedforward branch + base callback/helper",
            availability,
        )
    if record == "ControllerStageDecomposition":
        return (
            "R/C PIDController.update / LatControlTorque return / exact linked downstream stage",
            "PARTIAL_PUBLISHED_FLOAT32_OR_DOWNSTREAM_WRONG_STAGE_FOR_RAW",
        )
    if record == "DownstreamStageIdentity":
        return (
            "exact command publication and downstream source-command receipt, NOT consumed input",
            "PARTIAL_OBSERVATION_V2_RECEIPTS_NO_FRICTION_CORE_BINDING",
        )
    if record == "InstalledParameters":
        return (
            "actual torque_params/generation after latching; offset field origin separate",
            "STARTUP_OR_LIVE_CANDIDATES_MISSING_INSTALLED_COHORT",
        )
    if record == "GainSnapshot":
        return (
            "actual PID speed-effective k_p/k_i/k_d/k_f in same installed generation",
            "MISSING_GAIN_COHORT",
        )
    if record == "AppliedGeometryContext":
        return (
            "R static CP baseline + applied VM; C actually applied VM, not request/LP candidate",
            "PARTIAL_SOURCE_FIELDS_MISSING_APPLIED_VM_RECEIPT",
        )
    if record == "DelayContext":
        return (
            "exact effective SAD/liveDelay and downstream sample-pair alignment receipt",
            "PARTIAL_SOURCE_FIELDS_MISSING_APPLIED_ALIGNMENT_RECEIPT",
        )
    if record == "ConsumedSourceIdentity":
        return (
            "exact actually consumed event/object identity and clock; not latest-seen",
            "EVENT_TIMES_EXIST_CONSUMPTION_LINKAGE_NOT_PUBLISHED",
        )
    if record == "LimitState":
        return (
            "same-cycle active/health/override and timer versus instantaneous limit witnesses",
            "PARTIAL_SOURCE_FIELDS_MISSING_ATOMIC_LIMIT_COHORT",
        )
    return "future cycle-scoped immutable read-only capture metadata", "PROPOSED_NOT_PUBLISHED"


def semantic_schema() -> dict[str, object]:
    entries = []
    optional_names = {
        "offset_installed",
        "offset_source",
        "source_field",
        "requested_torque",
        "host_output",
        "applied_torque",
        "downstream_cycle_id",
        "requested_center_to_front_percent",
        "paramsd_target_ratio",
        "live_parameters_ratio",
        "sample_pair_id",
    }
    for cls in CONTRACT_TYPES:
        for item in fields(cls):
            expression = str(item.type)
            if "float" in expression:
                wire_type = "Float64 + explicit presence"
            elif "int" in expression:
                wire_type = "UInt64 + explicit presence"
            elif "bool" in expression:
                wire_type = "Bool + explicit presence"
            elif "str" in expression:
                wire_type = "Text/opaque digest + explicit presence"
            else:
                wire_type = "Enum/Struct/List + explicit presence: " + expression
            required = (
                "OPTIONAL"
                if item.name in optional_names
                else "STRUCTURAL"
                if item.default is MISSING and item.default_factory is MISSING
                else "ELIGIBILITY"
            )
            if cls is ConsumedSourceIdentity and item.name != "role":
                required = "CONDITIONAL_ON_ACTUAL_CONSUMPTION"
                if item.name == "controller_cycle_digest":
                    required = "CONDITIONAL_ON_CONSUMED_LOCAL_CYCLE_OBJECT"
            if cls is ControllerStageDecomposition and item.name in {
                "downstream_cycle_id",
                "downstream_identities",
            }:
                required = "CONDITIONAL_ON_DOWNSTREAM_VALUE"
            if cls is ObservationEligibilityDecision or cls is ObservationPolicy:
                required = "LOCAL_EVALUATOR_ONLY"
            source, availability = _source(cls.__name__, item.name)
            meaning = "STRUCTURAL_OBSERVATION_ONLY_NOT_ESTIMATOR_QUALIFICATION"
            if cls is InstalledParameters:
                meaning = "CONTEXT_ONLY_NOT_TRUTH_OR_TARGET"
            if item.name.endswith("_allowed") or item.name in {
                "application_authorized",
                "runtime_accepted",
            }:
                meaning = "FIXED_FALSE_NO_AUTHORITY"
            entries.append(
                {
                    "field": cls.__name__ + "." + item.name,
                    "python_type": expression,
                    "type": wire_type,
                    "unit": _unit(item.name),
                    "stage": _stage(cls.__name__, item.name),
                    "required": required,
                    "source": source,
                    "availability": availability,
                    "qualification_meaning": meaning,
                }
            )
    return {
        "schema": VERSION + ":neutral-semantic-manifest",
        "wire_format": "PROPOSED_NO_CEREAL_TAG_ASSIGNMENTS",
        "runtime_producer_implemented": False,
        "empirical_identification_qualified": False,
        "representation_encoding_design_ready": True,
        "representation_encoding_runtime_qualified": False,
        "digest_meaning": "CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY",
        "fields": entries,
        "enums": [
            {"type": enum.__name__, "values": [value.value for value in enum]}
            for enum in (
                AlignmentMethod,
                CallbackFamily,
                CallbackFunction,
                CallbackSite,
                CallbackStage,
                ClockDomain,
                ControllerMode,
                DelaySource,
                GeometryOrigin,
                OffsetSource,
                Precision,
                ScalarOrigin,
                Signal,
                SourceOrigin,
                SourceRole,
                Stage,
                EligibilityStatus,
                ObservationReason,
            )
        ],
        "authority": {
            name: False
            for name in (
                "candidate_generation_allowed",
                "application_authorized",
                "runtime_accepted",
                "owner_proposal_allowed",
            )
        },
    }


def validate_semantic_schema(manifest: object) -> None:
    require(manifest == semantic_schema(), "SEMANTIC_SCHEMA_MUTATION")
