"""Repository-only synthetic test harness, never a native runtime/Params client."""

import __future__

import ast
import copy
import functools
import hashlib
import json
from types import SimpleNamespace as NS

import numpy as np

from compatibility.friction_native import bundle
from compatibility.friction_native.test_native import bits, lateral, load_lateral, load_pid
from tests.native_friction.test_capture import native, observer


def load_callback(reference):
    """Execute only exact pinned callback/helper definitions, no native imports."""
    manifest = json.loads(
        (bundle.ROOT / "docs/evidence/carrot_friction_patch_sources.json").read_text()
    )
    files = {entry["id"]: entry for entry in manifest["files"]}
    raw = {}
    for name in ("R_helper", "R_callback"):
        entry = files[name]
        data = bundle.git_bytes(reference, entry["path"])
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("EXACT_CALLBACK_SOURCE_REQUIRED")
        raw[name] = ast.parse(data)
    scope = {"np": np, "__name__": "opendbc.car.interfaces"}
    helpers = [
        node
        for node in raw["R_helper"].body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"apply_center_deadzone", "get_friction"}
    ]
    base = next(
        node
        for node in raw["R_callback"].body
        if isinstance(node, ast.ClassDef) and node.name == "CarInterfaceBase"
    )
    method = next(
        node
        for node in base.body
        if isinstance(node, ast.FunctionDef) and node.name == "torque_from_lateral_accel_linear"
    )
    threshold = next(
        node
        for node in raw["R_callback"].body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "FRICTION_THRESHOLD" for t in node.targets)
    )
    minimal = ast.ClassDef(
        name=base.name, bases=[], keywords=[], body=[copy.deepcopy(method)], decorator_list=[]
    )
    tree = ast.fix_missing_locations(
        ast.Module(body=[*helpers, threshold, minimal], type_ignores=[])
    )
    exec(
        compile(
            tree, "<exact-R-friction-callback>", "exec", flags=__future__.annotations.compiler_flag
        ),
        scope,
    )
    return scope["CarInterfaceBase"]().torque_from_lateral_accel_linear


class SettingsFailure(RuntimeError):
    pass


class ScriptedSettings:
    """Explicit fixture values only; no Params instance, storage or IO."""

    def __init__(self, selector, fail_at):
        self.selector = selector
        self.fail_at = fail_at
        self.frame = 0
        self.reads = []

    def get_int(self, key):
        assert key == "LateralTorqueCustom"
        value = self.selector if 9 <= self.frame < 29 else 0
        self.reads.append((self.frame, "int", key, value))
        return value

    def get_float(self, key):
        if self.frame == self.fail_at:
            raise SettingsFailure("synthetic setting failure")
        cohort = (
            (1750.0, 125.0, 25.0, 12.5, 50.0, 6.25)
            if self.frame <= 10
            else (2000.0, 250.0, 50.0, 25.0, 75.0, 12.5)
        )
        keys = (
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "LateralTorqueKpV",
            "LateralTorqueKiV",
            "LateralTorqueKf",
            "LateralTorqueKd",
        )
        value = cohort[keys.index(key)]
        self.reads.append((self.frame, "float", key, value))
        return value


def run(
    source,
    callback,
    *,
    selector,
    family,
    observer_kind,
    schemas,
    inactive=(),
    freeze=False,
    fail_at=None,
):
    """31 post-construction updates with real native logs/tuning field precision."""
    log, car = schemas
    pid = load_pid(source["openpilot/common/pid.py"])
    cls = load_lateral(source["openpilot/selfdrive/controls/lib/latcontrol_torque.py"], pid, log)
    obs = None
    if observer_kind == "enabled":
        obs = observer()
    elif observer_kind == "disabled":
        obs = native().PassiveFrictionObserver()
    elif observer_kind == "failing":

        class Failing(native().PassiveFrictionObserver):
            def callback_enter(self, *args, **kwargs):
                raise RuntimeError("synthetic observer-only failure")

        obs = Failing(
            enabled=True,
            source_revision="11" * 20,
            source_schema_digest="22" * 32,
            vehicle_context_digest="33" * 32,
            session_id="44" * 32,
        )
    calls = []

    @functools.wraps(callback)
    def traced(inputs, params, error, deadzone, **flags):
        consumed = (params.latAccelFactor, params.friction, params.latAccelOffset)
        raw = callback(inputs, params, error, deadzone, **flags)
        calls.append(
            dict(
                acceleration=inputs.lateral_acceleration,
                error=error,
                deadzone=deadzone,
                installed=consumed,
                flags=tuple(sorted(flags.items())),
                raw=raw,
            )
        )
        return raw

    control = lateral(cls, pid, obs, traced)
    control.pid = pid(0.125, 0.0625, k_d=0.03125, k_f=0.5, pos_limit=1.0, neg_limit=-1.0)
    control.torque_params = car.CarParams.LateralTorqueTuning.new_message(
        latAccelFactor=2.0, friction=0.0625, latAccelOffset=0.03125
    )
    control.latAccelFactor_default = 2.0
    control.friction_default = 0.0625
    control.latAccelOffset_default = 0.03125
    control.params = ScriptedSettings(selector, fail_at)
    control.use_nnff_lite = family == "NN_LITE"
    control.lat_accel_friction_factor = 0.75
    control.lat_jerk_friction_factor = 0.5
    cs = NS(vEgo=10.0, aEgo=0.0, steeringAngleDeg=0.0, steeringRateDeg=0.0, steeringPressed=freeze)
    vm = NS(get_steer_from_curvature=lambda *a: 0.0, calc_curvature=lambda *a: 0.0)
    params = NS(roll=0.0, angleOffsetDeg=0.0)

    def installed():
        tuning = control.torque_params
        return tuning.latAccelFactor, tuning.friction, tuning.latAccelOffset

    steps = []
    for frame in range(1, 32):
        control.params.frame = frame
        # Same source ordering as controlsd: live update before LaC.update.
        live = (2.5, 0.125, 0.0625) if frame <= 20 else (3.0, 0.1875, 0.125)
        control.update_live_torque_params(live[0], live[2], live[1])
        live_accepted = installed() == live
        if obs is not None:
            obs.begin_cycle(frame)
            obs.geometry(2.8, 1.12, 1.0, 15.0, 1.0, 0.0)
        start = len(calls)
        active = frame not in inactive
        result = control.update(
            active, cs, vm, params, False, 0.0025, NS(angularVelocity=[], orientationNED=[]), False
        )
        receipt = None
        if obs is not None:
            stamp = obs.now()
            receipt = obs.complete(stamp, stamp)
        values = tuple(float(getattr(control.pid, key)) for key in ("p", "i", "d", "f", "control"))
        steps.append(
            dict(
                frame=control.frame,
                active=active,
                selector=control.lateralTorqueCustom,
                installed=installed(),
                gains=(
                    control.pid._k_p[1][0],
                    control.pid._k_i[1][0],
                    control.pid._k_d[1][0],
                    control.pid.k_f,
                ),
                live_accepted=live_accepted,
                pid_values=values,
                pid_bits=tuple(bits(v) for v in values),
                output_bits=(bits(result[0]), bits(result[1])),
                log_bytes=result[2].to_bytes(),
                calls=tuple(calls[start:]),
                receipt=receipt,
            )
        )
    return dict(steps=steps, settings_reads=tuple(control.params.reads))


def assert_parity(before, after):
    keys = (
        "frame",
        "active",
        "selector",
        "installed",
        "gains",
        "live_accepted",
        "pid_bits",
        "output_bits",
        "log_bytes",
    )
    assert len(before["steps"]) == len(after["steps"]) == 31, "CYCLE_COUNT"
    for old, new in zip(before["steps"], after["steps"], strict=True):
        assert tuple(old[k] for k in keys) == tuple(new[k] for k in keys), "CONTROL_PARITY"
    assert before["settings_reads"] == after["settings_reads"], "SETTINGS_READ_PARITY"
    assert tuple(s["calls"] for s in before["steps"]) == tuple(
        s["calls"] for s in after["steps"]
    ), "CALLBACK_PARITY"


def mutate(source, name):
    """Test-only byte-map mutants; never persisted to a native asset or Git ref."""
    result = dict(source)
    path = "openpilot/selfdrive/controls/lib/latcontrol_torque.py"
    substitutions = {
        "cadence": ("self.frame % 10 == 0", "self.frame % 9 == 0"),
        "reset": ("elif self.lateralTorqueCustom > 1:", "elif self.lateralTorqueCustom > 0:"),
        "live_bypass": ("if self.lateralTorqueCustom > 0:", "if False:"),
        "extra_read": (
            "self.frame += 1",
            "self.frame += 1\n    self.params.get_int('LateralTorqueCustom')",
        ),
        "installed_capture": (
            "self.torque_params.latAccelFactor, self.torque_params.friction,",
            "self.latAccelFactor_default, self.torque_params.friction,",
        ),
        "gain_capture": (
            "observed_ki, observed_kd, observed_kf,",
            "observed_ki, observed_kd, 0.5,",
        ),
    }
    if name == "gain_capture":
        path = "openpilot/common/pid.py"
    old, new = (s.encode() for s in substitutions[name])
    assert old in result[path], "MUTATION_SITE_MISSING"
    result[path] = result[path].replace(old, new)
    return result
