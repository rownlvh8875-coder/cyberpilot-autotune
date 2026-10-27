"""Synthetic research only: no relationship to real vehicle values or calibration."""

import json

from cyberpilot_autotune.contracts import ObservationSnapshot, ParameterSpec
from cyberpilot_autotune.core.residual import ResidualStatisticsConfig, ResidualStatisticsLearner
from cyberpilot_autotune.runtime.engine import AutoTuneEngine
from cyberpilot_autotune.runtime.mode import RuntimeMode
from cyberpilot_autotune.safety.gate import GateConfig, SafetyGate


class SyntheticClock:
    def __init__(self) -> None:
        self.value = 10.0

    def now_s(self) -> float:
        return self.value


def main() -> None:
    baseline = {"synthetic.test_only": 10.0}
    parameter = ParameterSpec(
        "synthetic.test_only",
        "synthetic_unit",
        0,
        20,
        2,
        1,
        "Test only; not for vehicle use; not a vehicle calibration",
        False,
    )
    config = ResidualStatisticsConfig(
        alpha=0.5,
        minimum_samples=3,
        maximum_samples=8,
        maximum_source_age_s=1,
        maximum_sample_gap_s=2,
        maximum_state_age_s=10,
        maximum_absolute_residual_inv_m=1,
        consistency_scale_inv_m=0.5,
        mean_deadband_inv_m=0.01,
        parameter_delta_per_inv_m=2,
    )
    learner = ResidualStatisticsLearner(parameter, config)
    clock = SyntheticClock()
    engine = AutoTuneEngine(
        mode=RuntimeMode.SHADOW,
        baseline_parameters=baseline,
        learner=learner,
        clock=clock,
        gate=SafetyGate({parameter.parameter_id: parameter}, GateConfig(1, 3, 0.8)),
    )
    for sequence in range(4):
        clock.value = 10.0 + sequence
        observation = ObservationSnapshot(
            timestamp_s=clock.value,
            sequence=sequence,
            source_age_s=0,
            context_key="synthetic/test-only",
            source_valid=True,
            speed_mps=2,
            desired_curvature_inv_m=0.25,
            measured_curvature_inv_m=0,
            lateral_acceleration_mps2=None,
            controller_saturated=False,
            driver_override=sequence == 3,
            baseline_parameters=baseline,
        )
        result = engine.step(observation)
        statistics = learner.statistics
        print(
            json.dumps(
                {
                    "scope": "SYNTHETIC_NOT_FOR_VEHICLE_USE",
                    "mode": result.mode.value,
                    "sequence": sequence,
                    "sample_count": statistics.sample_count if statistics else 0,
                    "confidence": statistics.confidence if statistics else None,
                    "proposal": result.proposals[0].proposed_value if result.proposals else None,
                    "gate": result.gate_decisions[0].reason.value
                    if result.gate_decisions
                    else None,
                    "baseline": dict(result.baseline_parameters),
                    "effective": dict(result.effective_parameters),
                    "effective_equals_baseline": result.effective_parameters
                    == result.baseline_parameters,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
