"""Synthetic generated-schema inputs; all expected projections are separate literals."""

from dataclasses import replace

from openpilot.cereal import log

from compatibility.carrot.builders import car_control, car_output, car_state, sample
from tests.fixtures.carrot_v2 import complete
from tests.fixtures.sidecar import sidecar_config


def stream(case):
    cfg = sidecar_config()
    attempt, _ = complete()
    cc, cs, co = (
        car_control(log, attempt.source_command),
        car_state(log, attempt.source_car_state),
        car_output(log, attempt.receipt),
    )
    obs, receipt = cc.carControl.lateralControlObservation, co.carOutput.actuationReceipt
    if case == "hyundai_true":
        cs.carState.steeringPressed = True
    if case == "exact_zero":
        cs.carState.vEgo = obs.measurement.inputSpeedMps.value = 0.0
    if case == "host_inactive":
        cc.carControl.latActive = False
        obs.instantaneousLimitState = receipt.instantaneousControllerLimitState = "unavailable"
        obs.init("measurement")
        receipt.hostLateralActivityState = "inactive"
    if case == "safety_disallowed":
        receipt.safetyPermissionState = "disallowed"
    if case == "instant_limited":
        obs.instantaneousLimitState = receipt.instantaneousControllerLimitState = "limited"
    if case == "output_limited":
        receipt.outputLimitState = "limited"
    if case == "unavailable_measurement":
        obs.measurement.measuredCurvatureInvM.unavailable = None
    if case == "unsupported_observation":
        obs.version = 3
    if case == "malformed_receipt":
        receipt.hostApplyMonoTime.unavailable = None
    if case == "outer_invalid":
        co.valid = False
    if case == "unknown_enum":
        receipt.safetyPermissionState = 65535
    if case == "nonfinite_target":
        obs.desiredTargetCurvatureInvM.value = float("inf")
    if case == "latest_cc":
        cc.logMonoTime += 1
    if case == "latest_cs":
        cs.logMonoTime += 1
    frames = [(cc, cs), (co,)]
    if case == "delayed":
        frames = [(cc,), (cs,), (), (co,)]
    if case == "repeated_cc":
        frames = [(cc,), (cc, cs), (co,)]
    if case == "missing_cc":
        frames = [(cs,), (co,)]
    if case == "missing_cs":
        frames = [(cc,), (co,)]
    if case in ("duplicate_receipt", "co_before_sources", "rejected_repaired", "apply_regression"):
        second = car_output(log, attempt.receipt, event_ns=10_006_000_000)
        if case == "apply_regression":
            second.carOutput.actuationReceipt.hostApplyMonoTime.value = 9_999_999_999
        if case == "rejected_repaired":
            receipt.safetyPermissionState = "unavailable"
        frames = (
            [(co,), (cc, cs), (second,)]
            if case == "co_before_sources"
            else [(cc, cs), (co,), (second,)]
        )
    if case in ("poison_cc", "evict_cc"):
        second = car_control(log, attempt.source_command)
        if case == "poison_cc":
            second.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 0.5
        else:
            second.logMonoTime += 1
        frames = [(cc, cs), (second,), (co,)]
    if case in ("poison_cs", "evict_cs"):
        second = car_state(log, attempt.source_car_state)
        if case == "poison_cs":
            second.carState.steeringPressed = True
        else:
            second.logMonoTime += 1
        frames = [(cc, cs), (second,), (co,)]
    if case.startswith("evict_"):
        cfg = replace(
            cfg,
            adapter=replace(
                cfg.adapter,
                cache_policy=replace(
                    cfg.adapter.cache_policy,
                    maximum_car_control_entries=1,
                    maximum_car_state_entries=1,
                ),
            ),
        )
    return cfg, [tuple(sample(event) for event in frame) for frame in frames]


def project(decisions, runner):
    last = decisions[-1]
    snapshot, d = last.snapshot, runner.diagnostics()
    return dict(
        reasons=[item.reason.value for item in decisions],
        snapshot_available=snapshot is not None,
        control_active=last.control_active,
        controller_saturated=last.controller_saturated,
        driver_override=snapshot.driver_override if snapshot is not None else None,
        attempts=d.receipt_attempt_count,
        poisoned=d.poisoned_key_count,
        cc_evicted=d.cc_eviction_count,
        cs_evicted=d.cs_eviction_count,
        fault=runner.fault is not None,
    )
