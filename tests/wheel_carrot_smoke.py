"""Run explicitly against an installed wheel, outside its source checkout."""

import argparse
import runpy
import sys
from dataclasses import replace
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-fixture", required=True, type=Path)
    parser.add_argument("--reference-checkout", type=Path)
    args = parser.parse_args()
    import cyberpilot_autotune

    assert Path(sys.prefix) in Path(cyberpilot_autotune.__file__).resolve().parents
    from cyberpilot_autotune.integrations.carrot.adapter import (
        AdapterConfig,
        CachePolicy,
        CarrotReadOnlyAdapter,
        ProducerAttestation,
        SteeringPressedCapability,
    )
    from cyberpilot_autotune.integrations.carrot.availability import (
        INTEGRATION_MERGE,
        SCHEMA_REVISION,
        SOURCE_REVISION,
    )
    from cyberpilot_autotune.integrations.carrot.errors import CarrotDependencyUnavailable
    from cyberpilot_autotune.integrations.carrot.health import SessionToken

    fixture = runpy.run_path(str(args.contract_fixture))
    attempt, policy = fixture["complete"]()
    context = replace(attempt.static_context, brand="tesla")
    policy = replace(policy, static_context_digest=context.digest)
    attestation = ProducerAttestation(
        SOURCE_REVISION,
        INTEGRATION_MERGE,
        SCHEMA_REVISION,
        context.digest,
        policy.baseline_epoch,
        SessionToken(0, "0" * 32),
        policy.allowed_controller_kinds,
        SteeringPressedCapability(
            "opendbc_repo/opendbc/car/tesla/carstate.py", "CarState.update", SOURCE_REVISION
        ),
    )
    config = AdapterConfig(context, policy, fixture["BASELINE"], CachePolicy(2, 2, 2), attestation)
    if args.reference_checkout is None:
        try:
            CarrotReadOnlyAdapter(config)
        except CarrotDependencyUnavailable:
            print("OPTIONAL_DEPENDENCY_ERROR_VERIFIED")
        else:
            raise AssertionError("unexpected vehicle dependency in base wheel environment")
        return
    sys.path.insert(0, str(args.reference_checkout))
    # Only test helpers are loaded from the checkout; package must remain in
    # this fresh environment's site-packages (src layout does not shadow it).
    root = args.contract_fixture.resolve().parents[2]
    sys.path.insert(0, str(root))
    from openpilot.cereal import log

    from compatibility.carrot.builders import car_control, car_output, car_state, sample

    adapter = CarrotReadOnlyAdapter(config)
    adapter.ingest_car_control(sample(car_control(log, attempt.source_command)))
    adapter.ingest_car_state(sample(car_state(log, attempt.source_car_state)))
    result = adapter.evaluate_car_output(
        sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
    )
    assert (
        result.snapshot.source_valid and result.snapshot.baseline_parameters == fixture["BASELINE"]
    )
    assert result.snapshot.source_age_s == 0.1
    assert Path(sys.prefix) in Path(cyberpilot_autotune.__file__).resolve().parents
    print("ACTUAL_SCHEMA_WHEEL_MAPPING_VERIFIED")
    from tests.fixtures.carrot_adapter import hyundai_config

    for platform in ("HYUNDAI_SANTA_FE_2022", "HYUNDAI_IONIQ_5"):
        for pressed in (False, True):
            hyundai = CarrotReadOnlyAdapter(hyundai_config(platform))
            cc, cs = (
                car_control(log, attempt.source_command),
                car_state(log, attempt.source_car_state),
            )
            cs.carState.steeringPressed = pressed
            hyundai.ingest_car_control(sample(cc))
            hyundai.ingest_car_state(sample(cs))
            result = hyundai.evaluate_car_output(
                sample(car_output(log, attempt.receipt)), evaluation_mono_time_ns=10_010_000_000
            )
            assert result.snapshot.source_valid and result.snapshot.driver_override is pressed
            assert result.snapshot.baseline_parameters == fixture["BASELINE"]
    print("HYUNDAI_FALSE_TRUE_WHEEL_MAPPING_VERIFIED_4_CASES")


if __name__ == "__main__":
    main()
