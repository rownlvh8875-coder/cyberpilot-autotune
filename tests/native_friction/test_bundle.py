"""Missing/unsafe native artifacts must fail before integration is attempted."""

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "native_patches/friction_observation"


def bundle():
    assert (ROOT / "compatibility/friction_native/bundle.py").is_file(), "NATIVE_BUNDLE_MISSING"
    return importlib.import_module("compatibility.friction_native.bundle")


def test_payload_compiles_with_134_fields_and_unknown_not_linear():
    assert (ASSETS / "receipt.capnp").is_file(), "NATIVE_SCHEMA_MISSING"
    capnp = pytest.importorskip("capnp", reason="required separately by native integration runner")

    parser = capnp.SchemaParser()
    schema = parser.load(str(ASSETS / "receipt.capnp"))
    msg = schema.LateralTorqueIdentificationReceipt.new_message()
    assert msg.cycle.clockDomain == "unknown"
    assert msg.callbackFamily == "unknown"
    assert msg.signals.frictionCompensationEnabled.which() == "unavailable"
    assert msg.stages.callbackOutputRaw.value.which() == "unavailable"
    msg.callbackFamily = "linear"
    assert msg.callbackFamily == "linear"
    msg.signals.desiredLateralAccel.precision = "controllerLocalBinary64"
    assert msg.signals.desiredLateralAccel.precision == "controllerLocalBinary64"
    fields = json.loads((ROOT / "docs/evidence/carrot_friction_patch_wire.json").read_text())[
        "fields"
    ]
    for field in fields:
        if not field["local_only"]:
            record = field["semantic_field"].split(".")[0]
            actual = getattr(schema, record).schema.fields[field["native_name"]]
            assert actual.proto.ordinal.explicit == field["ordinal"]


def test_exact_schema_slot_cannot_be_reused_if_reference_changes():
    audit = bundle()
    with pytest.raises(ValueError, match="SOURCE_PIN"):
        audit.instrument({"openpilot/cereal/custom.capnp": b"different"})


def test_bundle_targets_only_selected_native_surface():
    audit = bundle()
    assert set(audit.EDIT_PATHS) == {
        "openpilot/cereal/custom.capnp",
        "openpilot/cereal/log.capnp",
        "openpilot/cereal/services.py",
        "openpilot/common/pid.py",
        "openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        "openpilot/selfdrive/controls/controlsd.py",
        "openpilot/selfdrive/controls/lib/friction_observation.py",
    }
