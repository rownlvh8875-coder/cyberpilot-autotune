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


def capture(obs):
    obs.begin_cycle(1)
    obs.source("carState", 1, 7, True, True)
    obs.geometry(2.8, 1.12, 1.0, 15.0, 1.0, 0.0)
    obs.callback_enter(
        0.5,
        0.2,
        0.0,
        0.0,
        0.5,
        0.3,
        0.06,
        2.0,
        0.1,
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
