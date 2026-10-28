"""Pure reader-copy tests; actual generated schema tests live in compatibility/."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.availability import require_schema
from cyberpilot_autotune.integrations.carrot.errors import (
    CarrotDependencyUnavailable,
    CarrotInputError,
    CarrotSchemaIncompatible,
)
from cyberpilot_autotune.integrations.carrot.extraction import (
    extract_car_control,
    extract_car_output,
    extract_car_state,
)
from tests.fixtures.carrot_readers import binding, samples, union


def test_missing_optional_dependency_has_typed_error(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "capnp", None)
    with pytest.raises(CarrotDependencyUnavailable, match="CARROT_DEPENDENCY_UNAVAILABLE"):
        require_schema()


def test_schema_import_failure_is_typed_without_raw_backend_text(monkeypatch):
    import builtins
    import sys
    from types import SimpleNamespace

    original = builtins.__import__

    def failed(name, *args, **kwargs):
        if name == "openpilot.cereal":
            raise RuntimeError("sensitive backend input")
        return original(name, *args, **kwargs)

    monkeypatch.setitem(sys.modules, "capnp", SimpleNamespace(__version__="2.1.0"))
    monkeypatch.setattr(builtins, "__import__", failed)
    with pytest.raises(CarrotSchemaIncompatible, match="^CARROT_SCHEMA_INCOMPATIBLE$"):
        require_schema()


def test_healthy_transport_requires_every_flag_known_true():
    cc, _, _ = samples()
    for name in ("seen", "alive", "valid", "freq_ok", "updated"):
        assert not replace(cc.transport_health, **{name: False}).healthy
        assert not replace(cc.transport_health, **{name: None}).healthy
    assert cc.transport_health.healthy


def test_extraction_copies_zero_and_false_only_when_supported():
    cc, cs, co = samples()
    command = extract_car_control(cc, binding(), static_context_digest="a" * 64)
    state = extract_car_state(cs, binding(), steering_pressed_supported=True)
    receipt = extract_car_output(co, binding())
    assert command.desired_target_curvature_inv_m == 0.0
    assert command.measurement.measured_curvature_inv_m == 0.0
    assert state.steering_pressed is False
    assert (
        extract_car_state(cs, binding(), steering_pressed_supported=False).steering_pressed is None
    )
    assert receipt.controller_output_returned is True
    assert receipt.host_apply_time.value_ns == 10_000_000_000
    cc.reader.lateralControlObservation.desiredTargetCurvatureInvM.value = 99
    co.reader.actuationReceipt.finalRequestedActuators.torque = 99
    assert (
        command.desired_target_curvature_inv_m == receipt.final_requested_actuators["torque"] == 0.0
    )


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), True])
def test_bad_optional_number_never_becomes_zero(value):
    cc, _, _ = samples()
    cc.reader.lateralControlObservation.measurement.measuredCurvatureInvM = union(value)
    assert (
        extract_car_control(
            cc, binding(), static_context_digest="a" * 64
        ).measurement.measured_curvature_inv_m
        is None
    )


def test_unknown_enum_and_missing_pointer_are_unavailable():
    cc, _, co = samples()
    cc.reader.lateralControlObservation.instantaneousLimitState = "unknown_wire_ordinal"
    assert (
        extract_car_control(cc, binding(), static_context_digest="a" * 64).instantaneous_limit
        == "unavailable"
    )
    co.reader.actuationReceipt.finalRequestedActuators = None
    assert extract_car_output(co, binding()).final_requested_actuators is None


def test_wrong_topic_reader_or_malformed_nested_data_is_typed_rejection():
    cc, cs, _ = samples()
    with pytest.raises(CarrotInputError):
        extract_car_control(cs, binding(), static_context_digest="a" * 64)
    with pytest.raises(CarrotInputError):
        extract_car_control(replace(cc, reader=object()), binding(), static_context_digest="a" * 64)
    del cc.reader.lateralControlObservation.measurement.version
    with pytest.raises(CarrotInputError):
        extract_car_control(cc, binding(), static_context_digest="a" * 64)


def test_unqualified_sample_metadata_and_unrepresentable_numeric_are_rejected():
    cc, _, _ = samples()
    with pytest.raises(CarrotInputError):
        replace(cc, topic="unsupported")
    with pytest.raises(CarrotInputError):
        replace(cc, event_valid=1)
    cc.reader.lateralControlObservation.desiredTargetCurvatureInvM.value = 10**1000
    assert (
        extract_car_control(
            cc, binding(), static_context_digest="a" * 64
        ).desired_target_curvature_inv_m
        is None
    )
    cc.reader.lateralControlObservation.version = True
    with pytest.raises(CarrotInputError):
        extract_car_control(cc, binding(), static_context_digest="a" * 64)
