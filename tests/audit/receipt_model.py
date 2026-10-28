"""Synthetic audit oracle only: no wire extraction or production adapter.

All defaults below describe a synthetic test cohort, not vehicle policy. This
model independently specifies consumer decisions; it does not execute the fork.
"""

import math
from dataclasses import dataclass, fields

KINDS = frozenset({"torque", "pid", "angle", "mebCurvature"})


@dataclass(frozen=True, slots=True)
class Policy:
    maximum_age_s: float
    maximum_skew_s: float

    def __post_init__(self):
        for value in (self.maximum_age_s, self.maximum_skew_s):
            if isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("finite nonnegative caller policy required")


@dataclass(frozen=True, slots=True)
class AuditInput:
    receipt_version: int = 1
    command_ns: int | None = 9_990_000_000
    apply_ns: int | None = 10_000_000_000
    command_domain: str = "monotonic"
    apply_domain: str = "monotonic"
    host: str = "active"
    safety: str = "allowed"
    safety_state_ns: int | None = 9_980_000_000
    safety_observation_ns: int | None = 10_000_000_000
    safety_domain: str = "bootTime"
    safety_observation_domain: str = "bootTime"
    returned: str = "returned"
    request_actuators: tuple[float, ...] | None = (0.25, 2.0, 0.001)
    returned_actuators: tuple[float, ...] | None = (0.25, 2.0, 0.001)
    kind: str = "torque"
    expected_kind: str = "torque"
    calculation_version: int = 1
    instantaneous: str = "notLimited"
    output_limit: str = "notLimited"
    dummy_angle_limit: str = "unavailable"
    joined_command_ns: int | None = 9_990_000_000
    car_state_ns: int | None = 9_995_000_000
    controls_state_ns: int | None = 9_985_000_000
    car_state_domain: str = "monotonic"
    controls_state_domain: str = "monotonic"
    car_state_healthy: bool = True
    controls_state_healthy: bool = True
    measurement_valid: bool = True
    receipt_transport_healthy: bool = True
    outer_valid: bool = True
    speed_mps: float | None = 4.0
    driver_override: bool | None = False
    evaluation_ns: int = 10_020_000_000
    baseline_parameters: tuple[tuple[str, float], ...] = (("synthetic.test_only", 10.0),)
    trusted_baseline: tuple[tuple[str, float], ...] = (("synthetic.test_only", 10.0),)


@dataclass(frozen=True, slots=True)
class AuditDecision:
    control_active: bool | None
    controller_saturated: bool | None
    source_valid: bool
    reasons: tuple[str, ...]
    cohort_key: tuple[int, int] | None
    timestamp_s: float | None
    source_age_s: float | None
    evaluated_source_age_s: float | None
    conditional_checks_passed: bool
    baseline_unchanged: bool = True

    def as_record(self):
        return {
            "control_active": self.control_active,
            "controller_saturated": self.controller_saturated,
            "source_valid": self.source_valid,
            "reasons": list(self.reasons),
            "cohort_key": list(self.cohort_key) if self.cohort_key else None,
            "timestamp_s": self.timestamp_s,
            "source_age_s": self.source_age_s,
            "evaluated_source_age_s": self.evaluated_source_age_s,
            "conditional_checks_passed": self.conditional_checks_passed,
            "baseline_unchanged": self.baseline_unchanged,
        }


def _stamp(value):
    return type(value) is int and value > 0


def _finite_actuators(value):
    return (
        value is not None
        and len(value) > 0
        and all(type(number) in (int, float) and math.isfinite(number) for number in value)
    )


def evaluate(sample: AuditInput, policy: Policy) -> AuditDecision:
    """Project proposed admission truth tables without constructing a Snapshot."""
    reasons = []
    key = None
    anchor = None
    source_age = evaluated_age = None
    if (
        type(sample.receipt_version) is int
        and sample.receipt_version == 1
        and _stamp(sample.command_ns)
        and _stamp(sample.apply_ns)
        and sample.command_domain == sample.apply_domain == "monotonic"
        and sample.command_ns <= sample.apply_ns <= sample.evaluation_ns
    ):
        key = (sample.command_ns, sample.apply_ns)
        anchor = sample.apply_ns / 1e9
        times = (sample.command_ns, sample.car_state_ns, sample.controls_state_ns)
        if all(_stamp(stamp) and stamp <= sample.apply_ns for stamp in times):
            source_age = (sample.apply_ns - min(times)) / 1e9
            evaluated_age = (sample.evaluation_ns - min(times)) / 1e9
    if type(sample.receipt_version) is not int or sample.receipt_version != 1:
        reasons.append("UNSUPPORTED_RECEIPT")
    elif key is None:
        reasons.append("INVALID_COHORT_CLOCK")
    elif sample.joined_command_ns != sample.command_ns:
        reasons.append("COMMAND_COHORT_MISMATCH")
    elif sample.kind not in KINDS or sample.kind != sample.expected_kind:
        reasons.append("CONTROLLER_KIND_MISMATCH")
    elif type(sample.calculation_version) is not int or sample.calculation_version != 1:
        reasons.append("CALCULATION_VERSION_UNAVAILABLE")
    elif sample.returned != "returned":
        reasons.append("CONTROLLER_RETURN_UNAVAILABLE")
    elif not all(
        _finite_actuators(v) for v in (sample.request_actuators, sample.returned_actuators)
    ):
        reasons.append("ACTUATORS_UNAVAILABLE_OR_NONFINITE")
    elif (
        not _stamp(sample.safety_state_ns)
        or not _stamp(sample.safety_observation_ns)
        or sample.safety_state_ns > sample.safety_observation_ns
        or sample.safety_domain != "bootTime"
        or sample.safety_observation_domain != "bootTime"
        or sample.safety not in {"allowed", "disallowed"}
    ):
        reasons.append("SAFETY_PERMISSION_UNAVAILABLE")

    complete = not reasons
    active = saturated = None
    if complete:
        if sample.host == "inactive" or sample.host == "active" and sample.safety == "disallowed":
            active = False
        elif sample.host == "active" and sample.safety == "allowed":
            active = True
        if "limited" in (sample.instantaneous, sample.output_limit):
            saturated = True
        elif (
            sample.host == "active" and sample.instantaneous == sample.output_limit == "notLimited"
        ):
            saturated = False
        if active is None:
            reasons.append("HOST_ACTIVITY_UNAVAILABLE")
        if saturated is None:
            reasons.append("LIMIT_EVIDENCE_UNAVAILABLE")

    if key is not None:
        if (sample.evaluation_ns - sample.apply_ns) / 1e9 > policy.maximum_age_s:
            reasons.append("STALE_RECEIPT")
        for name, stamp, domain, healthy in (
            ("CAR_STATE", sample.car_state_ns, sample.car_state_domain, sample.car_state_healthy),
            (
                "CONTROLS_STATE",
                sample.controls_state_ns,
                sample.controls_state_domain,
                sample.controls_state_healthy,
            ),
        ):
            if domain != "monotonic" or not _stamp(stamp) or stamp > sample.apply_ns:
                reasons.append(name + "_ALIGNMENT_UNAVAILABLE")
            elif (sample.evaluation_ns - stamp) / 1e9 > policy.maximum_age_s:
                reasons.append("STALE_" + name)
            elif (sample.apply_ns - stamp) / 1e9 > policy.maximum_skew_s:
                reasons.append("EXCESSIVE_" + name + "_SKEW")
            if healthy is not True:
                reasons.append(name + "_UNHEALTHY")
        if _stamp(sample.controls_state_ns) and sample.controls_state_ns > sample.command_ns:
            reasons.append("CONTROLS_STATE_AFTER_COMMAND")
    if sample.receipt_transport_healthy is not True:
        reasons.append("RECEIPT_TRANSPORT_UNHEALTHY")
    if sample.measurement_valid is not True:
        reasons.append("MEASUREMENT_UNAVAILABLE")
    if (
        type(sample.speed_mps) not in (int, float)
        or not math.isfinite(sample.speed_mps)
        or sample.speed_mps < 0
    ):
        reasons.append("SPEED_UNAVAILABLE")
    if type(sample.driver_override) is not bool:
        reasons.append("DRIVER_OVERRIDE_UNAVAILABLE")
    if sample.baseline_parameters != sample.trusted_baseline:
        reasons.append("BASELINE_MISMATCH")
    conditional = not reasons
    # The exact inspected pin cannot prove the measurement producer's effective
    # configuration/input cohort. Synthetic health cannot waive this audit fact.
    reasons.append("MEASUREMENT_PROVENANCE_UNPROVEN_AT_PIN")
    if sample.kind == "mebCurvature":
        reasons.append("MEB_DESIRED_RESPONSE_UNPROVEN_AT_PIN")
    return AuditDecision(
        active,
        saturated,
        False,
        tuple(reasons),
        key,
        anchor,
        source_age,
        evaluated_age,
        conditional,
    )


def from_record(record):
    """Freeze a synthetic JSON fixture; never accepts a message or controller."""
    if set(record) - {field.name for field in fields(AuditInput)}:
        raise ValueError("unsupported synthetic field")
    record = dict(record)
    for key in ("request_actuators", "returned_actuators"):
        if key in record and record[key] is not None:
            record[key] = tuple(float("nan") if v == "NON_FINITE" else v for v in record[key])
    for key in ("baseline_parameters", "trusted_baseline"):
        if key in record:
            record[key] = tuple(sorted((name, value) for name, value in record[key].items()))
    return AuditInput(**record)
