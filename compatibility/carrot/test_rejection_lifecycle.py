"""Adversarial real-wire failures cannot hide required session invalidation."""

from dataclasses import replace

import pytest
from openpilot.cereal import log

from compatibility.carrot.builders import car_control, car_output, car_state, sample
from cyberpilot_autotune.integrations.carrot.adapter import CarrotReadOnlyAdapter
from tests.fixtures.carrot_adapter import config
from tests.fixtures.carrot_v2 import complete


@pytest.mark.parametrize(
    "fault",
    [
        "missing_apply",
        "missing_command",
        "command_after_apply",
        "safety_clock_regression",
        "kind_masked_by_bad_now",
        "measurement_fault_masked_by_missing_cs",
    ],
)
def test_known_fault_requires_new_session_despite_earlier_rejection(fault):
    attempt, _ = complete()
    adapter = CarrotReadOnlyAdapter(config())
    cc = car_control(log, attempt.source_command)
    cs = car_state(log, attempt.source_car_state)
    output = car_output(log, attempt.receipt)
    receipt = output.carOutput.actuationReceipt
    if fault == "missing_apply":
        receipt.hostApplyMonoTime.unavailable = None
    elif fault == "missing_command":
        receipt.sourceCarControlMonoTime.unavailable = None
    elif fault == "command_after_apply":
        receipt.sourceCarControlMonoTime.value = 10_000_000_001
    elif fault == "safety_clock_regression":
        receipt.safetyStateMonoTime.value = 20_000_000_001
        receipt.sourceCarControlMonoTime.value = 9_980_000_001
    elif fault == "kind_masked_by_bad_now":
        receipt.controllerKind = "pid"
    else:
        m = cc.carControl.lateralControlObservation.measurement
        m.carStateMonoTime.value = 9_970_000_000  # later than its calculation time
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    bad_now = 0 if fault == "kind_masked_by_bad_now" else 10_010_000_000
    first = adapter.evaluate_car_output(sample(output), evaluation_mono_time_ns=bad_now)
    assert first.snapshot is None
    assert adapter.session_required
    # Retimed and repaired data must not regain eligibility in the old session.
    repaired = car_output(
        log,
        replace(
            attempt.receipt,
            host_apply_time=replace(attempt.receipt.host_apply_time, value_ns=10_000_000_001),
        ),
        event_ns=10_006_000_000,
    )
    assert (
        adapter.evaluate_car_output(
            sample(repaired), evaluation_mono_time_ns=10_010_000_000
        ).snapshot
        is None
    )
    assert adapter.next_sequence == 2


@pytest.mark.parametrize("changed", ["receipt", "observation", "measurement"])
def test_unaudited_wire_version_requires_new_session(changed):
    attempt, _ = complete()
    adapter = CarrotReadOnlyAdapter(config())
    cc = car_control(log, attempt.source_command)
    output = car_output(log, attempt.receipt)
    if changed == "receipt":
        output.carOutput.actuationReceipt.receiptVersion = 2
    elif changed == "observation":
        cc.carControl.lateralControlObservation.version = 3
    else:
        cc.carControl.lateralControlObservation.measurement.version = 2
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(car_state(log, attempt.source_car_state)))
    result = adapter.evaluate_car_output(sample(output), evaluation_mono_time_ns=10_010_000_000)
    assert result.snapshot is None and result.reason.value == "UNSUPPORTED_VERSION"
    assert adapter.session_required
