"""Actual generated readers and public adapter, never a fake schema binding."""

from dataclasses import FrozenInstanceError, replace

import pytest
from openpilot.cereal import log

from compatibility.carrot.builders import car_control, car_output, car_state, sample
from cyberpilot_autotune.integrations.carrot.adapter import CarrotReadOnlyAdapter
from tests.fixtures.carrot_adapter import healthy, hyundai_config
from tests.fixtures.carrot_v2 import BASELINE, complete


@pytest.mark.parametrize("platform", ["HYUNDAI_SANTA_FE_2022", "HYUNDAI_IONIQ_5"])
@pytest.mark.parametrize("pressed", [False, True])
def test_real_hyundai_false_and_true_remain_known_and_immutable(platform, pressed):
    cfg = hyundai_config(platform)
    attempt, _ = complete()
    adapter = CarrotReadOnlyAdapter(cfg)
    cc, cs = car_control(log, attempt.source_command), car_state(log, attempt.source_car_state)
    cs.carState.steeringPressed = pressed
    cs.carState.steeringAngleDeg = 0.0
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    cached = adapter._states.lookup(cs.logMonoTime).evidence
    assert cached.steering_pressed is pressed and cached.steering_pressed_supported is True
    assert cached.steering_angle_deg == 0.0
    cs.carState.steeringPressed = not pressed
    with pytest.raises(FrozenInstanceError):
        cached.steering_pressed = not pressed
    decision = adapter.evaluate_car_output(
        sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
    )
    assert decision.snapshot.source_valid and decision.snapshot.driver_override is pressed
    assert decision.snapshot.baseline_parameters == BASELINE
    assert cfg.baseline_parameters == BASELINE


@pytest.mark.parametrize(
    "failure",
    [
        "missing_capability",
        "wrong_path",
        "wrong_symbol",
        "wrong_revision",
        "wrong_brand",
        "wrong_variant",
        "wrong_static_flags",
        "wrong_platform",
        "unconfirmed",
    ],
)
@pytest.mark.parametrize("platform", ["HYUNDAI_SANTA_FE_2022", "HYUNDAI_IONIQ_5"])
def test_unqualified_hyundai_default_false_is_unavailable(failure, platform):
    cfg = hyundai_config(platform, confirmed=failure != "unconfirmed")
    cap = cfg.attestation.steering_pressed_capability
    if failure == "missing_capability":
        cap = None
    if failure == "wrong_path":
        cap = replace(cap, producer_path="opendbc_repo/opendbc/car/tesla/carstate.py")
    if failure == "wrong_symbol":
        cap = replace(cap, producer_symbol="CarState.dummy")
    if failure == "wrong_revision":
        cap = replace(cap, source_revision="0" * 40)
    if failure == "wrong_variant":
        cap = replace(
            cap,
            producer_symbol="CarState.update"
            if platform == "HYUNDAI_IONIQ_5"
            else "CarState.update_canfd",
        )
    cfg = replace(cfg, attestation=replace(cfg.attestation, steering_pressed_capability=cap))
    if failure in ("wrong_brand", "wrong_static_flags"):
        ctx = replace(
            cfg.static_context,
            **({"brand": "mock"} if failure == "wrong_brand" else {"flags": 0}),
        )
        cfg = replace(
            cfg,
            static_context=ctx,
            snapshot_policy=replace(cfg.snapshot_policy, static_context_digest=ctx.digest),
            attestation=replace(
                cfg.attestation, static_context_digest=ctx.digest, platform_key=None
            ),
        )
    if failure == "wrong_platform":
        opposite = "HYUNDAI_SANTA_FE_2022" if platform == "HYUNDAI_IONIQ_5" else "HYUNDAI_IONIQ_5"
        cfg = replace(cfg, attestation=replace(cfg.attestation, platform_key=opposite))
    attempt, _ = complete()
    adapter = CarrotReadOnlyAdapter(cfg)
    cc, cs = car_control(log, attempt.source_command), car_state(log, attempt.source_car_state)
    # Leave the actual wire Bool at its default False. It is not a presence bit.
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    cached = adapter._states.lookup(cs.logMonoTime).evidence
    assert cached.steering_pressed is None and cached.steering_pressed_supported is False
    result = adapter.evaluate_car_output(
        sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
    )
    assert result.snapshot is None


@pytest.mark.parametrize(
    "failure", ["unseen", "dead", "invalid", "frequency", "not_updated", "event"]
)
def test_unhealthy_exact_source_never_makes_false_known(failure):
    cfg = hyundai_config("HYUNDAI_SANTA_FE_2022")
    attempt, _ = complete()
    adapter = CarrotReadOnlyAdapter(cfg)
    cc, cs = car_control(log, attempt.source_command), car_state(log, attempt.source_car_state)
    health = healthy()
    if failure == "event":
        cs.valid = False
    else:
        name = dict(
            unseen="seen", dead="alive", invalid="valid", frequency="freq_ok", not_updated="updated"
        )[failure]
        health = replace(health, **{name: False})
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs, health=health))
    cached = adapter._states.lookup(cs.logMonoTime).evidence
    assert cached.steering_pressed is None and cached.steering_pressed_supported is False
    result = adapter.evaluate_car_output(
        sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
    )
    assert result.snapshot is None


def test_hyundai_exact_cs_missing_cannot_use_current_latest_false():
    cfg = hyundai_config("HYUNDAI_SANTA_FE_2022")
    attempt, _ = complete()
    adapter = CarrotReadOnlyAdapter(cfg)
    cc, cs = car_control(log, attempt.source_command), car_state(log, attempt.source_car_state)
    cs.logMonoTime += 1
    adapter.ingest_car_control(sample(cc))
    adapter.ingest_car_state(sample(cs))
    result = adapter.evaluate_car_output(
        sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
    )
    assert result.snapshot is None and result.reason.value == "MISSING_SOURCE_CAR_STATE"
