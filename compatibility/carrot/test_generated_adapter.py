"""Public state-machine entry points with actual generated readers, no fake binding."""

from dataclasses import replace

import pytest
from openpilot.cereal import log

from compatibility.carrot.builders import car_control, car_output, car_state, sample
from cyberpilot_autotune.integrations.carrot.adapter import CarrotReadOnlyAdapter
from cyberpilot_autotune.integrations.carrot.errors import CarrotInputError
from tests.fixtures.carrot_adapter import config, healthy
from tests.fixtures.carrot_v2 import complete


@pytest.mark.parametrize("kind", ["pid", "torque", "angle", "mebCurvature"])
def test_all_controller_families_use_actual_readers(kind):
    adapter = CarrotReadOnlyAdapter(config(kind))
    attempt, _ = complete(kind)
    cc = car_control(log, attempt.source_command)
    cs = car_state(log, attempt.source_car_state)
    co = car_output(log, attempt.receipt)
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    decision = adapter.evaluate_car_output(sample(co), evaluation_mono_time_ns=10_010_000_000)
    assert decision.snapshot.source_valid and decision.snapshot.driver_override is False
    assert decision.snapshot.baseline_parameters == config(kind).baseline_parameters
    assert (
        decision.snapshot.measured_curvature_inv_m
        == decision.snapshot.desired_curvature_inv_m
        == 0.0
    )


@pytest.mark.parametrize(
    "case",
    [
        "inactive",
        "safety_disallowed",
        "instant",
        "output",
        "both",
        "outer_invalid",
        "capability_unknown",
    ],
)
def test_real_receipt_outcomes(case):
    cfg = config()
    attempt, _ = complete()
    if case == "capability_unknown":
        cfg = replace(cfg, attestation=replace(cfg.attestation, steering_pressed_capability=None))
    adapter = CarrotReadOnlyAdapter(cfg)
    cc = car_control(log, attempt.source_command)
    cs = car_state(log, attempt.source_car_state)
    co = car_output(log, attempt.receipt, event_valid=case != "outer_invalid")
    obs = cc.carControl.lateralControlObservation
    receipt = co.carOutput.actuationReceipt
    if case == "inactive":
        cc.carControl.latActive = False
        obs.instantaneousLimitState = "unavailable"
        obs.measurement.version = 0
        receipt.hostLateralActivityState = "inactive"
        receipt.instantaneousControllerLimitState = "unavailable"
    if case == "safety_disallowed":
        receipt.safetyPermissionState = "disallowed"
    if case in ("instant", "both"):
        obs.instantaneousLimitState = receipt.instantaneousControllerLimitState = "limited"
    if case in ("output", "both"):
        receipt.outputLimitState = "limited"
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    result = adapter.evaluate_car_output(sample(co), evaluation_mono_time_ns=10_010_000_000)
    if case == "inactive":
        assert result.snapshot is None and result.control_active is False
    elif case == "capability_unknown":
        assert result.snapshot is None
    else:
        assert result.snapshot.source_valid
        assert result.snapshot.control_active is (case != "safety_disallowed")
        assert result.snapshot.controller_saturated is (case in ("instant", "output", "both"))


def test_meb_pre_pid_target_differs_from_preserved_final_request():
    cfg = config("mebCurvature")
    adapter = CarrotReadOnlyAdapter(cfg)
    attempt, _ = complete("mebCurvature")
    cc = car_control(log, attempt.source_command)
    cs = car_state(log, attempt.source_car_state)
    co = car_output(log, attempt.receipt)
    cc.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 0.125
    cc.carControl.actuators.curvature = 0.25
    co.carOutput.actuationReceipt.finalRequestedActuators.curvature = 0.25
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    result = adapter.evaluate_car_output(sample(co), evaluation_mono_time_ns=10_010_000_000)
    assert result.snapshot.desired_curvature_inv_m == 0.125
    assert co.carOutput.actuationReceipt.finalRequestedActuators.curvature == 0.25


@pytest.mark.parametrize("evict", ["cc", "cs"])
def test_delayed_receipt_has_no_latest_fallback_after_eviction(evict):
    adapter = CarrotReadOnlyAdapter(config(capacities=(1, 1, 1)))
    attempt, _ = complete()
    cc = car_control(log, attempt.source_command)
    cs = car_state(log, attempt.source_car_state)
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    if evict == "cc":
        cc.logMonoTime += 1
        cc.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 0.5
        adapter.ingest_car_control(sample(cc))
    else:
        cs.logMonoTime += 1
        adapter.ingest_car_state(sample(cs))
    co = car_output(log, attempt.receipt)
    assert (
        adapter.evaluate_car_output(sample(co), evaluation_mono_time_ns=10_010_000_000).snapshot
        is None
    )


def test_default_bool_false_needs_capability_and_qualified_health():
    cfg = config()
    attempt, _ = complete()
    cs = car_state(log, replace(attempt.source_car_state, steering_pressed=None))
    # The wire cannot distinguish this False from explicit False. Availability
    # must come from the independently qualified producer/caller capability.
    assert cs.carState.steeringPressed is False
    for capability in (None, cfg.attestation.steering_pressed_capability):
        adapter = CarrotReadOnlyAdapter(
            replace(
                cfg, attestation=replace(cfg.attestation, steering_pressed_capability=capability)
            )
        )
        adapter.ingest_car_control(sample(car_control(log, attempt.source_command)))
        adapter.ingest_car_state(sample(cs))
        result = adapter.evaluate_car_output(
            sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
        )
        assert (result.snapshot is not None) == (capability is not None)


def test_conflicting_actual_source_command_never_becomes_usable():
    adapter = CarrotReadOnlyAdapter(config())
    attempt, _ = complete()
    cc = car_control(log, attempt.source_command)
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_control(sample(cc))
    cc.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 0.5
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(car_state(log, attempt.source_car_state)))
    assert (
        adapter.evaluate_car_output(
            sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
        ).snapshot
        is None
    )


def test_generated_legacy_defaults_and_unavailable_groups_fail_closed():
    adapter = CarrotReadOnlyAdapter(config())
    event = log.Event.new_message(logMonoTime=10_000_000_000, valid=True)
    event.init("carOutput")
    result = adapter.evaluate_car_output(sample(event), evaluation_mono_time_ns=10_010_000_000)
    assert result.snapshot is None
    assert result.control_active is None and adapter.next_sequence == 1


def test_wrong_reader_schema_is_rejected_without_payload_coercion():
    adapter = CarrotReadOnlyAdapter(config())
    attempt, _ = complete()
    state = sample(car_state(log, attempt.source_car_state))
    from cyberpilot_autotune.integrations.carrot.extraction import DecodedTopicSample

    forged = DecodedTopicSample(
        "carControl", state.log_mono_time_ns, True, healthy(), state.reader, state.session_token
    )
    with pytest.raises(CarrotInputError):
        adapter.ingest_car_control(forged)


def test_startup_default_receipt_can_be_followed_by_a_complete_cohort():
    adapter = CarrotReadOnlyAdapter(config())
    attempt, _ = complete()
    default = log.Event.new_message(logMonoTime=10_004_000_000, valid=False)
    default.init("carOutput")
    assert (
        adapter.evaluate_car_output(
            sample(default), evaluation_mono_time_ns=10_010_000_000
        ).snapshot
        is None
    )
    assert not adapter.session_required
    adapter.ingest_car_control(sample(car_control(log, attempt.source_command)))
    adapter.ingest_car_state(sample(car_state(log, attempt.source_car_state)))
    assert adapter.evaluate_car_output(
        sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
    ).snapshot.source_valid
