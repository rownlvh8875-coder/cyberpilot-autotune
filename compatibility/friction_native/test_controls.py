"""Actual Controls method bodies with synthetic IO/dependency boundaries only."""

import ast
import inspect
import math
import os
import subprocess
from numbers import Number
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
import pytest

from compatibility.friction_native import bundle
from compatibility.friction_native.test_native import lateral, load_lateral, load_pid
from tests.native_friction.test_capture import native, observer


@pytest.fixture(scope="module")
def source():
    before = bundle.originals(Path(os.environ["FRICTION_NATIVE_REFERENCE"]))
    return before, bundle.instrument(before)


@pytest.fixture(scope="module")
def schemas(tmp_path_factory, source):
    import capnp

    reference = Path(os.environ["FRICTION_NATIVE_REFERENCE"])
    result = []
    for index, values in enumerate(source):
        directory = tmp_path_factory.mktemp(f"native-schema-{index}")
        for path in ("log.capnp", "custom.capnp", "deprecated.capnp", "include/c++.capnp"):
            key = "openpilot/cereal/" + path
            raw = values.get(key)
            if raw is None:
                raw = bundle.git_bytes(reference, key)
            target = directory / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (directory / "car.capnp").write_bytes(
            bundle.git_bytes(reference, "opendbc_repo/opendbc/car/car.capnp")
        )
        parser = capnp.SchemaParser()
        result.append(
            (
                parser.load(str(directory / "log.capnp"), imports=[str(directory)]),
                parser.load(str(directory / "car.capnp"), imports=[str(directory)]),
            )
        )
    return result


def load_controls(raw, scope):
    nodes = [n for n in ast.parse(raw).body if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<exact-native-controls>", "exec"), scope)
    return scope["Controls"]


def test_controls_default_has_no_observer_and_no_new_transport(source):
    scope = {"Pose": object}
    cls = load_controls(source[1]["openpilot/selfdrive/controls/controlsd.py"], scope)
    sig = inspect.signature(cls.__init__)
    assert "friction_observer" in sig.parameters, "CONTROLS_CAPTURE_MISSING"
    assert sig.parameters["friction_observer"].default is None


def test_schema_event_evolution_preserves_reserved_identity_and_old_empty_payload(schemas):
    old, new = [pair[0] for pair in schemas]
    old_event = old.Event.new_message(logMonoTime=5, valid=True)
    old_event.init("customReserved3")
    with new.Event.from_bytes(old_event.to_bytes()) as decoded:
        assert decoded.which() == "lateralTorqueIdentification"
        assert decoded.lateralTorqueIdentification.receiptSchemaVersion == ""
        assert decoded.lateralTorqueIdentification.callbackFamily == "unknown"
        assert not decoded.lateralTorqueIdentification._has("cycle")
    new_event = new.Event.new_message(logMonoTime=6, valid=True)
    new_event.init("lateralTorqueIdentification").receiptSchemaVersion = "friction-observation-v1"
    with old.Event.from_bytes(new_event.to_bytes()) as decoded:
        assert decoded.which() == "customReserved3"
    old_field = old.Event.schema.fields["customReserved3"]
    new_field = new.Event.schema.fields["lateralTorqueIdentification"]
    assert old_field.proto.ordinal.explicit == new_field.proto.ordinal.explicit == 110
    assert old_field.schema.node.id == new_field.schema.node.id == 0xDA96579883444C35


def test_existing_native_transport_and_params_calls_not_extended(source):
    def calls(raw, name):
        return [
            ast.dump(n)
            for n in ast.walk(ast.parse(raw))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == name
        ]

    old, new = [s["openpilot/selfdrive/controls/controlsd.py"] for s in source]
    for name in ("PubMaster", "SubMaster", "get_float", "get_int", "get_bool", "send"):
        assert calls(old, name) == calls(new, name)


def test_generated_patch_applies_exactly_to_pinned_files_in_an_empty_sandbox(source, tmp_path):
    old, new = source
    for path, raw in old.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    patch = str(bundle.ASSETS / "instrumentation.patch")
    subprocess.run(["git", "-C", str(tmp_path), "apply", "--check", patch], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "apply", patch], check=True)
    assert all((tmp_path / path).read_bytes() == new[path] for path in bundle.EDIT_PATHS)


def test_bundle_build_refuses_existing_files_and_keeps_reference_read_only(tmp_path):
    reference = Path(os.environ["FRICTION_NATIVE_REFERENCE"])
    target = tmp_path / "overlay"
    old, new = bundle.build(reference, target)
    assert len(old) == 6 and len(new) == 7
    assert all((target / path).read_bytes() == new[path] for path in bundle.EDIT_PATHS)
    with pytest.raises(ValueError, match="DESTINATION_NOT_EMPTY"):
        bundle.build(reference, target)


def build_control(raw, log, car, obs, *, pose=False, lane=False):
    phase = {"now": 10}
    if obs:
        obs.now = lambda: phase["now"]
    params_calls = []
    outputs = []

    class Params:
        def get_float(self, key):
            params_calls.append(("float", key))
            return 1.0 if key == "SteerRatioRate" else 0.0

        def get_bool(self, key):
            params_calls.append(("bool", key))
            return False

        def get_int(self, key):
            params_calls.append(("int", key))
            return 0

    def event(topic):
        phase["now"] = 100 if topic == "controlsState" else 200
        value = log.Event.new_message(logMonoTime=phase["now"], valid=True)
        value.init(topic)
        return value

    class SM(dict):
        frame = 1
        seen = {}
        logMonoTime = {}
        recv_frame = {}
        valid = {}
        alive = {}

        def all_checks(self, topics):
            return True

    cs = car.CarState.new_message(
        vEgo=10.0,
        vCruise=30.0,
        vCruiseCluster=30.0,
        latEnabled=True,
        canValid=True,
        gearShifter="drive",
        vCluRatio=1.0,
    )
    model = NS(
        action=NS(desiredCurvature=0.005),
        orientation=NS(x=[]),
        meta=NS(
            laneChangeState=log.LaneChangeState.off,
            laneChangeDirection=log.LaneChangeDirection.none,
            desireState=[0.0] * 5,
        ),
    )
    sm = SM(
        carState=cs,
        carOutput=NS(actuatorsOutput=car.CarControl.Actuators.new_message()),
        liveParameters=NS(stiffnessFactor=1.0, steerRatio=15.0, angleOffsetDeg=0.0, roll=0.0),
        liveTorqueParameters=NS(useParams=False),
        modelV2=model,
        livePose=NS(),
        selfdriveState=NS(
            active=True,
            enabled=True,
            alertHudVisual="none",
            personality=NS(raw=1),
            state=log.SelfdriveState.OpenpilotState.enabled,
        ),
        longitudinalPlan=NS(speeds=[0.0], hasLead=False, xState=0),
        onroadEvents=[],
        lateralPlan=NS(useLaneLines=False, curvatures=[]),
        carrotMan=NS(vTurnSpeed=100.0, activeCarrot=0, xDistToTurn=0.0),
        radarState=NS(leadOne=NS(status=False, vRel=0.0, radar=False, dPath=0.0)),
        driverMonitoringState=NS(
            dm2Disabled=True, alertLevel=log.DriverMonitoringState.AlertLevel.none
        ),
        driverAssistance=NS(leftLaneDeparture=False, rightLaneDeparture=False),
    )
    for name in ("seen", "valid", "alive"):
        setattr(sm, name, {key: True for key in sm})
    sm.logMonoTime = {key: 5 for key in sm}
    sm.recv_frame = {key: 1 for key in sm}
    sm["liveDelay"] = NS(lateralDelay=0.12)
    for name in ("seen", "valid", "alive", "recv_frame", "logMonoTime"):
        getattr(sm, name)["liveDelay"] = (
            5 if name == "logMonoTime" else True if name in {"seen", "valid", "alive"} else 1
        )
    if lane:
        sm["lateralPlan"] = NS(useLaneLines=True, curvatures=[0.005], psis=[0.0], distances=[0.0])
    scope = dict(
        Pose=object,
        math=math,
        time=NS(),
        np=np,
        Number=Number,
        car=car,
        log=log,
        messaging=NS(new_message=event),
        MIN_LATERAL_CONTROL_SPEED=0.3,
        DT_CTRL=0.01,
        CV=NS(KPH_TO_MS=1 / 3.6, MS_TO_KPH=3.6),
        LaneChangeState=log.LaneChangeState,
        LaneChangeDirection=log.LaneChangeDirection,
        State=log.SelfdriveState.OpenpilotState,
        observe=native().observe,
        resolve_vehicle_model_steer_ratio=lambda learned, rate, custom: learned,
        capture_vm_measurement=lambda *a: None,
        capture_desired_target=lambda *a: None,
        clip_curvature=lambda speed, old, new, roll: (float(new), False),
        get_lag_adjusted_curvature=lambda *args: 0.005,
        record_lateral_observation=lambda *a, **k: None,
        record_measurement_and_target=lambda *a: None,
        get_carrot_man=lambda sm: None,
        driver_monitoring_hud_alert=lambda sm: 0,
        ACTUATOR_FIELDS=tuple(car.CarControl.Actuators.schema.fields.keys()),
        lateral_output_limited=lambda *a: False,
    )
    cls = load_controls(raw["openpilot/selfdrive/controls/controlsd.py"], scope)
    obj = object.__new__(cls)
    pid = load_pid(raw["openpilot/common/pid.py"])
    lac = load_lateral(raw["openpilot/selfdrive/controls/lib/latcontrol_torque.py"], pid, log)

    def ff(inputs, params, error, deadzone, **flags):
        return inputs.lateral_acceleration / 2.0 + 0.1

    ff.__qualname__ = "CarInterfaceBase.torque_from_lateral_accel_linear"
    ff.__module__ = "opendbc.car.interfaces"
    obj.LaC = lateral(lac, pid, obs, ff)
    obj.sm, obj.params = sm, Params()
    obj.CP = NS(
        lateralTuning=NS(which=lambda: "torque"),
        minSteerSpeed=0.0,
        brand="generic",
        steerAtStandstill=False,
        openpilotLongitudinalControl=False,
        steerControlType="torque",
        pcmCruise=False,
    )
    obj.VM = NS(
        l=2.8,
        aF=1.12,
        sR=15.0,
        update_params=lambda *a: None,
        calc_curvature=lambda *a: 0.0,
        get_steer_from_curvature=lambda *a: 0.0,
    )
    obj.LoC = NS(
        reset=lambda: None,
        update=lambda *a: (0.0, 0.0, 0.0),
        long_control_state="off",
        pid=NS(p=0.0, i=0.0, f=0.0),
    )
    obj.CI = NS(get_pid_accel_limits=lambda *a: (-1.0, 1.0))
    obj.lateral_startup = NS(update=lambda *a: True)
    obj.carrot_controls = NS(lat_suspend_control=lambda cs, active: active)
    obj.is_vw_meb = False
    obj.meb_curvature_pid = None
    obj.lateral_started = False
    obj.steer_limited_by_safety = False
    obj.desired_curvature = obj.curvature = 0.0
    obj.calibrated_pose = (
        NS(
            orientation=NS(xyz=np.array([0.1, 0.2, 0.3])),
            angular_velocity=NS(xyz=np.array([0.4, 0.5, 0.6])),
        )
        if pose
        else None
    )
    obj.physical_blinker_hold = NS(read=lambda valid: 0)
    obj.atc_turn_speed = 20
    obj.friction_observer = obs
    obj.pm = NS(send=lambda topic, msg: outputs.append((topic, msg.to_dict())))
    return obj, params_calls, outputs


@pytest.mark.parametrize("pose", [False, True])
@pytest.mark.parametrize("lane", [False, True])
@pytest.mark.parametrize("observer_enabled", [False, True])
def test_actual_controls_keeps_commands_and_sends_and_seals_only_after_publish(
    source, schemas, pose, lane, observer_enabled
):
    results = []
    for index, raw in enumerate(source):
        obs = observer() if index and observer_enabled else None
        log, car = schemas[index]
        obj, params, outputs = build_control(raw, log, car, obs, pose=pose, lane=lane)
        cc, lac_log = obj.state_control()
        if obs:
            assert obs.last_receipt is None
        obj.publish(cc, lac_log)
        results.append((params, outputs))
        if obs:
            assert obs.last_receipt is not None, "CONTROLLER_CYCLE_CAPTURE_MISSING"
            payload = obs.last_receipt.payload
            assert payload["cycle"]["control_event_mono_time_ns"] == 100
            assert payload["cycle"]["receipt_complete_mono_time_ns"] == 200
            sources = {s["role"]: s for s in payload["sources"]}
            assert sources["carControl"]["origin"] == "LOCAL_CYCLE_OBJECT"
            assert sources["carControl"]["source_time_ns"] == 10
            assert sources["modelV2"]["consumed"] is True
            assert sources["livePose"]["consumed"] is False
            if lane:
                assert payload["context"]["delay"]["source"] == "LIVE_DELAY"
                assert payload["context"]["delay"]["effective_delay_s"] == 0.12
            assert hasattr(native(), "to_event"), "NATIVE_EVENT_ENCODER_MISSING"
            event = native().to_event(obs.last_receipt, log)
            assert event.which() == "lateralTorqueIdentification"
            assert event.logMonoTime >= 200
            assert (
                event.lateralTorqueIdentification.stages.callbackOutputRaw.value.which() == "value"
            )
            assert not event.lateralTorqueIdentification.signals._has("qObserved")
    assert results[0] == results[1]
