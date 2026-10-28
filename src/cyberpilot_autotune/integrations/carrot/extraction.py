"""Immediate field-by-field copies from qualified decoded payload readers."""

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from cyberpilot_autotune.adapters.carrot_receipt_contract import (
    MeasurementEvidence,
    ReceiptEvidence,
    SourceCarStateEvidence,
    SourceCommandEvidence,
    TimestampEvidence,
)

from .availability import SchemaBinding
from .errors import CarrotInputError
from .health import SessionToken, TopicHealthEvidence, uint64


@dataclass(frozen=True, slots=True)
class DecodedTopicSample:
    topic: str
    log_mono_time_ns: int
    event_valid: bool
    transport_health: TopicHealthEvidence
    reader: object = field(repr=False, compare=False)
    session_token: SessionToken

    def __post_init__(self) -> None:
        if self.topic not in ("carControl", "carState", "carOutput"):
            raise CarrotInputError("UNSUPPORTED_TOPIC")
        uint64(self.log_mono_time_ns, present=False)
        if (
            type(self.event_valid) is not bool
            or type(self.transport_health) is not TopicHealthEvidence
            or type(self.session_token) is not SessionToken
        ):
            raise CarrotInputError("INVALID_DECODED_SAMPLE")


def _get(reader: object, name: str) -> object:
    return cast(object, getattr(reader, name))


def _has(reader: object, name: str) -> bool:
    return cast(Callable[[str], bool], _get(reader, "_has"))(name) is True


def _enum(
    reader: object, name: str, allowed: tuple[str, ...], unavailable: str = "unavailable"
) -> str:
    try:
        value = str(_get(reader, name))
    except Exception:
        return unavailable
    return value if value in allowed else unavailable


def _number(value: object) -> float | None:
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
        return number if math.isfinite(number) else None
    except (OverflowError, ValueError):
        return None


def _boolean(value: object) -> bool | None:
    return value if type(value) is bool else None


def _version(reader: object, name: str) -> int:
    value = _get(reader, name)
    if type(value) is not int or not 0 <= value < 2**16:
        raise CarrotInputError("INVALID_VERSION")
    return value


def _optional(reader: object, name: str) -> float | None:
    if not _has(reader, name):
        return None
    child = _get(reader, name)
    if cast(Callable[[], str], _get(child, "which"))() != "value":
        return None
    return _number(_get(child, "value"))


def _stamp(reader: object, name: str) -> TimestampEvidence:
    if not _has(reader, name):
        return TimestampEvidence(None, "unavailable")
    child = _get(reader, name)
    domain = _enum(child, "clockDomain", ("monotonic", "bootTime"))
    value = (
        _get(child, "value") if cast(Callable[[], str], _get(child, "which"))() == "value" else None
    )
    if type(value) is not int or not 0 < value < 2**64:
        value = None
    return TimestampEvidence(value, domain)


def _actuators(reader: object, name: str) -> dict[str, float] | None:
    if not _has(reader, name):
        return None
    child = _get(reader, name)
    result = {}
    for key in (
        "gas",
        "brake",
        "torque",
        "steeringAngleDeg",
        "accel",
        "speed",
        "curvature",
        "torqueOutputCan",
        "jerk",
        "aTarget",
    ):
        value = _number(_get(child, key))
        if value is None:
            return None
        result[key] = value
    return result


def _check(sample: DecodedTopicSample, binding: SchemaBinding, topic: str) -> object:
    if type(sample) is not DecodedTopicSample or sample.topic != topic:
        raise CarrotInputError("WRONG_TOPIC")
    expected = {
        "carControl": binding.car_control_id,
        "carState": binding.car_state_id,
        "carOutput": binding.car_output_id,
    }[topic]
    reader = sample.reader
    if (
        type(reader) is not binding.reader_type
        or _get(_get(_get(reader, "schema"), "node"), "id") != expected
    ):
        raise CarrotInputError("WRONG_READER_SCHEMA")
    return reader


def _boundary[T](operation: Callable[[], T]) -> T:
    try:
        return operation()
    except CarrotInputError:
        raise
    except Exception as exc:
        raise CarrotInputError("MALFORMED_READER") from exc


def _measurement(reader: object) -> MeasurementEvidence:
    return MeasurementEvidence(
        version=_version(reader, "version"),
        mode=_enum(reader, "measurementMode", ("vehicleModelLive", "vehicleModelFallback")),
        validity=_enum(reader, "validityState", ("valid", "invalid")),
        car_state_health=_enum(reader, "carStateHealthState", ("valid", "invalid")),
        live_parameters_health=_enum(reader, "liveParametersHealthState", ("valid", "invalid")),
        car_state_time=_stamp(reader, "carStateMonoTime"),
        live_parameters_time=_stamp(reader, "liveParametersMonoTime"),
        calculation_time=_stamp(reader, "calculationMonoTime"),
        measured_curvature_inv_m=_optional(reader, "measuredCurvatureInvM"),
        input_speed_mps=_optional(reader, "inputSpeedMps"),
        input_steering_angle_deg=_optional(reader, "inputSteeringAngleDeg"),
        effective_stiffness_factor=_optional(reader, "effectiveStiffnessFactor"),
        effective_steer_ratio=_optional(reader, "effectiveSteerRatio"),
        effective_angle_offset_deg=_optional(reader, "effectiveAngleOffsetDeg"),
        effective_roll_rad=_optional(reader, "effectiveRollRad"),
    )


def extract_car_control(
    sample: DecodedTopicSample, binding: SchemaBinding, *, static_context_digest: str
) -> SourceCommandEvidence:
    def copy() -> SourceCommandEvidence:
        reader = _check(sample, binding, "carControl")
        observed = _get(reader, "lateralControlObservation")
        return SourceCommandEvidence(
            event_time=TimestampEvidence(sample.log_mono_time_ns, "monotonic"),
            event_valid=sample.event_valid,
            observation_version=_version(observed, "version"),
            controller_kind=_enum(
                observed,
                "controllerKind",
                ("torque", "pid", "angle", "mebCurvature", "other"),
                "unknown",
            ),
            instantaneous_limit=_enum(
                observed, "instantaneousLimitState", ("notLimited", "limited")
            ),
            lat_active=_boolean(_get(reader, "latActive")),
            measurement=_measurement(_get(observed, "measurement")),
            desired_target_state=_enum(observed, "desiredTargetState", ("available",)),
            desired_target_curvature_inv_m=_optional(observed, "desiredTargetCurvatureInvM"),
            requested_actuators=_actuators(reader, "actuators"),
            static_context_digest=static_context_digest,
        )

    return _boundary(copy)


def extract_car_state(
    sample: DecodedTopicSample, binding: SchemaBinding, *, steering_pressed_supported: bool
) -> SourceCarStateEvidence:
    def copy() -> SourceCarStateEvidence:
        reader = _check(sample, binding, "carState")
        return SourceCarStateEvidence(
            event_time=TimestampEvidence(sample.log_mono_time_ns, "monotonic"),
            event_valid=sample.event_valid,
            can_valid=_boolean(_get(reader, "canValid")),
            steering_pressed=_boolean(_get(reader, "steeringPressed"))
            if steering_pressed_supported is True
            else None,
            steering_pressed_supported=steering_pressed_supported is True,
            speed_mps=_number(_get(reader, "vEgo")),
            steering_angle_deg=_number(_get(reader, "steeringAngleDeg")),
        )

    return _boundary(copy)


def extract_car_output(sample: DecodedTopicSample, binding: SchemaBinding) -> ReceiptEvidence:
    def copy() -> ReceiptEvidence:
        reader = _get(_check(sample, binding, "carOutput"), "actuationReceipt")
        return ReceiptEvidence(
            version=_version(reader, "receiptVersion"),
            source_command_time=_stamp(reader, "sourceCarControlMonoTime"),
            host_apply_time=_stamp(reader, "hostApplyMonoTime"),
            host_activity=_enum(reader, "hostLateralActivityState", ("active", "inactive")),
            safety_permission=_enum(reader, "safetyPermissionState", ("allowed", "disallowed")),
            safety_state_time=_stamp(reader, "safetyStateMonoTime"),
            safety_observation_time=_stamp(reader, "safetyObservationMonoTime"),
            controller_kind=_enum(
                reader,
                "controllerKind",
                ("torque", "pid", "angle", "mebCurvature", "other"),
                "unknown",
            ),
            instantaneous_limit=_enum(
                reader, "instantaneousControllerLimitState", ("notLimited", "limited")
            ),
            output_limit=_enum(reader, "outputLimitState", ("notLimited", "limited")),
            controller_output_returned=True
            if _enum(reader, "controllerOutputReturned", ("returned",)) == "returned"
            else None,
            final_requested_actuators=_actuators(reader, "finalRequestedActuators"),
            controller_output_actuators=_actuators(reader, "controllerOutputActuators"),
        )

    return _boundary(copy)
