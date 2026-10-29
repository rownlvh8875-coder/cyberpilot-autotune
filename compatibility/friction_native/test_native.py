"""Run actual pinned Python bodies; no simulator equations replace the controller."""

import ast
import inspect
import math
import os
import struct
from numbers import Number
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from compatibility.friction_native import bundle
from tests.native_friction.test_capture import native, observer


@pytest.fixture(scope="module")
def trees():
    assert (bundle.ASSETS / "edits.json").is_file(), "NATIVE_INSTRUMENTATION_MISSING"
    before = bundle.originals(Path(os.environ["FRICTION_NATIVE_REFERENCE"]))
    return before, bundle.instrument(before)


def load_pid(raw):
    tree = ast.parse(raw)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    scope = {"np": np, "Number": Number}
    exec(compile(ast.Module(body=classes, type_ignores=[]), "<exact-native-pid>", "exec"), scope)
    return scope["PIDController"]


def bits(value):
    return struct.pack("!d", float(value))


@pytest.mark.parametrize("override,freeze", [(False, False), (True, False), (False, True)])
@pytest.mark.parametrize("error", [0.0, -0.0, 0.1, -0.1, 1e10, float("nan")])
def test_actual_pid_parity_and_observer_errors_do_not_change_state(trees, override, freeze, error):
    old, new = [load_pid(tree["openpilot/common/pid.py"]) for tree in trees]
    assert "friction_observer" in inspect.signature(new.update).parameters, "PID_TAP_MISSING"

    class Sink:
        def pid(self, *values):
            self.values = values

    class Broken:
        def pid(self, *values):
            raise RuntimeError("observer-only")

    def controller(cls):
        return cls([[0, 20], [0.1, 0.2]], 0.1, k_f=0.7, k_d=0.1, pos_limit=1.0, neg_limit=-1.0)

    baseline = controller(old)
    for sink in (None, Sink(), Broken()):
        target = controller(new)
        baseline.reset()
        for _ in range(3):
            kw = dict(
                speed=10.0,
                feedforward=0.35,
                error_rate=0.02,
                override=override,
                freeze_integrator=freeze,
            )
            want = baseline.update(error, **kw)
            result = target.update(error, friction_observer=sink, **kw)
            assert bits(result) == bits(want)
            for attr in ("p", "i", "d", "f", "control"):
                assert bits(getattr(target, attr)) == bits(getattr(baseline, attr))
        if isinstance(sink, Sink):
            assert sink.values[1] is None if override or freeze else sink.values[1] == 0.1
            assert bits(sink.values[3]) == bits(0.7)
            assert bits(sink.values[7]) == bits(0.35 * 0.7)


def test_native_pid_observer_does_not_swallow_original_control_exception(trees):
    new = load_pid(trees[1]["openpilot/common/pid.py"])
    assert "friction_observer" in inspect.signature(new.update).parameters, "PID_TAP_MISSING"
    pid = new(1.0, 0.0)
    with pytest.raises((TypeError, ValueError)):
        pid.update(object(), friction_observer=object())


def load_lateral(raw, pid):
    tree = ast.parse(raw)
    body = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign))]
    scope = dict(
        math=math,
        np=np,
        deque=__import__("collections").deque,
        LatControl=object,
        PIDController=pid,
        ACCELERATION_DUE_TO_GRAVITY=9.81,
        CONTROL_N=17,
        ModelConstants=SimpleNamespace(T_IDXS=np.linspace(0.0, 1.6, 17)),
        LatControlInputs=lambda a, r, v, ae: SimpleNamespace(lateral_acceleration=a),
        instantaneous_limit_state=lambda *a: "clear",
        observe=native().observe,
    )

    class State:
        @staticmethod
        def new_message():
            # Actual native field error is Float32; do not replace readback by raw double.
            class Float32Log(SimpleNamespace):
                def __setattr__(self, name, value):
                    super().__setattr__(
                        name, float(np.float32(value)) if name == "error" else value
                    )

            return Float32Log()

    scope["log"] = SimpleNamespace(ControlsState=SimpleNamespace(LateralTorqueState=State))
    exec(compile(ast.Module(body=body, type_ignores=[]), "<exact-native-lateral>", "exec"), scope)
    return scope["LatControlTorque"]


def lateral(cls, pid, sink, callback):
    item = object.__new__(cls)
    item.frame = 0
    item.pid = pid(0.1, 0.1, k_f=0.7, pos_limit=1.0, neg_limit=-1.0)
    item.torque_params = SimpleNamespace(latAccelFactor=2.0, friction=0.1, latAccelOffset=0.0)
    item.lateralTorqueCustom = 0
    item.use_nnff = item.use_nnff_lite = False
    item.use_steering_angle = True
    item.steering_angle_deadzone_deg = 0.0
    item.torque_from_lateral_accel = callback
    item.steer_max = 1.0
    item._check_saturation = lambda *args: False
    item.friction_observer = sink
    return item


@pytest.mark.parametrize("mode", ["LINEAR", "NN_LITE", "NN", "GM_SIGLIN", "OTHER"])
@pytest.mark.parametrize("active", [False, True])
def test_native_ff_site_preserves_all_invocations_and_raw_not_pid_f(trees, mode, active):
    outputs = []
    all_calls = []
    for index, source in enumerate(trees):
        pid = load_pid(source["openpilot/common/pid.py"])
        cls = load_lateral(source["openpilot/selfdrive/controls/lib/latcontrol_torque.py"], pid)
        calls = []

        def callback(inputs, params, error, deadzone, _calls=calls, **flags):
            _calls.append((inputs.lateral_acceleration, error, deadzone, flags))
            return inputs.lateral_acceleration / 2.0 + 0.1

        callback.__qualname__ = {
            "LINEAR": "CarInterfaceBase.torque_from_lateral_accel_linear",
            "NN_LITE": "CarInterfaceBase.torque_from_lateral_accel_linear",
            "GM_SIGLIN": "CarInterface.torque_from_lateral_accel_siglin",
        }.get(mode, "Other.unsupported")
        callback.__module__ = (
            "opendbc.car.gm.interface" if mode == "GM_SIGLIN" else "opendbc.car.interfaces"
        )
        obs = observer() if index else None
        if obs:
            obs.begin_cycle(1)
            obs.geometry(2.8, 1.12, 1.0, 15.0, 1.0, 0.0)
        control = lateral(cls, pid, obs, callback)
        control.use_nnff_lite = mode == "NN_LITE"
        control.use_nnff = mode == "NN"
        control.nn_friction_override = False
        control.past_future_len = 0
        control.history_frame_offsets = control.nn_future_times = []
        control.roll_deque = __import__("collections").deque()
        control.lateral_accel_desired_deque = __import__("collections").deque()
        control.pitch = SimpleNamespace(update=lambda v: v)
        control.torque_from_nn = lambda values: 0.123456789
        control.lat_accel_friction_factor = 0.7
        control.lat_jerk_friction_factor = 0.4
        cs = SimpleNamespace(
            vEgo=10.0, aEgo=0.0, steeringAngleDeg=0.0, steeringRateDeg=0.0, steeringPressed=False
        )
        vm = SimpleNamespace(get_steer_from_curvature=lambda *a: 0.0, calc_curvature=lambda *a: 0.0)
        params = SimpleNamespace(roll=0.0, angleOffsetDeg=0.0)
        model = SimpleNamespace(orientation=SimpleNamespace(x=[0.0] * 17)) if mode == "NN" else None
        if mode == "NN":
            # Keep model_good while avoiding jerk preparation, using actual source branch code.
            control.friction_look_ahead_bp = [0, 20]
            control.friction_look_ahead_v = [0.0, 0.0]
            control.t_diffs = np.ones(16)
            control.desired_lat_jerk_time = 0.3
            model.acceleration = SimpleNamespace(y=[0.0] * 17)
            model.orientation.y = [0.0] * 17
        kwargs = dict(model_data=model)
        result = control.update(
            active,
            cs,
            vm,
            params,
            False,
            0.005,
            SimpleNamespace(angularVelocity=[], orientationNED=[]),
            False,
            **kwargs,
        )
        outputs.append((bits(result[0]), bits(control.pid.i)))
        all_calls.append(calls)
        if obs and active:
            stamp = obs.now()
            receipt = obs.complete(stamp, stamp)
            assert receipt is not None, "FEEDFORWARD_CAPTURE_MISSING"
            value = receipt.payload["stages"]["callback_output_raw"]["value"]
            assert value == (0.123456789 if mode == "NN" else 0.35)
            assert receipt.payload["callback_family"] == mode
            assert receipt.payload["signals"].get("q_observed") is None
    assert outputs[0] == outputs[1]
    assert all_calls[0] == all_calls[1]
