"""One explicit optional dependency entry point; no arbitrary import path."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

from .errors import CarrotDependencyUnavailable, CarrotSchemaIncompatible

ORIGINAL_BASE = "604bc0a22733e648ec05b268da1ffaae7db52a69"
SOURCE_REVISION = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
INTEGRATION_MERGE = "7a2f051b1f3847786318900444c88c2ba7a74a67"
SCHEMA_REVISION = "observation-v2-measurement-v1"
SCHEMA_LAYOUT_SHA256 = "ca3e63676b4deb03efbd7998c667a4fbcc74a4a1c47c9755869c62a76e7cf0a0"

# Fixed schema symbols/fields, never caller-provided module paths.
_FIELDS = (
    ("CarControl", ("latActive", "actuators", "lateralControlObservation")),
    ("CarState", ("canValid", "steeringPressed", "vEgo", "steeringAngleDeg")),
    ("CarOutput", ("actuationReceipt",)),
    (
        "Actuators",
        (
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
        ),
    ),
    (
        "LateralControlObservation",
        (
            "version",
            "controllerKind",
            "instantaneousLimitState",
            "measurement",
            "desiredTargetState",
            "desiredTargetCurvatureInvM",
        ),
    ),
    (
        "LateralMeasurementObservation",
        (
            "version",
            "measurementMode",
            "validityState",
            "measuredCurvatureInvM",
            "carStateMonoTime",
            "liveParametersMonoTime",
            "inputSpeedMps",
            "inputSteeringAngleDeg",
            "effectiveStiffnessFactor",
            "effectiveSteerRatio",
            "effectiveAngleOffsetDeg",
            "effectiveRollRad",
            "carStateHealthState",
            "liveParametersHealthState",
            "calculationMonoTime",
        ),
    ),
    ("ObservationFloat64", ("unavailable", "value")),
    ("ObservationMonoTime", ("unavailable", "value", "clockDomain")),
    (
        "ActuationReceipt",
        (
            "receiptVersion",
            "sourceCarControlMonoTime",
            "hostLateralActivityState",
            "safetyPermissionState",
            "safetyStateMonoTime",
            "controllerKind",
            "instantaneousControllerLimitState",
            "finalRequestedActuators",
            "controllerOutputActuators",
            "outputLimitState",
            "hostApplyMonoTime",
            "controllerOutputReturned",
            "safetyObservationMonoTime",
        ),
    ),
    ("Event", ("logMonoTime", "valid", "carControl", "carState", "carOutput")),
)


@dataclass(frozen=True, slots=True)
class SchemaBinding:
    reader_type: type[object]
    car_control_id: int
    car_state_id: int
    car_output_id: int
    reader_version: str
    layout_sha256: str


def schema_layout(car: Any, log: Any) -> dict[str, object]:
    """Describe only fields actually extracted, including ordinals/types/unions/enums."""
    result: dict[str, object] = {}
    for name, fields in _FIELDS:
        module = (
            car.CarControl.Actuators
            if name == "Actuators"
            else (log.Event if name == "Event" else getattr(car, name))
        )
        schema = module.schema
        record: dict[str, object] = {}
        for field_name in fields:
            field = schema.fields[field_name]
            kind = field.proto.slot.type.which()
            item = {
                "ordinal": int(field.proto.ordinal.explicit),
                "type": str(kind),
                "discriminant": int(field.proto.discriminantValue),
            }
            if kind in ("enum", "struct"):
                item["type_id"] = int(field.schema.node.id)
            if kind == "enum":
                item["enumerants"] = dict(field.schema.enumerants)
            record[field_name] = item
        result[name] = {
            "node_id": int(schema.node.id),
            "union_fields": list(schema.union_fields),
            "fields": record,
        }
    return result


def require_schema() -> SchemaBinding:
    """Load only the fixed optional schema modules, without messaging or vehicle services."""
    try:
        import capnp
        from openpilot.cereal import car, log
    except ImportError as exc:
        raise CarrotDependencyUnavailable() from exc
    except Exception as exc:
        raise CarrotSchemaIncompatible() from exc
    try:
        layout = schema_layout(car, log)
        digest = hashlib.sha256(
            json.dumps(layout, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if capnp.__version__ != "2.1.0" or digest != SCHEMA_LAYOUT_SHA256:
            raise CarrotSchemaIncompatible()
        return SchemaBinding(
            cast(type[object], type(car.CarControl.new_message().as_reader())),
            int(car.CarControl.schema.node.id),
            int(car.CarState.schema.node.id),
            int(car.CarOutput.schema.node.id),
            str(capnp.__version__),
            digest,
        )
    except CarrotSchemaIncompatible:
        raise
    except Exception as exc:
        raise CarrotSchemaIncompatible() from exc
