"""Production mutations caught: zero-fill, q reconstruction and mutable cohorts."""

import importlib.util
import sys
from pathlib import Path

import pytest

ASSETS = Path(__file__).resolve().parents[2] / "native_patches/friction_observation"


def native():
    path = ASSETS / "friction_observation.py"
    assert path.is_file(), "NATIVE_CAPTURE_MISSING"
    if "passive_native" in sys.modules:
        return sys.modules["passive_native"]
    spec = importlib.util.spec_from_file_location("passive_native", path)
    module = importlib.util.module_from_spec(spec)
    # Dataclasses inspect their defining module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def observer(**kw):
    return native().PassiveFrictionObserver(
        enabled=True,
        source_revision="11" * 20,
        source_schema_digest="22" * 32,
        vehicle_context_digest="33" * 32,
        session_id="44" * 32,
        **kw,
    )


def capture(obs, cycle=1, factor=2.0, friction=0.1, wheelbase=2.8):
    obs.begin_cycle(cycle)
    obs.source("carState", 1, 7, True, True)
    obs.geometry(wheelbase, 1.12, 1.0, 15.0, 1.0, 0.0)
    obs.callback_enter(
        0.5,
        0.2,
        0.0,
        0.0,
        0.5,
        0.3,
        0.06,
        factor,
        friction,
        0.0,
        0,
        "CarInterfaceBase.torque_from_lateral_accel_linear",
        False,
        False,
    )
    obs.callback_exit(0.35)
    obs.pid(1.0, None, 0.0, 0.7, 0.1, 0.0, 0.0, 0.245, 0.345, 0.345)
    obs.limits(False, False, False, False, False)
    return obs


def test_disabled_observer_does_not_capture_or_create_identity():
    obs = native().PassiveFrictionObserver()
    obs.begin_cycle(1)
    assert obs.complete(10, 11) is None
    assert obs.last_receipt is None


def test_native_sealed_receipt_retains_raw_stage_and_no_independent_q():
    obs = capture(observer())
    stamp = obs.now()
    result = obs.complete(stamp, stamp)
    assert result.payload["signals"].get("q_observed") is None
    assert result.payload["stages"]["callback_output_raw"]["value"] == 0.35
    assert result.payload["stages"]["pid_f"]["value"] == 0.245
    assert result.payload["context"]["gains"]["k_i"] is None
    with pytest.raises(TypeError):
        result.payload["context"]["installed"]["friction_installed"] = 0.2
    with pytest.raises(AttributeError):
        result.digest = "forged"
    assert obs.complete(stamp, stamp) is None


@pytest.mark.parametrize("kind", ["duplicate", "future", "clock", "nan", "origin"])
def test_invalid_native_cohort_drops_observation_not_control(kind):
    obs = capture(observer())
    if kind == "duplicate":
        obs.source("carState", 1, 8, True, True)
    elif kind == "future":
        obs.source("modelV2", 2**63, 1, True, True)
    elif kind == "clock":
        obs.source("modelV2", 1, 1, True, True, clock_domain="SENSOR")
    elif kind == "nan":
        obs.callback_exit(float("nan"))
    else:
        obs.source("modelV2", 1, 1, True, True, origin="UNKNOWN")
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is None


def test_duplicate_cycle_is_never_reused():
    obs = capture(observer())
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is not None
    obs.begin_cycle(1)
    assert obs.complete(stamp, stamp) is None
    assert obs.last_receipt is None


def test_schema_roundtrip_does_not_turn_unavailable_into_zero_or_false():
    capnp = pytest.importorskip("capnp", reason="required by native integration runner")
    module = native()
    obs = capture(observer())
    stamp = obs.now()
    result = obs.complete(stamp, stamp)
    schema = capnp.SchemaParser().load(str(ASSETS / "receipt.capnp"))
    message = schema.LateralTorqueIdentificationReceipt.new_message()
    assert hasattr(module, "encode"), "NATIVE_CODEC_MISSING"
    module.encode(result, message)
    with schema.LateralTorqueIdentificationReceipt.from_bytes(message.to_bytes()) as decoded:
        assert not decoded.signals._has("qObserved")
        assert decoded.signals.roll.value.which() == "value"
        assert decoded.signals.roll.value.value == 0.0
        assert decoded.limits.steeringPressed.which() == "value"
        assert decoded.limits.steeringPressed.value is False
        assert decoded.context.gains.kI.which() == "unavailable"
        assert decoded.stages.callbackOutputRaw.value.value == 0.35
        assert decoded.stages.pidF.value.value == 0.245


def test_receipt_callback_runs_after_sealing_and_can_fail_without_mutating_control():
    seen = []

    def sink(receipt):
        seen.append(receipt)
        raise RuntimeError("transport unavailable")

    obs = capture(observer(on_receipt=sink))
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is None
    assert len(seen) == 1
    assert seen[0].payload["signals"].get("q_observed") is None


def test_sealed_receipt_defensively_copies_and_rejects_nonfinite_or_false_digest():
    module = native()
    raw = {"nested": {"value": 1.0}}
    result = module.SealedReceipt(raw, module.content_digest(raw))
    raw["nested"]["value"] = 2.0
    assert result.payload["nested"]["value"] == 1.0
    with pytest.raises(ValueError):
        module.SealedReceipt({"value": float("nan")}, "11" * 32)
    with pytest.raises(ValueError):
        module.SealedReceipt({"value": 1.0}, "11" * 32)


@pytest.mark.parametrize("changed", [{"factor": 2.1}, {"friction": 0.11}, {"wheelbase": 2.9}])
def test_dynamic_installed_or_applied_change_never_keeps_old_generation(changed):
    obs = capture(observer())
    stamp = obs.now()
    first = obs.complete(stamp, stamp)
    capture(obs, cycle=2, **changed)
    stamp = obs.now()
    second = obs.complete(stamp, stamp)
    key = "geometry_generation" if "wheelbase" in changed else "installed_parameter_generation"
    assert first.payload["cycle"][key] == 0
    assert second.payload["cycle"][key] == 1


@pytest.mark.parametrize("source", ["MANUAL", "LIVE_DELAY"])
def test_only_actually_selected_delay_is_reported_without_alignment_correction(source):
    obs = capture(observer())
    assert hasattr(obs, "selected_delay"), "SELECTED_DELAY_TAP_MISSING"
    obs.selected_delay(0.12, source)
    stamp = obs.now()
    result = obs.complete(stamp, stamp)
    assert result.payload["context"]["delay"]["effective_delay_s"] == 0.12
    assert result.payload["context"]["delay"]["source"] == source
    assert result.payload["context"]["delay"]["correction_count"] == 0


@pytest.mark.parametrize(
    "operation",
    [
        lambda o: o.source("modelV2", 1, 1, 1, True),
        lambda o: o.source("modelV2", 1, -1, True, True),
        lambda o: o.source("modelV2", -1, 1, True, True),
        lambda o: o.source("modelV2", 1, 1, True, True, origin="LOCAL_CYCLE_OBJECT"),
        lambda o: o.selected_delay(0.12, "STATIC_CP"),
        lambda o: o.geometry(0.0, 1.0, 1.0, 15.0, 1.0, 0.0),
        lambda o: o.callback_enter(
            0.5, 0.2, 0.0, 0.0, 0.5, 0.3, 0.06, 2.0, 0.1, 0.0, 0, "OTHER", False, False
        ),
        lambda o: o.limits(1, False, False, False, False),
        lambda o: o.pid(0.1, 0.1, 0.0, 0.7, float("inf"), 0.0, 0.0, 0.245, 0.345, 0.345),
    ],
)
def test_malformed_source_context_and_stage_values_discard_only_diagnostic_cycle(operation):
    obs = capture(observer())
    operation(obs)
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is None


@pytest.mark.parametrize("value", [True, float("inf"), float("nan")])
def test_nonfinite_or_bool_callback_output_cannot_become_raw_exact(value):
    obs = observer()
    obs.begin_cycle(1)
    obs.callback_enter(0.5, 0.2, 0.0, 0.0, 0.5, 0.3, 0.06, 2.0, 0.1, 0.0, 0, "OTHER", False, False)
    obs.callback_exit(value)
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is None


def test_native_out_of_order_control_event_and_clock_reset_are_rejected():
    obs = capture(observer())
    assert obs.complete(0, 1) is None
    obs = capture(observer())
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is not None
    obs.now = lambda: 0
    obs.begin_cycle(2)
    assert obs.complete(0, 0) is None


@pytest.mark.parametrize("stage", ["callback_exit", "pid"])
def test_native_stages_cannot_appear_before_callback_enter(stage):
    obs = observer()
    obs.begin_cycle(1)
    if stage == "callback_exit":
        obs.callback_exit(0.35)
    else:
        obs.pid(0.1, 0.1, 0.0, 0.7, 0.1, 0.0, 0.0, 0.245, 0.345, 0.345)
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is None


@pytest.mark.parametrize("arguments", [{"enabled": 1}, {"on_receipt": 42}])
def test_invalid_startup_options_are_not_silent_enabling(arguments):
    with pytest.raises(ValueError):
        native().PassiveFrictionObserver(**arguments)


def test_observation_dispatch_failures_cannot_escape_or_create_evidence():
    module = native()
    from types import SimpleNamespace

    mutable = SimpleNamespace()
    assert module.observe(mutable, "missing") is None
    assert mutable.enabled is False
    assert module.observe(object(), "missing") is None
    with pytest.raises(ValueError, match="SEALED_RECEIPT_REQUIRED"):
        module.encode(object(), None)
    raw = {"cycle": {"receipt_complete_mono_time_ns": 2**63}}
    future = module.SealedReceipt(raw, module.content_digest(raw))
    with pytest.raises(ValueError, match="RECEIPT_EVENT_TIME_ORDER"):
        module.to_event(future, None)


def test_never_seen_wire_reader_cannot_supply_default_valid_or_false_as_observation():
    from types import SimpleNamespace

    obs = capture(observer())
    sm = SimpleNamespace(
        seen={"modelV2": False},
        logMonoTime={"modelV2": 0},
        recv_frame={"modelV2": 0},
        valid={"modelV2": True},
        alive={"modelV2": False},
    )
    obs.wire_source(sm, "modelV2")
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is None


def test_wrong_callback_module_cannot_masquerade_as_base_linear():
    obs = observer()
    obs.begin_cycle(1)
    obs.geometry(2.8, 1.12, 1.0, 15.0, 1.0, 0.0)

    def callback():
        return 0.0

    callback.__module__ = "opendbc.car.gm.interface"
    callback.__qualname__ = "CarInterfaceBase.torque_from_lateral_accel_linear"
    obs.callback_enter(0.5, 0.2, 0.0, 0.0, 0.5, 0.3, 0.06, 2.0, 0.1, 0.0, 0, callback, False, False)
    obs.callback_exit(0.35)
    obs.pid(0.1, None, 0.0, 0.7, 0.1, 0.0, 0.0, 0.245, 0.345, 0.345)
    stamp = obs.now()
    result = obs.complete(stamp, stamp)
    assert result.payload["callback_family"] == "OTHER"


def test_capture_taps_do_not_hash_or_serialize_until_after_original_command_boundary(monkeypatch):
    module = native()
    original = module.content_digest
    phase = {"after_command": False}

    def checked(value):
        assert phase["after_command"], "HASH_BEFORE_ORIGINAL_COMMAND"
        return original(value)

    monkeypatch.setattr(module, "content_digest", checked)
    obs = capture(observer())
    phase["after_command"] = True
    stamp = obs.now()
    assert obs.complete(stamp, stamp) is not None


def test_signed_zero_context_change_is_not_erased_by_epoch_comparison():
    obs = capture(observer(), friction=0.0)
    stamp = obs.now()
    first = obs.complete(stamp, stamp)
    capture(obs, cycle=2, friction=-0.0)
    stamp = obs.now()
    second = obs.complete(stamp, stamp)
    assert first.payload["cycle"]["installed_parameter_generation"] == 0
    assert second.payload["cycle"]["installed_parameter_generation"] == 1


@pytest.mark.parametrize(
    "revision",
    [
        "c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        "main",
    ],
)
def test_instrumented_source_cannot_claim_old_or_branch_revision(revision):
    with pytest.raises(ValueError):
        native().PassiveFrictionObserver(
            enabled=True,
            source_revision=revision,
            source_schema_digest="22" * 32,
            vehicle_context_digest="33" * 32,
            session_id="44" * 32,
        )
