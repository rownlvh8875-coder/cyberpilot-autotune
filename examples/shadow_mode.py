"""Synthetic only: not for vehicle use; no relationship to real tuning values."""

from cyberpilot_autotune.contracts import ObservationSnapshot, ParameterSpec, TuningProposal
from cyberpilot_autotune.core.no_op import NoOpLearner
from cyberpilot_autotune.runtime.clock import Clock
from cyberpilot_autotune.runtime.engine import AutoTuneEngine
from cyberpilot_autotune.runtime.mode import RuntimeMode
from cyberpilot_autotune.safety.gate import GateConfig, SafetyGate


class SyntheticClock:
    def now_s(self) -> float:
        return 10.0


def main() -> None:
    baseline = {"synthetic.test_only": 10.0}
    spec = ParameterSpec(
        "synthetic.test_only",
        "synthetic_unit",
        0,
        20,
        2,
        1,
        "Test only; not for vehicle use; unrelated to real tuning",
        False,
    )
    gate = SafetyGate({spec.parameter_id: spec}, GateConfig(1, 10, 0.8))
    snapshot = ObservationSnapshot(
        10, 1, 0, "synthetic/test-only", True, 2, 0.01, 0, None, False, False, baseline
    )
    clock: Clock = SyntheticClock()
    engine = AutoTuneEngine(
        mode=RuntimeMode.SHADOW,
        baseline_parameters=baseline,
        learner=NoOpLearner(),
        gate=gate,
        clock=clock,
    )
    result = engine.step(snapshot)
    # Demonstrate gate screening independently; NoOpLearner produces no proposals.
    proposal = TuningProposal(
        spec.parameter_id,
        10,
        10.5,
        0.9,
        20,
        snapshot.context_key,
        "manual-synthetic-v1",
        10,
        ("Demonstration only",),
    )
    decision = gate.evaluate(
        snapshot,
        proposal,
        now_s=10,
        baseline_parameters=baseline,
        previous_sequence=0,
        previous_timestamp_s=9,
    )
    print("Synthetic research example; NOT FOR VEHICLE USE")
    print("mode:", result.mode.value)
    print("baseline:", dict(result.baseline_parameters))
    print("NoOp proposals:", result.proposals)
    print("standalone synthetic proposal:", proposal.proposed_value)
    print("standalone gate decision:", decision.reason.value)
    print("effective:", dict(result.effective_parameters))
    print("effective == baseline:", result.effective_parameters == result.baseline_parameters)


if __name__ == "__main__":
    main()
