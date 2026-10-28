"""Real pycapnp reader stream -> source bridge -> existing adapter -> contract."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from openpilot.cereal import log

from compatibility.carrot.builders import car_control, car_output, car_state, sample
from compatibility.carrot.sidecar_streams import project, stream
from cyberpilot_autotune.integrations.carrot.adapter import CarrotReadOnlyAdapter
from cyberpilot_autotune.integrations.carrot.sidecar.runner import SidecarRunner
from cyberpilot_autotune.integrations.carrot.sidecar.source import SubMasterSource
from tests.fixtures.carrot_adapter import config, session
from tests.fixtures.carrot_v2 import BASELINE, complete
from tests.fixtures.sidecar import ScriptedSubMaster

CASES = json.loads(
    (Path(__file__).resolve().parents[2] / "tests/fixtures/sidecar_streams_v1.json").read_text()
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_actual_schema_sidecar_stream_matches_independent_expected_projection(case):
    cfg, frames = stream(case["id"])
    source = SubMasterSource(ScriptedSubMaster(frames), cfg.adapter.attestation.session)
    runner = SidecarRunner(cfg, source, clock=lambda: 10_010_000_000)
    decisions = []
    for _ in frames:
        decisions.extend(runner.poll_once())
    assert project(decisions, runner) == case["expected"]
    for decision in decisions:
        if decision.snapshot is not None:
            assert decision.snapshot.baseline_parameters == BASELINE
    runner.close()


def test_meb_bridge_preserves_pre_pid_target_vs_corrected_final_request():
    # MEB bridge regression only: the live CLI's platform gate remains Hyundai-only.
    attempt, _ = complete("mebCurvature")
    cc, cs, co = (
        car_control(log, attempt.source_command),
        car_state(log, attempt.source_car_state),
        car_output(log, attempt.receipt),
    )
    cc.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 0.125
    cc.carControl.actuators.curvature = (
        co.carOutput.actuationReceipt.finalRequestedActuators.curvature
    ) = 0.25
    adapter = CarrotReadOnlyAdapter(config("mebCurvature"))
    source = SubMasterSource(
        ScriptedSubMaster([(sample(cc), sample(cs)), (sample(co),)]), session()
    )
    decisions = []

    def ingest(value):
        if value.topic == "carControl":
            adapter.ingest_car_control(value)
        elif value.topic == "carState":
            adapter.ingest_car_state(value)
        else:
            decisions.append(
                adapter.evaluate_car_output(value, evaluation_mono_time_ns=10_010_000_000)
            )

    source.poll(1, ingest)
    cc.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 9.0
    cs.carState.steeringPressed = True
    source.poll(1, ingest)
    result = decisions[0].snapshot
    assert result.desired_curvature_inv_m == 0.125 and result.driver_override is False
    assert co.carOutput.actuationReceipt.finalRequestedActuators.curvature == 0.25
    source.close()


@pytest.mark.parametrize("missing", ["valid", "logMonoTime"])
def test_actual_output_with_unavailable_outer_metadata_consumes_closed_attempt(missing):
    cfg, frames = stream("hyundai_false")
    sm = ScriptedSubMaster(frames)
    update = sm.update

    def broken(timeout):
        update(timeout)
        if sm.updated["carOutput"]:
            getattr(sm, missing).pop("carOutput")

    sm.update = broken
    runner = SidecarRunner(
        cfg, SubMasterSource(sm, cfg.adapter.attestation.session), clock=lambda: 10_010_000_000
    )
    runner.poll_once()
    (result,) = runner.poll_once()
    assert result.reason.value == "INVALID_INPUT" and result.snapshot is None
    assert runner.diagnostics().receipt_attempt_count == 1
    assert runner.fault is not None
    runner.close()


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("legacy_observation", "SCHEMA_REVISION_MISMATCH"),
        ("limit_context", "CONTROLLER_CONTEXT_MISMATCH"),
    ],
)
def test_wire_schema_or_controller_context_mismatch_stops_the_session(fault, reason):
    cfg, frames = stream("hyundai_false")
    cc = frames[0][0].reader
    # These are actual generated readers backed by synthetic builders.
    if fault == "legacy_observation":
        changed = cc.as_builder()
        changed.lateralControlObservation.version = 1
        frames[0] = (replace(frames[0][0], reader=changed.as_reader()), frames[0][1])
    else:
        changed = frames[1][0].reader.as_builder()
        changed.actuationReceipt.instantaneousControllerLimitState = "limited"
        frames[1] = (replace(frames[1][0], reader=changed.as_reader()),)
    runner = SidecarRunner(
        cfg,
        SubMasterSource(ScriptedSubMaster(frames), cfg.adapter.attestation.session),
        clock=lambda: 10_010_000_000,
    )
    runner.poll_once()
    assert runner.poll_once()[0].snapshot is None
    assert runner.fault is not None and runner.fault.code == reason
    runner.close()
