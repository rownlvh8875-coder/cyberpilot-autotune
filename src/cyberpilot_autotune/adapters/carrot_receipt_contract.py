"""Pure observation-v2 contract; no messages, cache, extraction or control access.

Inputs are immutable copies from an independently qualified extraction boundary.
Context/session attestations are caller metadata, not additional wire fields.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from enum import Enum
from types import MappingProxyType

from cyberpilot_autotune.contracts import ObservationSnapshot
from cyberpilot_autotune.contracts.validation import ValidationError, count, finite, parameters


class MappingReason(Enum):
    ACCEPTED = "ACCEPTED"
    INVALID_INPUT = "INVALID_INPUT"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    DUPLICATE_COHORT = "DUPLICATE_COHORT"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    MISSING_SOURCE_COMMAND = "MISSING_SOURCE_COMMAND"
    MISSING_SOURCE_CAR_STATE = "MISSING_SOURCE_CAR_STATE"
    CLOCK_DOMAIN = "CLOCK_DOMAIN"
    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"
    TIME_ORDER = "TIME_ORDER"
    STALE_RECEIPT = "STALE_RECEIPT"
    COMMAND_DELAY = "COMMAND_DELAY"
    CAR_STATE_AGE = "CAR_STATE_AGE"
    LIVE_PARAMETERS_AGE = "LIVE_PARAMETERS_AGE"
    CALCULATION_AGE = "CALCULATION_AGE"
    SAFETY_AGE = "SAFETY_AGE"
    SOURCE_SKEW = "SOURCE_SKEW"
    CONTROLLER_MISMATCH = "CONTROLLER_MISMATCH"
    UNAVAILABLE_ACTIVITY = "UNAVAILABLE_ACTIVITY"
    UNAVAILABLE_LIMIT = "UNAVAILABLE_LIMIT"
    INVALID_ACTUATORS = "INVALID_ACTUATORS"
    INVALID_MEASUREMENT = "INVALID_MEASUREMENT"
    INVALID_TARGET = "INVALID_TARGET"
    STATIC_CONTEXT_MISMATCH = "STATIC_CONTEXT_MISMATCH"
    BASELINE_MISMATCH = "BASELINE_MISMATCH"
    INVALID_SOURCE_CAR_STATE = "INVALID_SOURCE_CAR_STATE"


@dataclass(frozen=True, slots=True)
class TimestampEvidence:
    value_ns: int | None
    domain: str


@dataclass(frozen=True, slots=True, kw_only=True)
class StaticVehicleContext:
    mass: float
    rotational_inertia: float
    wheelbase: float
    center_to_front: float
    steer_ratio_rear: float
    tire_stiffness_front: float
    tire_stiffness_rear: float
    initial_steer_ratio: float
    brand: str
    flags: int
    steer_control_type: str
    lateral_tuning_kind: str
    source_revision: str
    observation_schema_revision: str

    def __post_init__(self) -> None:
        for name in (
            "mass",
            "rotational_inertia",
            "wheelbase",
            "center_to_front",
            "steer_ratio_rear",
            "tire_stiffness_front",
            "tire_stiffness_rear",
            "initial_steer_ratio",
        ):
            value = finite(getattr(self, name), name)
            if name != "steer_ratio_rear" and value <= 0:
                raise ValidationError("static geometry must be positive")
            object.__setattr__(self, name, value)
        count(self.flags, "flags")
        if not 0 < self.center_to_front < self.wheelbase:
            raise ValidationError("invalid axle geometry")
        if (
            self.source_revision != "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
            or self.observation_schema_revision != "observation-v2-measurement-v1"
            or self.steer_control_type not in ("torque", "angle")
            or self.lateral_tuning_kind not in ("pid", "torque")
            or type(self.brand) is not str
            or not self.brand.isascii()
            or not self.brand.isalpha()
        ):
            raise ValidationError("unsupported pinned static context")

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(
                asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()

    @property
    def controller_kind(self) -> str:
        # Pinned is_volkswagen_meb/VolkswagenFlags.MEB, not a tuning constant.
        if self.brand == "volkswagen" and self.flags & 16:
            return "mebCurvature"
        return "angle" if self.steer_control_type == "angle" else self.lateral_tuning_kind


@dataclass(frozen=True, slots=True, kw_only=True)
class CarrotSnapshotPolicy:
    maximum_receipt_age_s: float
    maximum_command_to_apply_delay_s: float
    maximum_car_state_age_s: float
    maximum_live_parameters_age_s: float
    maximum_calculation_age_s: float
    maximum_safety_state_age_s: float
    maximum_source_skew_s: float
    supported_receipt_versions: tuple[int, ...]
    supported_observation_versions: tuple[int, ...]
    supported_measurement_versions: tuple[int, ...]
    allowed_controller_kinds: tuple[str, ...]
    static_context_digest: str
    baseline_epoch: int

    def __post_init__(self) -> None:
        for name in (
            "maximum_receipt_age_s",
            "maximum_command_to_apply_delay_s",
            "maximum_car_state_age_s",
            "maximum_live_parameters_age_s",
            "maximum_calculation_age_s",
            "maximum_safety_state_age_s",
            "maximum_source_skew_s",
        ):
            if finite(getattr(self, name), name) < 0:
                raise ValidationError("age/skew limits must be nonnegative")
        for name, supported in (
            ("supported_receipt_versions", 1),
            ("supported_observation_versions", 2),
            ("supported_measurement_versions", 1),
        ):
            values = tuple(getattr(self, name))
            if values != (supported,) or any(type(value) is not int for value in values):
                raise ValidationError("unsupported version policy")
            object.__setattr__(self, name, values)
        kinds = tuple(self.allowed_controller_kinds)
        if (
            not kinds
            or len(set(kinds)) != len(kinds)
            or not set(kinds)
            <= {
                "pid",
                "torque",
                "angle",
                "mebCurvature",
            }
        ):
            raise ValidationError("unsupported controller policy")
        object.__setattr__(self, "allowed_controller_kinds", kinds)
        if (
            type(self.static_context_digest) is not str
            or len(self.static_context_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.static_context_digest)
        ):
            raise ValidationError("invalid context digest")
        count(self.baseline_epoch, "baseline_epoch")


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasurementEvidence:
    version: int
    mode: str
    validity: str
    car_state_health: str
    live_parameters_health: str
    car_state_time: TimestampEvidence
    live_parameters_time: TimestampEvidence
    calculation_time: TimestampEvidence
    measured_curvature_inv_m: float | None
    input_speed_mps: float | None
    input_steering_angle_deg: float | None
    effective_stiffness_factor: float | None
    effective_steer_ratio: float | None
    effective_angle_offset_deg: float | None
    effective_roll_rad: float | None


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceCommandEvidence:
    event_time: TimestampEvidence
    event_valid: bool | None
    observation_version: int
    controller_kind: str
    instantaneous_limit: str
    lat_active: bool | None
    measurement: MeasurementEvidence
    desired_target_state: str
    desired_target_curvature_inv_m: float | None
    requested_actuators: Mapping[str, float] | None
    static_context_digest: str

    def __post_init__(self) -> None:
        if self.requested_actuators is not None:
            object.__setattr__(
                self, "requested_actuators", MappingProxyType(dict(self.requested_actuators))
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ReceiptEvidence:
    version: int
    source_command_time: TimestampEvidence
    host_apply_time: TimestampEvidence
    host_activity: str
    safety_permission: str
    safety_state_time: TimestampEvidence
    safety_observation_time: TimestampEvidence
    controller_kind: str
    instantaneous_limit: str
    output_limit: str
    controller_output_returned: bool | None
    final_requested_actuators: Mapping[str, float] | None
    controller_output_actuators: Mapping[str, float] | None

    def __post_init__(self) -> None:
        for name in ("final_requested_actuators", "controller_output_actuators"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, MappingProxyType(dict(value)))


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceCarStateEvidence:
    event_time: TimestampEvidence
    event_valid: bool | None
    can_valid: bool | None
    steering_pressed: bool | None
    steering_pressed_supported: bool
    speed_mps: float | None
    steering_angle_deg: float | None


@dataclass(frozen=True, slots=True, kw_only=True)
class MappingAttempt:
    receipt: ReceiptEvidence
    source_command: SourceCommandEvidence | None
    source_car_state: SourceCarStateEvidence | None
    static_context: StaticVehicleContext
    baseline_parameters: Mapping[str, float]
    baseline_epoch: int
    evaluation_time: TimestampEvidence
    sequence: int
    previous_sequence: int | None
    previous_host_apply_ns: int | None
    consumed_cohorts: tuple[tuple[int, int], ...]
    exact_lookup_unambiguous: bool
    car_output_transport_healthy: bool
    outer_car_output_valid: bool | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseline_parameters", parameters(self.baseline_parameters))
        object.__setattr__(
            self, "consumed_cohorts", tuple(tuple(key) for key in self.consumed_cohorts)
        )


@dataclass(frozen=True, slots=True)
class MappingDecision:
    snapshot: ObservationSnapshot | None
    reason: MappingReason
    cohort_key: tuple[int, int] | None
    control_active: bool | None = None
    controller_saturated: bool | None = None


class _Rejected(Exception):
    def __init__(self, reason: MappingReason) -> None:
        self.reason = reason


def _require(condition: bool, reason: MappingReason) -> None:
    if not condition:
        raise _Rejected(reason)


def _number(value: object, reason: MappingReason) -> float:
    try:
        return finite(value, "evidence number")
    except ValidationError as exc:
        raise _Rejected(reason) from exc


def _ns(value: TimestampEvidence, domain: str) -> int:
    _require(
        type(value) is TimestampEvidence and value.domain == domain, MappingReason.CLOCK_DOMAIN
    )
    stamp = value.value_ns
    if type(stamp) is not int or not 0 < stamp < 2**64:
        raise _Rejected(MappingReason.MISSING_TIMESTAMP)
    return stamp


def _actuators(values: Mapping[str, float] | None) -> Mapping[str, float]:
    if values is None:
        raise _Rejected(MappingReason.INVALID_ACTUATORS)
    _require(
        set(values)
        == {
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
        },
        MappingReason.INVALID_ACTUATORS,
    )
    for value in values.values():
        _number(value, MappingReason.INVALID_ACTUATORS)
    return values


def evaluate(
    attempt: MappingAttempt, policy: CarrotSnapshotPolicy, baseline_parameters: Mapping[str, float]
) -> MappingDecision:
    """Map one caller-owned attempt; this function cannot consume/cache anything."""
    cohort: tuple[int, int] | None = None
    active: bool | None = None
    limited: bool | None = None
    try:
        _require(
            type(attempt) is MappingAttempt and type(policy) is CarrotSnapshotPolicy,
            MappingReason.INVALID_INPUT,
        )
        # Revalidate immutable configuration, including objects corrupted outside the API.
        policy = replace(policy)
        context = replace(attempt.static_context)
        baseline = parameters(baseline_parameters)
        receipt = attempt.receipt
        command_ns = _ns(receipt.source_command_time, "monotonic")
        apply_ns = _ns(receipt.host_apply_time, "monotonic")
        cohort = command_ns, apply_ns
        count(attempt.sequence, "sequence")
        if attempt.previous_sequence is not None:
            count(attempt.previous_sequence, "previous_sequence")
            _require(attempt.sequence > attempt.previous_sequence, MappingReason.OUT_OF_ORDER)
        _require(attempt.car_output_transport_healthy is True, MappingReason.INVALID_INPUT)
        _require(cohort not in attempt.consumed_cohorts, MappingReason.DUPLICATE_COHORT)
        if attempt.previous_host_apply_ns is not None:
            count(attempt.previous_host_apply_ns, "previous_host_apply_ns")
            _require(apply_ns > attempt.previous_host_apply_ns, MappingReason.OUT_OF_ORDER)
        command = attempt.source_command
        if command is None or attempt.exact_lookup_unambiguous is not True:
            raise _Rejected(MappingReason.MISSING_SOURCE_COMMAND)
        _require(
            _ns(command.event_time, "monotonic") == command_ns, MappingReason.MISSING_SOURCE_COMMAND
        )
        measurement = command.measurement
        for version, supported in (
            (receipt.version, policy.supported_receipt_versions),
            (command.observation_version, policy.supported_observation_versions),
        ):
            _require(
                type(version) is int and version in supported, MappingReason.UNSUPPORTED_VERSION
            )
        source_cs = attempt.source_car_state
        if source_cs is None:
            raise _Rejected(MappingReason.MISSING_SOURCE_CAR_STATE)
        _require(
            context.digest == policy.static_context_digest == command.static_context_digest,
            MappingReason.STATIC_CONTEXT_MISMATCH,
        )
        _require(
            type(attempt.baseline_epoch) is int
            and attempt.baseline_epoch == policy.baseline_epoch
            and parameters(attempt.baseline_parameters) == baseline,
            MappingReason.BASELINE_MISMATCH,
        )
        _require(
            receipt.controller_kind == command.controller_kind == context.controller_kind
            and receipt.controller_kind in policy.allowed_controller_kinds
            and receipt.instantaneous_limit == command.instantaneous_limit,
            MappingReason.CONTROLLER_MISMATCH,
        )
        requested = _actuators(receipt.final_requested_actuators)
        _actuators(receipt.controller_output_actuators)
        if receipt.host_activity == "active":
            _require(
                requested == _actuators(command.requested_actuators),
                MappingReason.INVALID_ACTUATORS,
            )
        safety_state_ns = _ns(receipt.safety_state_time, "bootTime")
        safety_observation_ns = _ns(receipt.safety_observation_time, "bootTime")
        _require(safety_state_ns <= safety_observation_ns, MappingReason.TIME_ORDER)
        if receipt.host_activity == "inactive":
            _require(
                receipt.safety_permission in ("allowed", "disallowed")
                and receipt.controller_output_returned is True
                and command.event_valid is True,
                MappingReason.UNAVAILABLE_ACTIVITY,
            )
            # Inactive source commands intentionally have no measurement/target.
            active = False
            raise _Rejected(MappingReason.UNAVAILABLE_LIMIT)
        cs_ns = _ns(measurement.car_state_time, "monotonic")
        _require(
            _ns(source_cs.event_time, "monotonic") == cs_ns, MappingReason.MISSING_SOURCE_CAR_STATE
        )
        lp_ns = _ns(measurement.live_parameters_time, "monotonic")
        calculation_ns = _ns(measurement.calculation_time, "monotonic")
        now_ns = _ns(attempt.evaluation_time, "monotonic")
        _require(
            cs_ns <= calculation_ns <= command_ns <= apply_ns <= now_ns and lp_ns <= calculation_ns,
            MappingReason.TIME_ORDER,
        )
        _require(
            receipt.host_activity in ("active", "inactive")
            and receipt.safety_permission in ("allowed", "disallowed")
            and receipt.controller_output_returned is True
            and command.event_valid is True
            and (receipt.host_activity == "inactive" or command.lat_active is True),
            MappingReason.UNAVAILABLE_ACTIVITY,
        )
        active = receipt.host_activity == "active" and receipt.safety_permission == "allowed"
        a, b = receipt.instantaneous_limit, receipt.output_limit
        states = ("unavailable", "notLimited", "limited")
        if receipt.host_activity == "active" and a in states and b in states:
            if "limited" in (a, b):
                limited = True
            elif a == b == "notLimited":
                limited = False
        _require(limited is not None, MappingReason.UNAVAILABLE_LIMIT)
        _require(
            type(measurement.version) is int
            and measurement.version in policy.supported_measurement_versions,
            MappingReason.UNSUPPORTED_VERSION,
        )
        _require(
            measurement.mode == "vehicleModelLive"
            and measurement.validity == "valid"
            and measurement.car_state_health == measurement.live_parameters_health == "valid",
            MappingReason.INVALID_MEASUREMENT,
        )
        measured, speed, angle, stiffness, ratio, _offset, _roll = (
            _number(value, MappingReason.INVALID_MEASUREMENT)
            for value in (
                measurement.measured_curvature_inv_m,
                measurement.input_speed_mps,
                measurement.input_steering_angle_deg,
                measurement.effective_stiffness_factor,
                measurement.effective_steer_ratio,
                measurement.effective_angle_offset_deg,
                measurement.effective_roll_rad,
            )
        )
        _require(speed >= 0 and stiffness > 0 and ratio > 0, MappingReason.INVALID_MEASUREMENT)
        _require(
            source_cs.event_valid is True
            and source_cs.can_valid is True
            and source_cs.steering_pressed_supported is True
            and type(source_cs.steering_pressed) is bool
            and _number(source_cs.speed_mps, MappingReason.INVALID_SOURCE_CAR_STATE) == speed
            and _number(source_cs.steering_angle_deg, MappingReason.INVALID_SOURCE_CAR_STATE)
            == angle,
            MappingReason.INVALID_SOURCE_CAR_STATE,
        )
        _require(command.desired_target_state == "available", MappingReason.INVALID_TARGET)
        desired = _number(command.desired_target_curvature_inv_m, MappingReason.INVALID_TARGET)
        delays = (
            (now_ns - apply_ns, policy.maximum_receipt_age_s, MappingReason.STALE_RECEIPT),
            (
                apply_ns - command_ns,
                policy.maximum_command_to_apply_delay_s,
                MappingReason.COMMAND_DELAY,
            ),
            (apply_ns - cs_ns, policy.maximum_car_state_age_s, MappingReason.CAR_STATE_AGE),
            (
                apply_ns - lp_ns,
                policy.maximum_live_parameters_age_s,
                MappingReason.LIVE_PARAMETERS_AGE,
            ),
            (
                apply_ns - calculation_ns,
                policy.maximum_calculation_age_s,
                MappingReason.CALCULATION_AGE,
            ),
            (
                safety_observation_ns - safety_state_ns,
                policy.maximum_safety_state_age_s,
                MappingReason.SAFETY_AGE,
            ),
        )
        for delay_ns, maximum_s, reason in delays:
            _require(delay_ns / 1e9 <= maximum_s, reason)
        source_times = command_ns, cs_ns, lp_ns, calculation_ns
        _require(
            (max(source_times) - min(source_times)) / 1e9 <= policy.maximum_source_skew_s,
            MappingReason.SOURCE_SKEW,
        )
        context_key = (
            f"carrot-contract-v1/r1/o2/{receipt.controller_kind}/vm:{context.digest}"
            f"/baseline:{policy.baseline_epoch}"
        )
        snapshot = ObservationSnapshot(
            timestamp_s=apply_ns / 1e9,
            sequence=attempt.sequence,
            source_age_s=max(item[0] for item in delays[1:]) / 1e9,
            context_key=context_key,
            source_valid=True,
            speed_mps=speed,
            desired_curvature_inv_m=desired,
            measured_curvature_inv_m=measured,
            lateral_acceleration_mps2=None,
            controller_saturated=limited,
            driver_override=source_cs.steering_pressed,
            baseline_parameters=baseline,
            control_active=active,
        )
        return MappingDecision(snapshot, MappingReason.ACCEPTED, cohort, active, limited)
    except _Rejected as exc:
        return MappingDecision(None, exc.reason, cohort, active, limited)
    except Exception:
        # One boundary handles malformed evidence, not core programming errors elsewhere.
        return MappingDecision(None, MappingReason.INVALID_INPUT, cohort, active, limited)
