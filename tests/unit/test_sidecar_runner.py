"""Sticky runtime faults and immediate ingestion; no live service is launched."""

import json
from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.sidecar.config import SidecarError
from cyberpilot_autotune.integrations.carrot.sidecar.diagnostics import format_summary
from cyberpilot_autotune.integrations.carrot.sidecar.runner import SidecarRunner
from cyberpilot_autotune.integrations.carrot.sidecar.source import SubMasterSource
from tests.fixtures.carrot_readers import binding, samples, session
from tests.fixtures.sidecar import ScriptedSubMaster, sidecar_config


@pytest.fixture
def make(monkeypatch):
    monkeypatch.setattr("cyberpilot_autotune.integrations.carrot.adapter.require_schema", binding)

    def factory(frames, *, clock=lambda: 10_010_000_000):
        source = SubMasterSource(ScriptedSubMaster(frames), session())
        return SidecarRunner(sidecar_config(), source, clock=clock)

    return factory


def test_delayed_join_is_copied_before_mutation_and_summary_is_allowlisted(make):
    cc, cs, co = samples()
    runner = make([(cc, cs), (co,), ()])
    assert runner.poll_once() == ()
    cs.reader.steeringPressed = True
    cc.reader.actuators.torque = 999.0
    (decision,) = runner.poll_once()
    assert decision.snapshot.driver_override is False
    assert decision.snapshot.baseline_parameters == {"synthetic.test_only": 10.0}
    assert runner.poll_once() == ()
    summary = json.loads(format_summary(runner.diagnostics()))
    assert summary["received_counts"] == [["carControl", 1], ["carState", 1], ["carOutput", 1]]
    assert summary["healthy_transport_count"] == 3
    assert summary["receipt_attempt_count"] == summary["accepted_mapping_count"] == 1
    assert summary["latest_snapshot_available"] is True
    assert "999" not in json.dumps(summary) and "baseline_parameters" not in summary


def test_rejected_receipt_is_consumed_despite_later_source_arrival(make):
    cc, cs, co = samples()
    runner = make([(co,), (cc, cs), (replace(co, log_mono_time_ns=10_006_000_000),)])
    (first,) = runner.poll_once()
    assert first.snapshot is None
    runner.poll_once()
    (second,) = runner.poll_once()
    assert second.snapshot is None
    assert runner.diagnostics().receipt_attempt_count == 2


def test_malformed_receipt_fault_is_sticky_and_clears_latest_diagnostics(make):
    cc, cs, co = samples()
    broken = replace(co, reader=None, log_mono_time_ns=10_006_000_000)
    runner = make([(cc, cs, co), (broken,), (co,)])
    assert runner.poll_once()[0].snapshot is not None
    assert runner.poll_once()[0].snapshot is None
    assert runner.fault is not None
    state = runner.diagnostics()
    assert state.session_state == "faulted" and state.session_fault_count == 1
    assert state.latest_control_active is None and not state.latest_snapshot_available
    with pytest.raises(SidecarError):
        runner.poll_once()


def test_local_monotonic_regression_requires_explicit_new_source_and_generation(make):
    clock = iter([10_010_000_000] * 3 + [10_009_000_000])
    runner = make([(), ()], clock=lambda: next(clock))
    runner.poll_once()
    with pytest.raises(SidecarError, match="MONOTONIC_REGRESSION"):
        runner.poll_once()
    assert runner.fault.code == "MONOTONIC_REGRESSION"


@pytest.mark.parametrize("source_topics", [False, True])
@pytest.mark.parametrize("elapsed_ns", [5_000_000_000, -1, None])
def test_final_poll_without_output_updates_uptime_and_checks_clock(make, elapsed_ns, source_topics):
    clock = [10_010_000_000]
    runner = make([samples()[:2] if source_topics else ()], clock=lambda: clock[0])
    sm = runner._source._sm
    update = sm.update

    def receive(timeout):
        update(timeout)
        clock[0] = None if elapsed_ns is None else clock[0] + elapsed_ns

    sm.update = receive
    if elapsed_ns is None or elapsed_ns < 0:
        reason = "RUNTIME_INVARIANT_FAULT" if elapsed_ns is None else "MONOTONIC_REGRESSION"
        with pytest.raises(SidecarError, match=reason):
            runner.poll_once()
        assert runner.diagnostics().session_fault_count == 1
    else:
        assert runner.poll_once() == ()
        runner.close()
        assert runner.diagnostics().uptime_s == elapsed_ns / 1e9
        assert runner.diagnostics().session_state == "closed"


def test_explicit_restart_never_automatically_recovers_and_normal_close_is_idempotent(make):
    runner = make([samples()])
    runner.producer_restarted()
    with pytest.raises(SidecarError, match="PRODUCER_RESTARTED"):
        runner.poll_once()
    assert runner.diagnostics().session_fault_count == 1
    runner.close()
    runner.close()


def test_new_session_rejects_old_generation_and_old_source_then_accepts_fresh(make):
    cfg = sidecar_config()
    runner = make([samples()])
    runner.producer_restarted()
    old_source = runner._source
    with pytest.raises(SidecarError):
        runner.new_session(cfg, old_source)
    cfg = replace(
        cfg,
        adapter=replace(
            cfg.adapter, attestation=replace(cfg.adapter.attestation, session=session(1))
        ),
    )
    fresh = SubMasterSource(ScriptedSubMaster([samples()]), session(1))
    runner.new_session(cfg, fresh)
    assert runner.poll_once()[0].snapshot is not None
    assert runner.diagnostics().session_fault_count == 0
    runner.close()
    with pytest.raises(SidecarError, match="SOURCE_CLOSED"):
        runner.poll_once()


@pytest.mark.parametrize("failure", ["source", "metadata", "wrong_topic", "clock"])
def test_boundary_exceptions_are_sanitized_sticky_faults(make, failure):
    cc, _, _ = samples()
    runner = make([(cc,)])
    if failure == "clock":
        runner._clock = lambda: True
    elif failure == "metadata":
        sm = runner._source._sm
        update = sm.update

        def missing(timeout):
            update(timeout)
            sm.valid.pop("carControl")

        sm.update = missing
    else:

        def failed(timeout, consume):
            if failure == "source":
                raise RuntimeError("SECRET-VIN-RAW")
            consume(replace(cc, topic="invalid"))

        runner._source.poll = failed
    with pytest.raises(SidecarError) as error:
        runner.poll_once()
    assert "SECRET" not in str(error.value)
    assert runner.fault is not None


def test_unexpected_new_session_failure_closes_both_receivers_and_latches(make):
    runner = make([samples()])
    cfg = sidecar_config()
    cfg = replace(
        cfg,
        adapter=replace(
            cfg.adapter, attestation=replace(cfg.adapter.attestation, session=session(1))
        ),
    )
    fresh = SubMasterSource(ScriptedSubMaster([]), session(1))

    def broken_clock():
        raise RuntimeError("SECRET-RESET")

    runner._clock = broken_clock
    with pytest.raises(SidecarError, match="RUNTIME_INVARIANT_FAULT"):
        runner.new_session(cfg, fresh)
    assert runner.fault is not None
    with pytest.raises(SidecarError, match="SOURCE_CLOSED"):
        fresh.poll(1, lambda sample: None)


def test_initial_clock_exception_is_typed_and_releases_source(make):
    def clock():
        raise RuntimeError("SECRET-CLOCK")

    with pytest.raises(SidecarError, match="RUNTIME_INVARIANT_FAULT"):
        make([], clock=clock)


def test_known_source_controller_change_is_a_session_fault(make):
    cc, _, _ = samples()
    cc.reader.lateralControlObservation.controllerKind = "pid"
    runner = make([(cc,)])
    with pytest.raises(SidecarError, match="SESSION_REQUIRED"):
        runner.poll_once()


def test_missing_valid_metadata_still_counts_the_observed_updated_topic(make):
    cc, _, _ = samples()
    runner = make([(cc,)])
    sm = runner._source._sm
    update = sm.update

    def missing(timeout):
        update(timeout)
        sm.valid.pop("carControl")

    sm.update = missing
    with pytest.raises(SidecarError):
        runner.poll_once()
    assert dict(runner.diagnostics().received_counts)["carControl"] == 1


def test_unparseable_output_envelope_consumes_attempt_without_fabricated_metadata(make):
    cc, cs, co = samples()
    runner = make([(cc, cs, co)])
    sm = runner._source._sm
    update = sm.update

    def missing(timeout):
        update(timeout)
        sm.logMonoTime.pop("carOutput")

    sm.update = missing
    (result,) = runner.poll_once()
    assert result.snapshot is None and result.reason.value == "INVALID_INPUT"
    state = runner.diagnostics()
    assert state.receipt_attempt_count == 1
    assert dict(state.received_counts)["carOutput"] == 1
    assert state.session_state == "faulted" and state.session_fault_count == 1
    with pytest.raises(SidecarError):
        runner.poll_once()


@pytest.mark.parametrize("failed_clock", [None, 10_009_000_000])
def test_output_attempt_is_consumed_when_evaluation_clock_fails_during_receive(make, failed_clock):
    clock = [10_010_000_000]
    runner = make([samples()], clock=lambda: clock[0])
    sm = runner._source._sm
    update = sm.update

    def receive(timeout):
        update(timeout)
        clock[0] = failed_clock

    sm.update = receive
    (result,) = runner.poll_once()
    assert result.snapshot is None and result.reason.value == "INVALID_INPUT"
    assert runner.diagnostics().receipt_attempt_count == 1
    assert runner._adapter.previous_host_apply_ns == 10_000_000_000
    assert runner.fault is not None


def test_old_receive_generation_after_explicit_reset_is_a_session_fault(make):
    runner = make([])
    cfg = sidecar_config()
    cfg = replace(
        cfg,
        adapter=replace(
            cfg.adapter, attestation=replace(cfg.adapter.attestation, session=session(1))
        ),
    )
    fresh = SubMasterSource(ScriptedSubMaster([]), session(1))
    runner.new_session(cfg, fresh)
    old_cc, _, _ = samples()
    fresh.poll = lambda timeout, consume: consume(old_cc)
    with pytest.raises(SidecarError, match="SESSION_REQUIRED"):
        runner.poll_once()
    assert runner.diagnostics().latest_snapshot_available is False
    assert runner.diagnostics().session_fault_count == 1
