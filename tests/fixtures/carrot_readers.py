"""Duck-reader doubles for unit failures only; never schema compatibility proof."""

from types import SimpleNamespace

from cyberpilot_autotune.integrations.carrot.availability import SchemaBinding
from cyberpilot_autotune.integrations.carrot.extraction import DecodedTopicSample
from cyberpilot_autotune.integrations.carrot.health import SessionToken, TopicHealthEvidence
from tests.fixtures.carrot_v2 import complete


class Reader:
    def __init__(self, schema_id=0, **fields):
        self.schema = SimpleNamespace(node=SimpleNamespace(id=schema_id))
        self.__dict__.update(fields)

    def _has(self, name):
        return getattr(self, name, None) is not None

    def which(self):
        return self.tag


def union(value, domain=None):
    return Reader(
        tag="unavailable" if value is None else "value",
        value=value,
        clockDomain="unavailable" if domain is None else domain,
    )


def healthy():
    return TopicHealthEvidence(True, True, True, True, True)


def session(generation=0):
    return SessionToken(generation, f"{generation:032x}")


def binding():
    return SchemaBinding(Reader, 1, 2, 3, "2.1.0", "unit-double-not-compatibility")


def samples(kind="torque"):
    attempt, _ = complete(kind)
    source = attempt.source_command
    m = source.measurement
    measurement = Reader(
        version=m.version,
        measurementMode=m.mode,
        validityState=m.validity,
        carStateHealthState=m.car_state_health,
        liveParametersHealthState=m.live_parameters_health,
        carStateMonoTime=union(m.car_state_time.value_ns, m.car_state_time.domain),
        liveParametersMonoTime=union(
            m.live_parameters_time.value_ns, m.live_parameters_time.domain
        ),
        calculationMonoTime=union(m.calculation_time.value_ns, m.calculation_time.domain),
        **{
            wire: union(getattr(m, neutral))
            for wire, neutral in (
                ("measuredCurvatureInvM", "measured_curvature_inv_m"),
                ("inputSpeedMps", "input_speed_mps"),
                ("inputSteeringAngleDeg", "input_steering_angle_deg"),
                ("effectiveStiffnessFactor", "effective_stiffness_factor"),
                ("effectiveSteerRatio", "effective_steer_ratio"),
                ("effectiveAngleOffsetDeg", "effective_angle_offset_deg"),
                ("effectiveRollRad", "effective_roll_rad"),
            )
        },
    )
    command = Reader(
        1,
        latActive=True,
        actuators=Reader(**source.requested_actuators),
        lateralControlObservation=Reader(
            version=2,
            controllerKind=kind,
            instantaneousLimitState="notLimited",
            measurement=measurement,
            desiredTargetState="available",
            desiredTargetCurvatureInvM=union(0.0),
        ),
    )
    cs = Reader(2, canValid=True, steeringPressed=False, vEgo=2.0, steeringAngleDeg=0.0)
    r = attempt.receipt
    receipt = Reader(
        receiptVersion=1,
        sourceCarControlMonoTime=union(r.source_command_time.value_ns, "monotonic"),
        hostApplyMonoTime=union(r.host_apply_time.value_ns, "monotonic"),
        hostLateralActivityState="active",
        safetyPermissionState="allowed",
        safetyStateMonoTime=union(r.safety_state_time.value_ns, "bootTime"),
        safetyObservationMonoTime=union(r.safety_observation_time.value_ns, "bootTime"),
        controllerKind=kind,
        instantaneousControllerLimitState="notLimited",
        outputLimitState="notLimited",
        controllerOutputReturned="returned",
        finalRequestedActuators=Reader(**r.final_requested_actuators),
        controllerOutputActuators=Reader(**r.controller_output_actuators),
    )
    return tuple(
        DecodedTopicSample(topic, stamp, True, healthy(), reader, session())
        for topic, stamp, reader in (
            ("carControl", source.event_time.value_ns, command),
            ("carState", m.car_state_time.value_ns, cs),
            ("carOutput", 10_005_000_000, Reader(3, actuationReceipt=receipt)),
        )
    )
