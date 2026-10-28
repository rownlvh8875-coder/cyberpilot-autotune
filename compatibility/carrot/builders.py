"""Build synthetic Events using the actual pinned generated bindings."""

from cyberpilot_autotune.integrations.carrot.extraction import DecodedTopicSample
from tests.fixtures.carrot_adapter import healthy, session


def _enum(parent, field, value, allowed):
    setattr(parent, field, value if value in allowed else 65535)


def _stamp(parent, field, stamp):
    child = getattr(parent, field)
    if stamp.value_ns is not None:
        child.value = stamp.value_ns
    _enum(child, "clockDomain", stamp.domain, ("unavailable", "monotonic", "bootTime"))


def _number(parent, field, value):
    if value is not None:
        getattr(parent, field).value = value


def _actuators(parent, field, value):
    if value is not None:
        target = getattr(parent, field)
        for key, number in value.items():
            setattr(target, key, number)


def car_control(log, source):
    event = log.Event.new_message(logMonoTime=source.event_time.value_ns, valid=source.event_valid)
    target = event.init("carControl")
    target.latActive = source.lat_active
    _actuators(target, "actuators", source.requested_actuators)
    obs = target.lateralControlObservation
    obs.version = source.observation_version
    _enum(
        obs,
        "controllerKind",
        source.controller_kind,
        ("unknown", "torque", "pid", "angle", "mebCurvature", "other"),
    )
    _enum(
        obs,
        "instantaneousLimitState",
        source.instantaneous_limit,
        ("unavailable", "notLimited", "limited"),
    )
    _enum(obs, "desiredTargetState", source.desired_target_state, ("unavailable", "available"))
    _number(obs, "desiredTargetCurvatureInvM", source.desired_target_curvature_inv_m)
    m = obs.measurement
    source = source.measurement
    m.version = source.version
    _enum(
        m,
        "measurementMode",
        source.mode,
        ("unavailable", "vehicleModelLive", "vehicleModelFallback"),
    )
    for wire, neutral in (
        ("validityState", "validity"),
        ("carStateHealthState", "car_state_health"),
        ("liveParametersHealthState", "live_parameters_health"),
    ):
        _enum(m, wire, getattr(source, neutral), ("unavailable", "invalid", "valid"))
    for wire, neutral in (
        ("carStateMonoTime", "car_state_time"),
        ("liveParametersMonoTime", "live_parameters_time"),
        ("calculationMonoTime", "calculation_time"),
    ):
        _stamp(m, wire, getattr(source, neutral))
    for wire, neutral in (
        ("measuredCurvatureInvM", "measured_curvature_inv_m"),
        ("inputSpeedMps", "input_speed_mps"),
        ("inputSteeringAngleDeg", "input_steering_angle_deg"),
        ("effectiveStiffnessFactor", "effective_stiffness_factor"),
        ("effectiveSteerRatio", "effective_steer_ratio"),
        ("effectiveAngleOffsetDeg", "effective_angle_offset_deg"),
        ("effectiveRollRad", "effective_roll_rad"),
    ):
        _number(m, wire, getattr(source, neutral))
    return event


def car_state(log, source):
    event = log.Event.new_message(logMonoTime=source.event_time.value_ns, valid=source.event_valid)
    target = event.init("carState")
    target.canValid = source.can_valid
    if source.steering_pressed is not None:
        target.steeringPressed = source.steering_pressed
    if source.speed_mps is not None:
        target.vEgo = source.speed_mps
    if source.steering_angle_deg is not None:
        target.steeringAngleDeg = source.steering_angle_deg
    return event


def car_output(log, source, *, event_valid=True, event_ns=10_005_000_000):
    event = log.Event.new_message(logMonoTime=event_ns, valid=event_valid)
    r = event.init("carOutput").actuationReceipt
    r.receiptVersion = source.version
    for wire, neutral in (
        ("sourceCarControlMonoTime", "source_command_time"),
        ("hostApplyMonoTime", "host_apply_time"),
        ("safetyStateMonoTime", "safety_state_time"),
        ("safetyObservationMonoTime", "safety_observation_time"),
    ):
        _stamp(r, wire, getattr(source, neutral))
    _enum(
        r, "hostLateralActivityState", source.host_activity, ("unavailable", "active", "inactive")
    )
    _enum(
        r,
        "safetyPermissionState",
        source.safety_permission,
        ("unavailable", "allowed", "disallowed"),
    )
    _enum(
        r,
        "controllerKind",
        source.controller_kind,
        ("unknown", "torque", "pid", "angle", "mebCurvature", "other"),
    )
    for wire, neutral in (
        ("instantaneousControllerLimitState", "instantaneous_limit"),
        ("outputLimitState", "output_limit"),
    ):
        _enum(r, wire, getattr(source, neutral), ("unavailable", "notLimited", "limited"))
    r.controllerOutputReturned = (
        "returned" if source.controller_output_returned is True else "unavailable"
    )
    _actuators(r, "finalRequestedActuators", source.final_requested_actuators)
    _actuators(r, "controllerOutputActuators", source.controller_output_actuators)
    return event


def sample(event, *, health=None, token=None):
    reader = event.as_reader()
    topic = reader.which()
    return DecodedTopicSample(
        topic,
        reader.logMonoTime,
        reader.valid,
        healthy() if health is None else health,
        getattr(reader, topic),
        session() if token is None else token,
    )
