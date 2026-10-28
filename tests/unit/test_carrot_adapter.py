"""State/health/session tests with reader doubles; actual schema is separate."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.adapter import (
    CarrotReadOnlyAdapter,
)
from cyberpilot_autotune.integrations.carrot.errors import CarrotInputError, CarrotSessionRequired
from tests.fixtures.carrot_adapter import config
from tests.fixtures.carrot_readers import binding, healthy, samples, session, union
from tests.fixtures.carrot_v2 import BASELINE


@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setattr("cyberpilot_autotune.integrations.carrot.adapter.require_schema", binding)
    return CarrotReadOnlyAdapter(config())


def feed(adapter, *, token=None):
    cc, cs, co = samples()
    if token is not None:
        cc, cs, co = (replace(s, session_token=token) for s in (cc, cs, co))
    adapter.ingest_car_control(cc)
    adapter.ingest_car_state(cs)
    return cc, cs, co


def test_exact_delayed_join_and_reader_copy(adapter):
    cc, cs, co = feed(adapter)
    cc.reader.lateralControlObservation.desiredTargetCurvatureInvM.value = 0.75
    cs.reader.steeringPressed = True
    result = adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000)
    assert result.snapshot.source_valid and result.snapshot.driver_override is False
    assert result.snapshot.desired_curvature_inv_m == 0.0
    assert result.snapshot.baseline_parameters == BASELINE and result.snapshot.sequence == 0


def test_rejected_receipt_is_consumed_and_high_water_survives_id_eviction(adapter):
    cc, cs, co = samples()
    adapter.ingest_car_control(cc)
    first = adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000)
    assert first.snapshot is None
    adapter.ingest_car_state(cs)
    repaired = replace(co, log_mono_time_ns=10_006_000_000)
    assert (
        adapter.evaluate_car_output(repaired, evaluation_mono_time_ns=10_010_000_000).snapshot
        is None
    )
    for i in (1, 2, 3):
        current = replace(co, log_mono_time_ns=10_006_000_000 + i)
        current.reader.actuationReceipt.hostApplyMonoTime.value = 10_000_000_000 + i
        adapter.evaluate_car_output(current, evaluation_mono_time_ns=10_010_000_000)
    co.reader.actuationReceipt.hostApplyMonoTime.value = 10_000_000_000
    late = adapter.evaluate_car_output(
        replace(co, log_mono_time_ns=10_007_000_000), evaluation_mono_time_ns=10_010_000_000
    )
    assert late.snapshot is None and adapter.previous_host_apply_ns == 10_000_000_003
    assert adapter.next_sequence == 6


def test_unhealthy_output_cannot_be_repaired_at_same_publication(adapter):
    _, _, co = feed(adapter)
    bad = replace(co, transport_health=replace(healthy(), valid=False))
    assert adapter.evaluate_car_output(bad, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.next_sequence == 2


def test_outer_event_valid_is_separate_from_explicit_transport_health(adapter):
    _, _, co = feed(adapter)
    result = adapter.evaluate_car_output(
        replace(co, event_valid=False), evaluation_mono_time_ns=10_010_000_000
    )
    assert result.snapshot.source_valid


def test_inactive_receipt_preserves_false_without_source_measurement(adapter):
    cc, _, co = samples()
    cc.reader.latActive = False
    cc.reader.lateralControlObservation.measurement.version = 0
    cc.reader.lateralControlObservation.instantaneousLimitState = "unavailable"
    co.reader.actuationReceipt.hostLateralActivityState = "inactive"
    co.reader.actuationReceipt.instantaneousControllerLimitState = "unavailable"
    adapter.ingest_car_control(cc)
    result = adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000)
    assert result.control_active is False and result.snapshot is None


def test_explicit_new_session_reset_and_old_tag_rejection(adapter):
    cc, _, _ = feed(adapter)
    with pytest.raises(CarrotSessionRequired):
        adapter.ingest_car_control(replace(cc, log_mono_time_ns=9_970_000_000))
    assert adapter.session_required
    adapter.reset_session(config(generation=1))
    assert not adapter.session_required and adapter.next_sequence == 0
    with pytest.raises(CarrotInputError):
        adapter.ingest_car_control(cc)
    _, _, co = feed(adapter, token=session(1))
    assert adapter.evaluate_car_output(
        co, evaluation_mono_time_ns=10_010_000_000
    ).snapshot.source_valid
    with pytest.raises(CarrotInputError):
        adapter.reset_session(config(generation=1))


def test_explicit_producer_restart_requires_reset(adapter):
    _, _, co = feed(adapter)
    adapter.producer_restarted()
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.session_required


def test_future_apply_cannot_be_repaired_by_clock_guessing(adapter):
    _, _, co = feed(adapter)
    co.reader.actuationReceipt.hostApplyMonoTime = union(20_000_000_000, "monotonic")
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.session_required


def test_known_controller_context_change_requires_new_session(adapter):
    cc, _, _ = samples()
    cc.reader.lateralControlObservation.controllerKind = "pid"
    with pytest.raises(CarrotSessionRequired):
        adapter.ingest_car_control(cc)
    assert adapter.session_required


@pytest.mark.parametrize("topic", ["cc", "cs"])
def test_cached_source_health_is_not_replaced_by_current_good_health(adapter, topic):
    cc, cs, co = samples()
    cc = replace(cc, transport_health=replace(healthy(), freq_ok=False)) if topic == "cc" else cc
    cs = replace(cs, transport_health=replace(healthy(), alive=False)) if topic == "cs" else cs
    adapter.ingest_car_control(cc)
    adapter.ingest_car_state(cs)
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None


def test_capability_is_checked_against_source_and_context(monkeypatch):
    monkeypatch.setattr("cyberpilot_autotune.integrations.carrot.adapter.require_schema", binding)
    cfg = config()
    cfg = replace(cfg, attestation=replace(cfg.attestation, steering_pressed_capability=None))
    adapter = CarrotReadOnlyAdapter(cfg)
    _, _, co = feed(adapter)
    result = adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000)
    assert result.snapshot is None and result.reason.value == "INVALID_SOURCE_CAR_STATE"


def test_malformed_source_key_is_poisoned_before_repaired_reingestion(adapter):
    cc, cs, co = samples()
    del cc.reader.lateralControlObservation.version
    with pytest.raises(CarrotInputError):
        adapter.ingest_car_control(cc)
    cc.reader.lateralControlObservation.version = 2
    adapter.ingest_car_control(cc)
    adapter.ingest_car_state(cs)
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None


@pytest.mark.parametrize("failure", ["outer_timestamp", "evaluation_clock"])
def test_receipt_key_is_consumed_even_when_sample_clock_validation_fails(adapter, failure):
    _, _, co = feed(adapter)
    broken = replace(co, log_mono_time_ns=0) if failure == "outer_timestamp" else co
    now = 0 if failure == "evaluation_clock" else 10_010_000_000
    assert adapter.evaluate_car_output(broken, evaluation_mono_time_ns=now).snapshot is None
    repaired = replace(co, log_mono_time_ns=10_006_000_000)
    assert (
        adapter.evaluate_car_output(repaired, evaluation_mono_time_ns=10_010_000_000).snapshot
        is None
    )
    assert adapter.previous_host_apply_ns == 10_000_000_000


def test_malformed_receipt_cannot_be_repaired_in_the_same_session(adapter):
    _, _, co = feed(adapter)
    broken = replace(co, reader=object())
    assert (
        adapter.evaluate_car_output(broken, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    )
    assert (
        adapter.evaluate_car_output(
            replace(co, log_mono_time_ns=10_006_000_000), evaluation_mono_time_ns=10_010_000_000
        ).snapshot
        is None
    )
    assert adapter.session_required


def test_startup_unavailable_receipt_does_not_invent_a_clock_restart(adapter):
    _, _, co = feed(adapter)
    first = samples()[2]
    first.reader.actuationReceipt.receiptVersion = 0
    for field in (
        "sourceCarControlMonoTime",
        "hostApplyMonoTime",
        "safetyStateMonoTime",
        "safetyObservationMonoTime",
    ):
        setattr(first.reader.actuationReceipt, field, union(None))
    assert (
        adapter.evaluate_car_output(first, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    )
    assert not adapter.session_required
    result = adapter.evaluate_car_output(
        replace(co, log_mono_time_ns=10_006_000_000), evaluation_mono_time_ns=10_010_000_000
    )
    assert result.snapshot.source_valid


def test_wrong_adapter_topic_never_reaches_a_mapping(adapter):
    cc, cs, _ = samples()
    with pytest.raises(CarrotInputError):
        adapter.ingest_car_control(cs)
    assert adapter.evaluate_car_output(cc, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.next_sequence == 1


def test_malformed_car_state_cannot_be_repaired_at_its_key(adapter):
    cc, cs, co = samples()
    del cs.reader.vEgo
    with pytest.raises(CarrotInputError):
        adapter.ingest_car_state(cs)
    cs.reader.vEgo = 2.0
    adapter.ingest_car_state(cs)
    adapter.ingest_car_control(cc)
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None


def test_missing_cohort_command_key_still_consumes_known_apply(adapter):
    _, _, co = feed(adapter)
    co.reader.actuationReceipt.sourceCarControlMonoTime = union(None, "monotonic")
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.previous_host_apply_ns == 10_000_000_000


def test_receipt_known_kind_or_explicit_clock_mismatch_requires_new_session(adapter):
    _, _, co = feed(adapter)
    co.reader.actuationReceipt.controllerKind = "pid"
    assert adapter.evaluate_car_output(co, evaluation_mono_time_ns=10_010_000_000).snapshot is None
    assert adapter.session_required
