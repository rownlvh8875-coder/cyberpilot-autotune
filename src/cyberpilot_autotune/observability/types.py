"""Strict neutral primitives; unknown, numeric zero and false are distinct."""

import hashlib
import json
import math
import re
from enum import StrEnum

RUNTIME = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
CURRENT = "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3"
VERSION = "friction-observation-v1"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def real(value: object) -> float | None:
    if value is None:
        return None
    try:
        require(type(value) in (int, float) and math.isfinite(value), "NONFINITE_INPUT")  # type: ignore[arg-type]
        return float(value)  # type: ignore[arg-type]
    except OverflowError as exc:
        raise ValueError("NONFINITE_INPUT") from exc


def uint64(value: object, *, optional: bool = False) -> None:
    require((optional and value is None) or (type(value) is int and 0 <= value < 2**64), "UINT64")


def sha(value: object, length: int = 64, *, optional: bool = False) -> None:
    require(
        (optional and value is None)
        or (type(value) is str and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None),
        "CONTENT_ID",
    )


def boolean(value: object) -> None:
    require(value is None or type(value) is bool, "OPTIONAL_BOOL")


def token(value: object, *, optional: bool = False) -> None:
    require(
        (optional and value is None)
        or (type(value) is str and re.fullmatch("[A-Za-z0-9_.:-]{1,96}", value) is not None),
        "SEMANTIC_TOKEN",
    )


def enum_value(value: object, enum: type[StrEnum]) -> None:
    require(type(value) is enum, "ENUM_TYPE")


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class ClockDomain(StrEnum):
    MONOTONIC = "MONOTONIC"
    UNKNOWN = "UNKNOWN"
    SENSOR = "SENSOR"


class CallbackStage(StrEnum):
    LINEAR_CALLBACK_PRE_PID = "LINEAR_CALLBACK_PRE_PID"
    NN_LITE_CALLBACK_PRE_PID = "NN_LITE_CALLBACK_PRE_PID"
    NN_CALLBACK_PRE_PID = "NN_CALLBACK_PRE_PID"
    GM_SIGLIN_CALLBACK_PRE_PID = "GM_SIGLIN_CALLBACK_PRE_PID"
    OTHER_UNSUPPORTED = "OTHER_UNSUPPORTED"


class CallbackFamily(StrEnum):
    LINEAR = "LINEAR"
    NN_LITE = "NN_LITE"
    NN = "NN"
    GM_SIGLIN = "GM_SIGLIN"
    GM_NEURAL = "GM_NEURAL"
    OTHER = "OTHER"


class CallbackFunction(StrEnum):
    BASE_LINEAR = "CarInterfaceBase.torque_from_lateral_accel_linear"
    GM_SIGLIN = "CarInterface.torque_from_lateral_accel_siglin"
    GM_NEURAL = "CarInterface.torque_from_lateral_accel_neural"
    NN_MODEL = "get_ff_nn"
    OTHER = "OTHER"


class CallbackSite(StrEnum):
    FEEDFORWARD = "FEEDFORWARD"
    SETPOINT = "SETPOINT"
    MEASUREMENT = "MEASUREMENT"
    NN_FRICTION_OVERRIDE = "NN_FRICTION_OVERRIDE"
    UNKNOWN = "UNKNOWN"


class ControllerMode(StrEnum):
    STANDARD = "STANDARD"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"


class SourceRole(StrEnum):
    CAR_STATE = "carState"
    LIVE_POSE = "livePose"
    LIVE_PARAMETERS = "liveParameters"
    CAR_CONTROL = "carControl"
    MODEL = "modelV2"
    CONTROL_STATE = "controlState"
    DELAY = "liveDelay"


class SourceOrigin(StrEnum):
    WIRE_EVENT = "WIRE_EVENT"
    LOCAL_CYCLE_OBJECT = "LOCAL_CYCLE_OBJECT"
    UNKNOWN = "UNKNOWN"


class Precision(StrEnum):
    BINARY64 = "CONTROLLER_LOCAL_BINARY64"
    FLOAT32 = "LEGACY_FLOAT32"
    UNKNOWN = "UNKNOWN"


class ScalarOrigin(StrEnum):
    LOCAL_DIRECT = "LOCAL_DIRECT"
    HELPER_OBSERVED = "HELPER_OBSERVED"
    LEGACY_PUBLISHED = "LEGACY_PUBLISHED"
    RECONSTRUCTED = "RECONSTRUCTED_DIAGNOSTIC"
    INSTALLED_C_DERIVED = "DERIVED_FROM_INSTALLED_C"
    DOWNSTREAM = "DOWNSTREAM"
    UNAVAILABLE = "UNAVAILABLE"


class Stage(StrEnum):
    CALLBACK_INPUT = "CALLBACK_INPUT"
    HELPER_Q = "HELPER_Q"
    RAW_CALLBACK = "RAW_CALLBACK_PRE_PID_KF"
    PID_P = "PID_P"
    PID_I = "PID_I"
    PID_D = "PID_D"
    PID_F = "PID_SCALED_F"
    PID_SUM = "PID_PRE_CLIP_SUM"
    PID_CLIPPED = "PID_POST_CLIP_INTERNAL_SIGN"
    REQUESTED_TORQUE = "REQUESTED_ACTUATOR_TORQUE"
    HOST_OUTPUT = "HOST_CONTROLLER_OUTPUT"
    APPLIED_TORQUE = "APPLIED_NORMALIZED_TORQUE"


class Signal(StrEnum):
    DESIRED_ACCEL = "desired_lateral_accel"
    ACTUAL_ACCEL = "actual_lateral_accel"
    ROLL = "roll"
    ROLL_COMPENSATION = "roll_compensation"
    CALLBACK_ACCEL = "callback_acceleration"
    FRICTION_INPUT = "friction_input"
    DEADZONE = "friction_deadzone"
    THRESHOLD = "friction_threshold"
    Q_OBSERVED = "q_observed"
    CALLBACK_OUTPUT = "callback_output_raw"
    PID_P = "pid_p"
    PID_I = "pid_i"
    PID_D = "pid_d"
    PID_F = "pid_f"
    PID_SUM = "pid_sum"
    PID_OUTPUT = "post_pid_output"
    REQUESTED_TORQUE = "requested_torque"
    HOST_OUTPUT = "host_output"
    APPLIED_TORQUE = "applied_torque"


class GeometryOrigin(StrEnum):
    STATIC_CP = "STATIC_CP_BASELINE_APPLIED_VM"
    APPLIED_VM = "ACTUALLY_APPLIED_VM"
    REQUESTED = "REQUESTED_NOT_APPLIED"
    LIVE_CANDIDATE = "LIVE_PARAMETERS_CANDIDATE"
    UNAVAILABLE = "UNAVAILABLE"


class DelaySource(StrEnum):
    STATIC_CP = "STATIC_CP"
    MANUAL = "MANUAL"
    LIVE_DELAY = "LIVE_DELAY"
    UNAVAILABLE = "UNAVAILABLE"


class AlignmentMethod(StrEnum):
    NONE = "RAW_CALLBACK_NO_ALIGNMENT"
    SINGLE_DOWNSTREAM_PAIR = "SINGLE_DOWNSTREAM_PAIR"
    CORE_VALUES_SHIFTED = "CORE_VALUES_SHIFTED"
    UNKNOWN = "UNKNOWN"


class OffsetSource(StrEnum):
    INSTALLED_UNUSED_LINEAR = "INSTALLED_BUT_UNUSED_LINEAR"
    FILTERED_LIVE = "FILTERED_LIVE_CONTEXT_ONLY"
    RAW_LIVE = "RAW_LIVE_CONTEXT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
