"""Passive bounded native capture. No IO, controller imports or estimator bridge.

Not activated by normal controlsd startup. Publication/target execution remain
unqualified; complete() only seals an in-memory receipt. q is never reconstructed.
"""

import hashlib
import json
import math
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from functools import wraps
from types import MappingProxyType

VERSION = "friction-observation-v1"
OLD_REVISIONS = {
    "c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
    "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
}
ROLES = (
    "carState",
    "livePose",
    "liveParameters",
    "carControl",
    "modelV2",
    "controlState",
    "liveDelay",
)


def content_digest(value):
    def plain(item):
        if isinstance(item, Mapping):
            return {key: plain(value) for key, value in item.items()}
        if isinstance(item, (tuple, list)):
            return [plain(value) for value in item]
        return item

    return hashlib.sha256(
        json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


def number(value):
    if value is None:
        return None
    if isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("NONFINITE_OR_BOOL")
    return float(value)


def uint(value):
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError("UINT64")
    return value


def sha(value, length=64):
    if type(value) is not str or re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is None:
        raise ValueError("EXACT_CONTENT_ID")
    return value


def guarded(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        if not self.enabled or self._bad or self._data is None:
            return None
        try:
            return method(self, *args, **kwargs)
        except Exception:
            self._bad = True
            return None

    return call


@dataclass(frozen=True)
class SealedReceipt:
    payload: object
    digest: str

    def __post_init__(self):
        if self.digest != content_digest(self.payload):
            raise ValueError("CONTENT_DIGEST_MISMATCH")
        object.__setattr__(self, "payload", freeze(self.payload))


class PassiveFrictionObserver:
    """One cycle in flight and one immutable result; all startup identities explicit.

    Constructor IDs identify source/content only, never register an approved source
    profile or grant runtime/application authority. Tests use synthetic IDs. A real
    patched native SHA must be registered/qualified separately before runtime use.
    """

    def __init__(
        self,
        enabled=False,
        *,
        source_revision=None,
        source_schema_digest=None,
        vehicle_context_digest=None,
        session_id=None,
        on_receipt=None,
    ):
        if type(enabled) is not bool:
            raise ValueError("ENABLED_BOOL")
        self.enabled = enabled
        self._data = None
        self._bad = False
        self._last_cycle = -1
        self._last_command = 0
        self._epochs = {}
        self.last_receipt = None
        if on_receipt is not None and not callable(on_receipt):
            raise ValueError("RECEIPT_CALLBACK")
        self._on_receipt = on_receipt
        if enabled:
            sha(source_revision, 40)
            if source_revision in OLD_REVISIONS:
                raise ValueError("INSTRUMENTED_SOURCE_CANNOT_REUSE_OLD_PIN")
            self._origin = (
                source_revision,
                sha(source_schema_digest),
                sha(vehicle_context_digest),
                sha(session_id),
            )

    @staticmethod
    def now():
        # Same monotonic clock and conversion used by pinned messaging.new_message.
        return int(time.monotonic() * 1e9)

    def begin_cycle(self, cycle):
        self._data = None
        self._bad = False
        self.last_receipt = None
        if not self.enabled:
            return
        try:
            uint(cycle)
            if cycle <= self._last_cycle:
                raise ValueError("DUPLICATE_CYCLE")
            self._last_cycle = cycle
            start = self.now()
            if start < self._last_command:
                raise ValueError("TIME_ORDER")
            self._data = {
                "cycle_id": cycle,
                "start": start,
                "sources": {},
                "signals": {},
                "stages": {},
                "context": {},
                "limits": {},
            }
        except Exception:
            self._bad = True

    def _generation(self, name, values):
        # Fixed-size scalar comparison only. Preserve signed zero without JSON,
        # binary packing or content hashing in the pre-command capture path.
        key = tuple(
            (value, math.copysign(1.0, value))
            if type(value) is float and value == 0.0
            else (value, None)
            for value in values
        )
        previous, generation = self._epochs.get(name, (None, -1))
        if key != previous:
            generation += 1
        self._epochs[name] = (key, generation)
        return generation

    @guarded
    def source(
        self,
        role,
        source_time,
        sequence,
        valid,
        alive,
        *,
        consumed=True,
        origin="WIRE_EVENT",
        clock_domain="MONOTONIC",
    ):
        if role not in ROLES or role in self._data["sources"]:
            raise ValueError("SOURCE_ROLE_OR_DUPLICATE")
        if clock_domain != "MONOTONIC" or origin not in {"WIRE_EVENT", "LOCAL_CYCLE_OBJECT"}:
            raise ValueError("SOURCE_DOMAIN_OR_ORIGIN")
        if any(value is not None and type(value) is not bool for value in (valid, alive, consumed)):
            raise ValueError("SOURCE_BOOL")
        now = self.now()
        if source_time is not None:
            uint(source_time)
            if source_time > now or (
                origin == "LOCAL_CYCLE_OBJECT" and source_time < self._data["start"]
            ):
                raise ValueError("SOURCE_TIME")
        if sequence is not None:
            uint(sequence)
        self._data["sources"][role] = dict(
            role=role,
            source_time_ns=source_time,
            sequence=sequence,
            source_identity=None,
            consumed=consumed,
            valid=valid,
            alive=alive,
            origin=origin,
            clock_domain=clock_domain,
        )

    @guarded
    def wire_source(self, sm, topic, role=None, consumed=True):
        seen = bool(sm.seen[topic])
        if not seen:
            raise ValueError("CONSUMED_SOURCE_NEVER_SEEN")
        self.source(
            role or topic,
            int(sm.logMonoTime[topic]) if seen else None,
            int(sm.recv_frame[topic]) if seen else None,
            bool(sm.valid[topic]),
            bool(sm.alive[topic]),
            consumed=consumed,
        )

    @guarded
    def local_source(self, role):
        sequence = self._data.get("local_sequence", 0)
        self._data["local_sequence"] = sequence + 1
        self.source(role, self.now(), sequence, True, True, origin="LOCAL_CYCLE_OBJECT")

    @guarded
    def unused(self, role):
        self.source(role, None, None, None, None, consumed=False)

    @guarded
    def applied_geometry(self, vm, stiffness, raw_rate, raw_custom):
        self.geometry(vm.l, vm.aF, stiffness, vm.sR, raw_rate, raw_custom)

    @guarded
    def selected_delay(self, value, source):
        if source not in {"MANUAL", "LIVE_DELAY"}:
            raise ValueError("SELECTED_DELAY_SOURCE")
        self._data["context"]["delay"] = dict(
            effective_delay_s=number(value),
            source=source,
            alignment_method="RAW_CALLBACK_NO_ALIGNMENT",
            alignment_version="raw-v1",
            correction_count=0,
            values_already_aligned=False,
        )

    @guarded
    def geometry(self, wheelbase, center_to_front, stiffness, steer_ratio, raw_rate, raw_custom):
        values = tuple(
            number(v)
            for v in (wheelbase, center_to_front, stiffness, steer_ratio, raw_rate, raw_custom)
        )
        if wheelbase <= 0:
            raise ValueError("GEOMETRY")
        generation = self._generation("geometry", values)
        self._data["geometry_values"] = values
        self._data["context"]["geometry"] = dict(
            source_revision=self._origin[0],
            vehicle_context_digest=self._origin[2],
            generation=generation,
            applied_vm_context_id=None,
            origin="ACTUALLY_APPLIED_VM",
            wheelbase=values[0],
            center_to_front=values[1],
            center_to_front_ratio=None,
            stiffness_factor=values[2],
            effective_steer_ratio=values[3],
            steer_ratio_rate_raw=values[4],
            custom_sr_raw=values[5],
            precision="CONTROLLER_LOCAL_BINARY64",
        )
        # Effective modifier witnesses are not reconstructed from requested values.
        self._data["context_time"] = self.now()

    @guarded
    def callback_enter(
        self,
        desired,
        actual,
        roll,
        roll_compensation,
        acceleration,
        friction_input,
        deadzone,
        factor,
        friction,
        offset,
        selector,
        function,
        nn_lite,
        full_nn,
        invocation_index=2,
    ):
        if "callback_enter" in self._data:
            raise ValueError("MULTIPLE_FEEDFORWARD_CALLBACKS")
        values = tuple(number(v) for v in (factor, friction, offset))
        if not isinstance(function, str):
            name = getattr(function, "__qualname__", "OTHER")
            module = getattr(function, "__module__", "")
            approved = {
                ("opendbc.car.interfaces", "CarInterfaceBase.torque_from_lateral_accel_linear"),
                ("opendbc.car.gm.interface", "CarInterface.torque_from_lateral_accel_siglin"),
                ("opendbc.car.gm.interface", "CarInterface.torque_from_lateral_accel_neural"),
            }
            function = name if (module, name) in approved else "OTHER"
        generation = self._generation("installed", values + (uint(selector),))
        family = "OTHER"
        if full_nn:
            family = "NN"
            function = "get_ff_nn"
        elif function == "CarInterfaceBase.torque_from_lateral_accel_linear":
            family = "NN_LITE" if nn_lite else "LINEAR"
        elif function == "CarInterface.torque_from_lateral_accel_siglin":
            family = "GM_SIGLIN"
        elif function == "CarInterface.torque_from_lateral_accel_neural":
            family = "GM_NEURAL"
        else:
            function = "OTHER"
        self._data.update(
            family=family,
            function=function,
            selector=selector,
            invocation_index=uint(invocation_index),
        )
        self._data["context"]["installed"] = dict(
            generation=generation,
            factor_installed=values[0],
            friction_installed=values[1],
            offset_installed=values[2],
            offset_source="INSTALLED_BUT_UNUSED_LINEAR" if family == "LINEAR" else "UNAVAILABLE",
            source_field="torque_params.latAccelOffset",
            precision="CONTROLLER_LOCAL_BINARY64",
            custom_selector=selector,
        )
        self._data["context_time"] = self.now()
        self._data["callback_enter"] = self.now()
        for name, value in zip(
            (
                "desired_lateral_accel",
                "actual_lateral_accel",
                "roll",
                "roll_compensation",
                "callback_acceleration",
                "friction_input",
                "friction_deadzone",
            ),
            (desired, actual, roll, roll_compensation, acceleration, friction_input, deadzone),
            strict=True,
        ):
            self._scalar("signals", name, value, "CALLBACK_INPUT")
        if family == "LINEAR":
            self._scalar("signals", "friction_threshold", 0.3, "CALLBACK_INPUT")
            self._data["signals"].update(friction_compensation_enabled=True, gravity_adjusted=True)

    def _scalar(self, section, signal, value, stage):
        if value is not None:
            self._data[section][signal] = dict(
                signal=signal,
                stage=stage,
                value=number(value),
                precision="CONTROLLER_LOCAL_BINARY64",
                origin="LOCAL_DIRECT",
                captured_mono_time_ns=self.now(),
            )

    @guarded
    def callback_exit(self, value):
        if "callback_enter" not in self._data or "callback_exit" in self._data:
            raise ValueError("CALLBACK_BOUNDARY")
        self._scalar("stages", "callback_output_raw", value, "RAW_CALLBACK_PRE_PID_KF")
        self._data["callback_exit"] = self.now()

    @guarded
    def pid(self, kp, ki, kd, kf, p, i, d, f, preclip, postclip):
        if "callback_exit" not in self._data:
            raise ValueError("PID_BOUNDARY")
        gains = tuple(number(v) for v in (kp, ki, kd, kf))
        self._data["context"]["gains"] = dict(
            k_p=gains[0],
            k_i=gains[1],
            k_d=gains[2],
            k_f=gains[3],
            generation=self._generation("gain", gains) if None not in gains else None,
            captured_mono_time_ns=self.now(),
            precision="CONTROLLER_LOCAL_BINARY64",
        )
        for name, value, stage in zip(
            ("pid_p", "pid_i", "pid_d", "pid_f", "pid_sum", "post_pid_output"),
            (p, i, d, f, preclip, postclip),
            (
                "PID_P",
                "PID_I",
                "PID_D",
                "PID_SCALED_F",
                "PID_PRE_CLIP_SUM",
                "PID_POST_CLIP_INTERNAL_SIGN",
            ),
            strict=True,
        ):
            self._scalar("stages", name, value, stage)
        self._data["pid_time"] = self.now()

    @guarded
    def limits(self, steering_pressed, timer_saturation, instantaneous, curvature, controls):
        values = (steering_pressed, timer_saturation, instantaneous, curvature, controls)
        if any(value is not None and type(value) is not bool for value in values):
            raise ValueError("LIMIT_BOOL")
        self._data["limits"] = dict(
            zip(
                (
                    "steering_pressed",
                    "timer_saturated",
                    "instantaneous_controller_limited",
                    "curvature_limited",
                    "steer_limited_by_controls",
                ),
                values,
                strict=True,
            )
        )

    @guarded
    def complete(self, control_time, command_time):
        data = self._data
        end = self.now()
        uint(control_time)
        uint(command_time)
        if not (
            data["start"]
            <= data["context_time"]
            <= data["callback_enter"]
            <= data["callback_exit"]
            <= data["pid_time"]
            <= control_time
            <= command_time
            <= end
        ):
            raise ValueError("FINAL_TIME_ORDER")
        cycle = dict(
            session_id=self._origin[3],
            controller_cycle_id=data["cycle_id"],
            controller_cycle_start_mono_time_ns=data["start"],
            context_capture_mono_time_ns=data["context_time"],
            callback_enter_mono_time_ns=data["callback_enter"],
            callback_exit_mono_time_ns=data["callback_exit"],
            control_event_mono_time_ns=control_time,
            receipt_complete_mono_time_ns=end,
            source_revision=self._origin[0],
            source_schema_digest=self._origin[1],
            vehicle_context_digest=self._origin[2],
            controller_instance_generation=0,
            installed_parameter_generation=data["context"]["installed"]["generation"],
            geometry_generation=data["context"]["geometry"]["generation"],
            callback_invocation_index=data["invocation_index"],
            clock_domain="MONOTONIC",
        )
        cycle_id = content_digest(cycle)
        geometry_values = data["geometry_values"]
        data["context"]["geometry"]["applied_vm_context_id"] = content_digest(geometry_values)
        data["context"]["geometry"]["center_to_front_ratio"] = (
            geometry_values[1] / geometry_values[0]
        )
        sources = list(data["sources"].values())
        for source in sources:
            source["controller_cycle_digest"] = cycle_id
            if source["source_time_ns"] is not None and source["sequence"] is not None:
                source["source_identity"] = content_digest(
                    {
                        "session": self._origin[3],
                        "role": source["role"],
                        "time": source["source_time_ns"],
                        "sequence": source["sequence"],
                        "origin": source["origin"],
                        "local_cycle": data["cycle_id"]
                        if source["origin"] == "LOCAL_CYCLE_OBJECT"
                        else None,
                    }
                )
        for section in ("signals", "stages"):
            for value in data[section].values():
                if isinstance(value, dict):
                    value["cycle_digest"] = cycle_id
        data["context"].update(cycle_digest=cycle_id, snapshot_time_ns=data["context_time"])
        data["context"]["gains"]["cycle_digest"] = cycle_id
        data["context"].setdefault(
            "delay",
            dict(
                source="UNAVAILABLE",
                alignment_method="RAW_CALLBACK_NO_ALIGNMENT",
                alignment_version="raw-v1",
                correction_count=0,
                values_already_aligned=False,
            ),
        )
        family = data["family"]
        stage = (
            family + "_CALLBACK_PRE_PID"
            if family in {"LINEAR", "NN_LITE", "NN", "GM_SIGLIN"}
            else "OTHER_UNSUPPORTED"
        )
        payload = dict(
            cycle=cycle,
            callback_stage=stage,
            controller_mode="CUSTOM" if data["selector"] > 0 else "STANDARD",
            callback_family=family,
            callback_function=data["function"],
            callback_site="FEEDFORWARD",
            sources=sources,
            signals=data["signals"],
            stages=data["stages"],
            context=data["context"],
            limits=data["limits"],
            receipt_schema_version=VERSION,
            consumption_manifest_complete=False,
        )
        sealed = SealedReceipt(freeze(payload), content_digest(payload))
        self._last_command = command_time
        self.last_receipt = sealed
        self._data = None
        if self._on_receipt is not None:
            self._on_receipt(sealed)
        return sealed


def observe(observer, method, *args, **kwargs):
    """Catch only observation failures, never any original control computation."""
    if observer is not None:
        try:
            return getattr(observer, method)(*args, **kwargs)
        except Exception:
            try:
                observer.enabled = False
            except Exception:
                pass
    return None


def enum_token(value):
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    first = parts[0].lower() if parts[0].isupper() else parts[0][0].lower() + parts[0][1:]
    return first + "".join(word.title() for word in parts[1:])


def encode(receipt, target):
    """Serialize a sealed native payload only; no native/H7 decoder or authority.

    Caller supplies a compiled schema builder. No import of cereal/openpilot and
    no socket is needed. A callback may invoke this only after original sends.
    """
    if type(receipt) is not SealedReceipt:
        raise ValueError("SEALED_RECEIPT_REQUIRED")

    def fill(values, builder):
        for name, value in values.items():
            if value is None:
                continue
            field_name = name.split("_")[0] + "".join(p.title() for p in name.split("_")[1:])
            field = builder.schema.fields[field_name]
            kind = field.proto.slot.type.which()
            if kind == "struct" and "unavailable" in field.schema.fields:
                wrapper = builder.init(field_name)
                payload_type = field.schema.fields["value"].proto.slot.type.which()
                wrapper.value = bytes.fromhex(value) if payload_type == "data" else value
            elif isinstance(value, Mapping):
                fill(value, builder.init(field_name))
            elif isinstance(value, tuple):
                items = builder.init(field_name, len(value))
                for i, item in enumerate(value):
                    fill(item, items[i])
            elif kind == "enum":
                setattr(builder, field_name, enum_token(value))
            else:
                setattr(builder, field_name, value)

    fill(receipt.payload, target)
    return target


def to_event(receipt, log_schema):
    """Encode a post-seal Event; caller owns transport, which is unqualified."""
    stamp = PassiveFrictionObserver.now()
    if stamp < receipt.payload["cycle"]["receipt_complete_mono_time_ns"]:
        raise ValueError("RECEIPT_EVENT_TIME_ORDER")
    event = log_schema.Event.new_message(logMonoTime=stamp, valid=True)
    encode(receipt, event.init("lateralTorqueIdentification"))
    return event
